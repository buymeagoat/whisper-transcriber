# Integrations

👤 Target Audience: Developers and Operators

This document lists optional third-party services that can enhance or extend Whisper Transcriber.

## Cloud Storage Providers
- **Amazon S3** – Set `STORAGE_BACKEND=cloud` and configure `S3_BUCKET` and credentials. The worker uploads transcripts and audio files to the bucket.
- **Local filesystem** – Default mode where data stays under `uploads/` and `transcripts/`.

## LLMs
- **OpenAI API** – Used for optional text analysis or future features. Set `OPENAI_API_KEY` to enable.

## Monitoring Systems
- **Prometheus** – Metrics endpoint exposed at `/metrics`. Point Prometheus to the API container.
- **Log streaming** – Containers write logs under `logs/`. Use existing tools such as Filebeat to ship them.

## CI/CD Pipelines
- No official pipeline is provided yet. The scripts are designed to run in Docker-based CI platforms. Contributions are welcome to integrate GitHub Actions or similar services.
