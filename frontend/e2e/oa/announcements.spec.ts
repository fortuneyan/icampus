import { test, expect } from '@playwright/test'

test.describe('公告管理模块', () => {
  test.beforeEach(async ({ page }) => {
    // 登录
    await page.goto('/login')
    await page.fill('input[type="text"], input[placeholder*="用户名"], input[placeholder*="账号"]', 'admin')
    await page.fill('input[type="password"]', 'admin123')
    await page.click('button[type="submit"]')
    await page.waitForURL('**/dashboard**', { timeout: 10000 })
  })

  test('公告列表页加载', async ({ page }) => {
    await page.goto('/oa/announcements')

    // 验证页面标题
    await expect(page.locator('.card-header span, .el-card__header span')).toContainText('公告管理')

    // 验证查询表单存在
    await expect(page.locator('.query-form')).toBeVisible()
    await expect(page.locator('input[placeholder*="标题"]')).toBeVisible()
    await expect(page.locator('button:has-text("查询")')).toBeVisible()
    await expect(page.locator('button:has-text("重置")')).toBeVisible()

    // 验证表格存在
    await expect(page.locator('.el-table')).toBeVisible()

    // 验证发布按钮存在
    await expect(page.locator('button:has-text("发布公告")')).toBeVisible()
  })

  test('新建公告表单', async ({ page }) => {
    await page.goto('/oa/announcements/create')

    // 验证页面标题
    await expect(page.locator('.card-header span, .el-card__header span')).toContainText('发布公告')

    // 验证标题输入框
    await expect(page.locator('input[placeholder*="标题"]')).toBeVisible()

    // 验证分类选择
    await expect(page.locator('.el-select').first()).toBeVisible()

    // 验证优先级单选
    await expect(page.locator('.el-radio-group')).toBeVisible()
    await expect(page.locator('.el-radio:has-text("普通")')).toBeVisible()
    await expect(page.locator('.el-radio:has-text("重要")')).toBeVisible()
    await expect(page.locator('.el-radio:has-text("紧急")')).toBeVisible()

    // 验证 Markdown 编辑器
    await expect(page.locator('.md-editor')).toBeVisible()

    // 验证操作按钮
    await expect(page.locator('button:has-text("发布")')).toBeVisible()
    await expect(page.locator('button:has-text("保存草稿")')).toBeVisible()
    await expect(page.locator('button:has-text("取消")')).toBeVisible()

    // 验证返回按钮
    await expect(page.locator('button:has-text("返回列表")')).toBeVisible()
  })

  test('公告详情页', async ({ page }) => {
    // 先访问列表页，再点击查看按钮进入详情
    await page.goto('/oa/announcements')

    // 等待表格加载
    await page.waitForSelector('.el-table', { timeout: 10000 })

    // 点击第一行的查看按钮
    const viewButton = page.locator('button:has-text("查看")').first()
    if (await viewButton.isVisible()) {
      await viewButton.click()
      await page.waitForURL('**/oa/announcements/**', { timeout: 10000 })

      // 验证详情页标题
      await expect(page.locator('.card-header span, .el-card__header span')).toContainText('公告详情')

      // 验证返回按钮
      await expect(page.locator('button:has-text("返回列表")')).toBeVisible()

      // 验证详情内容区域存在
      await expect(page.locator('.detail-content, .detail-title')).toBeVisible()
    }
  })

  test('编辑公告表单', async ({ page }) => {
    // 先访问列表页，再点击编辑按钮
    await page.goto('/oa/announcements')

    // 等待表格加载
    await page.waitForSelector('.el-table', { timeout: 10000 })

    // 点击第一行的编辑按钮
    const editButton = page.locator('button:has-text("编辑")').first()
    if (await editButton.isVisible()) {
      await editButton.click()
      await page.waitForURL('**/oa/announcements/**/edit', { timeout: 10000 })

      // 验证编辑页标题
      await expect(page.locator('.card-header span, .el-card__header span')).toContainText('编辑公告')

      // 验证表单字段存在
      await expect(page.locator('input[placeholder*="标题"]')).toBeVisible()

      // 验证优先级选择
      await expect(page.locator('.el-radio-group')).toBeVisible()

      // 验证 Markdown 编辑器
      await expect(page.locator('.md-editor')).toBeVisible()

      // 验证操作按钮
      await expect(page.locator('button:has-text("保存")')).toBeVisible()
      await expect(page.locator('button:has-text("保存草稿")')).toBeVisible()

      // 验证返回按钮
      await expect(page.locator('button:has-text("返回列表")')).toBeVisible()
    }
  })
})
