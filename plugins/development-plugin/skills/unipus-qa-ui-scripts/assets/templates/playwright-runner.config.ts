import { defineConfig, devices } from "@playwright/test";
import dotenv from "dotenv";
dotenv.config();

export default defineConfig({
  testDir: "./e2e",
  testMatch: ["**/run-all-tests.spec.ts"],
  timeout: 30 * 60 * 1000,
  fullyParallel: false,
  retries: 0,
  workers: 1,
  reporter: [["line"]],
  use: { trace: "off" },
  projects: [
    {
      name: "runner",
      use: { ...devices["Desktop Chrome"] },
    },
  ],
});
