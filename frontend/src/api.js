// Thin API client for the AgriTech Suite backend.
const BASE = import.meta.env.VITE_API_BASE || "";

export function getToken() {
  return localStorage.getItem("agri_token") || "";
}
export function setToken(t) {
  if (t) localStorage.setItem("agri_token", t);
  else localStorage.removeItem("agri_token");
}

async function request(path, { method = "GET", body, isForm = false } = {}) {
  const headers = {};
  const token = getToken();
  if (token) headers["Authorization"] = `Bearer ${token}`;
  let payload = body;
  if (body && !isForm) {
    headers["Content-Type"] = "application/json";
    payload = JSON.stringify(body);
  }
  const res = await fetch(`${BASE}${path}`, { method, headers, body: payload });
  if (res.status === 204) return null;
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    throw new Error(data.detail || `Request failed (${res.status})`);
  }
  return data;
}

export const api = {
  base: BASE,
  // auth
  register: (b) => request("/api/auth/register", { method: "POST", body: b }),
  login: (b) => request("/api/auth/login", { method: "POST", body: b }),
  firebaseAuth: (id_token, role) =>
    request("/api/auth/firebase", { method: "POST", body: { id_token, role } }),
  me: () => request("/api/auth/me"),
  updateProfile: (b) => request("/api/auth/me", { method: "PUT", body: b }),
  health: () => request("/api/health"),
  // diagnosis
  diagnose: (form) =>
    request("/api/diagnosis", { method: "POST", body: form, isForm: true }),
  diagnosisHistory: () => request("/api/diagnosis/history"),
  // advisory
  advisory: () => request("/api/advisory"),
  // news
  news: (location) =>
    request(`/api/news${location ? `?location=${encodeURIComponent(location)}` : ""}`),
  // marketplace
  listings: (q = "") => request(`/api/marketplace/listings${q}`),
  marketFeed: () => request("/api/marketplace/feed"),
  createListing: (b) =>
    request("/api/marketplace/listings", { method: "POST", body: b }),
  myListings: () => request("/api/marketplace/my-listings"),
  deleteListing: (id) =>
    request(`/api/marketplace/listings/${id}`, { method: "DELETE" }),
  // community
  posts: (topic = "") =>
    request(`/api/community/posts${topic ? `?topic=${topic}` : ""}`),
  createPost: (b) => request("/api/community/posts", { method: "POST", body: b }),
  comment: (id, b) =>
    request(`/api/community/posts/${id}/comments`, { method: "POST", body: b }),
  like: (id) => request(`/api/community/posts/${id}/like`, { method: "POST" }),
  // chat
  chatHistory: (session = "default") =>
    request(`/api/chat/history?session_id=${session}`),
};
