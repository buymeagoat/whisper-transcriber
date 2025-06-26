import { useContext } from "react";
import { AuthContext } from "../context/AuthContext";
import { ROUTES } from "../routes";

const BASE_URL = ROUTES.API;

function parseResponse(res) {
  return res.text().then((text) => {
    try {
      return { ok: res.ok, data: JSON.parse(text) };
    } catch {
      return { ok: res.ok, data: text };
    }
  });
}

export function useApi() {
  const { token } = useContext(AuthContext);

  const request = async (method, path, options = {}) => {
    const headers = { ...(options.headers || {}) };
    if (token) headers["Authorization"] = `Bearer ${token}`;
    const res = await fetch(`${BASE_URL}${path}`, {
      ...options,
      method,
      headers,
    });
    const { ok, data } = await parseResponse(res);
    if (!ok) {
      const msg = typeof data === "string" ? data : data.error || "Request failed";
      throw new Error(msg);
    }
    return data;
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

  return { get, post, put, del };
}
