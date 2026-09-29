import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig(({ mode, command }) => {
  const env = loadEnv(mode, process.cwd(), '');
  if (command === 'build' && process.env.VERCEL === '1') {
    const api = new URL(env.VITE_API_BASE_URL || 'http://localhost');
    if (api.protocol !== 'https:' || api.hostname === 'localhost' || api.pathname !== '/' || api.search || api.hash || api.username || api.password) {
      throw new Error('Vercel requires VITE_API_BASE_URL to be the deployed HTTPS API origin, without a path or credentials.');
    }
  }
  const target = env.API_PROXY_TARGET || 'http://127.0.0.1:8000';
  const proxy = { '/api': { target }, '/health': { target } };
  return {
    plugins: [react()],
    server: { port: 5173, strictPort: true, proxy },
    preview: { port: 4173, strictPort: true, proxy },
  };
});
