import numpy as np
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import joblib
from pathlib import Path

from recognizer import MFCCExtractor, MFCCConfig, compute_rms

SR = 48000
MODEL_PATH = Path(__file__).parent / "model.joblib"

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

model = joblib.load(MODEL_PATH)
extractor = MFCCExtractor(MFCCConfig(sr=SR))

print("Classes du modèle:", list(model.classes_))

@app.get("/health")
def health():
    return {"ok": True, "classes": list(model.classes_)}

@app.websocket("/detect")
async def detect(ws: WebSocket):
    await ws.accept()
    try:
        while True:
            raw = await ws.receive_bytes()
            # 👇 une frame invalide ne doit PAS fermer la socket
            try:
                x = np.frombuffer(raw, dtype=np.float32)

                rms = compute_rms(x)
                if rms < 0.01:
                    await ws.send_json({"label": None, "confidence": 0.0, "rms": rms})
                    continue

                feat = extractor.features(x).reshape(1, -1)
                probas = model.predict_proba(feat)[0]
                top = int(np.argmax(probas))
                await ws.send_json({
                    "label": str(model.classes_[top]),
                    "confidence": float(probas[top]),
                    "rms": float(rms),
                })
            except Exception as e:
                print("frame error:", e)
                continue
    except WebSocketDisconnect:
        pass