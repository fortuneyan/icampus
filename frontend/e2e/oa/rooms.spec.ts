import { test, expect } from '@playwright/test'

test.describe('教室预约模块', () => {
  test.beforeEach(async ({ page }) => {
    // 设置 localStorage 中的 token 以绕过登录
    await page.goto('/')
    await page.evaluate(() => {
      localStorage.setItem('token', 'test-token')
    })
  })

  test('教室列表页加载', async ({ page }) => {
    await page.goto('/oa/rooms')

    // 验证页面标题
    await expect(page.locator('.card-header span')).toHaveText('教室管理')

    // 验证新增按钮存在
    await expect(page.locator('button:has-text("新增教室")')).toBeVisible()

    // 验证筛选表单存在
    await expect(page.locator('label:has-text("教室名称")')).toBeVisible()
    await expect(page.locator('label:has-text("类型")')).toBeVisible()
    await expect(page.locator('label:has-text("楼栋")')).toBeVisible()
    await expect(page.locator('label:has-text("状态")')).toBeVisible()

    // 验证查询和重置按钮存在
    await expect(page.locator('button:has-text("查询")')).toBeVisible()
    await expect(page.locator('button:has-text("重置")')).toBeVisible()

    // 验证表格列标题
    await expect(page.locator('.el-table th:has-text("名称")')).toBeVisible()
    await expect(page.locator('.el-table th:has-text("类型")')).toBeVisible()
    await expect(page.locator('.el-table th:has-text("楼栋")')).toBeVisible()
    await expect(page.locator('.el-table th:has-text("楼层")')).toBeVisible()
    await expect(page.locator('.el-table th:has-text("容量")')).toBeVisible()
    await expect(page.locator('.el-table th:has-text("设备")')).toBeVisible()
    await expect(page.locator('.el-table th:has-text("状态")')).toBeVisible()
    await expect(page.locator('.el-table th:has-text("操作")')).toBeVisible()
  })

  test('新建教室弹窗', async ({ page }) => {
    await page.goto('/oa/rooms')

    // 点击新增教室按钮
    await page.click('button:has-text("新增教室")')

    // 验证弹窗出现
    await expect(page.locator('.el-dialog:has-text("新增教室")')).toBeVisible()

    // 验证表单字段
    await expect(page.locator('.el-dialog label:has-text("名称")')).toBeVisible()
    await expect(page.locator('.el-dialog label:has-text("类型")')).toBeVisible()
    await expect(page.locator('.el-dialog label:has-text("楼栋")')).toBeVisible()
    await expect(page.locator('.el-dialog label:has-text("楼层")')).toBeVisible()
    await expect(page.locator('.el-dialog label:has-text("容量")')).toBeVisible()
    await expect(page.locator('.el-dialog label:has-text("面积")')).toBeVisible()
    await expect(page.locator('.el-dialog label:has-text("位置描述")')).toBeVisible()
    await expect(page.locator('.el-dialog label:has-text("设备清单")')).toBeVisible()
    await expect(page.locator('.el-dialog label:has-text("预约规则")')).toBeVisible()

    // 验证取消和确定按钮
    await expect(page.locator('.el-dialog button:has-text("取消")')).toBeVisible()
    await expect(page.locator('.el-dialog button:has-text("确定")')).toBeVisible()

    // 关闭弹窗
    await page.click('.el-dialog button:has-text("取消")')
    await expect(page.locator('.el-dialog:has-text("新增教室")')).not.toBeVisible()
  })

  test('预约详情页', async ({ page }) => {
    // 使用一个示例 ID 访问预约详情页
    await page.goto('/oa/room-bookings/test-booking-id')

    // 验证页面标题区域
    await expect(page.locator('.page-title:has-text("预约详情")')).toBeVisible()

    // 验证返回按钮存在
    await expect(page.locator('.el-page-header:has-text("返回列表")')).toBeVisible()

    // 验证基本信息区域
    await expect(page.locator('.section-title:has-text("基本信息")')).toBeVisible()

    // 验证信息字段标签
    await expect(page.locator('label:has-text("教室名称")')).toBeVisible()
    await expect(page.locator('label:has-text("预约主题")')).toBeVisible()
    await expect(page.locator('label:has-text("申请人")')).toBeVisible()
    await expect(page.locator('label:has-text("预约日期")')).toBeVisible()
    await expect(page.locator('label:has-text("时间段")')).toBeVisible()
    await expect(page.locator('label:has-text("参与人数")')).toBeVisible()
  })

  test('教室预约列表页', async ({ page }) => {
    await page.goto('/oa/room-booking')

    // 验证页面标题
    await expect(page.locator('.card-header span')).toHaveText('教室预约')

    // 验证新建预约按钮存在
    await expect(page.locator('button:has-text("新建预约")')).toBeVisible()

    // 验证筛选表单存在
    await expect(page.locator('label:has-text("预约日期")')).toBeVisible()
    await expect(page.locator('label:has-text("教室")')).toBeVisible()
    await expect(page.locator('label:has-text("状态")')).toBeVisible()

    // 验证查询和重置按钮
    await expect(page.locator('button:has-text("查询")')).toBeVisible()
    await expect(page.locator('button:has-text("重置")')).toBeVisible()

    // 验证表格列标题
    await expect(page.locator('.el-table th:has-text("教室")')).toBeVisible()
    await expect(page.locator('.el-table th:has-text("预约主题")')).toBeVisible()
    await expect(page.locator('.el-table th:has-text("日期")')).toBeVisible()
    await expect(page.locator('.el-table th:has-text("时间段")')).toBeVisible()
    await expect(page.locator('.el-table th:has-text("申请人")')).toBeVisible()
    await expect(page.locator('.el-table th:has-text("状态")')).toBeVisible()
    await expect(page.locator('.el-table th:has-text("操作")')).toBeVisible()

    // 验证分页组件存在
    await expect(page.locator('.el-pagination')).toBeVisible()
  })
})
