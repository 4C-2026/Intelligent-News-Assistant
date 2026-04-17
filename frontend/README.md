# Intelligent News Assistant - Frontend

Frontend for **Intelligent News Assistant**.

## Tech Stack (pinned)

- Node.js: **18.17.0** (as per architecture doc)
- Vue: **3.4.21**
- Vite: **5.2.0**
- Element Plus: **2.6.1**
- Vue Router: **4.3.0**
- Axios: **1.6.8**

## Environment Variables (Vite)

Vite will only expose env vars prefixed with `VITE_`.

This project uses:

- `VITE_API_BASE_URL` (backend API base url)
  - local dev default: `http://localhost:8000`

See `.env`:

```env
VITE_API_BASE_URL=http://localhost:8000
```

In code, axios baseURL is configured via:

```js
baseURL: import.meta.env.VITE_API_BASE_URL
```

## Run (local dev)

From repo root:

```powershell
cd frontend
npm install
npm run dev
```

Build:

```powershell
cd frontend
npm run build
```

## Pages

- `/login` 登录
- `/` 新闻列表
- `/news/:id` 新闻详情
- `/recommend` 个性推荐
- `/chat` 智能对话（RAG UI）
