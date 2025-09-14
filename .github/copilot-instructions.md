# OpenSource Sensei - AI Coding Agent Instructions

## Architecture Overview

This is a **multi-agent AI system** for guiding open source contributors through analysis, code review, and project improvement. The system follows a **FastAPI + Agent Pattern** with MongoDB storage and Redis communication.

### Core Components
- **`agents/`**: Specialized AI agents inheriting from `BaseAgent` class with message passing system
- **`backend/app/`**: FastAPI API with service layer pattern using MongoDB/Beanie ODM
- **Frontend**: React application (directory present but not analyzed in this scan)
- **Storage**: File-based repository analysis with MongoDB document storage

## Agent System Patterns

### Agent Base Class (`agents/base_agent.py`)
All agents inherit from `BaseAgent` and implement:
- **`async def initialize()`**: Setup resources (API keys, caches)
- **`async def process_task(task: Dict[str, Any]) -> Dict[str, Any]`**: Core task processing
- **`get_capabilities()`**: Returns list of `AgentCapability` objects

### Message Passing System
Agents communicate via `AgentMessage` objects with:
- `MessageType` enum: TASK, RESPONSE, ERROR, COLLABORATION, etc.
- Performance metrics tracking (success_rate, avg_response_time)
- Cache management with TTL (default 3600s)

### Agent Implementation Example
```python
class ResearchAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            agent_id="research_agent",
            name="Research Agent", 
            description="Researches programming topics..."
        )
        self.documentation_sources = {
            "python": ["docs.python.org", "pypi.org"],
            # ... language-specific sources
        }
```

## Backend Service Layer

### Service Pattern (`backend/app/services/`)
All services inherit from `BaseService[T]` generic class providing:
- **CRUD operations**: `create()`, `get_by_id()`, `get_all()`, `update()`, `delete()`
- **Pagination**: `skip`, `limit` parameters standard across all endpoints
- **Filtering**: `filters` dict parameter for complex queries
- **Soft deletes**: via `is_active` field in `BaseDocument`

### Document Models (`backend/app/models/`)
All models inherit from `BaseDocument` which provides:
- **Timestamps**: `created_at`, `updated_at` auto-managed
- **Soft delete**: `is_active` boolean field
- **State management**: Beanie ODM with `use_state_management = True`

### API Endpoints (`backend/app/api/endpoints/`)
Standard RESTful patterns:
- **POST** `/` - Create resource
- **GET** `/` - List with pagination (`skip`, `limit`) and filtering
- **GET** `/{id}` - Get by ID
- **PUT** `/{id}` - Update resource
- **DELETE** `/{id}` - Delete resource

## Environment & Configuration

### Required Environment Variables
Create `.env` file (never commit) with:
```env
MONGODB_URI=mongodb://localhost:27017/opensourcesensei
GITHUB_API_KEY=your_github_token    # Optional but recommended
OPENAI_API_KEY=your_openai_key       # For AI agents
STACKOVERFLOW_API_KEY=your_so_key    # Optional research capability
```

### Settings Pattern (`backend/app/core/config.py`)
- Uses `pydantic_settings.BaseSettings` with environment variable binding
- Singleton pattern via `@lru_cache` decorator: `get_settings()`
- Development-friendly defaults with graceful degradation

## Development Workflows

### Running the Application
```bash
# Full stack with Docker
docker-compose up

# Backend only (development)
cd backend
pip install -r requirements.txt
uvicorn main:app --reload

# Database-optional development mode
# App starts without MongoDB connection in development
```

### Database Integration
- **Beanie ODM** for MongoDB document mapping
- **Graceful degradation**: App runs without DB connection for development
- **Health checks**: `/health` endpoint reports database connectivity status
- **Connection lifecycle**: Managed in FastAPI lifespan events

### Agent Development
1. **Inherit from `BaseAgent`** class
2. **Implement required methods**: `initialize()`, `process_task()`, `get_capabilities()`
3. **Define capabilities** with JSON schemas for input/output validation
4. **Use caching** for expensive operations (self.cache with TTL)
5. **Load API keys** in `initialize()` from environment variables

### Service Layer Development
1. **Inherit from `BaseService[ModelType]`** 
2. **Use dependency injection** in endpoints: `Depends(get_model_service)`
3. **Standard CRUD** methods available, override for custom logic
4. **Pagination and filtering** built-in via base class

### Testing Patterns
- **pytest + pytest-asyncio** for async test support
- **httpx** for API testing
- Test files should follow `test_*.py` naming convention

## Project-Specific Conventions

### File Organization
- **Agent files**: `agents/{agent_name}_agent.py` (snake_case)
- **Service files**: `backend/app/services/{model}_service.py`
- **Model files**: `backend/app/models/{model}.py` (singular)
- **Endpoint files**: `backend/app/api/endpoints/{resource}.py` (plural)

### Language-Specific Sources (`agents/research_agent.py`)
When building research capabilities, use the predefined `documentation_sources` mapping for each programming language to ensure consistent, authoritative documentation references.

### Error Handling
- **Service layer**: Catch exceptions, log errors, re-raise with context
- **API layer**: Use FastAPI `HTTPException` with appropriate status codes
- **Agents**: Return error messages via `MessageType.ERROR` in message system

### Performance Considerations
- **Agent caching**: Use `self.cache` with TTL for expensive operations
- **Database queries**: Leverage Beanie's aggregation pipelines for complex queries
- **Request timing**: Automatic middleware adds `X-Process-Time` header