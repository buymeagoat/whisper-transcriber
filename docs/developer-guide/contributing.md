# Contributing Guide

Thank you for your interest in contributing to Whisper Transcriber! This guide will help you get started with development.

## Development Setup

### Prerequisites

- **Docker & Docker Compose** (recommended)
- **Python 3.11+** (for local development)
- **Node.js 18+** (for frontend development)
- **Git**

### Quick Start

1. **Fork and clone the repository**
   ```bash
   git clone https://github.com/your-username/whisper-transcriber.git
   cd whisper-transcriber
   ```

2. **Set up development environment**
   ```bash
   # Copy environment template
   cp config/.env.example .env
   
   # Start development stack
   docker-compose up -d
   ```

3. **Verify setup**
   ```bash
   # Check application health
   curl http://localhost:8000/
   
   # Check web interface
   open http://localhost:8000
   ```

## Project Structure

```
whisper-transcriber/
├── app/                    # Backend (FastAPI + SQLite)
│   ├── main.py            # Main application
│   ├── worker.py          # Celery background worker
│   └── requirements.txt   # Python dependencies
├── web/                   # Frontend (React PWA)
│   ├── src/               # React components
│   ├── package.json       # Node dependencies
│   └── vite.config.js     # Build configuration
├── docs/                  # Documentation
│   ├── user-guide/        # End-user documentation
│   ├── developer-guide/   # Technical documentation
│   └── deployment/        # Operations documentation
└── docker-compose.yml     # Development environment
```

## Development Workflow

### Backend Development

The backend is a **FastAPI** application with **SQLite** database.

**Local development:**
```bash
# Install dependencies
cd app/
pip install -r requirements.txt

# Run development server
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Run worker (separate terminal)
celery -A worker worker --loglevel=info
```

**Key files:**
- `app/main.py` - Main FastAPI application
- `app/worker.py` - Celery worker for background jobs
- `app/requirements.txt` - Python dependencies

### Frontend Development

The frontend is a **React PWA** built with **Vite**.

**Local development:**
```bash
# Install dependencies
cd web/
npm install

# Start development server
npm run dev

# Build for production
npm run build
```

**Key files:**
- `web/src/App.jsx` - Main React application
- `web/src/components/` - React components
- `web/package.json` - Node dependencies

## Making Changes

### Code Style

**Python (Backend):**
- Follow **PEP 8** style guidelines
- Use **type hints** for function parameters and returns
- Add **docstrings** to public functions
- Keep functions small and focused

**JavaScript (Frontend):**
- Use **ES6+** syntax and features
- Follow **React Hooks** patterns
- Use **functional components** over class components
- Apply **consistent naming** (camelCase for variables, PascalCase for components)

### Testing

**Backend testing:**
```bash
# Install test dependencies
pip install pytest pytest-asyncio

# Run tests
pytest app/tests/
```

**Frontend testing:**
```bash
# Run unit tests
cd web/
npm test

# Run e2e tests
npm run test:e2e
```

### Database Changes

The application uses **SQLite** with **SQLAlchemy** models defined in `app/main.py`.

**Making schema changes:**
1. Update the model in `app/main.py`
2. For production deployments, consider migration scripts
3. Test with a fresh database: `rm app.db && restart application`

## Submitting Changes

### Pull Request Process

1. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**
   - Write clear, focused commits
   - Add tests for new functionality
   - Update documentation if needed

3. **Test your changes**
   ```bash
   # Backend tests
   pytest
   
   # Frontend tests
   cd web/ && npm test
   
   # Integration test
   docker-compose up -d && curl http://localhost:8000/
   ```

4. **Submit pull request**
   - Use a clear, descriptive title
   - Describe what the change does and why
   - Reference any related issues
   - Include screenshots for UI changes

### Commit Guidelines

Use **conventional commit** format:

```
type(scope): description

feat(api): add new transcription endpoint
fix(ui): resolve upload progress display issue
docs(readme): update installation instructions
style(app): format code with black
test(worker): add unit tests for job processing
```

**Types:**
- `feat` - New feature
- `fix` - Bug fix
- `docs` - Documentation changes
- `style` - Code formatting (no functional changes)
- `refactor` - Code changes that neither fix bugs nor add features
- `test` - Adding or updating tests
- `chore` - Maintenance tasks

## Architecture Guidelines

### Backend Principles

- **Keep it simple** - Prefer straightforward solutions
- **SQLite for data** - No complex database setup
- **Celery for background jobs** - Async transcription processing
- **RESTful API design** - Clear, predictable endpoints
- **Minimal dependencies** - Only include what's needed

### Frontend Principles

- **Mobile-first design** - Touch-friendly, responsive interface
- **Progressive Web App** - Offline capabilities, installable
- **Real-time updates** - WebSocket for progress tracking
- **Accessible design** - Screen reader friendly, keyboard navigation
- **Fast performance** - Optimized builds, lazy loading

## Common Tasks

### Adding a New API Endpoint

1. **Define the endpoint** in `app/main.py`:
   ```python
   @app.get("/new-endpoint")
   async def new_endpoint():
       return {"message": "Hello World"}
   ```

2. **Add to API documentation** in `docs/developer-guide/api-reference.md`

3. **Test the endpoint**:
   ```bash
   curl http://localhost:8000/new-endpoint
   ```

### Adding a New Frontend Component

1. **Create component** in `web/src/components/`:
   ```jsx
   // NewComponent.jsx
   const NewComponent = () => {
     return <div>New Component</div>
   }
   export default NewComponent
   ```

2. **Import and use** in `App.jsx`:
   ```jsx
   import NewComponent from './components/NewComponent'
   ```

3. **Test the component** in browser

### Updating Dependencies

**Backend:**
```bash
cd app/
pip install package-name==version
pip freeze > requirements.txt
```

**Frontend:**
```bash
cd web/
npm install package-name@version
# package.json is automatically updated
```

## Getting Help

### Development Issues

- **Check the logs**: `docker-compose logs`
- **Verify setup**: Follow troubleshooting guide
- **Search existing issues**: GitHub issues page
- **Ask questions**: Create a new issue with `question` label

### Contributing Questions

- **Code style**: Follow existing patterns in the codebase
- **Architecture decisions**: Open an issue for discussion
- **Feature ideas**: Create an issue with `enhancement` label

## Release Process

Maintainers handle releases using this process:

1. **Update version** in relevant files
2. **Update CHANGELOG.md** with new features and fixes
3. **Create GitHub release** with release notes
4. **Build and tag Docker images**

Contributors don't need to worry about releases - just focus on great code!
