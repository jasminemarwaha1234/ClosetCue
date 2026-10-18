from fastapi import FastAPI

from backend.routes import catalog, checkout, faces, me, scan, tryon

app = FastAPI()
app.include_router(scan.router)
app.include_router(faces.router)
app.include_router(checkout.router)
app.include_router(me.router)
app.include_router(tryon.router)
app.include_router(catalog.router)


@app.get("/health")
async def health():
    return {"ok": True}
