import axios from 'axios';
import api from './client';
import { API_BASE_URL } from './config';

// Отдельный инстанс для обновления токена
const authApi = axios.create({
    baseURL: API_BASE_URL,
});

export interface LoginData {
    email: string;
    password: string;
}

export interface RegisterData {
    email: string;
    password: string;
}

export const login = async (data: LoginData) => {
    const response = await api.post('/auth/login/', data);
    saveTokens(response.data);
};

export const register = async (data: RegisterData) => {
    const response = await api.post('/auth/register/', data);
    saveTokens(response.data);
};

export const refreshToken = async () => {
    const refresh = localStorage.getItem('refresh_token');
    if (!refresh) {
        localStorage.removeItem('access_token');
        throw new Error('No refresh token');
    }

    try {
        const response = await authApi.post('/auth/token/refresh/', { refresh });
        localStorage.setItem('access_token', response.data.access);
        return response.data.access;
    } catch (error) {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        throw error;
    }
};

export const saveTokens = (tokens: { access: string; refresh: string }) => {
    localStorage.setItem('access_token', tokens.access);
    localStorage.setItem('refresh_token', tokens.refresh);
};

export const logout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
};
