#!/usr/bin/env bash
# Shared helper functions for build and start scripts

# Expect ROOT_DIR to be defined by the caller

# Verify required Whisper model files exist in $ROOT_DIR/models
check_whisper_models() {
    local model_dir="${MODEL_DIR:-$ROOT_DIR/models}"
    local required=(base.pt small.pt medium.pt large-v3.pt tiny.pt)
    if [ ! -d "$model_dir" ]; then
        echo "Models directory $model_dir is missing. Place Whisper model files here before running." >&2
        return 1
    fi
    for m in "${required[@]}"; do
        if [ ! -f "$model_dir/$m" ]; then
            echo "Missing $model_dir/$m. Populate the models directory before building." >&2
            return 1
        fi
    done
}

# Ensure .env exists and SECRET_KEY is populated
ensure_env_file() {
    local env_file="$ROOT_DIR/.env"
    if [ ! -f "$env_file" ]; then
        if [ -f "$ROOT_DIR/.env.example" ]; then
            cp "$ROOT_DIR/.env.example" "$env_file"
        else
            echo "No .env or .env.example found. Create one with a SECRET_KEY" >&2
            return 1
        fi
    fi

    local secret_key
    secret_key=$(grep -E '^SECRET_KEY=' "$env_file" | cut -d= -f2- || true)
    if [ -z "$secret_key" ] || [ "$secret_key" = "CHANGE_ME" ]; then
        secret_key=$(python - <<'PY'
import secrets
print(secrets.token_hex(32))
PY
)
        sed -i "s/^SECRET_KEY=.*/SECRET_KEY=$secret_key/" "$env_file"
        echo "Generated SECRET_KEY saved in $env_file"
    fi
    export SECRET_KEY="$secret_key"
}

# Create uploads, transcripts and logs directories with UID 1000 ownership
setup_persistent_dirs() {
    mkdir -p "$ROOT_DIR/uploads" "$ROOT_DIR/transcripts" "$ROOT_DIR/logs"
    if command -v sudo >/dev/null 2>&1; then
        sudo chown -R 1000:1000 "$ROOT_DIR/uploads" "$ROOT_DIR/transcripts" "$ROOT_DIR/logs" || true
    fi
}

