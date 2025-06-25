export const ROUTES = {
  LOGIN: "/login",
  UPLOAD: "/upload",
  ACTIVE: "/active",
  COMPLETED: "/completed",
  FAILED: "/failed",
  ADMIN: "/admin",
  TRANSCRIPT_VIEW: "/transcript/:jobId/view",
  STATUS: "/status/:jobId",
  PROGRESS: "/progress/:jobId",
  API: import.meta.env.VITE_API_HOST || "http://localhost:8000"
};
