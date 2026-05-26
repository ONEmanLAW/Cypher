# BeatPath

## Install

```sh
bun install
cd backend
python3 -m venv venv
source venv/bin/activate
pip install fastapi uvicorn numpy scikit-learn joblib websockets
```

## Run

Backend :
```sh
cd backend
source venv/bin/activate
uvicorn server:app --reload --port 8000
```

Frontend :
```sh
bun run dev
```