import os
import uuid
import json
import base64
from datetime import datetime
from typing import Optional
from pathlib import Path

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel
import anthropic

app = FastAPI(title="ChatGPT Clone API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory conversation store: {conversation_id: [messages]}
conversations: dict[str, list] = {}

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY", ""))


class NewConversation(BaseModel):
    title: Optional[str] = "New Chat"


class ConversationRename(BaseModel):
    title: str


@app.get("/health")
def health():
    return {"status": "ok"}


# ── Conversations CRUD ──────────────────────────────────────────────────────

@app.get("/conversations")
def list_conversations():
    result = []
    for cid, msgs in conversations.items():
        title = msgs[0].get("title", "New Chat") if msgs else "New Chat"
        updated = msgs[-1].get("timestamp", "") if msgs else ""
        result.append({"id": cid, "title": title, "updated_at": updated})
    return sorted(result, key=lambda x: x["updated_at"], reverse=True)


@app.post("/conversations")
def create_conversation(body: NewConversation):
    cid = str(uuid.uuid4())
    conversations[cid] = []
    return {"id": cid, "title": body.title}


@app.delete("/conversations/{cid}")
def delete_conversation(cid: str):
    conversations.pop(cid, None)
    return {"deleted": cid}


@app.patch("/conversations/{cid}")
def rename_conversation(cid: str, body: ConversationRename):
    if cid not in conversations:
        raise HTTPException(404, "Not found")
    if conversations[cid]:
        conversations[cid][0]["title"] = body.title
    return {"id": cid, "title": body.title}


@app.get("/conversations/{cid}/messages")
def get_messages(cid: str):
    if cid not in conversations:
        raise HTTPException(404, "Not found")
    return conversations[cid]


# ── Chat (streaming) ────────────────────────────────────────────────────────

@app.post("/conversations/{cid}/chat")
async def chat(
    cid: str,
    message: str = Form(...),
    files: list[UploadFile] = File(default=[]),
):
    if cid not in conversations:
        conversations[cid] = []

    # Build user content
    content_parts = []

    for f in files:
        raw = await f.read()
        mime = f.content_type or "application/octet-stream"
        b64 = base64.standard_b64encode(raw).decode()

        if mime.startswith("image/"):
            content_parts.append({
                "type": "image",
                "source": {"type": "base64", "media_type": mime, "data": b64}
            })
        elif mime == "application/pdf":
            content_parts.append({
                "type": "document",
                "source": {"type": "base64", "media_type": "application/pdf", "data": b64}
            })
        else:
            # Plain text / code files
            try:
                text_content = raw.decode("utf-8")
                content_parts.append({
                    "type": "text",
                    "text": f"[File: {f.filename}]\n```\n{text_content}\n```"
                })
            except Exception:
                content_parts.append({
                    "type": "text",
                    "text": f"[Binary file attached: {f.filename}]"
                })

    content_parts.append({"type": "text", "text": message})

    user_msg = {
        "role": "user",
        "content": content_parts,
        "timestamp": datetime.utcnow().isoformat(),
    }
    if not conversations[cid]:
        # Store title from first message
        user_msg["title"] = message[:60] or "New Chat"

    conversations[cid].append(user_msg)

    # Build messages for Anthropic (strip internal keys)
    api_messages = []
    for m in conversations[cid]:
        api_messages.append({"role": m["role"], "content": m["content"]})

    async def stream_response():
        full_text = ""
        try:
            with client.messages.stream(
                model="claude-sonnet-4-20250514",
                max_tokens=4096,
                system=(
                    "You are a helpful, harmless, and honest AI assistant. "
                    "You can analyze images, read documents, and help with code, writing, math, and more. "
                    "Be concise and clear. Use markdown formatting when helpful."
                ),
                messages=api_messages,
            ) as stream:
                for text in stream.text_stream:
                    full_text += text
                    yield f"data: {json.dumps({'type': 'delta', 'text': text})}\n\n"

            # Save assistant message
            conversations[cid].append({
                "role": "assistant",
                "content": [{"type": "text", "text": full_text}],
                "timestamp": datetime.utcnow().isoformat(),
            })
            yield f"data: {json.dumps({'type': 'done'})}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(
        stream_response(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


# ── Clear conversation ───────────────────────────────────────────────────────

@app.delete("/conversations/{cid}/messages")
def clear_messages(cid: str):
    if cid in conversations:
        title_msg = conversations[cid][0] if conversations[cid] else None
        title = title_msg.get("title", "New Chat") if title_msg else "New Chat"
        conversations[cid] = []
    return {"cleared": cid}
