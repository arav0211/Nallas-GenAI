import asyncio
import json
import os
from collections.abc import AsyncIterator
from typing import Optional

import boto3
from botocore.config import Config
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

MODEL_ID = os.getenv(
    "BEDROCK_MODEL_ID",
    "anthropic.claude-3-haiku-20240307-v1:0",
)
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")

app = FastAPI(title="Bedrock Streaming API")


class ChatRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=100_000)
    max_tokens: int = Field(1024, ge=1, le=4096)


def get_bedrock_client():
    return boto3.client(
        "bedrock-runtime",
        region_name=AWS_REGION,
        config=Config(read_timeout=300, retries={"max_attempts": 3}),
    )


def _next_event(event_iterator) -> Optional[dict]:
    try:
        return next(event_iterator)
    except StopIteration:
        return None


async def stream_bedrock(request: ChatRequest, client) -> AsyncIterator[str]:
    try:
        response = await asyncio.to_thread(
            client.converse_stream,
            modelId=MODEL_ID,
            messages=[{"role": "user", "content": [{"text": request.prompt}]}],
            inferenceConfig={"maxTokens": request.max_tokens, "temperature": 0.7},
        )
        event_iterator = iter(response["stream"])

        while True:
            event = await asyncio.to_thread(_next_event, event_iterator)
            if event is None:
                break

            delta = event.get("contentBlockDelta", {}).get("delta")
            if delta and "text" in delta:
                yield "data: " + json.dumps({"text": delta["text"]}, ensure_ascii=False) + "\n\n"

            if "messageStop" in event:
                yield "event: done\ndata: {}\n\n"
                return

        yield "event: done\ndata: {}\n\n"
    except Exception as exc:
        yield "event: error\ndata: " + json.dumps({"error": str(exc)}, ensure_ascii=False) + "\n\n"


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/chat/stream")
async def chat_stream(request: ChatRequest, http_request: Request):
    if not http_request.app:
        raise HTTPException(status_code=500, detail="Application unavailable")

    client = get_bedrock_client()
    return StreamingResponse(
        stream_bedrock(request, client),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
