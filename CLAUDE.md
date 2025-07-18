# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**FlowPlayground** is an AI-powered backend service for iOS photo/video applications. It was created as a scalable, production-ready service with clean architecture principles.

### Original Project Requirements

- **Framework**: FastAPI for REST API endpoints
- **AI Integration**: fal.ai API for image generation, enhancement, style transfer
- **Development UI**: Gradio interface for testing AI capabilities
- **Architecture**: Clean separation of concerns (API routes, business logic, external services)
- **Target**: iOS photo/video app backend with scalability focus

### Key Features Implemented

- Authentication via API key for iOS apps
- File handling with temporary storage
- Async processing for fal.ai API calls
- Redis caching for AI results
- Rate limiting per API key
- Comprehensive error handling
- Structured logging with correlation IDs
- Docker deployment setup
- Production-ready configuration management

## Development Commands

### Running the Application

```bash
# Start the FastAPI server with hot reload
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Start the Gradio development UI
python -m gradio_app.interface

# Using the configured scripts
python -m app.main           # Start API server
python -m gradio_app.interface  # Start Gradio interface
```

### Docker Development

```bash
# Start all services (API + Redis)
docker-compose up -d

# Start with development profile (includes Gradio)
docker-compose --profile dev up -d

# Start with monitoring (includes Prometheus + Grafana)
docker-compose --profile monitoring up -d
```

### Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app

# Run specific test categories
pytest -m unit          # Unit tests only
pytest -m integration   # Integration tests only
pytest -m "not slow"    # Skip slow tests
pytest -m "not network" # Skip network-dependent tests
```

### Code Quality

```bash
# Format code
black .

# Sort imports
isort .

# Lint code
ruff check .

# Type checking
mypy app/

# Security scanning
bandit -r app/

# Run all linting tools
ruff check . && black --check . && isort --check-only . && mypy app/
```

## Architecture Overview

FlowPlayground is a FastAPI-based AI-powered photo and video processing service designed for iOS applications. The architecture follows a clean, modular design:

### Core Components

- **FastAPI Application** (`app/main.py`): Main application with middleware, exception handlers, and lifecycle management
- **API Layer** (`app/api/v1/`): RESTful endpoints for image/video processing, health checks
- **Services Layer** (`app/services/`): Business logic including fal.ai integration and media processing
- **Models Layer** (`app/models/`): Pydantic models for requests/responses
- **Core** (`app/core/`): Configuration management and security utilities
- **Utils** (`app/utils/`): File handling and utility functions

### Key Services

- **fal.ai Integration** (`app/services/fal_ai.py`): Handles AI model inference via fal.ai API
- **Media Processor** (`app/services/media_processor.py`): Image and video processing utilities
- **File Handler** (`app/utils/file_handler.py`): Secure file upload, validation, and cleanup

### External Dependencies

- **fal.ai API**: Requires `FAL_AI_API_KEY` environment variable
- **Redis**: Used for caching (optional but recommended)
- **Gradio**: Development UI for testing capabilities

## Environment Configuration

### Required Environment Variables

```env
SECRET_KEY=your-secret-key-here
FAL_AI_API_KEY=your-fal-ai-api-key-here
```

### Optional Environment Variables

```env
ENVIRONMENT=development|staging|production
DEBUG=true|false
REDIS_URL=redis://localhost:6379/0
GRADIO_ENABLED=true|false
GRADIO_PORT=7860
```

### Development Setup

1. Copy `.env.example` to `.env` and configure required variables
2. Install dependencies: `pip install -r requirements.txt`
3. Install additional core packages: `pip install pydantic-settings redis`
4. Start Redis (if using caching): `redis-server`
5. Run the application: `python -m uvicorn app.main:app --reload`

### Common Issues and Solutions

**Pydantic v2 Migration**: The codebase has been updated to work with Pydantic v2.x. Key changes:
- `BaseSettings` moved to `pydantic-settings` package
- `regex` parameter replaced with `pattern` in Field definitions
- `schema_extra` replaced with `json_schema_extra` in Config classes

**Dependencies**: If you encounter build wheel errors, install core packages individually:
```bash
pip install fastapi uvicorn pydantic-settings redis python-multipart aiofiles
```

**Python 3.13 Compatibility**: The project has compatibility issues with Python 3.13:
- `audioop` module was removed in Python 3.13 (affects Gradio)
- Some package versions may be incompatible
- Use Python 3.11 or 3.12 for best compatibility, or use the provided Docker setup

**Dependency Cleanup**: Removed unused dependencies and reorganized requirements:
- **Core dependencies**: Only packages actually imported in the codebase
- **Optional dependencies**: Grouped by purpose in `pyproject.toml`
- **Separate requirement files**: `requirements-dev.txt` and `requirements-prod.txt`
- **Removed unused packages**: torch, opencv-python, sqlalchemy, celery, and many others that weren't imported

**Installation Options**:
```bash
# Core dependencies only
pip install -r requirements.txt

# Development setup
pip install -r requirements-dev.txt

# Production setup  
pip install -r requirements-prod.txt

# Or use pyproject.toml optional dependencies
pip install -e ".[dev]"     # Development tools
pip install -e ".[prod]"    # Production tools
pip install -e ".[ml]"      # Machine learning packages
pip install -e ".[all]"     # Everything
```

## API Endpoints Structure

### Image Processing

- `POST /api/v1/image/enhance` - Enhance image quality
- `POST /api/v1/image/style-transfer` - Apply artistic styles
- `POST /api/v1/image/generate` - Generate images from text prompts
- `GET /api/v1/image/job/{job_id}` - Check processing status

### Video Processing

- `POST /api/v1/video/process` - Process videos (enhance, stabilize, style transfer)
- `GET /api/v1/video/job/{job_id}` - Check processing status

### System

- `GET /api/v1/health` - Health check with service status
- `GET /api/v1/capabilities` - List available processing capabilities

## Configuration Management

The application uses Pydantic Settings for configuration management (`app/core/config.py`):

- Environment-based configuration with `.env` file support
- Validation and type checking for all settings
- Environment-specific defaults (development/staging/production)
- Automatic handling of file paths and security settings

## Error Handling

The application implements comprehensive error handling:

- Custom error codes and responses (`app/models/responses.py`)
- Structured error responses with request IDs
- Validation error handling
- HTTP exception mapping
- Request/response logging with timing

## File Upload Security

- File type validation based on MIME types
- Size limits (default 50MB, configurable)
- Filename sanitization
- Temporary file cleanup with scheduled tasks
- Secure file serving through FastAPI static files

## Testing Strategy

Tests are organized by category using pytest markers:

- `unit`: Unit tests for individual components
- `integration`: Integration tests for API endpoints
- `slow`: Tests that take significant time to run
- `network`: Tests requiring external network access

## Production Considerations

- Disable debug mode and API documentation in production
- Use environment variables for all sensitive configuration
- Enable proper CORS settings for your domains
- Set up reverse proxy (Nginx) for SSL termination
- Use Redis for caching and session management
- Configure monitoring with Prometheus/Grafana
- Set up proper logging and error tracking