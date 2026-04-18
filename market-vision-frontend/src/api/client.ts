import axios from 'axios';
import { refreshToken } from './auth';
import { API_BASE_URL } from './config';

const api = axios.create({
    baseURL: API_BASE_URL,
});

api.interceptors.request.use((config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
        config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
});

api.interceptors.response.use(
    (response) => response,
    async (error) => {
        const originalRequest = error.config;
        const requestUrl = originalRequest?.url || '';
        const isAuthRequest = requestUrl.includes('/auth/login/')
            || requestUrl.includes('/auth/register/')
            || requestUrl.includes('/auth/token/refresh');

        if (error.response?.status === 401 && 
            !originalRequest._retry && 
            !isAuthRequest) {
            
            originalRequest._retry = true;

            try {
                const newAccessToken = await refreshToken();
                originalRequest.headers.Authorization = `Bearer ${newAccessToken}`;
                return api(originalRequest);
            } catch (refreshError) {
                localStorage.removeItem('access_token');
                localStorage.removeItem('refresh_token');
                window.location.href = '/login';
                return Promise.reject(refreshError);
            }
        }

        return Promise.reject(error);
    }
);

export default api;

export const toNumber = (value: number | string | undefined | null) => {
    if (value === null || value === undefined) return 0;
    const parsed = typeof value === "number" ? value : Number(value);
    return Number.isNaN(parsed) ? 0 : parsed;
};
