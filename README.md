# AI Coach - Medical Representative Training Platform

A sophisticated AI-powered training platform that simulates realistic conversations between medical representatives and doctors using OpenAI's Realtime API for voice-to-voice interactions.

## 🎯 Overview

AI Coach is designed to train medical representatives through realistic, persona-driven conversations with AI "doctors". The platform uses speech-to-speech technology powered by OpenAI's `gpt-4o-realtime-preview` model, providing real-time voice interactions with dynamic coaching and evaluation.

### Key Features

- **Voice-to-Voice Training**: Real-time speech-to-speech conversations using OpenAI Realtime API
- **Dynamic Doctor Personas**: 8 realistic doctor personas with unique communication styles and behavioral patterns
- **Real-time Coaching**: Live feedback and guidance during conversations
- **Comprehensive Evaluation**: Detailed scoring and analysis of conversation performance
- **Tone Management**: Dynamic mood and behavior adaptation based on conversation flow
- **Compliance Tracking**: Monitor must-say/must-not-say requirements

### Technology Stack

**Backend (Python FastAPI)**
- FastAPI for REST API endpoints
- OpenAI API integration for AI conversations
- Pydantic for data validation
- Uvicorn ASGI server

**Frontend (TypeScript + jQuery)**
- TypeScript for type safety
- jQuery for DOM manipulation
- ESBuild for bundling
- WebRTC for real-time audio streaming

### System Components

1. **Backend API Server**: Handles session management, persona serving, evaluation, and tone control
2. **Frontend Web App**: Provides the user interface for voice interactions and feedback
3. **OpenAI Realtime API**: Powers the voice-to-voice conversation engine
4. **Evaluation Engine**: Analyzes conversation quality and provides structured feedback

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+
- OpenAI API key with access to `gpt-4o-realtime-preview`

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd AI_Coach
   ```

2. **Backend Setup**
   ```bash
   cd backend
   pip install -r requirements.txt
   
   # Create environment file
   cp env.example .env
   
   # Edit .env and add your OpenAI API key
   OPENAI_API_KEY=sk-your-actual-openai-api-key-here
   ```

3. **Frontend Setup**
   ```bash
   cd frontend
   npm install
   ```

### Running the Application

1. **Start the Backend Server**
   ```bash
   cd backend
   uvicorn app.main:app --reload --app-dir backend
   ```
   Server will be available at `http://localhost:8000`

2. **Start the Frontend**
   ```bash
   cd frontend
   npm run dev
   ```
   Open `http://localhost:3000` in your browser

3. **Begin Training**
   - Click "Start" to begin a voice session
   - Allow microphone access when prompted
   - Speak naturally as a medical representative
   - Use Space for push-to-talk, M to mute, P to toggle PTT
   - Click "Stop" to end the session and view evaluation

## 🎮 Usage Controls

### Voice Controls
- **Space**: Push-to-talk (hold to speak)
- **M**: Toggle mute
- **P**: Toggle push-to-talk mode
- **Click Start**: Begin voice session
- **Click Stop**: End session and view evaluation

## 🔒 Security

- OpenAI API keys are never exposed to the frontend
- Ephemeral session tokens are generated server-side
- Short-lived credentials for each session
- CORS protection for API endpoints

### Backend Development
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --app-dir backend
```

### Frontend Development
```bash
cd frontend
npm dev run
```
**"OPENAI_API_KEY missing" Error**
- Ensure `.env` file exists in `backend/` directory
- Verify API key starts with `sk-`
- Check for extra spaces or quotes around the key

**"OpenAI session creation failed" Error**
- Verify API key is valid and active
- Check OpenAI account has sufficient credits
- Ensure access to `gpt-4o-realtime-preview` model

**No Audio Output**
- Check browser autoplay permissions
- Verify microphone access is granted
- Ensure HTTPS or localhost is used for WebRTC

**CORS Errors**
- Backend allows all origins (`*`) in development
- For production, configure specific origins in CORS settings

## 🤝 Contributing

I have done this project as part of my internship at NTT DATA

**Note**: This platform is designed for training purposes and should not be used as a substitute for actual medical consultation or decision-making.
