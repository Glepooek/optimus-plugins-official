import { defineConfig, devices } from "@playwright/test";
import dotenv from "dotenv";
dotenv.config();

export default defineConfig({
  testDir: "./e2e",
  testMatch: ["**/*.spec.ts"],
  timeout: 10 * 60 * 1000, // 10分钟超时
  fullyParallel: false,
  retries: process.env.CI ? 0 : 0,
  reporter: [
    ["line"],
    ["html", { open: "never" }],
    ["@midscene/web/playwright-report"],
  ],
  use: {
    trace: "on",
    screenshot: "on",
    video: "on",
  },
  projects: [
    {
      name: "setup",
      testMatch: /auth\.setup\.ts/,
    },
    {
      name: "chromium",
      use: {
        ...devices["Desktop Chrome"],
        viewport: { width: 1280, height: 720 },
        headless: false,
        // 直接复用已保存的登录状态，不依赖 setup project（避免每次运行都触发登录）
        storageState: "e2e/.auth/state.json",
      },
    },
  ],
});
