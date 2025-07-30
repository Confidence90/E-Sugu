import axios from 'axios';
import jwt_decode from 'jwt-decode';
import dayjs from 'dayjs';
import { toast } from 'react-toastify';

const baseURL = 'http://localhost:8000';

axios.defaults.withCredentials = true; // Activer les cookies pour toutes les requêtes
axios.defaults.xsrfCookieName = 'csrftoken';
axios.defaults.xsrfHeaderName = 'X-CSRFToken';
const axiosInstance = axios.create({
  baseURL: "http://localhost:8000/api",
  withCredentials: true, // 👈 important pour inclure les cookies (dont CSRF)
});
axiosInstance.post("/users/register/", data)
  .then(response => console.log(response))
  .catch(error => console.error(error));


// Initialisation
let accessToken = localStorage.getItem('access_token');
let refreshToken = localStorage.getItem('refresh_token');

const api = axios.create({
  baseURL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// ➤ Intercepteur avant chaque requête
api.interceptors.request.use(async (config) => {
  accessToken = localStorage.getItem('access_token');
  refreshToken = localStorage.getItem('refresh_token');

  if (!accessToken) return config;

  try {
    const user = jwt_decode(accessToken);
    const isExpired = dayjs.unix(user.exp).diff(dayjs()) < 1;

    if (!isExpired) {
      config.headers.Authorization = `Bearer ${accessToken}`;
      return config;
    }

    // ➤ Si expiré : on tente de rafraîchir le token
    const response = await axios.post(`${baseURL}/api/token/refresh/`, {
      refresh: refreshToken,
    });

    const newAccess = response.data.access;
    localStorage.setItem('access_token', newAccess);
    config.headers.Authorization = `Bearer ${newAccess}`;
    return config;

  } catch (err) {
    // ➤ Si le refresh échoue
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user');
    toast.error('Session expirée, veuillez vous reconnecter');
    window.location.href = '/login';
    return Promise.reject(err);
  }
});

// ➤ Intercepteur de réponse : pour rattraper les 401 inattendus
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      try {
        const refreshToken = localStorage.getItem('refresh_token');
        if (!refreshToken) throw new Error('Aucun refresh token');

        const res = await axios.post(`${baseURL}/api/token/refresh/`, {
          refresh: refreshToken,
        });

        const newAccess = res.data.access;
        localStorage.setItem('access_token', newAccess);
        api.defaults.headers.common['Authorization'] = `Bearer ${newAccess}`;
        originalRequest.headers['Authorization'] = `Bearer ${newAccess}`;

        return api(originalRequest);
      } catch (err) {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        localStorage.removeItem('user');
        toast.error('Session expirée. Veuillez vous reconnecter.');
        window.location.href = '/login';
        return Promise.reject(err);
      }
    }

    return Promise.reject(error);
  }
);

export default axiosInstance;
