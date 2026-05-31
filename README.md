# 🤖 Claude Chat — ChatGPT-like Interface

A full-stack ChatGPT-style chat app using **Python FastAPI** (backend) + **vanilla HTML/CSS/JS** (frontend), powered by the **Anthropic Claude API**.

---

## ✨ Features

- 💬 **Multi-conversation sidebar** — create, switch, rename, delete chats
- 📡 **Streaming responses** — tokens appear in real-time like ChatGPT
- 📎 **File uploads** — images, PDFs, code files, text files
- 🖼️ **Image analysis** — drag & drop or paste images from clipboard
- 📋 **Code blocks** — syntax highlighting + one-click copy button
- ✍️ **Markdown rendering** — tables, lists, bold, code, blockquotes
- 🗑️ **Clear conversation** — wipe messages while keeping the chat
- ⌨️ **Shift+Enter** for newline, **Enter** to send
- 📱 **Responsive** — works on mobile

---

## 📁 Project Structure

```
chatgpt-clone/
├── backend/
│   ├── main.py            ← FastAPI app (all API logic)
│   └── requirements.txt   ← Python dependencies
├── frontend/
│   └── index.html         ← Full UI (single file, no build step)
├── start_backend.sh       ← Quick start script
└── README.md
```

---

## 🚀 Setup & Run

### 1. Get your Anthropic API Key
Sign up at https://console.anthropic.com and create an API key.

### 2. Install backend dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 3. Start the backend

```bash
export ANTHROPIC_API_KEY="sk-ant-..."

cd backend
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

Or simply:
```bash
bash start_backend.sh
```

### 4. Open the frontend

Just open `frontend/index.html` in your browser:
```bash
open frontend/index.html       # macOS
xdg-open frontend/index.html  # Linux
start frontend/index.html      # Windows
```

No build step, no npm, no bundler needed.

---

## 🔧 Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| Backend port | `8000` | Change in `uvicorn` command and in `frontend/index.html` (`const API = ...`) |
| Model | `claude-sonnet-4-20250514` | Change in `backend/main.py` |
| Max tokens | `4096` | Change in `backend/main.py` |

---

## 🌐 Deploy

### Backend (e.g. Railway, Render, Fly.io)
- Set env var `ANTHROPIC_API_KEY`
- Run: `uvicorn main:app --host 0.0.0.0 --port $PORT`

### Frontend
- Update `const API = 'http://localhost:8000'` to your deployed backend URL
- Host `index.html` on Netlify, Vercel, or any static host

---

## 📡 API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/conversations` | List all conversations |
| POST | `/conversations` | Create new conversation |
| DELETE | `/conversations/{id}` | Delete conversation |
| PATCH | `/conversations/{id}` | Rename conversation |
| GET | `/conversations/{id}/messages` | Get message history |
| POST | `/conversations/{id}/chat` | Send message (streaming SSE) |
| DELETE | `/conversations/{id}/messages` | Clear messages |

---

## 📦 Dependencies

**Backend:**
- `fastapi` — web framework
- `uvicorn` — ASGI server
- `anthropic` — Claude API client
- `python-multipart` — file upload support

**Frontend:**
- `markdown-it` (CDN) — markdown rendering
- `highlight.js` (CDN) — code syntax highlighting
- Zero npm packages, no build step
