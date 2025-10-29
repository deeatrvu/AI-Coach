# MedRep Coach Frontend (jQuery + TypeScript)

Prerequisites
- Node 18+
- Backend running at http://localhost:8000 (FastAPI)

Install
```bash
cd frontend
npm install
```

Develop
```bash
npm run watch
# open frontend/public/index.html in a browser (served by any static server or direct file)
```

Build
```bash
npm run build
# outputs public/bundle.js
```

Configure
Add this before bundle.js in index.html if backend URL differs:
```html
<script>
  window.API_BASE = "http://localhost:8000/api";
<\/script>
```

Features
- Start/Stop conversation via REST
- Send rep messages and receive dynamic doctor replies
- Live persona indicators (mood, stage, skepticism, trust, time pressure)
- Transcript and feedback view

Next steps
- Integrate WebRTC audio pipeline (AudioManager)
- Add waveform and barge-in controls
- Improve feedback visualization

