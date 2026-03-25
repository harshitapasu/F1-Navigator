# 🚀 F1 Navigator Vercel Deployment Guide

## Overview
- **Frontend:** Deployed on Vercel (Next.js)
- **Backend:** Deployed on Railway (FastAPI)
- **Database:** PostgreSQL on Railway
- **Total time:** ~30-45 minutes

---

## STEP 1: Prepare Your GitHub Repository

Your repository is already cloned. Before deploying, ensure:

```bash
# Navigate to project directory
cd C:\Users\harsh\F1-Navigator

# If not already done, ensure these files exist:
# backend/.env.example (created)
# frontend/.env.local.example (created)

# Add to .gitignore (should already be there):
# backend/.env (keep secret locally)
# frontend/.env.local (keep secret locally)
```

---

## STEP 2: Get Required API Keys

You'll need several API keys. Obtain them now:

### 🔑 A. OpenAI API Key
1. Go to https://platform.openai.com/api-keys
2. Sign up or log in
3. Click "Create new secret key"
4. Copy and save it somewhere safe (you'll need it later)
5. **Cost:** Pay-as-you-go (includes free credits)

### 🔑 B. Pinecone Vector Database
1. Go to https://www.pinecone.io/
2. Sign up for free
3. Create a new index (or use existing "edtech")
4. Copy:
   - `PINECONE_INDEX_NAME`
   - `PINECONE_HOST` (API endpoint)
5. Generate an API key
6. **Cost:** Free tier available

### 🔑 C. Gmail App Password (for email notifications)
1. Go to https://myaccount.google.com/security
2. Enable "2-Step Verification" (if not done)
3. Go to https://myaccount.google.com/apppasswords
4. Select "Mail" and "Windows Computer"
5. Generate and copy the 16-character password
6. **Cost:** Free (your Gmail account)

---

## STEP 3: Deploy Backend to Railway 🚂

Railway is the easiest way to deploy Python backends with free tier.

### 3.1 Create Railway Account
1. Go to https://railway.app
2. Click "Start Project"
3. Sign in with GitHub (recommended)
4. Authorize Railway to access your repositories

### 3.2 Create PostgreSQL Database
1. In Railway dashboard, click "New Project"
2. Select "Provision PostgreSQL"
3. A PostgreSQL instance will be created
4. Click on it and go to "Variables" tab
5. You'll see `DATABASE_URL` - copy it
6. **Important:** Save this URL - you'll need it in step 3.5

### 3.3 Deploy Backend Service
1. In same Railway project, click "New Service"
2. Select "GitHub Repo"
3. Search for `geee28/F1-Navigator`
4. Select it
5. In the "Variables" tab, add:
   - `OPENAI_API_KEY` (from Step 2A)
   - `PINECONE_INDEX_NAME` (from Step 2B)
   - `PINECONE_HOST` (from Step 2B)
   - `SMTP_HOST=smtp.gmail.com`
   - `SMTP_PORT=587`
   - `SMTP_USER` (your Gmail)
   - `SMTP_PASS` (16-char from Step 2C)
   - `FRONTEND_URL` (leave blank for now, will update after Vercel)

### 3.4 Configure Service
1. Click "Settings" tab
2. Set "Root Directory" to `backend`
3. Set "Start Command" to: `uvicorn main:app --host 0.0.0.0 --port 8000`
4. In "Environment" section ensure Python 3.11+ is selected

### 3.5 Deploy
1. Click "Deploy"
2. Wait 3-5 minutes for deployment
3. Once complete, you'll get a public URL like: `https://your-backend-xxxxxx.railway.app`
4. **Copy this URL** - you'll need it for Vercel configuration

---

## STEP 4: Set Up Vercel Account

### 4.1 Create Vercel Account
1. Go to https://vercel.com
2. Click "Sign Up"
3. Sign in with GitHub (recommended)
4. Authorize Vercel

### 4.2 Create Vercel Project
1. Click "Add New..." → "Project"
2. Search for `F1-Navigator` repository
3. Click "Import"
4. In "Configure Project":
   - **Framework Preset:** Next.js (auto-detected)
   - **Project Name:** f1-navigator (or choose your own)
   - **Root Directory:** `./frontend`

### 4.3 Environment Variables Setup
1. Before deploying, click "Environment Variables"
2. Add one variable:
   - **Name:** `NEXT_PUBLIC_API_URL`
   - **Value:** `https://your-backend-xxxxxx.railway.app` (from Step 3.5)
   - **Environments:** All (Production, Preview, Development)
3. Click "Add"

### 4.4 Deploy to Vercel
1. Click "Deploy"
2. Wait 3-5 minutes
3. Once complete, you'll get a public URL: `https://f1-navigator-xxxxxx.vercel.app`

---

## STEP 5: Update Backend CORS Settings

Your backend needs to allow requests from Vercel domain:

1. Go back to Railway dashboard
2. Select your backend service
3. In "Variables" tab, update:
   - `FRONTEND_URL=https://f1-navigator-xxxxxx.vercel.app`
4. Railway will auto-redeploy

---

## STEP 6: Test the Deployment ✅

1. Open your Vercel URL: `https://f1-navigator-xxxxxx.vercel.app`
2. Try creating an account
3. Test the chat feature
4. Verify document upload works
5. Check backend logs on Railway dashboard

---

## Troubleshooting

### Chat not working / API errors
- Check Railway dashboard → Backend service → Logs
- Verify `OPENAI_API_KEY` is set correctly
- Ensure `NEXT_PUBLIC_API_URL` matches Railway backend URL

### Database connection errors
- Check `DATABASE_URL` is properly set in Railway backend variables
- Ensure PostgreSQL service is running

### Email notifications not sending
- Verify Gmail app password is correct (not regular password)
- Ensure 2FA is enabled on Gmail
- Check railway logs for SMTP errors

### CORS errors in browser console
- Update `FRONTEND_URL` in Railway backend variables
- Wait a few minutes for redeploy

---

## Local Testing Before Deployment (Optional but Recommended)

```bash
# Setup local environment
cd C:\Users\harsh\F1-Navigator
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt

# Create backend/.env with all variables
# Create frontend/.env.local with NEXT_PUBLIC_API_URL=http://localhost:8000

# Terminal 1: Start backend
cd backend
uvicorn main:app --reload --port 8000

# Terminal 2: Start frontend
cd frontend
npm install
npm run dev

# Visit http://localhost:3000
```

---

## Summary of URLs You'll Have

After deployment:
- **Frontend URL:** https://f1-navigator-xxxxxx.vercel.app
- **Backend API:** https://your-backend-xxxxxx.railway.app
- **API Docs:** https://your-backend-xxxxxx.railway.app/docs

---

## Next Steps

1. Gather API keys (OpenAI, Pinecone, Gmail)
2. Follow Step 3 to deploy backend on Railway
3. Follow Step 4 to deploy frontend on Vercel
4. Test everything works
5. Share your Vercel URL with others for demo!

Need help with any specific step? Ask!
