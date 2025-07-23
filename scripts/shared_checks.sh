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

# Verify ffmpeg is installed and on PATH
check_ffmpeg() {
    if ! command -v ffmpeg >/dev/null 2>&1; then
        echo "ffmpeg executable not found. Please install ffmpeg and ensure it is in your PATH." >&2
        return 1
    fi
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

# Ensure the Docker registry is reachable
check_docker_registry() {
    echo "Checking Docker Hub connectivity..." >&2
    if ! docker pull --quiet docker/dockerfile:1.4 >/dev/null 2>&1; then
        echo "Unable to reach registry-1.docker.io. Configure network or proxy settings before building." >&2
        return 1
    fi
}

# Return 0 when pypi.org and registry.npmjs.org are reachable
check_internet() {
    curl -sSf https://pypi.org >/dev/null 2>&1 \
        && curl -sSf https://registry.npmjs.org >/dev/null 2>&1
}

# Verify Node.js is installed and at least version 18
check_node_version() {
    if ! command -v node >/dev/null 2>&1; then
        echo "Node.js executable not found in PATH" >&2
        return 1
    fi
    local version
    version=$(node --version | sed 's/^v//')
    local major=${version%%.*}
    if [ "$major" -lt 18 ]; then
        echo "Node.js 18 or newer is required. Found $version" >&2
        return 1
    fi
}

# Ensure the docker compose CLI is available
check_docker_compose() {
    if ! docker compose version >/dev/null 2>&1; then
        echo "'docker compose' command not available. Install Docker Compose v2." >&2
        return 1
    fi
}

# Ensure python packages and node modules are installed and docker images pulled
stage_build_dependencies() {
    check_node_version
    check_docker_compose
    local compose_file="$ROOT_DIR/docker-compose.yml"
    local base_image
    base_image=$(grep -m1 '^FROM ' "$ROOT_DIR/Dockerfile" | awk '{print $2}')

    local pip_cache="${CACHE_DIR:-$ROOT_DIR/cache}/pip"
    local npm_cache="${CACHE_DIR:-$ROOT_DIR/cache}/npm"
    local image_cache="${CACHE_DIR:-$ROOT_DIR/cache}/images"

    mapfile -t compose_images < <(docker compose -f "$compose_file" config | awk '/image:/ {print $2}' | sort -u)
    local images=("$base_image" "${compose_images[@]}")

    if check_internet && check_docker_registry; then
        echo "Prefetching build dependencies..." >&2
        for img in "${images[@]}"; do
            if ! docker image inspect "$img" >/dev/null 2>&1; then
                docker pull "$img"
            fi
        done
        if [ -d "$pip_cache" ]; then
            pip install --no-index --find-links "$pip_cache" -r "$ROOT_DIR/requirements.txt"
        else
            pip install -r "$ROOT_DIR/requirements.txt"
        fi
        if [ -d "$npm_cache" ]; then
            npm ci --offline --prefix "$ROOT_DIR/frontend" --cache "$npm_cache"
        else
            (cd "$ROOT_DIR/frontend" && npm install)
        fi
    else
        echo "No internet connection. Verifying staged components..." >&2
        if [ ! -d "$image_cache" ]; then
            echo "Image cache directory $image_cache missing" >&2
            return 1
        fi
        for img in "${images[@]}"; do
            if ! docker image inspect "$img" >/dev/null 2>&1; then
                local tar="$image_cache/$(echo "$img" | sed 's#[/:]#_#g').tar"
                if [ -f "$tar" ]; then
                    docker load -i "$tar" >/dev/null
                else
                    echo "Missing cached Docker image $tar" >&2
                    return 1
                fi
            fi
        done

        if [ -d "$pip_cache" ]; then
            pip install --no-index --find-links "$pip_cache" -r "$ROOT_DIR/requirements.txt"
        else
            echo "Pip cache directory $pip_cache missing" >&2
            while read -r pkg; do
                pkg=${pkg%%[*#]*}
                pkg=$(echo "$pkg" | xargs)
                [ -z "$pkg" ] && continue
                pkg=${pkg%%=*}
                if ! pip show "$pkg" >/dev/null 2>&1; then
                    echo "Missing python dependency $pkg" >&2
                    return 1
                fi
            done < "$ROOT_DIR/requirements.txt"
        fi

        if [ -d "$npm_cache" ]; then
            npm ci --offline --prefix "$ROOT_DIR/frontend" --cache "$npm_cache"
        else
            echo "Npm cache directory $npm_cache missing" >&2
            if [ ! -d "$ROOT_DIR/frontend/node_modules" ]; then
                echo "Missing frontend/node_modules" >&2
                return 1
            fi
        fi
    fi
}

