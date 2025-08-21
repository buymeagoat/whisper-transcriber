# Whisper Transcriber Frontend

This directory contains the React interface built with [Vite](https://vitejs.dev). It
communicates with the FastAPI backend and must be built before packaging the
application.

## Installation

From this directory install the Node dependencies (requires Node 18 or newer).
The repository's build scripts install or upgrade Node.js 18 automatically when
needed:

```bash
npm install
```

## Environment Variables

Copy `.env.example` to `.env` to configure how the frontend connects to the API.
Key variables include:

- `VITE_API_HOST` – base URL of the backend.
- `VITE_DEV_HOST` – hostname used when running `npm run dev`.
- `VITE_DEV_PORT` – port for the development server.

## Building

Generate the production assets with:

```bash
npm run build
```

The compiled files are written to `dist/` and served by the backend.
