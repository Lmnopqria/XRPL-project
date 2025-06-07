# XRPL API Server

This is a FastAPI-based server for the XRPL Project.

## Prerequisites

- Python 3.8 or higher
- pip (Python package installer)

## Installation

1. Clone the repository:
```bash
git clone [your-repository-url]
cd XRPL-project
```

2. Create a virtual environment (recommended):
```bash
python -m venv venv
```

3. Activate the virtual environment:

- For Windows:
```bash
.\venv\Scripts\activate
```
- For Unix or MacOS:
```bash
source venv/bin/activate
```

4. Install dependencies:
```bash
pip install -r requirements.txt
```

## Running the Server

1. Start the server:
```bash
python run.py
```

The server will start at `http://localhost:8000`

## Available Endpoints

- `GET /`: Welcome message
- `GET /api/v1/health`: Health check endpoint
- `GET /docs`: Swagger UI documentation
- `GET /redoc`: ReDoc documentation

## Development

The server runs in development mode with auto-reload enabled. Any changes to the code will automatically restart the server.

## API Documentation

After starting the server, you can view the API documentation at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`