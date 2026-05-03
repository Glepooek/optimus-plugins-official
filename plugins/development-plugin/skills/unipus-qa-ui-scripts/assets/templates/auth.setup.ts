import { test as setup } from "@playwright/test";
import path from "path";
import fs from "fs";
import "dotenv/config";

const authFile = path.join(__dirname, ".auth/state.json");

setup("authenticate", async ({ page }) => {
  // 确保 .auth 目录存在
  const authDir = path.dirname(authFile);
  if (!fs.existsSync(authDir)) {
    fs.mkdirSync(authDir, { recursive: true });
  }

  // 从 environments.json 读取登录信息
  const configPath = path.join(process.cwd(), "config", "environments.json");
  const config = JSON.parse(fs.readFileSync(configPath, "utf-8"));
  const env = process.env.TEST_ENV || "test";
  const { loginUrl, username, password } = config[env].auth;

  console.log(`\n登录环境: ${env}`);
  console.log(`登录地址: ${loginUrl}`);
  console.log(`账号: ${username}\n`);

  await page.goto(loginUrl);
  await page.waitForLoadState("networkidle");

  // 自动填写用户名和密码
  await page.locator('#email, input[name="email"]').fill(username);
  await page.locator('#password, input[name="password"]').fill(password);
  await page.locator('button[type="submit"]').click();

  // 等待登录成功（跳转离开登录页）
  await page.waitForURL((url) => !url.toString().includes("/login"), { timeout: 15000 });
  await page.waitForLoadState("networkidle");

  console.log("登录成功，当前页面:", page.url());

  // 保存登录状态
  await page.context().storageState({ path: authFile });
  console.log("登录状态已保存到:", authFile);
});
