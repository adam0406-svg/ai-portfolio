from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path

app = FastAPI()

FRONTEND = Path(__file__).parent.parent / "frontend"
app.mount("/assets", StaticFiles(directory=FRONTEND / "assets"), name="assets")

@app.get("/")
async def root():
    return FileResponse(FRONTEND / "index.html")

@app.get("/adam.png")
async def portrait():
    return FileResponse(FRONTEND / "adam.png")
