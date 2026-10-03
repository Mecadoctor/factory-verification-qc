FROM python:3.11-slim

# ffmpeg + dépendances système pour onnxruntime / opencv / soundfile
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg curl libsndfile1 libgl1 libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Pré-téléchargement du modèle Whisper (évite le téléchargement au 1er job)
# Décommentez pour pré-charger : WHISPER_MODEL=small
# RUN python -c "from faster_whisper import WhisperModel; WhisperModel('small', device='cpu', compute_type='int8')"

EXPOSE 5057
CMD ["bash", "start.sh"]
