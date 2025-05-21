#!/bin/bash

MODEL_DIR="models"
MODELS=("tiny" "base" "small" "medium" "large")
DUMMY_WAV="dummy.wav"
LOG_FILE="logs/model_download.log"

mkdir -p "$MODEL_DIR"
mkdir -p "logs"

timestamp() {
  date +"%Y-%m-%dT%H:%M:%S"
}

log() {
  echo "[$(timestamp)] $1" | tee -a "$LOG_FILE"
}

# Generate dummy WAV if needed
if [ ! -f "$DUMMY_WAV" ]; then
  log "🎙️ Generating silent dummy file: $DUMMY_WAV"
  ffmpeg -f lavfi -i anullsrc=r=16000:cl=mono -t 0.1 -q:a 9 -acodec pcm_s16le "$DUMMY_WAV" -y
fi

# Download loop
for MODEL in "${MODELS[@]}"; do
  log "🔽 Attempting download for model: $MODEL"
  
  whisper "$DUMMY_WAV" \
    --model "$MODEL" \
    --model_dir "$MODEL_DIR" \
    --output_dir /tmp/ignore_output \
    --output_format txt \
    --language en \
    --task translate \
    --verbose False

  if [ $? -eq 0 ]; then
    log "✅ Model '$MODEL' successfully cached"
  else
    log "❌ ERROR downloading model: $MODEL"
  fi
done

log "🎉 Model caching complete. Check '$MODEL_DIR' and '$LOG_FILE' for status."
