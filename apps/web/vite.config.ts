import { defineConfig } from 'vitest/config'
import vue from '@vitejs/plugin-vue'
import AutoImport from 'unplugin-auto-import/vite'
import Components from 'unplugin-vue-components/vite'
import { ElementPlusResolver } from 'unplugin-vue-components/resolvers'

export default defineConfig({
  plugins: [
    vue(),
    AutoImport({ dts: false, resolvers: [ElementPlusResolver()] }),
    Components({ dts: false, resolvers: [ElementPlusResolver()] }),
  ],
  server: {
    port: 5173,
  },
  test: {
    environment: 'happy-dom',
    globals: true,
    server: {
      deps: { inline: ['element-plus'] },
    },
  },
})
