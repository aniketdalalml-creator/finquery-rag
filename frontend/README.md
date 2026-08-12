# FinQuery Frontend

```
src/
  app/             # entry + global styles
  features/chat/   # chat feature (UI + API client + hooks)
  shared/          # reusable chrome (Logo, Header)
```

## Run

```powershell
# API (repo root / backend)
cd ../backend
$env:PYTHONPATH = "."
$env:CHAT_MODE = "dummy"
uvicorn app.main:app --reload --port 8000

# UI
cd ../frontend
npm run dev
```

Vite proxies `/api` → `http://localhost:8000`.
