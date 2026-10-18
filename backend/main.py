from fastapi import FastAPI

from backend.routes import checkout, faces, scan

app = FastAPI()
app.include_router(scan.router)
app.include_router(faces.router)
app.include_router(checkout.router)


@app.get("/health")
async def health():
    return {"ok": True}
