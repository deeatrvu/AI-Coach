# MedRep Coach - Environment Setup Guide

## Required Environment Variables

### 1. OpenAI API Key (Required)
```bash
OPENAI_API_KEY=sk-your-actual-openai-api-key-here
```

**How to get:**
1. Go to https://platform.openai.com/api-keys
2. Create a new secret key
3. Copy the key (starts with `sk-`)
4. Add it to your `.env` file

### 2. Optional Configuration
```bash
# Model selection
OPENAI_TEXT_MODEL=gpt-4o-mini
OPENAI_REALTIME_VOICE=verse

# Server settings
HOST=localhost
PORT=8000
DEBUG=true
```

## Setup Instructions

### Step 1: Create Environment File
```bash
cd backend
cp env.example .env
```

### Step 2: Add Your OpenAI API Key
Edit `backend/.env` and replace `your_openai_api_key_here` with your actual API key.

### Step 3: Verify Setup
```bash
# Test the backend
cd backend
python -m uvicorn app.main:app --reload
```

You should see:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
```

### Step 4: Test API Key
```bash
curl http://localhost:8000/health
```

Should return: `{"status":"ok"}`

## Security Notes

- **Never commit `.env` files** to version control
- **Keep your OpenAI API key secret** - it's used for billing
- **Use different keys** for development and production
- **Rotate keys regularly** for security

## Troubleshooting

### "OPENAI_API_KEY missing" Error
- Check that `.env` file exists in `backend/` directory
- Verify the key starts with `sk-`
- Ensure no extra spaces or quotes around the key

### "OpenAI session creation failed" Error
- Verify your API key is valid and active
- Check your OpenAI account has sufficient credits
- Ensure you have access to `gpt-4o-realtime-preview` model

### CORS Errors
- Add your frontend URL to `CORS_ORIGINS` in `.env`
- Default allows all origins (`*`) in development
