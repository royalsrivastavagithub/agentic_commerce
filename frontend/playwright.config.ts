import { defineConfig, devices } from "@playwright/test"

export default defineConfig({
  testDir: "./tests/e2e",
  fullyParallel: true,
  workers: 4,
  outputDir: "./tests/test-results",
  reporter: "list",
  webServer: [
    {
      command: ".venv/bin/uvicorn app.main:app --port 8000",
      url: "http://localhost:8000/docs",
      reuseExistingServer: true,
      cwd: "../backend",
    },
    {
      command: "npx next dev --port 3000",
      url: "http://localhost:3000",
      reuseExistingServer: true,
      cwd: ".",
    },
  ],
  use: {
    baseURL: "http://localhost:3000",
    trace: "off",
    screenshot: "off",
  },
  projects: [
    {
      name: "setup",
      testMatch: "**/*.setup.ts",
      use: { ...devices["Desktop Chrome"] },
    },
    {
      name: "chromium",
      dependencies: ["setup"],
      use: {
        ...devices["Desktop Chrome"],
        storageState: "./tests/e2e/.auth/alice.json",
      },
    },
  ],
})
