# FastAPI Bedrock SSE Endpoint

A FastAPI endpoint that streams Amazon Bedrock `converse_stream` responses to clients as Server-Sent Events (SSE).

## Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Configure AWS credentials and region through AWS CLI, environment variables, or an AWS profile. The default Bedrock model is `anthropic.claude-3-haiku-20240307-v1:0`; override it with `BEDROCK_MODEL_ID`.

## Run

```powershell
uvicorn main:app --reload
```

Test with EventSource-compatible tooling or curl:

```powershell
curl.exe -N -H "Content-Type: application/json" -d '{"prompt":"Explain SSE in one sentence"}' http://127.0.0.1:8000/chat/stream
```

Health endpoint: `GET /health`

Streaming endpoint: `POST /chat/stream`

Request body:

```json
{"prompt":"Hello", "max_tokens":1024}
```
