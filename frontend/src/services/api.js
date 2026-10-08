import axios from "axios";

const api = axios.create({
  baseURL:
    import.meta.env.VITE_API_URL ||
    "http://127.0.0.1:8000",
});

api.interceptors.request.use((config) => {
  const token =
    localStorage.getItem("touchgrass_token");

  if (token) {
    config.headers.Authorization =
      `Bearer ${token}`;
  }

  return config;
});


export const getProfile = async () => {
  const response = await api.get("/profile");
  return response.data;
};


export const normalizeProfile = async () => {
  const response =
    await api.post("/profile/normalize");

  return response.data;
};


export const chatWithAgent = async ({
  message,
  latitude,
  longitude,
}) => {
  const response = await api.post(
    "/agent/chat",
    {
      message,
      latitude,
      longitude,
    }
  );

  return response.data;
};


export const transcribeVoice = async (
  audioBlob
) => {
  const formData = new FormData();

  formData.append(
    "audio",
    audioBlob,
    "recording.webm"
  );

  const response = await api.post(
    "/voice/transcribe",
    formData
  );

  return response.data;
};


export const getActivities = async () => {
  const response =
    await api.get("/activities");

  return response.data;
};


export default api;