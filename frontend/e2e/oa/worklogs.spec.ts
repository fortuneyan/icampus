import { test, expect } from '@playwright/test'

test.describe('工作日志模块', () => {
  test.beforeEach(async ({ page }) => {
    // 登录
    await page.goto('/login')
    await page.fill('input[type="text"], input[placeholder*="用户名"], input[placeholder*="账号"]', 'admin')
    await page.fill('input[type="password"]', 'admin123')
    await page.click('button[type="submit"]')
    await page.waitForURL('**/dashboard**', { timeout: 10000 })
  })

  test('工作日志列表页加载', async ({ page }) => {
    await page.goto('/oa/worklogs')

    // 验证页面标题
    await expect(page.locator('.card-header span, .el-card__header span')).toContainText('工作日志')

    // 验证 Tab 存在
    await expect(page.locator('.el-tabs')).toBeVisible()
    await expect(page.locator('.el-tab-pane:has-text("我的日志")')).toBeVisible()

    // 验证写日志按钮
    await expect(page.locator('button:has-text("写日志")')).toBeVisible()

    // 验证团队日志按钮
    await expect(page.locator('button:has-text("团队日志")')).toBeVisible()

    // 验证查询表单
    await expect(page.locator('.query-form')).toBeVisible()
    await expect(page.locator('button:has-text("查询")')).toBeVisible()
    await expect(page.locator('button:has-text("重置")')).toBeVisible()
  })

  test('撰写日志编辑器', async ({ page }) => {
    await page.goto('/oa/worklogs/editor')

    // 验证页面标题
    await expect(page.locator('.card-header span, .el-card__header span')).toContainText('撰写日志')

    // 验证日志类型单选
    await expect(page.locator('.el-radio-group')).toBeVisible()
    await expect(page.locator('.el-radio:has-text("日报")')).toBeVisible()
    await expect(page.locator('.el-radio:has-text("周报")')).toBeVisible()
    await expect(page.locator('.el-radio:has-text("月报")')).toBeVisible()

    // 验证日期选择器
    await expect(page.locator('input[placeholder*="开始日期"]')).toBeVisible()
    await expect(page.locator('input[placeholder*="结束日期"]')).toBeVisible()

    // 验证 Markdown 编辑器（总结和计划各一个）
    const mdEditors = page.locator('.md-editor')
    await expect(mdEditors.first()).toBeVisible()

    // 验证附件上传
    await expect(page.locator('button:has-text("上传附件")')).toBeVisible()

    // 验证操作按钮
    await expect(page.locator('button:has-text("保存草稿")')).toBeVisible()
    await expect(page.locator('button:has-text("提交审核")')).toBeVisible()
    await expect(page.locator('button:has-text("返回")')).toBeVisible()
  })

  test('团队日志页面', async ({ page }) => {
    await page.goto('/oa/worklogs/team')

    // 验证页面标题
    await expect(page.locator('.card-header span, .el-card__header span')).toContainText('团队日志')

    // 验证统计面板
    await expect(page.locator('.stats-panel')).toBeVisible()
    await expect(page.locator('text=本月提交数')).toBeVisible()
    await expect(page.locator('text=已审核数')).toBeVisible()
    await expect(page.locator('text=待审核数')).toBeVisible()

    // 验证筛选区域
    await expect(page.locator('.query-form')).toBeVisible()
    await expect(page.locator('button:has-text("查询")')).toBeVisible()
    await expect(page.locator('button:has-text("重置")')).toBeVisible()

    // 验证返回按钮
    await expect(page.locator('button:has-text("返回列表")')).toBeVisible()
  })
})
