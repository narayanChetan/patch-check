import axios from "axios";

const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

const client = axios.create({ baseURL: API_BASE_URL });

client.interceptors.request.use((config) => {
  const token = localStorage.getItem("packcheck_token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

export const api = {
  login: (username, password) =>
    client.post("/api/auth/login", { username, password }).then((r) => r.data),

  scanLabel: (file, productName, save = true) => {
    const form = new FormData();
    form.append("file", file);
    form.append("product_name", productName || "Untitled product");
    form.append("save", String(save));
    return client.post("/api/scan", form).then((r) => r.data);
  },

  downloadReport: (scanId) =>
    client.get(`/api/scan/${scanId}/report.pdf`, { responseType: "blob" }).then((r) => r.data),

  listLedger: (params = {}) => client.get("/api/ledger", { params }).then((r) => r.data),

  getScanDetail: (scanId) => client.get(`/api/ledger/${scanId}`).then((r) => r.data),

  deleteScan: (scanId) => client.delete(`/api/ledger/${scanId}`).then((r) => r.data),

  getStats: () => client.get("/api/ledger/stats/summary").then((r) => r.data),
};

export default client;
