import { test, expect } from '@playwright/test'

test.describe('任务看板模块', () => {
  test.beforeEach(async ({ page }) => {
    // 登录
    await page.goto('/login')
    await page.fill('input[type="text"], input[placeholder*="用户名"], input[placeholder*="账号"]', 'admin')
    await page.fill('input[type="password"]', 'admin123')
    await page.click('button[type="submit"]')
    await page.waitForURL('**/dashboard**', { timeout: 10000 })
  })

  test('项目列表页加载', async ({ page }) => {
    await page.goto('/oa/projects')

    // 验证页面标题
    await expect(page.locator('.header-title')).toContainText('项目管理')

    // 验证搜索框存在
    await expect(page.locator('input[placeholder*="搜索项目名称"]')).toBeVisible()

    // 验证状态筛选
    await expect(page.locator('.el-select').first()).toBeVisible()

    // 验证新建项目按钮
    await expect(page.locator('button:has-text("新建项目")')).toBeVisible()

    // 验证项目网格区域存在
    await expect(page.locator('.project-grid')).toBeVisible()
  })

  test('新建项目弹窗', async ({ page }) => {
    await page.goto('/oa/projects')

    // 点击新建项目按钮
    await page.click('button:has-text("新建项目")')

    // 验证弹窗出现
    await expect(page.locator('.el-dialog')).toBeVisible()
    await expect(page.locator('.el-dialog__title')).toContainText('新建项目')

    // 验证表单字段
    await expect(page.locator('input[placeholder*="项目名称"]')).toBeVisible()
    await expect(page.locator('textarea')).toBeVisible()

    // 验证负责人下拉
    await expect(page.locator('.el-dialog .el-select')).toBeVisible()

    // 验证日期选择器
    await expect(page.locator('.el-dialog .el-date-editor')).toBeVisible()

    // 验证操作按钮
    await expect(page.locator('.el-dialog button:has-text("取消")')).toBeVisible()
    await expect(page.locator('.el-dialog button:has-text("创建")')).toBeVisible()
  })

  test('任务看板页面', async ({ page }) => {
    await page.goto('/oa/task-board')

    // 验证看板选择器
    await expect(page.locator('.header-left .el-select')).toBeVisible()

    // 验证新建看板按钮
    await expect(page.locator('button:has-text("新建看板")')).toBeVisible()

    // 验证新建任务按钮
    await expect(page.locator('button:has-text("新建任务")')).toBeVisible()

    // 验证看板容器
    await expect(page.locator('.board-container')).toBeVisible()
  })

  test('新建任务弹窗', async ({ page }) => {
    await page.goto('/oa/task-board')

    // 点击新建任务按钮
    await page.click('button:has-text("新建任务")')

    // 验证弹窗出现
    await expect(page.locator('.el-dialog')).toBeVisible()
    await expect(page.locator('.el-dialog__title')).toContainText('新建任务')

    // 验证表单字段
    await expect(page.locator('input[placeholder*="任务标题"]')).toBeVisible()
    await expect(page.locator('textarea')).toBeVisible()

    // 验证负责人下拉
    await expect(page.locator('.el-dialog .el-select').first()).toBeVisible()

    // 验证优先级下拉
    await expect(page.locator('.el-dialog .el-select').nth(1)).toBeVisible()

    // 验证日期选择器
    await expect(page.locator('.el-dialog .el-date-editor')).toBeVisible()

    // 验证操作按钮
    await expect(page.locator('.el-dialog button:has-text("取消")')).toBeVisible()
    await expect(page.locator('.el-dialog button:has-text("创建")')).toBeVisible()
  })

  test('任务详情抽屉', async ({ page }) => {
    await page.goto('/oa/task-board')

    // 等待看板加载
    await page.waitForSelector('.board-container', { timeout: 10000 })

    // 尝试点击任务卡片（如果存在）
    const taskCard = page.locator('.task-card').first()
    if (await taskCard.isVisible()) {
      await taskCard.click()

      // 验证抽屉出现
      await expect(page.locator('.el-drawer')).toBeVisible()
      await expect(page.locator('.el-drawer__header')).toContainText('任务详情')

      // 验证状态选择
      await expect(page.locator('.el-drawer .el-select').first()).toBeVisible()

      // 验证描述区域
      await expect(page.locator('.el-drawer textarea')).toBeVisible()

      // 验证子任务区域
      await expect(page.locator('.el-drawer').locator('text=子任务')).toBeVisible()

      // 验证评论区域
      await expect(page.locator('.el-drawer').locator('text=评论')).toBeVisible()

      // 验证底部操作按钮
      await expect(page.locator('.el-drawer button:has-text("保存")')).toBeVisible()
      await expect(page.locator('.el-drawer button:has-text("删除任务")')).toBeVisible()
    }
  })
})
