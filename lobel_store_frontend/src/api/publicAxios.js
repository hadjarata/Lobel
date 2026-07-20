import axios from 'axios';
import { API_BASE_URL } from '../config/api';

const publicApi = axios.create({
  baseURL: API_BASE_URL,
  headers: { 'Content-Type': 'application/json' },
  timeout: 15000,
});

export default publicApi;
