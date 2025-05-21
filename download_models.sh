#!/bin/bash

# Target directory for model files
MODEL_DIR="models"
MODELS=("tiny" "base" "small" "medium" "large")
DUMMY_WAV="dummy.wav"

# Create model directory
mkdir -p "$MODEL_DIR"

# Generate 0.1 sec silent WAV file if missing
if [ ! -f "$DUMMY_WAV" ]; then
    echo "🎙️ Generating silent dummy file: $DUMMY_WAV"
    ffmpeg -f lavfi -i anullsrc=r=16000:cl=mono -t 0.1 -q:a 9 -acodec pcm_s16le "$DUMMY_WAV" -y
fi

# Download each model using the dummy audio
for MODEL in "${MODELS[@]}"; do
    echo "🔽 Downloading model: $MODEL"
    whisper "$DUMMY_WAV" \
        --model "$MODEL" \
        --model_dir "$MODEL_DIR" \
        --output_dir /tmp/ignore_output \
        --output_format txt \
        --language en \
        --task translate \
        --verbose False
    echo "✅ $MODEL cached"
done

echo "🎉 All models are cached in $MODEL_DIR/"
