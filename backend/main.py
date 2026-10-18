from fastapi import FastAPI

from backend.routes import catalog, checkout, faces, me, outfits, profile, rate, scan, tryon

app = FastAPI()
app.include_router(scan.router)
app.include_router(faces.router)
app.include_router(checkout.router)
app.include_router(me.router)
app.include_router(tryon.router)
app.include_router(catalog.router)
app.include_router(outfits.router)
app.include_router(profile.router)
app.include_router(rate.router)


@app.get("/health")
async def health():
    return {"ok": True}
