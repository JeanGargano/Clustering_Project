import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    proxy: {
      // Interceptamos la ruta
      '/minio-api': {
        target: 'http://localhost:9000', // Apunta al MinIO expuesto en tu PC
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/minio-api/, ''), // Limpiamos la ruta
        headers: {
          Host: 'minio:9000' // ¡EL TRUCO!: Engaña a MinIO para que la firma coincida
        }
      }
    }
  }})