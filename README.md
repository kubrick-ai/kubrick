# kubrick

A Flask API for semantic search on video content using TwelveLabs embeddings.

## Requirements

- `ffmpeg` (binary, not python package)
- PostgreSQL with pgvector extension
- TwelveLabs API key

## Setup

1. Install dependencies:

```bash
uv sync
```

2. Set up environment variables:

```bash
cp .env.example .env
# Edit .env with your configuration
```

3. Set up database:

TODO: This is temporary

```bash
uv run python -c "from app.services.vector_db_service import VectorDBService; VectorDBService().setup()"
```

or in cli:

```bash
uv run python cli.py
/setup_db
```

## Usage

### Web API

```bash
uv run python wsgi.py
```

Or:

```bash
uv run flask --app wsgi:app run --debug --port 5003
```

### CLI Interface

```bash
uv run python cli.py
```

## API Endpoints

### Search

```bash
# Text search
curl -X POST http://localhost:5003/search \
  -F "query_text=your search query"

# Video search
curl -X POST http://localhost:5003/search \
  -F "query_media_type=video" \
  -F "query_media_url=https://example.com/video.mp4"
```

### Health Check

```bash
curl http://localhost:5003/health
```
