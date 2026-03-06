from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import httpx
import os

app = FastAPI(title="Movement & Miles \u2013 Nelly Chat Backend")

# CORS: allow the GitHub Pages frontend (and local dev)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://wilwixqa1.github.io",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "http://localhost:5500",
        "http://127.0.0.1:5500",
    ],
    allow_methods=["POST", "OPTIONS"],
    allow_headers=["Content-Type"],
)

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

NELLY_SYSTEM_PROMPT = """You are Nelly, the friendly AI coaching assistant for Movement & Miles \u2014 a running coaching brand founded by experienced coaches who help runners of all levels train smarter and stay injury-free.

Your personality:
- Warm, encouraging, and knowledgeable
- You speak like a supportive running coach, not a robot
- Keep responses concise (2-4 sentences) unless the user asks for detail
- Use casual, approachable language

Your knowledge:
- Movement & Miles offers training programs for beginners through advanced runners
- Programs include running plans (5K through 50K), strength training, and mobility/prehab work
- Race plans range from 5K Beginner Treadmill to 50K Advanced
- The M&M Bands Kit ($14.99) is available in the store
- You can help with: training questions, program recommendations, race prep advice, injury prevention tips, general running guidance

Guidelines:
- If someone asks about pricing or specific plan details, point them to the Training Programs or Race Plans pages
- For medical/injury concerns, recommend they see a professional but offer general prevention tips
- Always be motivating \u2014 running is for everyone!
- If you don't know something specific about M&M, say so honestly and offer general coaching advice instead"""


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    reply: str


@app.post("/api/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    if not ANTHROPIC_API_KEY:
        raise HTTPException(status_code=500, detail="API key not configured")

    if not req.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            resp = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": ANTHROPIC_API_KEY,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": "claude-sonnet-4-20250514",
                    "max_tokens": 300,
                    "system": NELLY_SYSTEM_PROMPT,
                    "messages": [{"role": "user", "content": req.message}],
                },
            )
            resp.raise_for_status()
            data = resp.json()
            reply_text = data["content"][0]["text"]
            return ChatResponse(reply=reply_text)
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=502, detail=f"Anthropic API error: {e.response.status_code}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))


@app.get("/")
async def root():
    return {"status": "ok", "service": "Nelly Chat Backend"}
