import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// https://vite.dev/config/
export default defineConfig({
  plugins: [vue()],

  // Reduce large vendor chunk warning by splitting heavy deps
  build: {
    // Element Plus can be quite large; this only affects build-time warnings.
    chunkSizeWarningLimit: 1200,
    rollupOptions: {
      output: {
        manualChunks: {
          vue: ['vue', 'vue-router'],
          elementPlus: ['element-plus', '@element-plus/icons-vue'],
          axios: ['axios']
        }
      }
    }
  }
})
