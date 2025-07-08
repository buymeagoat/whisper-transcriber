# Future Updates

This document organizes upcoming features for Whisper Transcriber. Items are grouped by status and each includes context for implementation.

## Status Definitions
- **Open** – prioritized but not yet started.
- **On Hold** – work paused pending other dependencies.
- **Partial** – partially implemented; more work remains.

## Open

### Sortable Job Table Component
- **Summary**: Provide a table view where jobs can be ordered by time, name, or status.
- **Motivation**: Helps admins locate active and completed jobs quickly.
- **Implementation Notes**: Add sort parameters to the `/jobs` API and adopt a sortable React table library.
- **Considerations**: Large datasets will require pagination.
- **Roadblocks**: None identified.
- **Next Steps**: Evaluate table components and update API queries.

### Job Runtime Display (Live & Final)
- **Summary**: Show how long each job has been running and its total duration once complete.
- **Motivation**: Gives users feedback on job progress and performance.
- **Implementation Notes**: Store start and end timestamps; update progress WebSocket with runtime data.
- **Considerations**: Ensure timestamps remain accurate after restarts.
- **Roadblocks**: None.
- **Next Steps**: Extend job model with runtime fields and update the frontend.

### Admin Health Checks and Job Cleanup
- **Summary**: Add periodic health checks and automatic cleanup of old jobs.
- **Motivation**: Keeps the system stable and frees disk space.
- **Implementation Notes**: Define checks for database, disk usage, and worker heartbeats. Schedule cleanup via a cron task.
- **Considerations**: Admin endpoints must verify permissions.
- **Roadblocks**: None yet.
- **Next Steps**: Outline specific metrics and retention rules.

### Dashboard KPIs for Throughput
- **Summary**: Display metrics such as jobs per hour, average runtime, and queue length.
- **Motivation**: Allows admins to gauge overall system performance.
- **Implementation Notes**: Aggregate statistics in SQL and cache results.
- **Considerations**: Metrics queries should remain efficient on large tables.
- **Roadblocks**: None.
- **Next Steps**: Define the exact KPIs and create API endpoints.

### Settings Page to Customize Default Model
- **Summary**: UI for selecting the default Whisper model used for new jobs.
- **Motivation**: Lets admins tune quality versus speed without editing config files.
- **Implementation Notes**: Persist preference in the database; expose via admin API.
- **Considerations**: Changing the default should not affect jobs already queued.
- **Roadblocks**: None.
- **Next Steps**: Add model preference column and create settings form.

### Allow Multiple Files per Upload with Validation
- **Summary**: Permit submitting several audio files at once with size and count checks.
- **Motivation**: Speeds up batch processing.
- **Implementation Notes**: Modify the upload endpoint to accept a list and validate each file.
- **Considerations**: Adjust concurrency limits to avoid overwhelming workers.
- **Roadblocks**: None.
- **Next Steps**: Update API schema and UI uploader component.

### Web-based Log Viewer
- **Summary**: Provide an in-browser viewer for log files.
- **Motivation**: Avoids needing server access to inspect logs.
- **Implementation Notes**: Tail log files via WebSocket and display in a scrollable window.
- **Considerations**: Handle rotated logs and large files.
- **Roadblocks**: None.
- **Next Steps**: Create a secure endpoint that streams log lines.

### Status Toasts for Admin Actions
- **Summary**: Show success or failure notifications when admins trigger actions.
- **Motivation**: Gives immediate feedback in the UI.
- **Implementation Notes**: Use a React toast component tied to API responses.
- **Considerations**: Ensure messages are localized and auto-dismissed.
- **Roadblocks**: None.
- **Next Steps**: Integrate toast library and emit events from admin requests.

### Playback or Text Toggle for Completed Jobs
- **Summary**: Allow switching between audio playback and transcript text.
- **Motivation**: Improves review workflow.
- **Implementation Notes**: Add a toggle button in the job detail page.
- **Considerations**: Preload audio efficiently.
- **Roadblocks**: None.
- **Next Steps**: Design the UI component and update routes.

### Use `updated_at` for Job Sorting/Pagination
- **Summary**: Order job lists by the `updated_at` timestamp and paginate results.
- **Motivation**: Ensures the most recent activity appears first.
- **Implementation Notes**: Add an index on `updated_at`; extend queries with `ORDER BY` and `LIMIT`.
- **Considerations**: Existing API consumers must support pagination.
- **Roadblocks**: None.
- **Next Steps**: Create migration for the index and update endpoints.

### Heartbeat Table and `/heartbeat` Endpoint
- **Summary**: Record periodic worker heartbeats and expose them via an API endpoint.
- **Motivation**: Detect stalled or crashed workers.
- **Implementation Notes**: New database table storing heartbeat timestamps keyed by worker ID.
- **Considerations**: Keep writes lightweight to avoid DB contention.
- **Roadblocks**: None.
- **Next Steps**: Implement heartbeat sender in the worker process.

### Kill (Cancel) a Running Job
- **Summary**: Provide a way to terminate an in-progress transcription.
- **Motivation**: Allows admins to stop stuck or misconfigured jobs.
- **Implementation Notes**: Send a termination signal to the worker and clean up partial output.
- **Considerations**: Ensure cancellation cannot corrupt the queue.
- **Roadblocks**: Process management and permissions.
- **Next Steps**: Add cancel endpoint and update worker to handle signals.

### Shell/CLI Access from Admin Page
- **Summary**: Lightweight web terminal for executing maintenance commands.
- **Motivation**: Enables quick diagnostics without SSH access.
- **Implementation Notes**: Use a sandboxed shell over WebSocket.
- **Considerations**: High security risk; must restrict commands.
- **Roadblocks**: Security design.
- **Next Steps**: Evaluate libraries for web terminals and draft permission model.

### Resume Jobs After Crash or Cancel
- **Summary**: Restart incomplete jobs using intermediate output.
- **Motivation**: Prevents losing progress when the server crashes or a job is cancelled.
- **Implementation Notes**: Save partial transcripts periodically and reload them on resume.
- **Considerations**: Handle model version changes between runs.
- **Roadblocks**: Complex state handling.
- **Next Steps**: Define checkpoint format and resume logic.

### UI Progress Bars with Word-Level Timestamps
- **Summary**: Display real-time progress with word or token positions.
- **Motivation**: Visual feedback during long transcriptions.
- **Implementation Notes**: Parse SRT offsets and emit incremental progress events.
- **Considerations**: Frequent updates may stress the WebSocket.
- **Roadblocks**: None.
- **Next Steps**: Extend progress endpoint and UI component.

### Workflow Automation Hooks
- **Summary**: Trigger webhooks when jobs complete.
- **Motivation**: Allows integration with external systems like ticketing or messaging apps.
- **Implementation Notes**: Maintain a list of URLs to POST job metadata upon completion.
- **Considerations**: Secure the hooks with tokens.
- **Roadblocks**: None.
- **Next Steps**: Design hook configuration UI and server logic.

### Audio Cleanup Utilities
- **Summary**: Provide noise reduction, normalization, and silence trimming tools.
- **Motivation**: Improve transcription accuracy by cleaning audio before processing.
- **Implementation Notes**: Investigate libraries such as SoX or PyDub.
- **Considerations**: CPU heavy operations may need queuing.
- **Roadblocks**: External library selection.
- **Next Steps**: Prototype a cleaning pipeline and measure quality gains.

### Integration with Meeting Platforms
- **Summary**: Import recordings from Zoom and Google Meet via OAuth.
- **Motivation**: Streamlines getting meeting audio into the system.
- **Implementation Notes**: Handle OAuth flows, API rate limits, and recording retrieval.
- **Considerations**: Different APIs may require separate integrations.
- **Roadblocks**: Authentication complexity.
- **Next Steps**: Create proof-of-concept for one provider.

### Searchable Transcript Archive
- **Summary**: Index completed transcripts for full-text search.
- **Motivation**: Quickly locate past discussions or keywords.
- **Implementation Notes**: Evaluate search backends like Elasticsearch or Postgres full-text search.
- **Considerations**: Storage footprint grows with index size.
- **Roadblocks**: None.
- **Next Steps**: Prototype indexing on a subset of transcripts.

### Speaker Diarization Support
- **Summary**: Detect and label individual speakers in transcripts.
- **Motivation**: Distinguish who said what during meetings.
- **Implementation Notes**: Test models such as pyannote or Whisper diarization.
- **Considerations**: Accuracy varies with audio quality.
- **Roadblocks**: Heavy processing requirements.
- **Next Steps**: Evaluate available models and storage format.

### Summarization and Keyword Extraction
- **Summary**: Generate a short summary and tag important terms for each transcript.
- **Motivation**: Helps users grasp the key points quickly.
- **Implementation Notes**: Use an NLP library or external API for summarization and TF‑IDF for keywords.
- **Considerations**: Balance cost and privacy if using hosted models.
- **Roadblocks**: None.
- **Next Steps**: Compare LLM services versus open-source models.

### Automatic Language Translation
- **Summary**: Detect the transcript language and provide translations.
- **Motivation**: Allows sharing results with non-native speakers.
- **Implementation Notes**: Integrate with a translation service such as Google or AWS.
- **Considerations**: API costs and latency.
- **Roadblocks**: None.
- **Next Steps**: Add language detection step and translation endpoint.

### AI-powered Sentiment Analysis
- **Summary**: Score transcript segments for positive or negative sentiment.
- **Motivation**: Gauge audience reactions or meeting tone.
- **Implementation Notes**: Apply a sentiment model per sentence and store scores alongside text.
- **Considerations**: Language support varies by model.
- **Roadblocks**: Accuracy across domains.
- **Next Steps**: Select a sentiment model and define output schema.

### Live Streaming Transcription
- **Summary**: Transcribe audio streams in real time via WebRTC or RTMP.
- **Motivation**: Enables live captions for events.
- **Implementation Notes**: Buffer audio chunks and send them to Whisper in streaming mode.
- **Considerations**: Latency and network reliability.
- **Roadblocks**: Real-time performance tuning.
- **Next Steps**: Prototype a basic WebRTC ingestion path.

### Voice Cloning for Playback
- **Summary**: Synthesize corrected speech using a cloned voice model.
- **Motivation**: Allows generating polished audio for sharing.
- **Implementation Notes**: Collect user voice samples and train a cloning model.
- **Considerations**: Ethical and privacy concerns.
- **Roadblocks**: Requires heavy compute resources.
- **Next Steps**: Research available voice cloning APIs and licensing.

### Comprehensive Audio Toolbox
- **Summary**: Offer trimming, re-encoding, and effects within the UI.
- **Motivation**: Provides one place for basic audio edits.
- **Implementation Notes**: Wrap common SoX commands behind a simple interface.
- **Considerations**: Advanced options may overwhelm users.
- **Roadblocks**: Maintenance burden.
- **Next Steps**: Identify the most requested tools and design a minimal UI.

### Text-to-Speech from Documents
- **Summary**: Convert uploaded text documents to speech files.
- **Motivation**: Enables audio playback for scripts or notes.
- **Implementation Notes**: Use a TTS engine supporting multiple languages.
- **Considerations**: Large documents may need batching.
- **Roadblocks**: Model size and voice quality.
- **Next Steps**: Expose a simple upload form and choose default voices.

### Mobile Voice Memo Support
- **Summary**: Simplify uploads from phones and tablets.
- **Motivation**: Capture ideas on the go.
- **Implementation Notes**: Create a mobile-friendly upload page and handle large files over cellular connections.
- **Considerations**: Touch-oriented UI elements.
- **Roadblocks**: None.
- **Next Steps**: Audit current layout on mobile devices.

### Collaborative Transcript Editing
- **Summary**: Allow multiple users to edit transcripts simultaneously.
- **Motivation**: Teams can correct errors together.
- **Implementation Notes**: Investigate OT or CRDT frameworks for real-time sync.
- **Considerations**: Conflict resolution and permissions.
- **Roadblocks**: Complex sync logic.
- **Next Steps**: Prototype shared editing with a small document store.

### Automated Meeting Minutes
- **Summary**: Create formatted minutes and action items from transcripts.
- **Motivation**: Saves time after meetings.
- **Implementation Notes**: Combine summarization with a template for tasks and decisions.
- **Considerations**: Accuracy of generated notes.
- **Roadblocks**: None.
- **Next Steps**: Draft a minutes template and tie into summarization feature.

### Cloud Storage Sync
- **Summary**: Upload artifacts to cloud drives and optionally keep them in sync.
- **Motivation**: Offloads storage from the local server.
- **Implementation Notes**: Support providers like Google Drive or Dropbox through their APIs.
- **Considerations**: Handle OAuth tokens and retry logic.
- **Roadblocks**: Reliability of third-party services.
- **Next Steps**: Implement one-way uploads before attempting two-way sync.

### Personalized Speech Models
- **Summary**: Fine-tune recognition models per user.
- **Motivation**: Improves accuracy for frequent speakers.
- **Implementation Notes**: Collect opt-in training data and run fine-tuning jobs.
- **Considerations**: Significant compute and storage costs.
- **Roadblocks**: Managing many small models.
- **Next Steps**: Design the data collection workflow.

### Sign Language Video Generation
- **Summary**: Produce sign language videos aligned with transcripts.
- **Motivation**: Provides accessibility for deaf audiences.
- **Implementation Notes**: Translate text to sign language and render via an animated avatar.
- **Considerations**: Very compute intensive and requires high-quality models.
- **Roadblocks**: Availability of accurate sign language datasets.
- **Next Steps**: Research existing libraries and evaluate feasibility.

## On Hold

### Provide CLI Wrapper for Non-UI Usage
- **Summary**: Command-line script that mirrors API functionality.
- **Motivation**: Allows automation without the web interface.
- **Implementation Notes**: Simple Python wrapper calling REST endpoints.
- **Considerations**: Must handle authentication tokens.
- **Roadblocks**: None currently.
- **Next Steps**: Outline command structure and packaging approach.

## Partial

### Sortable and Searchable Job Lists
- **Summary**: Filter jobs via search query; sorting still pending.
- **Motivation**: Makes large job lists manageable.
- **Implementation Notes**: The API supports a `search` query but does not sort results yet.
- **Considerations**: Implement consistent sorting in the backend and UI.
- **Roadblocks**: None.
- **Next Steps**: Add sorting parameters and update the frontend list.


## Completed

### Docker Compose Helper Script
- **Summary**: Added `scripts/start_containers.sh` to automatically build the frontend and start the Docker Compose stack.
- **Motivation**: Simplifies setup by launching the API, worker, broker and database with one command.

### Incremental Image Update Script
- **Summary**: Added `scripts/update_images.sh` to rebuild the API and worker images using cached layers.
- **Motivation**: Speeds up development by avoiding full image pruning when only code changes.

### Build Argument for SECRET_KEY
- **Summary**: Dockerfile now expects a `SECRET_KEY` build argument so model validation can run during image creation.
- **Motivation**: `validate_models_dir()` loads settings which require a secret key. Passing it via build argument keeps the build compatible with older Docker Compose versions.
