# File Upload Security - Usage Examples

## Basic Usage in FastAPI Routes

```python
from fastapi import FastAPI, UploadFile, Depends
from api.middlewares.secure_file_upload import validate_audio_upload, AudioUploadValidator

app = FastAPI()

# Method 1: Direct validation
@app.post("/upload-audio/")
async def upload_audio_file(file: UploadFile):
    try:
        result = await validate_audio_upload(file, "./uploads/audio")
        return {"message": "File uploaded successfully", "file_info": result}
    except HTTPException as e:
        return {"error": e.detail}

# Method 2: Using dependency injection
@app.post("/transcribe/")
async def transcribe_audio(file_info: dict = Depends(AudioUploadValidator())):
    # file_info contains validated file information
    file_path = file_info["file_path"]
    # Process the validated file...
    return {"status": "processing", "file": file_info}
```

## Customizing Security Configuration

```python
from api.utils.file_upload_security import FileSecurityConfig
from api.middlewares.secure_file_upload import SecureFileUploadHandler

# Create custom configuration
custom_config = FileSecurityConfig(
    max_audio_file_size=100 * 1024 * 1024,  # 100MB
    enable_content_scanning=True,
    enable_file_quarantine=True
)

# Use custom handler
handler = SecureFileUploadHandler(custom_config)
```

## Security Features

1. **File Type Validation**: Extension and MIME type checking
2. **Content Scanning**: Malicious content detection
3. **Size Limits**: Configurable per file type
4. **Path Traversal Protection**: Prevents directory traversal attacks
5. **Hash Tracking**: Prevents duplicate uploads
6. **Quarantine System**: Isolates suspicious files
7. **Metadata Stripping**: Removes potentially dangerous metadata

## Environment-Specific Settings

The system automatically detects the environment (production/development/test) and applies appropriate security settings. Production has the most restrictive settings for maximum security.

## Monitoring and Logging

All file upload attempts are logged with detailed information about validation results, enabling security monitoring and incident response.
