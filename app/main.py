# Streamlined Whisper Transcriber
# Mobile-first, modern transcription service

from contextlib import asynccontextmanager
from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, WebSocket, WebSocketDisconnect, Request, status
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.security.utils import get_authorization_scheme_param
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, Boolean
from sqlalchemy.orm import sessionmaker, Session, declarative_base
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, ValidationError
import uuid
import os
import json
import asyncio
import magic
import hashlib
import logging
import logging.config
import psutil
import time
from pathlib import Path
from typing import Optional, List, Dict, Set
import logging

# Import security components
from schemas import (
    UserRegistrationSchema, UserLoginSchema, PasswordChangeSchema,
    FileUploadSchema, JobQuerySchema, JobIdSchema,
    TokenResponseSchema, UserResponseSchema, JobResponseSchema,
    ErrorResponseSchema, HealthResponseSchema, MetricsResponseSchema,
    create_validation_error_response, validate_request_size
)
from rate_limiter import RateLimitMiddleware, RateLimitConfig, create_development_rate_limiter
from security_middleware import SecurityMiddleware, create_development_security_middleware, security_logger

# Setup paths
BASE_DIR = Path(__file__).parent.parent
STORAGE_DIR = BASE_DIR / "storage"
UPLOADS_DIR = STORAGE_DIR / "uploads"
TRANSCRIPTS_DIR = STORAGE_DIR / "transcripts"
DATABASE_URL = f"sqlite:///{BASE_DIR}/app.db"

# Environment configuration
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "").split(",") if os.getenv("ALLOWED_ORIGINS") else []

# File upload security configuration
MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE", "104857600"))  # 100MB default
MAX_FILENAME_LENGTH = int(os.getenv("MAX_FILENAME_LENGTH", "255"))
UPLOAD_TIMEOUT = int(os.getenv("UPLOAD_TIMEOUT", "300"))  # 5 minutes default

# Allowed audio file types (MIME types and magic number signatures)
ALLOWED_AUDIO_TYPES = {
    # Common audio formats
    "audio/mpeg": [b"\xff\xfb", b"\xff\xf3", b"\xff\xf2", b"ID3"],  # MP3
    "audio/wav": [b"RIFF", b"WAVE"],  # WAV
    "audio/x-wav": [b"RIFF", b"WAVE"],  # WAV alternative
    "audio/flac": [b"fLaC"],  # FLAC
    "audio/ogg": [b"OggS"],  # OGG
    "audio/mp4": [b"ftyp"],  # M4A/MP4 audio
    "audio/x-m4a": [b"ftyp"],  # M4A
    "audio/aac": [b"\xff\xf1", b"\xff\xf9"],  # AAC
    "audio/webm": [b"\x1a\x45\xdf\xa3"],  # WebM audio
    "audio/3gpp": [b"ftyp3gp"],  # 3GP
    "audio/amr": [b"#!AMR"],  # AMR
}

# Allowed file extensions (as backup check)
ALLOWED_EXTENSIONS: Set[str] = {
    ".mp3", ".wav", ".flac", ".ogg", ".m4a", ".aac", ".webm", ".3gp", ".amr", ".opus"
}

# CORS configuration based on environment
def get_cors_origins():
    """Get CORS origins based on environment and configuration."""
    if ENVIRONMENT == "production":
        # Production: Only allow explicitly configured origins
        if not ALLOWED_ORIGINS or ALLOWED_ORIGINS == [""]:
            # If no origins configured, use restrictive defaults
            return ["https://localhost:8000", "https://127.0.0.1:8000"]
        return [origin.strip() for origin in ALLOWED_ORIGINS if origin.strip()]
    else:
        # Development: Allow localhost and configured origins
        dev_origins = [
            "http://localhost:3000",  # React dev server
            "http://localhost:8000",  # FastAPI server
            "http://127.0.0.1:3000",
            "http://127.0.0.1:8000",
        ]
        if ALLOWED_ORIGINS and ALLOWED_ORIGINS != [""]:
            dev_origins.extend(origin.strip() for origin in ALLOWED_ORIGINS if origin.strip())
        return dev_origins

# Authentication configuration
SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
ALLOW_REGISTRATION = os.getenv("ALLOW_REGISTRATION", "true").lower() == "true"

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme for token URL
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Logging configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT = os.getenv("LOG_FORMAT", "standard")  # standard or json

def setup_logging():
    """Configure structured logging based on environment."""
    
    if LOG_FORMAT.lower() == "json":
        # JSON logging for production/monitoring
        logging_config = {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "json": {
                    "format": "%(asctime)s %(name)s %(levelname)s %(message)s",
                    "class": "pythonjsonlogger.jsonlogger.JsonFormatter"
                }
            },
            "handlers": {
                "default": {
                    "formatter": "json",
                    "class": "logging.StreamHandler",
                    "stream": "ext://sys.stdout"
                }
            },
            "root": {
                "level": LOG_LEVEL,
                "handlers": ["default"]
            },
            "loggers": {
                "uvicorn": {"level": LOG_LEVEL},
                "uvicorn.error": {"level": LOG_LEVEL},
                "uvicorn.access": {"level": LOG_LEVEL},
                "sqlalchemy": {"level": "WARNING"},
                "app": {"level": LOG_LEVEL}
            }
        }
    else:
        # Standard logging for development
        logging_config = {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "standard": {
                    "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
                }
            },
            "handlers": {
                "default": {
                    "formatter": "standard",
                    "class": "logging.StreamHandler",
                    "stream": "ext://sys.stdout"
                }
            },
            "root": {
                "level": LOG_LEVEL,
                "handlers": ["default"]
            }
        }
    
    logging.config.dictConfig(logging_config)
    return logging.getLogger("app")

# Initialize logging
logger = setup_logging()

class FileValidationError(Exception):
    """Custom exception for file validation errors."""
    pass

async def validate_uploaded_file(file: UploadFile) -> bytes:
    """
    Comprehensive file validation for security.
    
    Validates:
    - File size limits
    - Filename safety
    - MIME type verification
    - Magic number validation
    - File extension allowlist
    
    Returns:
        bytes: File content if validation passes
        
    Raises:
        FileValidationError: If validation fails
    """
    # Check filename length and safety
    if not file.filename:
        raise FileValidationError("Filename is required")
    
    if len(file.filename) > MAX_FILENAME_LENGTH:
        raise FileValidationError(f"Filename too long (max {MAX_FILENAME_LENGTH} characters)")
    
    # Check for dangerous filename patterns
    dangerous_patterns = ["../", "..\\", "/", "\\", "|", "&", ";", "$", "`", "~"]
    if any(pattern in file.filename for pattern in dangerous_patterns):
        raise FileValidationError("Filename contains invalid characters")
    
    # Check file extension
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        allowed = ", ".join(sorted(ALLOWED_EXTENSIONS))
        raise FileValidationError(f"Invalid file extension. Allowed: {allowed}")
    
    # Read file content with size limit
    content = b""
    total_size = 0
    
    while chunk := await file.read(8192):  # Read in 8KB chunks
        total_size += len(chunk)
        if total_size > MAX_FILE_SIZE:
            raise FileValidationError(f"File too large (max {MAX_FILE_SIZE // 1024 // 1024}MB)")
        content += chunk
    
    # Reset file pointer for potential re-reading
    await file.seek(0)
    
    # Validate minimum file size (empty files are suspicious)
    if len(content) < 100:
        raise FileValidationError("File too small (minimum 100 bytes)")
    
    # Validate MIME type against content-type header
    if not file.content_type or not file.content_type.startswith('audio/'):
        raise FileValidationError("Invalid content type. Must be audio file")
    
    # Magic number validation - verify file signature
    try:
        file_type = magic.from_buffer(content[:2048], mime=True)
        
        # Check if detected MIME type is in our allowlist
        if file_type not in ALLOWED_AUDIO_TYPES:
            raise FileValidationError(f"Unsupported file type detected: {file_type}")
        
        # Verify magic numbers match expected signatures
        magic_signatures = ALLOWED_AUDIO_TYPES[file_type]
        content_start = content[:20]  # Check first 20 bytes
        
        if not any(content_start.startswith(sig) for sig in magic_signatures):
            raise FileValidationError(f"File signature does not match expected format for {file_type}")
            
    except Exception as e:
        if isinstance(e, FileValidationError):
            raise
        raise FileValidationError(f"File type validation failed: {str(e)}")
    
    # Generate secure hash for deduplication/integrity
    file_hash = hashlib.sha256(content).hexdigest()
    logging.info(f"File validated: {file.filename}, size: {len(content)} bytes, hash: {file_hash[:16]}...")
    
    return content

def sanitize_filename(filename: str) -> str:
    """Create a safe filename for storage."""
    # Remove path components and dangerous characters
    safe_name = Path(filename).name
    # Remove all potentially dangerous characters, keep only alphanumeric, dots, dashes, underscores
    safe_name = "".join(c for c in safe_name if c.isalnum() or c in ".-_")
    # Remove any remaining path separators that might have slipped through
    safe_name = safe_name.replace("/", "").replace("\\", "").replace("..", "")
    
    # Ensure reasonable length
    if len(safe_name) > 100:
        # If there's an extension, preserve it
        if "." in safe_name:
            parts = safe_name.rsplit(".", 1)
            if len(parts) == 2 and len(parts[1]) <= 10:  # Valid extension
                name_part = parts[0][:90]
                ext_part = "." + parts[1]
                safe_name = name_part + ext_part
            else:
                safe_name = safe_name[:100]
        else:
            safe_name = safe_name[:100]
    
    return safe_name or "upload"

# Ensure directories exist
STORAGE_DIR.mkdir(exist_ok=True)
UPLOADS_DIR.mkdir(exist_ok=True)
TRANSCRIPTS_DIR.mkdir(exist_ok=True)

# Database setup
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Models
class Job(Base):
    __tablename__ = "jobs"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    filename = Column(String, nullable=False)
    original_filename = Column(String, nullable=False)
    status = Column(String, default="pending")  # pending, processing, completed, failed
    transcript = Column(Text)
    model_used = Column(String, default="small")
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    error_message = Column(Text)
    file_size = Column(Integer)
    duration = Column(Integer)  # seconds

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String, default="user")  # user, admin
    must_change_password = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

# Pydantic schemas for API
from pydantic import BaseModel

class TokenOut(BaseModel):
    access_token: str
    token_type: str

class TokenLoginOut(BaseModel):
    access_token: str
    token_type: str
    must_change_password: bool

class PasswordChangeIn(BaseModel):
    password: str

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, job_id: str):
        await websocket.accept()
        if job_id not in self.active_connections:
            self.active_connections[job_id] = []
        self.active_connections[job_id].append(websocket)

    def disconnect(self, websocket: WebSocket, job_id: str):
        if job_id in self.active_connections:
            self.active_connections[job_id].remove(websocket)
            if not self.active_connections[job_id]:
                del self.active_connections[job_id]

    async def send_progress(self, job_id: str, data: dict):
        if job_id in self.active_connections:
            for connection in self.active_connections[job_id][:]:  # Copy list to avoid modification during iteration
                try:
                    await connection.send_json(data)
                except:
                    self.active_connections[job_id].remove(connection)

manager = ConnectionManager()

# Dependency to get database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Authentication utility functions
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a hashed password."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hash a password."""
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_user_by_username(db: Session, username: str) -> Optional[User]:
    """Get user by username."""
    return db.query(User).filter(User.username == username).first()

def create_user(db: Session, username: str, password: str, role: str = "user", must_change_password: bool = False) -> User:
    """Create a new user."""
    hashed_password = get_password_hash(password)
    user = User(
        username=username,
        password_hash=hashed_password,
        role=role,
        must_change_password=must_change_password
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

async def get_token(request: Request = None, websocket: WebSocket = None) -> str:
    """Get JWT token from request or websocket."""
    if request is not None:
        authorization: str = request.headers.get("Authorization")
        scheme, token = get_authorization_scheme_param(authorization)
        if not authorization or scheme.lower() != "bearer":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return token
    
    # WebSocket token extraction
    if websocket is not None:
        token = websocket.query_params.get("token")
        if not token:
            authorization = websocket.headers.get("Authorization")
            scheme, token = get_authorization_scheme_param(authorization)
            if not authorization or scheme.lower() != "bearer":
                raise HTTPException(status_code=401, detail="Not authenticated")
        return token
    
    raise HTTPException(status_code=401, detail="Not authenticated")

async def get_current_user(token: str = Depends(get_token), db: Session = Depends(get_db)) -> User:
    """Get current user from JWT token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = get_user_by_username(db, username)
    if user is None:
        raise credentials_exception
    
    return user

def require_admin(user: User = Depends(get_current_user)) -> User:
    """Require admin role."""
    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return user

# Lifespan manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    Base.metadata.create_all(bind=engine)
    logging.info("Database initialized")
    yield
    # Shutdown
    logging.info("Application shutting down")

# Create FastAPI app
app = FastAPI(
    title="Whisper Transcriber",
    description="Modern, mobile-first audio transcription service",
    version="2.0.0",
    lifespan=lifespan
)

# CORS middleware for web frontend
cors_origins = get_cors_origins()
logging.info(f"CORS configured for environment: {ENVIRONMENT}")
logging.info(f"Allowed origins: {cors_origins}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Security middleware for request validation and attack prevention
if ENVIRONMENT == "production":
    # Strict security for production
    security_config = {
        "max_request_size": 52428800,  # 50MB
        "max_json_depth": 5,
        "max_array_length": 100
    }
    app.add_middleware(SecurityMiddleware, config=security_config)
    
    # Strict rate limiting for production
    from rate_limiter import create_strict_rate_limiter
    app.add_middleware(create_strict_rate_limiter())
else:
    # Development-friendly settings
    app.add_middleware(create_development_security_middleware())
    app.add_middleware(create_development_rate_limiter())

logger.info(f"Security middleware configured for {ENVIRONMENT} environment")

# Mount static files (will serve the React frontend)
if (BASE_DIR / "web" / "dist").exists():
    app.mount("/static", StaticFiles(directory=BASE_DIR / "web" / "dist"), name="static")

# Routes
@app.get("/")
async def root():
    """Health check and basic info - redirect to /health for detailed status"""
    return {
        "service": "Whisper Transcriber",
        "version": "2.0.0",
        "status": "online",
        "features": ["audio-upload", "real-time-progress", "mobile-friendly", "monitoring"],
        "endpoints": {
            "health": "/health",
            "metrics": "/metrics (admin only)",
            "stats": "/stats (authenticated users)"
        }
    }

# Authentication endpoints
@app.post("/token", response_model=TokenResponseSchema)
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(), 
    db: Session = Depends(get_db)
):
    """Secure login endpoint with validation and security logging"""
    try:
        # Validate login data using secure schema
        login_data = UserLoginSchema(
            username=form_data.username,
            password=form_data.password
        )
        
        # Get client IP for security logging
        client_ip = request.client.host if request.client else "unknown"
        
        user = get_user_by_username(db, login_data.username)
        if not user or not verify_password(login_data.password, user.password_hash):
            # Log authentication failure
            security_logger.log_authentication_failure(
                client_ip=client_ip,
                username=login_data.username,
                failure_reason="invalid_credentials"
            )
            
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        access_token = create_access_token(
            data={"sub": user.username, "role": user.role}
        )
        
        # Log successful login
        logger.info(f"Successful login for user: {user.username} from IP: {client_ip}")
        
        return TokenResponseSchema(
            access_token=access_token,
            token_type="bearer",
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )
        
    except ValidationError as e:
        # Log validation error attempt
        security_logger.log_attack_attempt(
            attack_type="validation_bypass",
            client_ip=request.client.host if request.client else "unknown",
            user_agent=request.headers.get("user-agent", "unknown"),
            payload=str(form_data.username)[:200],
            request_path="/token"
        )
        
        error_response = create_validation_error_response(e)
        raise HTTPException(status_code=400, detail=error_response)

@app.post("/register", response_model=TokenResponseSchema, status_code=status.HTTP_201_CREATED)
async def register(
    request: Request,
    registration_data: UserRegistrationSchema, 
    db: Session = Depends(get_db)
):
    """Secure user registration with comprehensive validation"""
    try:
        if not ALLOW_REGISTRATION:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Registration disabled"
            )
        
        client_ip = request.client.host if request.client else "unknown"
        
        # Check if user already exists
        existing_user = get_user_by_username(db, registration_data.username)
        if existing_user:
            security_logger.log_suspicious_activity(
                activity_type="duplicate_registration_attempt",
                client_ip=client_ip,
                details={"username": registration_data.username}
            )
            
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User already exists"
            )
        
        # Create new user with validated data
        user = create_user(
            db, 
            registration_data.username, 
            registration_data.password,
            is_admin=registration_data.is_admin
        )
        
        # Create access token
        access_token = create_access_token(
            data={"sub": user.username, "role": user.role}
        )
        
        logger.info(f"New user registered: {user.username} from IP: {client_ip}")
        
        return TokenResponseSchema(
            access_token=access_token, 
            token_type="bearer",
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )
        
    except ValidationError as e:
        security_logger.log_attack_attempt(
            attack_type="registration_validation_bypass",
            client_ip=request.client.host if request.client else "unknown",
            user_agent=request.headers.get("user-agent", "unknown"),
            payload=str(registration_data.dict() if hasattr(registration_data, 'dict') else registration_data)[:200],
            request_path="/register"
        )
        
        error_response = create_validation_error_response(e)
        raise HTTPException(status_code=400, detail=error_response)

@app.post("/change-password", status_code=status.HTTP_204_NO_CONTENT)
async def change_password(
    request: Request,
    password_data: PasswordChangeSchema,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Secure password change with validation"""
    try:
        client_ip = request.client.host if request.client else "unknown"
        
        # Verify current password
        if not verify_password(password_data.current_password, current_user.password_hash):
            security_logger.log_authentication_failure(
                client_ip=client_ip,
                username=current_user.username,
                failure_reason="invalid_current_password"
            )
            
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Current password is incorrect"
            )
        
        # Update password with validated new password
        current_user.password_hash = get_password_hash(password_data.new_password)
        current_user.must_change_password = False
        db.commit()
        
        logger.info(f"Password changed for user: {current_user.username} from IP: {client_ip}")
        
        return {"message": "Password changed successfully"}
        
    except ValidationError as e:
        security_logger.log_attack_attempt(
            attack_type="password_change_validation_bypass", 
            client_ip=client_ip,
            user_agent=request.headers.get("user-agent", "unknown"),
            payload="[password change attempt]",
            request_path="/change-password"
        )
        
        error_response = create_validation_error_response(e)
        raise HTTPException(status_code=400, detail=error_response)

# Health and monitoring endpoints
@app.get("/health", response_model=HealthResponseSchema)
async def health_check(db: Session = Depends(get_db)):
    """Secure health check endpoint with validation"""
    try:
        # Test database connectivity
        from sqlalchemy import text
        db.execute(text("SELECT 1"))
        
        return HealthResponseSchema(
            status="healthy",
            version="2.0.0",
            timestamp=datetime.utcnow()
        )
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(status_code=503, detail="Service unhealthy")

@app.get("/metrics")
async def get_metrics(current_user: User = Depends(require_admin), db: Session = Depends(get_db)):
    """Detailed system metrics for monitoring"""
    try:
        # System metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Database metrics
        jobs_total = db.query(Job).count()
        jobs_pending = db.query(Job).filter(Job.status == "pending").count()
        jobs_processing = db.query(Job).filter(Job.status == "processing").count()
        jobs_completed = db.query(Job).filter(Job.status == "completed").count()
        jobs_failed = db.query(Job).filter(Job.status == "failed").count()
        
        # User metrics
        users_total = db.query(User).count()
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "system": {
                "cpu_percent": cpu_percent,
                "memory": {
                    "total": memory.total,
                    "available": memory.available,
                    "percent": memory.percent,
                    "used": memory.used
                },
                "disk": {
                    "total": disk.total,
                    "used": disk.used,
                    "free": disk.free,
                    "percent": (disk.used / disk.total) * 100
                }
            },
            "application": {
                "jobs": {
                    "total": jobs_total,
                    "pending": jobs_pending,
                    "processing": jobs_processing,
                    "completed": jobs_completed,
                    "failed": jobs_failed
                },
                "users": {
                    "total": users_total
                }
            },
            "storage": {
                "uploads_dir": str(UPLOADS_DIR),
                "transcripts_dir": str(TRANSCRIPTS_DIR)
            }
        }
    except Exception as e:
        logger.error(f"Metrics collection failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Metrics collection failed")

@app.get("/stats")
async def get_stats(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """User-accessible statistics"""
    try:
        # Get user's job statistics
        user_jobs_total = db.query(Job).count()  # In real app, filter by user
        user_jobs_completed = db.query(Job).filter(Job.status == "completed").count()
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "user_stats": {
                "jobs_total": user_jobs_total,
                "jobs_completed": user_jobs_completed,
                "success_rate": (user_jobs_completed / user_jobs_total * 100) if user_jobs_total > 0 else 0
            },
            "system_stats": {
                "service_uptime": "Available via /metrics (admin only)",
                "version": "2.0.0"
            }
        }
    except Exception as e:
        logger.error(f"Stats collection failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Stats collection failed")

@app.get("/dashboard")
async def monitoring_dashboard(current_user: User = Depends(require_admin)):
    """Simple monitoring dashboard (HTML)"""
    dashboard_html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Whisper Transcriber - Monitoring Dashboard</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
            .container { max-width: 1200px; margin: 0 auto; }
            .card { background: white; padding: 20px; margin: 10px 0; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
            .metric { display: inline-block; margin: 10px 20px 10px 0; }
            .metric-value { font-size: 2em; font-weight: bold; color: #007bff; }
            .metric-label { font-size: 0.9em; color: #666; }
            .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }
            .status-good { color: #28a745; }
            .status-warning { color: #ffc107; }
            .status-danger { color: #dc3545; }
        </style>
        <script>
            async function loadMetrics() {
                try {
                    const response = await fetch('/metrics');
                    const data = await response.json();
                    
                    // Update system metrics
                    document.getElementById('cpu-usage').textContent = data.system.cpu_percent.toFixed(1) + '%';
                    document.getElementById('memory-usage').textContent = data.system.memory.percent.toFixed(1) + '%';
                    document.getElementById('disk-usage').textContent = data.system.disk.percent.toFixed(1) + '%';
                    
                    // Update job metrics
                    document.getElementById('jobs-total').textContent = data.application.jobs.total;
                    document.getElementById('jobs-pending').textContent = data.application.jobs.pending;
                    document.getElementById('jobs-processing').textContent = data.application.jobs.processing;
                    document.getElementById('jobs-completed').textContent = data.application.jobs.completed;
                    document.getElementById('jobs-failed').textContent = data.application.jobs.failed;
                    
                    // Update timestamp
                    document.getElementById('last-updated').textContent = new Date(data.timestamp).toLocaleString();
                    
                } catch (error) {
                    console.error('Failed to load metrics:', error);
                }
            }
            
            // Load metrics every 30 seconds
            setInterval(loadMetrics, 30000);
            loadMetrics(); // Initial load
        </script>
    </head>
    <body>
        <div class="container">
            <h1>🎤 Whisper Transcriber - Monitoring Dashboard</h1>
            <p>Real-time system and application metrics</p>
            
            <div class="grid">
                <div class="card">
                    <h3>System Resources</h3>
                    <div class="metric">
                        <div class="metric-value" id="cpu-usage">-</div>
                        <div class="metric-label">CPU Usage</div>
                    </div>
                    <div class="metric">
                        <div class="metric-value" id="memory-usage">-</div>
                        <div class="metric-label">Memory Usage</div>
                    </div>
                    <div class="metric">
                        <div class="metric-value" id="disk-usage">-</div>
                        <div class="metric-label">Disk Usage</div>
                    </div>
                </div>
                
                <div class="card">
                    <h3>Transcription Jobs</h3>
                    <div class="metric">
                        <div class="metric-value" id="jobs-total">-</div>
                        <div class="metric-label">Total Jobs</div>
                    </div>
                    <div class="metric">
                        <div class="metric-value status-warning" id="jobs-pending">-</div>
                        <div class="metric-label">Pending</div>
                    </div>
                    <div class="metric">
                        <div class="metric-value status-warning" id="jobs-processing">-</div>
                        <div class="metric-label">Processing</div>
                    </div>
                    <div class="metric">
                        <div class="metric-value status-good" id="jobs-completed">-</div>
                        <div class="metric-label">Completed</div>
                    </div>
                    <div class="metric">
                        <div class="metric-value status-danger" id="jobs-failed">-</div>
                        <div class="metric-label">Failed</div>
                    </div>
                </div>
            </div>
            
            <div class="card">
                <h3>Quick Actions</h3>
                <p>
                    <a href="/metrics" target="_blank">📊 Raw Metrics JSON</a> |
                    <a href="/health" target="_blank">❤️ Health Check</a> |
                    <a href="/stats" target="_blank">📈 User Stats</a>
                </p>
                <p><small>Last updated: <span id="last-updated">Loading...</span></small></p>
            </div>
        </div>
    </body>
    </html>
    """
    
    from fastapi.responses import HTMLResponse
    return HTMLResponse(content=dashboard_html)

@app.post("/transcribe", response_model=JobResponseSchema)
async def create_transcription(
    request: Request,
    file: UploadFile = File(...),
    model: str = "small",
    language: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Secure audio file upload and transcription with comprehensive validation"""
    
    start_time = time.time()
    client_ip = request.client.host if request.client else "unknown"
    
    try:
        # Validate upload parameters using secure schema
        upload_data = FileUploadSchema(
            filename=file.filename,
            model=model,
            language=language
        )
        
        # Validate request size
        content_length = request.headers.get('content-length')
        if content_length:
            validate_request_size(int(content_length))
        
        # Log upload attempt with security context
        logger.info(f"Secure transcription request started", extra={
            "user": current_user.username,
            "filename": upload_data.filename,
            "model": upload_data.model,
            "language": upload_data.language,
            "client_ip": client_ip,
            "file_size": file.size if hasattr(file, 'size') else None
        })
        
        # Comprehensive file validation with security checks
        content = await validate_uploaded_file(file)
        
        # Create secure filename
        safe_filename = sanitize_filename(file.filename)
        job_id = str(uuid.uuid4())
        storage_filename = f"{job_id}_{safe_filename}"
        file_path = UPLOADS_DIR / storage_filename
        
        # Save validated file
        with open(file_path, "wb") as f:
            f.write(content)
        
        # Create database record with security metadata
        job = Job(
            id=job_id,
            filename=storage_filename,
            original_filename=upload_data.filename,
            model_used=upload_data.model,
            file_size=len(content),
            status="pending"
        )
        db.add(job)
        db.commit()
        
        # Log security event
        upload_duration = time.time() - start_time
        logger.info(f"Secure file upload completed", extra={
            "job_id": job_id,
            "original_filename": upload_data.filename,
            "file_size": len(content),
            "content_type": file.content_type,
            "upload_duration": upload_duration,
            "user": current_user.username,
            "client_ip": client_ip
        })
        
        # Queue transcription job (using Celery)
        from worker import transcribe_audio
        task = transcribe_audio.delay(job_id)
        
        return JobResponseSchema(
            id=job_id,
            filename=upload_data.filename,
            status="pending",
            model_used=upload_data.model,
            created_at=job.created_at,
            completed_at=None,
            file_size=len(content),
            error_message=None
        )
        
    except ValidationError as e:
        # Schema validation failed
        security_logger.log_attack_attempt(
            attack_type="file_upload_validation_bypass",
            client_ip=client_ip,
            user_agent=request.headers.get("user-agent", "unknown"),
            payload=f"file:{file.filename}, model:{model}",
            request_path="/transcribe"
        )
        
        error_response = create_validation_error_response(e)
        raise HTTPException(status_code=400, detail=error_response)
        
    except FileValidationError as e:
        # Security file validation failed
        upload_duration = time.time() - start_time
        
        security_logger.log_attack_attempt(
            attack_type="malicious_file_upload",
            client_ip=client_ip,
            user_agent=request.headers.get("user-agent", "unknown"),
            payload=f"file:{file.filename}, size:{file.size if hasattr(file, 'size') else 'unknown'}",
            request_path="/transcribe"
        )
        
        logger.warning(f"File validation failed", extra={
            "filename": file.filename,
            "error": str(e),
            "user": current_user.username,
            "client_ip": client_ip,
            "upload_duration": upload_duration
        })
        raise HTTPException(status_code=400, detail=f"File validation failed: {str(e)}")
    
    except Exception as e:
        # Unexpected error during upload
        upload_duration = time.time() - start_time
        logger.error(f"Upload error", extra={
            "filename": file.filename,
            "error": str(e),
            "user": current_user.username,
            "upload_duration": upload_duration
        })
        raise HTTPException(status_code=500, detail="File upload failed")

@app.get("/jobs/{job_id}")
async def get_job(job_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get job status and details"""
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return {
        "job_id": job.id,
        "filename": job.original_filename,
        "status": job.status,
        "model_used": job.model_used,
        "created_at": job.created_at.isoformat(),
        "completed_at": job.completed_at.isoformat() if job.completed_at else None,
        "file_size": job.file_size,
        "duration": job.duration,
        "error_message": job.error_message,
        "has_transcript": bool(job.transcript)
    }

@app.get("/jobs/{job_id}/download")
async def download_transcript(job_id: str, format: str = "txt", current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Download completed transcript"""
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job.status != "completed" or not job.transcript:
        raise HTTPException(status_code=400, detail="Transcript not ready")
    
    # Create transcript file
    if format == "json":
        content = json.dumps({"transcript": job.transcript, "metadata": {
            "filename": job.original_filename,
            "model": job.model_used,
            "duration": job.duration
        }}, indent=2)
        media_type = "application/json"
        extension = "json"
    else:  # txt format
        content = job.transcript
        media_type = "text/plain"
        extension = "txt"
    
    filename = f"{job.original_filename.rsplit('.', 1)[0]}_transcript.{extension}"
    
    # Save to transcripts directory
    transcript_path = TRANSCRIPTS_DIR / f"{job_id}.{extension}"
    with open(transcript_path, "w", encoding="utf-8") as f:
        f.write(content)
    
    return FileResponse(
        transcript_path,
        media_type=media_type,
        filename=filename
    )

@app.get("/jobs", response_model=List[JobResponseSchema])
async def list_jobs(
    request: Request,
    limit: Optional[int] = 20,
    offset: Optional[int] = 0,
    status: Optional[str] = None,
    current_user: User = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    """List jobs with secure pagination and filtering"""
    try:
        # Validate query parameters using secure schema
        query_params = JobQuerySchema(
            limit=limit,
            offset=offset,
            status=status
        )
        
        # Build query with security context
        query = db.query(Job).order_by(Job.created_at.desc())
        
        # Apply status filter if provided
        if query_params.status:
            query = query.filter(Job.status == query_params.status)
        
        # Apply pagination with security limits
        jobs = query.offset(query_params.offset).limit(query_params.limit).all()
        
        # Return sanitized job data
        return [
            JobResponseSchema(
                id=job.id,
                filename=job.original_filename,
                status=job.status,
                model_used=job.model_used,
                created_at=job.created_at,
                completed_at=job.completed_at,
                file_size=job.file_size,
                error_message=job.error_message
            )
            for job in jobs
        ]
        
    except ValidationError as e:
        client_ip = request.client.host if request.client else "unknown"
        security_logger.log_attack_attempt(
            attack_type="job_query_validation_bypass",
            client_ip=client_ip,
            user_agent=request.headers.get("user-agent", "unknown"),
            payload=f"limit:{limit}, offset:{offset}, status:{status}",
            request_path="/jobs"
        )
        
        error_response = create_validation_error_response(e)
        raise HTTPException(status_code=400, detail=error_response)

@app.delete("/jobs/{job_id}")
async def delete_job(
    request: Request,
    job_id: str, 
    current_user: User = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    """Securely delete a job and its files with validation"""
    try:
        # Validate job ID format
        validated_id = JobIdSchema(job_id=job_id)
        
        client_ip = request.client.host if request.client else "unknown"
        
        job = db.query(Job).filter(Job.id == validated_id.job_id).first()
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        # Delete files securely
        upload_path = UPLOADS_DIR / job.filename
        if upload_path.exists():
            upload_path.unlink()
        
        transcript_path = TRANSCRIPTS_DIR / f"{validated_id.job_id}.txt"
        if transcript_path.exists():
            transcript_path.unlink()
        
        # Delete database record
        db.delete(job)
        db.commit()
        
        logger.info(f"Job deleted: {validated_id.job_id} by user: {current_user.username} from IP: {client_ip}")
        
        return {"message": "Job deleted successfully"}
        
    except ValidationError as e:
        client_ip = request.client.host if request.client else "unknown"
        security_logger.log_attack_attempt(
            attack_type="job_id_validation_bypass",
            client_ip=client_ip,
            user_agent=request.headers.get("user-agent", "unknown"),
            payload=job_id,
            request_path=f"/jobs/{job_id}"
        )
        
        error_response = create_validation_error_response(e)
        raise HTTPException(status_code=400, detail=error_response)

@app.websocket("/ws/jobs/{job_id}")
async def websocket_job_progress(websocket: WebSocket, job_id: str):
    """Real-time job progress updates"""
    # Authenticate WebSocket connection
    try:
        token = await get_token(websocket=websocket)
        # We could validate the token here, but for simplicity we'll just check it exists
        # In production, you might want to decode and validate the token
        if not token:
            await websocket.close(code=1008, reason="Authentication required")
            return
    except:
        await websocket.close(code=1008, reason="Authentication failed")
        return
    
    await manager.connect(websocket, job_id)
    try:
        while True:
            # Keep connection alive and listen for disconnect
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket, job_id)

# Simplified transcription processor (will be moved to Celery later)
async def process_transcription(job_id: str):
    """Process transcription job"""
    db = SessionLocal()
    try:
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            return
        
        # Update status
        job.status = "processing"
        db.commit()
        
        await manager.send_progress(job_id, {
            "status": "processing",
            "progress": 0,
            "message": "Starting transcription..."
        })
        
        # Simulate transcription process (replace with actual Whisper)
        await asyncio.sleep(2)  # Simulate processing time
        
        await manager.send_progress(job_id, {
            "status": "processing",
            "progress": 50,
            "message": "Processing audio..."
        })
        
        await asyncio.sleep(3)  # More processing
        
        # Mock transcript (replace with actual Whisper result)
        job.transcript = f"This is a mock transcript for {job.original_filename}. In the real implementation, this would be generated by Whisper."
        job.status = "completed"
        job.completed_at = datetime.utcnow()
        job.duration = 120  # Mock duration
        db.commit()
        
        await manager.send_progress(job_id, {
            "status": "completed",
            "progress": 100,
            "message": "Transcription completed!",
            "transcript": job.transcript
        })
        
    except Exception as e:
        job.status = "failed"
        job.error_message = str(e)
        db.commit()
        
        await manager.send_progress(job_id, {
            "status": "failed",
            "progress": 0,
            "message": f"Transcription failed: {str(e)}"
        })
    finally:
        db.close()

if __name__ == "__main__":
    import uvicorn
    
    # Get configuration from environment
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    
    # Setup basic logging for startup
    logging.basicConfig(level=logging.INFO)
    logging.info(f"Starting Whisper Transcriber on {host}:{port}")
    logging.info(f"Environment: {ENVIRONMENT}")
    
    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        reload=ENVIRONMENT == "development",
        log_level="info" if ENVIRONMENT == "production" else "debug"
    )
