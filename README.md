# 🎨 FlowPlayground

**AI-Powered Photo & Video Processing Backend for iOS Applications**

FlowPlayground is a production-ready FastAPI backend service that provides AI-powered photo and video processing capabilities for iOS applications. Built with scalability, performance, and ease of use in mind.

## ✨ Features

### 🖼️ Image Processing
- **Enhancement**: Improve image quality, reduce noise, enhance colors
- **Style Transfer**: Apply artistic styles while preserving structure
- **Generation**: Create images from text prompts using AI models
- **Batch Processing**: Process multiple images efficiently
- **Format Support**: JPEG, PNG, WebP

### 🎬 Video Processing
- **Enhancement**: Improve video quality and reduce artifacts
- **Stabilization**: Reduce camera shake and improve stability
- **Style Transfer**: Apply artistic styles to videos
- **Format Support**: MP4, AVI, MOV

### 🚀 Production Features
- **FastAPI**: Modern, fast web framework with automatic OpenAPI documentation
- **Async Processing**: Non-blocking operations for better performance
- **Redis Caching**: Intelligent caching for faster response times
- **Rate Limiting**: Protect your API from abuse
- **Authentication**: API key-based authentication
- **File Management**: Secure file upload and storage
- **Health Checks**: Comprehensive health monitoring
- **Docker Support**: Easy deployment with Docker
- **Gradio Interface**: Development UI for testing capabilities

## 🏗️ Architecture

```
FlowPlayground/
├── app/                          # Main application code
│   ├── api/v1/                   # API version 1
│   │   ├── endpoints/            # API endpoints
│   │   │   ├── image.py         # Image processing endpoints
│   │   │   ├── video.py         # Video processing endpoints
│   │   │   └── health.py        # Health check endpoints
│   │   └── api.py               # API router configuration
│   ├── core/                    # Core application components
│   │   ├── config.py           # Configuration management
│   │   └── security.py         # Security utilities
│   ├── models/                  # Data models
│   │   ├── requests.py         # Request models
│   │   └── responses.py        # Response models
│   ├── services/               # Business logic
│   │   ├── fal_ai.py          # fal.ai integration
│   │   └── media_processor.py  # Media processing utilities
│   ├── utils/                  # Utility functions
│   │   └── file_handler.py     # File handling utilities
│   └── main.py                 # FastAPI application
├── gradio_app/                 # Gradio development interface
│   └── interface.py           # Gradio UI
├── tests/                     # Test suite
├── docker-compose.yml         # Docker compose configuration
├── Dockerfile                 # Docker configuration
├── requirements.txt           # Python dependencies
└── .env.example              # Environment variables template
```

## 🚀 Quick Start

### Prerequisites
- Python 3.8+ (Python 3.11-3.12 recommended for best compatibility)
- Redis (for caching)
- fal.ai API key

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/flowplayground.git
   cd flowplayground
   ```

2. **Set up environment**
   ```bash
   # Create virtual environment
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\\Scripts\\activate
   
   # Install dependencies (choose one)
   pip install -r requirements.txt              # Core dependencies only
   pip install -r requirements-dev.txt          # Development setup
   pip install -r requirements-prod.txt         # Production setup
   
   # Or use pyproject.toml
   pip install -e ".[dev]"                      # Development tools
   pip install -e ".[prod]"                     # Production tools
   ```

3. **Configure environment variables**
   ```bash
   # Copy environment template
   cp .env.example .env
   
   # Edit .env with your configuration
   nano .env
   ```

4. **Set required environment variables**
   ```env
   SECRET_KEY=your-secret-key-here
   FAL_AI_API_KEY=your-fal-ai-api-key-here
   REDIS_URL=redis://localhost:6379/0
   ```

5. **Start Redis**
   ```bash
   # Using Docker (recommended)
   docker-compose up -d redis
   
   # Or install locally
   # On macOS with Homebrew:
   brew install redis && brew services start redis
   
   # On Ubuntu:
   sudo apt-get install redis-server && sudo systemctl start redis
   ```

6. **Run the application**
   ```bash
   # Start the API server
   python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   
   # In another terminal, start Gradio (optional, may have Python 3.13 issues)
   python -m gradio_app.interface
   ```

7. **Access the application**
   - API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs
   - Gradio Interface: http://localhost:7860 (if started)
   - Health Check: http://localhost:8000/api/v1/health/health

## 🐳 Docker Deployment

### Using Docker Compose (Recommended)

```bash
# Clone the repository
git clone https://github.com/yourusername/flowplayground.git
cd flowplayground

# Set environment variables
export FAL_AI_API_KEY=your-fal-ai-api-key-here
export SECRET_KEY=your-secret-key-here

# Start all services
docker-compose up -d

# Start with development profile (includes Gradio)
docker-compose --profile dev up -d
```

### Using Docker Only

```bash
# Build the image
docker build -t flowplayground .

# Run Redis
docker run -d --name redis -p 6379:6379 redis:7-alpine

# Run the application
docker run -d --name flowplayground \\
  -p 8000:8000 \\
  -e FAL_AI_API_KEY=your-fal-ai-api-key-here \\
  -e SECRET_KEY=your-secret-key-here \\
  -e REDIS_URL=redis://redis:6379/0 \\
  --link redis:redis \\
  flowplayground
```

## 📚 API Documentation

### Authentication
All API endpoints require authentication using API keys:

```bash
curl -H "Authorization: Bearer YOUR_API_KEY" \\
     -H "Content-Type: application/json" \\
     http://localhost:8000/api/v1/health
```

### Image Processing Endpoints

#### Enhance Image
```bash
POST /api/v1/image/enhance
```

**Parameters:**
- `file`: Image file (multipart/form-data)
- `strength`: Enhancement strength (0.1-1.0)
- `preserve_details`: Preserve image details (boolean)
- `enhance_colors`: Enhance colors (boolean)
- `reduce_noise`: Reduce noise (boolean)

**Example:**
```bash
curl -X POST "http://localhost:8000/api/v1/image/enhance" \\
     -H "Authorization: Bearer YOUR_API_KEY" \\
     -F "file=@image.jpg" \\
     -F "strength=0.8" \\
     -F "preserve_details=true"
```

#### Style Transfer
```bash
POST /api/v1/image/style-transfer
```

**Parameters:**
- `file`: Image file (multipart/form-data)
- `style_strength`: Style application strength (0.1-1.0)
- `preserve_structure`: Preserve image structure (boolean)
- `style_reference`: Style reference ID (string)

#### Generate Image
```bash
POST /api/v1/image/generate
```

**Parameters:**
- `prompt`: Text description of the image
- `negative_prompt`: What to avoid in the image (optional)
- `width`: Image width (128-2048, multiple of 8)
- `height`: Image height (128-2048, multiple of 8)
- `num_inference_steps`: Number of inference steps (1-100)
- `guidance_scale`: Guidance scale (1.0-20.0)
- `seed`: Random seed for reproducibility (optional)

**Example:**
```bash
curl -X POST "http://localhost:8000/api/v1/image/generate" \\
     -H "Authorization: Bearer YOUR_API_KEY" \\
     -H "Content-Type: application/json" \\
     -d '{
       "prompt": "A beautiful landscape with mountains and a lake",
       "width": 512,
       "height": 512,
       "num_inference_steps": 20,
       "guidance_scale": 7.5
     }'
```

### Video Processing Endpoints

#### Process Video
```bash
POST /api/v1/video/process
```

**Parameters:**
- `file`: Video file (multipart/form-data)
- `operation`: Processing operation (enhance, stabilize, style_transfer)
- `quality`: Output quality (low, medium, high)
- `fps`: Target frame rate (optional)
- `resolution`: Target resolution (optional)

### Health and Status Endpoints

#### Health Check
```bash
GET /api/v1/health
```

#### Get Capabilities
```bash
GET /api/v1/capabilities
```

#### Job Status
```bash
GET /api/v1/image/job/{job_id}
GET /api/v1/video/job/{job_id}
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `SECRET_KEY` | Application secret key | Required |
| `FAL_AI_API_KEY` | fal.ai API key | Required |
| `ENVIRONMENT` | Environment (development, staging, production) | `development` |
| `DEBUG` | Enable debug mode | `true` |
| `HOST` | Server host | `0.0.0.0` |
| `PORT` | Server port | `8000` |
| `REDIS_URL` | Redis connection URL | `redis://localhost:6379/0` |
| `MAX_FILE_SIZE` | Maximum file size in bytes | `52428800` (50MB) |
| `RATE_LIMIT_REQUESTS` | Rate limit requests per period | `100` |
| `RATE_LIMIT_PERIOD` | Rate limit period in seconds | `3600` |
| `GRADIO_ENABLED` | Enable Gradio interface | `true` |
| `GRADIO_PORT` | Gradio server port | `7860` |

### File Upload Limits

- **Maximum file size**: 50MB (configurable)
- **Supported image formats**: JPEG, PNG, WebP
- **Supported video formats**: MP4, AVI, MOV
- **Maximum video duration**: 5 minutes

## 🧪 Testing

### Running Tests
```bash
# Install development dependencies
pip install -r requirements.txt

# Run all tests
pytest

# Run with coverage
pytest --cov=app

# Run specific test categories
pytest -m unit      # Unit tests only
pytest -m integration  # Integration tests only
pytest -m "not slow"   # Skip slow tests
```

### Test Structure
```
tests/
├── unit/           # Unit tests
├── integration/    # Integration tests
├── fixtures/       # Test fixtures
└── conftest.py     # Pytest configuration
```

## 🔒 Security

### Authentication
- API key-based authentication
- Request signing support for iOS apps
- Rate limiting per API key

### File Security
- File type validation
- Size limits
- Filename sanitization
- Temporary file cleanup

### Production Security
- HTTPS enforcement
- CORS configuration
- Security headers
- Input validation

## 🚀 Deployment

### Production Checklist

1. **Environment Configuration**
   - [ ] Set `ENVIRONMENT=production`
   - [ ] Set `DEBUG=false`
   - [ ] Generate strong `SECRET_KEY`
   - [ ] Configure proper `CORS_ORIGINS`

2. **Security**
   - [ ] Enable HTTPS
   - [ ] Set up reverse proxy (Nginx)
   - [ ] Configure firewall rules
   - [ ] Set up monitoring

3. **Scaling**
   - [ ] Use Redis cluster for caching
   - [ ] Set up load balancing
   - [ ] Configure auto-scaling
   - [ ] Set up monitoring and logging

### Docker Production Deployment

```bash
# Use production profile
docker-compose --profile production up -d

# Scale API service
docker-compose up -d --scale api=3

# Monitor services
docker-compose logs -f api
```

### Kubernetes Deployment

```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: flowplayground-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: flowplayground-api
  template:
    metadata:
      labels:
        app: flowplayground-api
    spec:
      containers:
      - name: api
        image: flowplayground:latest
        ports:
        - containerPort: 8000
        env:
        - name: ENVIRONMENT
          value: "production"
        - name: FAL_AI_API_KEY
          valueFrom:
            secretKeyRef:
              name: flowplayground-secrets
              key: fal-ai-api-key
        livenessProbe:
          httpGet:
            path: /api/v1/health/liveness
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /api/v1/health/readiness
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
```

## 📊 Monitoring

### Health Checks
- `/api/v1/health` - Basic health check
- `/api/v1/health/detailed` - Detailed system information
- `/api/v1/health/liveness` - Kubernetes liveness probe
- `/api/v1/health/readiness` - Kubernetes readiness probe

### Metrics
- Request/response times
- Error rates
- Cache hit rates
- File processing statistics
- System resource usage

### Logging
- Structured logging with JSON format
- Request correlation IDs
- Error tracking with stack traces
- Performance monitoring

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Setup

```bash
# Clone your fork
git clone https://github.com/yourusername/flowplayground.git
cd flowplayground

# Set up development environment
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Install pre-commit hooks
pre-commit install

# Run tests
pytest

# Start development server
python -m uvicorn app.main:app --reload
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [FastAPI](https://fastapi.tiangolo.com/) for the excellent web framework
- [fal.ai](https://fal.ai/) for AI model inference
- [Gradio](https://gradio.app/) for the development interface
- [Redis](https://redis.io/) for caching capabilities

## 📞 Support

- **Documentation**: [https://docs.flowplayground.com](https://docs.flowplayground.com)
- **Issues**: [GitHub Issues](https://github.com/yourusername/flowplayground/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/flowplayground/discussions)

---

**Built with ❤️ for the iOS developer community**