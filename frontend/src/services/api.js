import axios from "axios";

const API_URL =
  import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

const api = axios.create({
  baseURL: API_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

// Automatically attach JWT to every authenticated request.
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("touchgrass_token");

  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }

  return config;
});

// If JWT expires, remove it so the app can redirect to login.
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem("touchgrass_token");
      localStorage.removeItem("touchgrass_user");
    }

    return Promise.reject(error);
  }
);

// -----------------------------
// Authentication
// -----------------------------

export const signup = async (data) => {
  const response = await api.post("/auth/signup", data);
  return response.data;
};

export const login = async (data) => {
  const response = await api.post("/auth/login", data);
  return response.data;
};

export const getCurrentUser = async () => {
  const response = await api.get("/auth/me");
  return response.data;
};

// -----------------------------
// Profile
// -----------------------------

export const normalizeProfile = async (answers) => {
  const response = await api.post("/profile/normalize", {
    answers,
  });

  return response.data;
};

export const saveProfile = async (profile) => {
  const response = await api.post("/profile", profile);
  return response.data;
};

export const getProfile = async () => {
  const response = await api.get("/profile");
  return response.data;
};

export const deleteProfile = async () => {
  const response = await api.delete("/profile");
  return response.data;
};

// -----------------------------
// Activities
// -----------------------------

export const getActivities = async () => {
  const response = await api.get("/activities");
  return response.data;
};

export const getActivity = async (activityId) => {
  const response = await api.get(`/activities/${activityId}`);
  return response.data;
};

export const submitFeedback = async (activityId, feedback) => {
  const response = await api.post(
    `/activities/${activityId}/feedback`,
    feedback
  );

  return response.data;
};

// -----------------------------
// Agent
// -----------------------------

export const chatWithAgent = async (data) => {
  const response = await api.post("/agent/chat", data);
  return response.data;
};

// -----------------------------
// Voice
// -----------------------------

export const transcribeVoice = async (audioBlob) => {
  const formData = new FormData();

  formData.append(
    "file",
    audioBlob,
    "voice.webm"
  );

  const response = await api.post(
    "/voice/transcribe",
    formData,
    {
      headers: {
        "Content-Type": "multipart/form-data",
      },
    }
  );

  return response.data;
};

export default api;