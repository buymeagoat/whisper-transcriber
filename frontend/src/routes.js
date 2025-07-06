export const ROUTES = {
  LOGIN: "/login",
  UPLOAD: "/upload",
  ACTIVE: "/active",
  COMPLETED: "/completed",
  FAILED: "/failed",
  ADMIN: "/admin",
  SETTINGS: "/settings",
  TRANSCRIPT_VIEW: "/transcript/:jobId/view",
  STATUS: "/status/:jobId",
  PROGRESS: "/progress/:jobId",
  FILE_BROWSER: "/admin/files",
  CHANGE_PASSWORD: "/change-password",
  API: import.meta.env.VITE_API_HOST || "http://192.168.1.52:8000"
};

export const DEFAULT_DOWNLOAD_FORMAT =
  localStorage.getItem("downloadFormat") ||
  import.meta.env.VITE_DEFAULT_TRANSCRIPT_FORMAT ||
  "txt";

export function getTranscriptDownloadUrl(
  jobId,
  format = DEFAULT_DOWNLOAD_FORMAT
) {
  return `${ROUTES.API}/jobs/${jobId}/download?format=${format}`;
}
