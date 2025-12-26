import os
import logging
import uvicorn
from fastapi import FastAPI
from flask import Flask

# --- Logging setup for clarity ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("unified_app")

# --- Flask UI app ---
flask_app = Flask(__name__)

@flask_app.route("/")
def index():
    return "AIlice UI is alive (Flask)"

# --- FastAPI backend app ---
fastapi_app = FastAPI()

@fastapi_app.get("/")
def read_root():
    return {"message": "AIlice API is alive (FastAPI)"}

# --- Unified entrypoint ---
def main():
    mode = os.getenv("APP_MODE", "fastapi").lower()
    port = int(os.getenv("PORT", "8080"))

    if mode == "flask":
        logger.info("Starting Flask UI service on port %s", port)
        flask_app.run(host="0.0.0.0", port=port)
    elif mode == "fastapi":
        logger.info("Starting FastAPI backend service on port %s", port)
        uvicorn.run(fastapi_app, host="0.0.0.0", port=port)
    else:
        logger.error("Unknown APP_MODE '%s'. Use 'flask' or 'fastapi'.", mode)
        raise ValueError(f"Invalid APP_MODE: {mode}")

if __name__ == "__main__":
    main()
