FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py .

# Pre-download the model at build time so the first real request isn't slow
# and so a container that can't reach GitHub at runtime still works.
RUN python3 -c "from rembg import new_session; new_session('u2netp')"

ENV REMBG_MODEL=u2netp
EXPOSE 8000

# If you ever switch REMBG_MODEL to "sam" (Segment Anything), that session
# imports opencv-python, which needs libgl1/libglib2.0-0 at the OS level —
# confirmed by checking rembg's source, not needed for u2net/u2netp (the
# default here). Add `apt-get install -y libgl1 libglib2.0-0` above if so.

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
