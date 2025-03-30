# Fatwa Search API

A containerized API for querying Islamic fatwas using vector embeddings. Built with FastAPI, ChromaDB, and OpenAI's embeddings.

## Features

- 🔒 Secure API with API key authentication
- ⏱️ Rate limiting to prevent abuse
- 🚀 Fast vector search using ChromaDB
- 🔍 Semantic search using OpenAI embeddings
- 🐳 Fully containerized with Docker

## Getting Started

### Prerequisites

- Docker and Docker Compose
- OpenAI API key

### Configuration

1. Copy the example environment file and edit it:

```bash
cp .env.example .env
```

2. Edit the `.env` file with your own settings:
   - Set a strong `API_KEY` for authentication
   - Add your `OPENAI_API_KEY`
   - Optionally adjust the `RATE_LIMIT` and `COLLECTION_NAME`

### Running the API

Build and start the containers:

```bash
docker-compose up -d
```

The API will be available at http://localhost:8000.

## API Usage

### Authentication

All API requests (except health check) require an API key in the header:

```
X-API-Key: your-api-key-here
```

### Endpoints

#### Health Check

```
GET /health
```

No authentication required. Returns the health status of the API.

#### Search Fatwas

```
POST /search
```

Request body:

```json
{
  "query": "Your search query in any language",
  "limit": 3  // Optional, defaults to 3
}
```

Response:

```json
{
  "results": [
    {
      "title": "Fatwa Title",
      "url": "https://example.com/fatwa",
      "score": 0.92
    },
    ...
  ],
  "query": "Your search query in any language",
  "processing_time": 0.45
}
```

## Development

### Local Development

To run the API locally without Docker:

1. Install the dependencies:

```bash
pip install -r requirements.txt
pip install -r api/requirements.txt
```

2. Run the API:

```bash
cd api
python -m uvicorn main:app --reload
```

## Deployment

For production deployment, make sure to:

1. Set a strong API key
2. Secure your OpenAI API key
3. Consider using a reverse proxy like Nginx
4. Configure proper CORS settings in the FastAPI app 