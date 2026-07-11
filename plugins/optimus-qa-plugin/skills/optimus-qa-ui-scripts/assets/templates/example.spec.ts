import { test } from "./fixture";
import { configManager } from "./utils/config";

test.describe("示例功能模块", () => {
  test.beforeEach(async ({ page }) => {
    const config = configManager.getConfig();
    await page.goto(config.pages.home);
    await page.waitForLoadState("networkidle");
  });

  test("TC001: 页面基础功能验证", async ({ ai, aiAssert, page }) => {
    console.log("开始执行TC001");

    try {
      // 1. 验证页面加载
      await aiAssert("页面已正常加载，显示主要内容");

      // 2. 示例操作
      await ai("点击页面上的主要功能按钮");
      await page.waitForLoadState("networkidle");

      // 3. 验证结果
      await aiAssert("操作执行成功，页面显示正确内容");

      console.log("TC001执行成功");
    } catch (error) {
      await page.screenshot({
        path: `test-screenshots/TC001-error-${Date.now()}.png`,
        fullPage: true,
      });
      console.error("TC001执行失败:", error);
      throw error;
    }
  });

  test("TC002: 表单输入功能验证", async ({ ai, aiInput, aiAssert, page }) => {
    console.log("开始执行TC002");

    try {
      // 1. 找到输入框并输入内容
      await aiInput("在搜索框中", "测试内容");
      await page.keyboard.press("Enter");
      await page.waitForLoadState("networkidle");

      // 2. 验证搜索结果
      await aiAssert("页面显示搜索结果");

      console.log("TC002执行成功");
    } catch (error) {
      await page.screenshot({
        path: `test-screenshots/TC002-error-${Date.now()}.png`,
        fullPage: true,
      });
      console.error("TC002执行失败:", error);
      throw error;
    }
  });
});
