// https://nuxt.com/docs/api/configuration/nuxt-config
export default defineNuxtConfig({
  compatibilityDate: '2025-01-01',
  // Keep the documented flat structure (pages/, components/, composables/ at root)
  srcDir: '.',
  devtools: { enabled: true },
  modules: ['@nuxtjs/tailwindcss'],
  runtimeConfig: {
    public: {
      // Local default. In production Nuxt auto-overrides this from the
      // NUXT_PUBLIC_API_URL environment variable (set it on Vercel to the
      // Railway backend URL, e.g. https://listas-venezuela.up.railway.app).
      apiUrl: 'http://localhost:8000',
    },
  },
})
