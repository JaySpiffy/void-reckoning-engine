import axios from 'axios';
import type { LiveMetrics } from '../types/telemetry';

const api = axios.create({
  baseURL: '/api',
});

export const getLiveMetrics = async (): Promise<LiveMetrics> => {
  const response = await api.get<LiveMetrics>('/metrics/live');
  return response.data;
};

export const getStatus = async () => {
    const response = await api.get('/status');
    return response.data;
}
