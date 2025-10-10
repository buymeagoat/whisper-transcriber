import { useContext } from "react";
import { AuthContext } from "../context/AuthContext";
import { ROUTES } from "../routes";
import { handleApiResponse } from "../services/errorHandler";

const BASE_URL = ROUTES.API;

function parseResponse(res) {
  return res.text().then((text) => {
    try {
      const data = JSON.parse(text);
      return handleApiResponse(res, data);
    } catch {
      return handleApiResponse(res, text);
    }
  });
}

export function useApi() {
  const { token } = useContext(AuthContext);

  const request = async (method, path, options = {}) => {
    try {
      const headers = { ...(options.headers || {}) };
      if (token) headers["Authorization"] = `Bearer ${token}`;
      
      const res = await fetch(`${BASE_URL}${path}`, {
        ...options,
        method,
        headers,
      });
      
      return await parseResponse(res);
    } catch (error) {
      // Re-throw with additional context
      throw {
        ...error,
        method,
        path,
        timestamp: new Date().toISOString()
      };
    }
  };

  const get = (path, options) => request("GET", path, options);
  const del = (path, options) => request("DELETE", path, options);
  const post = (path, body, options = {}) => {
    const opts = { ...options };
    if (body !== undefined) {
      if (
        !(body instanceof FormData) &&
        !(typeof body === "string") &&
        !(body instanceof URLSearchParams)
      ) {
        opts.headers = { "Content-Type": "application/json", ...(opts.headers || {}) };
        body = JSON.stringify(body);
      }
      opts.body = body;
    }
    return request("POST", path, opts);
  };
  const put = (path, body, options = {}) => {
    const opts = { ...options };
    if (body !== undefined) {
      if (
        !(body instanceof FormData) &&
        !(typeof body === "string") &&
        !(body instanceof URLSearchParams)
      ) {
        opts.headers = { "Content-Type": "application/json", ...(opts.headers || {}) };
        body = JSON.stringify(body);
      }
      opts.body = body;
    }
    return request("PUT", path, opts);
  };

  const postWithProgress = (path, body, onProgress, options = {}) => {
    return new Promise((resolve, reject) => {
      const xhr = new XMLHttpRequest();
      
      // Set up progress tracking
      if (onProgress && xhr.upload) {
        xhr.upload.addEventListener('progress', (e) => {
          if (e.lengthComputable) {
            const percentComplete = (e.loaded / e.total) * 100;
            onProgress(percentComplete, e.loaded, e.total);
          }
        });
      }
      
      // Set up completion handling
      xhr.addEventListener('load', () => {
        try {
          const data = JSON.parse(xhr.responseText);
          if (xhr.status >= 200 && xhr.status < 300) {
            resolve(data);
          } else {
            const error = handleApiResponse({ status: xhr.status, ok: false }, data);
            reject(error);
          }
        } catch (e) {
          if (xhr.status >= 200 && xhr.status < 300) {
            resolve(xhr.responseText);
          } else {
            reject(new Error(`HTTP ${xhr.status}: ${xhr.statusText}`));
          }
        }
      });
      
      xhr.addEventListener('error', () => {
        reject(new Error('Network error occurred'));
      });
      
      xhr.addEventListener('timeout', () => {
        reject(new Error('Upload timed out'));
      });
      
      // Configure request
      xhr.open('POST', `${BASE_URL}${path}`);
      
      // Set headers
      if (token) {
        xhr.setRequestHeader('Authorization', `Bearer ${token}`);
      }
      
      // Set custom headers (but not Content-Type for FormData)
      if (options.headers && !(body instanceof FormData)) {
        Object.entries(options.headers).forEach(([key, value]) => {
          xhr.setRequestHeader(key, value);
        });
      }
      
      // Set timeout (30 seconds)
      xhr.timeout = 30000;
      
      // Send request
      xhr.send(body);
    });
  };

  return { get, post, postWithProgress, put, del };
}
