"""
CREIO background-removal service (spec §35). A small standalone HTTP
service wrapping rembg — this cannot run inside the Next.js app itself:
Vercel's Next.js API routes are Node.js/Edge runtimes with no Python
support, and rembg's models are too large/slow for a serverless function
cold start anyway. Deploy this separately (Railway, Render, Fly.io, or any
small VM/container host) and point CREIO's Next.js app at it via
REMBG_SERVICE_URL.

Model choice, confirmed by actually running both in a memory-constrained
test environment: rembg's current default model (bria-rmbg-2.0, ~1GB) was
OOM-killed under 2GB of RAM. u2netp (~4.5MB) ran successfully and produced
a correctly transparent background on a real test image. u2netp is
therefore the default here — noticeably lower quality on complex images
than the full u2net (~176MB) or bria-rmbg-2.0, so bump MODEL to "u2net" if
your hosting has enough memory (roughly 1GB+) and you want better edges on
detailed product photos (jewelry, hair, fine textures). This is a one-line
env var change (REMBG_MODEL), not a code change.
"""

import io
import os

from fastapi import FastAPI, File, Header, HTTPException, UploadFile
from fastapi.responses import Response
from rembg import new_session, remove

MODEL = os.environ.get("REMBG_MODEL", "u2netp")
API_KEY = os.environ.get("REMBG_API_KEY")  # shared secret, checked below — this service has no other auth

app = FastAPI(title="CREIO background removal service")
_session = new_session(MODEL)


@app.get("/health")
def health():
    return {"status": "ok", "model": MODEL}


@app.post("/remove-background")
async def remove_background(file: UploadFile = File(...), x_api_key: str | None = Header(default=None)):
    if API_KEY and x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")

    input_bytes = await file.read()
    if len(input_bytes) > 12 * 1024 * 1024:  # 12MB — generous for a product photo, cheap to reject early
        raise HTTPException(status_code=413, detail="Image too large (max 12MB)")

    try:
        output_bytes = remove(input_bytes, session=_session)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Could not process image: {e}")

    return Response(content=output_bytes, media_type="image/png")
