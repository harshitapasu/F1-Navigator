# Railway Full Deployment - Updated Workflow

## 🎯 Strategy
**Single Railway service** with multi-stage Docker build that includes:
- Frontend (Next.js) compiled in Stage 1
- Backend (FastAPI) runtime in Stage 2  
- Both served from `https://your-app.railway.app`

---

## 📝 Files Changed

### 1. **Root Dockerfile** (UPDATED)
- **What changed**: Now multi-stage build
- **Stage 1**: Builds Next.js frontend with pnpm
- **Stage 2**: Python + FastAPI backend that serves compiled frontend
- **Why**: Single Docker image = simpler Railway deployment

### 2. **`.dockerignore`** (NEW)
- Creates cleaner Docker builds
- Excludes node_modules, .next, __pycache__, .git, etc.

### 3. **`backend/main.py`** (UPDATED - CORS)
- **Changed from**: Hardcoded Vercel URLs
- **Changed to**: Environment-based CORS + localhost fallback
- **Why**: Works with Railway domain without code changes

### 4. **`frontend/next.config.mjs`** (UPDATED)
- **Changed from**: Hardcoded `http://localhost:8000` rewrites
- **Changed to**: Uses `NEXT_PUBLIC_API_URL` environment variable
- **Why**: Frontend can point to Railway backend dynamically

### 5. **`railway.json`** (UPDATED)
- **Changed from**: Generic Dockerfile detection
- **Changed to**: Explicit root Dockerfile context
- **Why**: Ensures Railway uses the new multi-stage Dockerfile

### 6. **`backend/Dockerfile`** (OPTIONAL - Can keep or delete)
- No longer used by Railway
- Can be deleted to reduce clutter
- Or kept for local development

---

## ⚙️ Railway Configuration

In Railway Dashboard, **no special configuration needed**:

1. Backend service should have these variables set:
   - `DATABASE_URL` ✅ (already set)
   - `OPENAI_API_KEY` ✅ (already set)
   - `PINECONE_API_KEY` ✅ (already set)
   - `PINECONE_INDEX_NAME` ✅ (already set)
   - `PINECONE_HOST` ✅ (already set)
   - `SMTP_HOST` ✅ (already set)
   - `SMTP_PORT` ✅ (already set)
   - `SMTP_USER` ✅ (already set)
   - `SMTP_PASS` ✅ (already set)
   - `FRONTEND_URL` ❌ (Can be removed or left empty)
   - `JWT_SECRET` (optional - uses default if not set)

2. **Root Directory**: Should be `.` (root)
3. **Builder**: Should auto-detect `Dockerfile`

---

## 🚀 Deployment Steps

1. **Push code to GitHub**:
   ```bash
   git add .
   git commit -m "Railway full deployment: monolithic Docker build"
   git push
   ```

2. **Railway auto-deploys**:
   - Detects new code push
   - Builds with multi-stage Dockerfile
   - Deploys single service with both frontend + backend

3. **Access your app**:
   ```
   https://f1-navigator-production.up.railway.app
   ```
   - Frontend loads automatically
   - Frontend API calls go to `/api/*` on same domain
   - Next.config rewrites handle routing to backend

---

## 🧪 Testing Checklist

- [ ] Push code to GitHub
- [ ] Check Railway Deploy tab - build should complete in 3-5 min
- [ ] Visit `https://f1-navigator-production.up.railway.app`
- [ ] See Next.js frontend load
- [ ] Try signup (POST `/api/auth/signup`)
- [ ] Try login (POST `/api/auth/login`)
- [ ] Check browser console for no CORS errors
- [ ] Test chat functionality
- [ ] Test document upload
- [ ] Check Railway logs for any errors

---

## 🐛 If Something Goes Wrong

**Build fails?**
- Check Railway Deploy logs for errors
- Likely Docker issue: Node/Python versions, missing packages
- Run locally first: `docker build -t test-build .`

**Frontend doesn't load?**
- Check Railway container logs
- Ensure multi-stage build Stage 1 succeeded
- Verify frontend was copied to `/app/static/`

**API calls fail (CORS)?**
- Check `backend/main.py` CORS config
- Ensure frontend can reach backend on same domain
- No need for CORS headers when same domain

**Auth failing?**
- Check database connection (DATABASE_URL)
- Verify user exists in PostgreSQL
- Check JWT_SECRET is set (or uses default)

---

## 📊 Architecture Diagram

```
┌─────────────────────────────┐
│   GitHub Repository         │
│  (All code + Dockerfile)    │
└──────────┬──────────────────┘
           │ git push
           ▼
┌─────────────────────────────┐
│ Railway Docker Build        │
│ ┌───────────────────────┐   │
│ │ Stage 1: Next.js      │   │
│ │ Compiles to .next/    │   │
│ └───────────────────────┘   │
│ ┌───────────────────────┐   │
│ │ Stage 2: Python       │   │
│ │ + FastAPI + Frontend  │   │
│ └───────────────────────┘   │
└──────────┬──────────────────┘
           │
           ▼
┌─────────────────────────────┐
│  Single Railway Service     │
│                             │
│  https://your-app.railway   │
│   ├── Frontend (Next.js)    │
│   ├── Backend (FastAPI)     │
│   └── DB (PostgreSQL)       │
└─────────────────────────────┘
```

---

## ✅ Summary

**Before:**
- Frontend on Vercel (separate platform)
- Backend on Railway (separate platform)
- CORS complexity, multiple deployments

**After:**
- Everything on Railway
- Single monolithic Docker image
- Simple deployment, no CORS issues
- Same domain for frontend + backend
- Easier to manage, debug, scale

