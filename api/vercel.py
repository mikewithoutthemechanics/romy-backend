from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.main import app as main_app

app = FastAPI(title="Romy Agent API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Forward all routes from main app
app.root_path = main_app.root_path

# ========================
# Add routes from main.py
# ========================