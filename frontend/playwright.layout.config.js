import { defineConfig } from '@playwright/test'

export default defineConfig({
  testDir: './tests/layout',
  fullyParallel: false,
  retries: 0,
  use: {
    baseURL: 'http://127.0.0.1:4173',
    trace: 'on-first-retry',
  },
  reporter: [['list']],
})

