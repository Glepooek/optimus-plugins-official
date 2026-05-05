import { test as base } from "@playwright/test";
import { PlaywrightAiFixture } from "@midscene/web/playwright";
import type { PlayWrightAiFixtureType } from "@midscene/web/playwright";
import "dotenv/config";

export const test = base.extend<PlayWrightAiFixtureType>(
  PlaywrightAiFixture({
    waitForNetworkIdleTimeout: 10000,
  })
);

export { expect } from "@playwright/test";
