// fetch wrapper for the JSON API: JWT from localStorage, lang param, 401 -> logout.
import { getLang, t, translateApiError } from "./i18n.js";

const TOKEN_KEY = "pu_token";

export class ApiError extends Error {
  constructor(status, message, detail) {
    super(message);
    this.status = status;
    this.detail = detail;
  }
}

export function getToken() {
  try { return localStorage.getItem(TOKEN_KEY); } catch { return null; }
}

export function setToken(token) {
  try { localStorage.setItem(TOKEN_KEY, token); } catch { /* ignore */ }
  window.dispatchEvent(new Event("auth:change"));
}

export function logout() {
  try { localStorage.removeItem(TOKEN_KEY); } catch { /* ignore */ }
  window.dispatchEvent(new Event("auth:change"));
}

export function isAuthenticated() {
  return Boolean(getToken());
}

function errorMessage(detail) {
  if (typeof detail === "string") return translateApiError(detail);
  if (Array.isArray(detail)) {  // FastAPI validation errors
    return detail.map((e) => e.msg?.replace(/^Value error, /, "")).filter(Boolean).join("; ") || t("error.generic");
  }
  return t("error.generic");
}

/**
 * api("/products", { query: { q: "phone" } })
 * api("/cart/items", { method: "POST", body: { product_id: 1 } })
 */
export async function api(path, { method = "GET", body, query = {}, form } = {}) {
  const url = new URL(path, window.location.origin);
  url.searchParams.set("lang", getLang());
  for (const [key, value] of Object.entries(query)) {
    if (value !== undefined && value !== null && value !== "") url.searchParams.set(key, value);
  }

  const headers = { Accept: "application/json" };
  const token = getToken();
  if (token) headers.Authorization = `Bearer ${token}`;
  let payload;
  if (form) {
    payload = form;  // FormData, browser sets the multipart boundary
  } else if (body !== undefined) {
    headers["Content-Type"] = "application/json";
    payload = JSON.stringify(body);
  }

  let response;
  try {
    response = await fetch(url, { method, headers, body: payload });
  } catch {
    throw new ApiError(0, t("error.network"));
  }

  if (response.status === 401 && token) {
    logout();
    throw new ApiError(401, t("error.session_expired"));
  }
  if (response.status === 204) return null;

  const data = await response.json().catch(() => null);
  if (!response.ok) {
    throw new ApiError(response.status, errorMessage(data?.detail), data?.detail);
  }
  return data;
}
