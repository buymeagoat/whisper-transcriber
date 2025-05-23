# Whisper Transcriber — Full System Blueprint and Guardrails

---

## 🔭 Project Vision

An AI-enhanced transcription and job management tool for uploading audio files, selecting transcription settings, processing with OpenAI Whisper, managing jobs (active/completed), and accessing results — all within a clean web-based frontend backed by a Python FastAPI backend.

Goal: Build a scalable MVP supporting real-time job tracking, basic admin tools, and extendability.

---

## 🗂️ Folder and File Structure

```
whisper-transcriber/
├── backend/
│   ├── main.py                # FastAPI app, all API endpoints
│   ├── jobs.db                # SQLite DB file
│   └── ...                    # Future: logs, utils
├── frontend/
│   ├── src/
│   │   ├── App.jsx            # Main React Router + Nav
│   │   ├── main.jsx          # Entrypoint
│   │   ├── ActiveJobsPage.jsx
│   │   ├── CompletedJobsPage.jsx
│   │   ├── AdminLogsPage.jsx
│   │   ├── TranscriptViewPage.jsx
│   │   └── UploadPage.jsx
│   └── ...
├── jobs.db (or backend/jobs.db)
└── design_scope.md            # This file — authoritative project blueprint
```

---

## 📦 Core Features

### Upload Page

* File selector
* Model selector
* Optional settings (temperature, language, etc.)
* Submit button creates new job and routes to Active Jobs

### Active Jobs Page

* Polling or refresh button for status
* Shows filename, model, time submitted, and status
* Always shows table, even if no jobs

### Completed Jobs Page

* Table with:

  * Filename (links to transcript view)
  * Model used
  * Timestamp completed
  * Buttons:

    * View Transcript (routes to TranscriptViewPage)
    * Download Transcript (link)
    * Download Audio (link)
    * Restart (opens prompt for model, POSTs to /restart)
    * Delete (calls DELETE and removes row)

### Transcript View Page

* `/transcript/:jobId/view`
* Fetches text of transcript
* Displays in scrollable container
* Back link to Completed Jobs

### Admin Logs Page

* Shows server logs
* May show errors or system events
* Future: export/download, filter

---

## 🔌 API Endpoints

```
GET    /jobs?status=active|completed
GET    /transcript/{job_id}/view
GET    /audio/{job_id}
POST   /jobs/{job_id}/restart
DELETE /jobs/{job_id}
POST   /upload (WIP)
```

All return JSON or file downloads. Failures must return JSON `{"error": "msg"}`.

---

## 🚨 Anti-Drift Project Safeguards

1. **Component Placement:**

   * All `.jsx` components go under `frontend/src/`
   * Do **not** create subfolders like `/pages` unless explicitly approved

2. **Naming Consistency:**

   * Component and filename match (e.g., `CompletedJobsPage.jsx → CompletedJobsPage`)
   * All routes declared in `App.jsx`

3. **Interaction Rules:**

   * Avoid duplicate component declarations in `App.jsx`
   * All components imported, not defined inline

4. **Fail-Safe Behaviors:**

   * Show empty tables rather than conditional renders
   * Handle failed fetches with fallback error messages

5. **Prompting Consistency:**

   * All page-level components must:

     * use `useEffect()`
     * handle loading, error, and data display states

---

## 🤝 Assistant Interaction Guardrails

1. **Explicit File Placement:**

   * Always state: “Save this as `CompletedJobsPage.jsx` in `/frontend/src/`”
   * No assumptions — always specify

2. **Patch Format Rules:**

   * Use full file rewrites when refactoring
   * Only use patch instructions when explicitly asked

3. **Assumption Echoing:**

   * Repeat back implicit user assumptions before acting
   * If a component is already in `App.jsx`, confirm whether to delete it before refactoring

4. **Naming Conflicts:**

   * Do not duplicate component names — check `App.jsx` before defining new component

5. **Session Continuity:**

   * New session must begin with:

     > “Continue whisper-transcriber session. Use `design_scope.md` as the authority.”

6. **Frontend Behavior:**

   * Vite + React assumed as dev environment
   * Local API assumed at `localhost:8000`

---

## 🧱 Future Features (post-MVP)

* Multi-user authentication
* Job prioritization
* Batch upload
* Subtitle (SRT/VTT) support
* Real-time log stream via WebSockets
* Auto-restart failed jobs
* Configurable server settings from admin UI
* Job tagging + notes

---

## ✅ Status Summary

| Component              | Status   |
| ---------------------- | -------- |
| UploadPage.jsx         | TODO     |
| ActiveJobsPage.jsx     | ✅ Stable |
| CompletedJobsPage.jsx  | ✅ Stable |
| TranscriptViewPage.jsx | ✅ Stable |
| AdminLogsPage.jsx      | ✅ Stable |
| main.py (API)          | ✅ Stable |
| App.jsx                | ✅ Stable |

---

## 🧭 Update Instructions

Only update `design_scope.md` when:

* Folder structure changes
* Endpoint behavior changes
* Page responsibilities shift
* Guardrails are refined for consistency
