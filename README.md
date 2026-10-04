# CREIO background-removal service

Spec §35's "Remove Background" feature. This is a small standalone Python service — it cannot live inside the main Next.js app, because Vercel's Next.js API routes are Node.js/Edge runtimes with no Python support, and rembg's ML models are too large/slow for a serverless cold start anyway. Deploy this separately and point the main app at it.

## What's actually been verified (not just written)

This was built and tested for real in the environment that produced it — not just written and assumed to work:
- `pip install rembg` succeeds and the model downloads from GitHub.
- **The current default rembg model (`bria-rmbg-2.0`, ~1GB) was OOM-killed under 2GB RAM.** This service defaults to `u2netp` (~4.5MB) instead, which ran successfully. If you deploy on a host with more memory (~1GB+) and want better edge quality on detailed photos (jewelry, hair, fine textures), set `REMBG_MODEL=u2net` (~176MB, better quality than u2netp, much lighter than the 1GB default) — one env var, no code change.
- A real end-to-end test: started the service, sent an actual image over real HTTP, got back a correctly-transparent PNG. Confirmed the `X-Api-Key` auth check actually rejects unauthenticated requests (401) and accepts authenticated ones (200).

**Not verified:** the Dockerfile itself — no Docker available in the build environment to actually run `docker build`. It follows a standard, common pattern for a Python service, but "should build" and "has built" are different claims, same distinction as everywhere else in this project. Build it once yourself before relying on it.

## Deploying it

Any container host works — Railway, Render, Fly.io, or your own VM. Steps are the same shape everywhere:

1. Push this `rembg-service/` folder (or the whole repo, pointing the platform at this subdirectory) to your host of choice.
2. Set environment variables:
   - `REMBG_API_KEY` — a random secret string. The main CREIO app sends this as an `X-Api-Key` header; without it set, the service accepts unauthenticated requests, which is fine for local testing but not for a public URL.
   - `REMBG_MODEL` — optional, defaults to `u2netp`.
3. Deploy. The platform builds from the `Dockerfile` and exposes port 8000.
4. Test it: `curl https://your-service-url/health` should return `{"status":"ok","model":"u2netp"}`.
5. In the main CREIO app's `.env.local` / production environment: set `REMBG_SERVICE_URL=https://your-service-url` and `REMBG_API_KEY` to the same secret from step 2.

## Local development

```
cd rembg-service
pip install -r requirements.txt
REMBG_API_KEY=dev-secret uvicorn main:app --reload --port 8000
```

## API

`POST /remove-background` — multipart form with a `file` field (an image), `X-Api-Key` header if `REMBG_API_KEY` is set. Returns the processed image as `image/png` with a transparent background, or a 4xx with a JSON `detail` on failure (image too large, unreadable, or missing/wrong API key).

`GET /health` — for your hosting platform's health checks.
