import { test, expect } from '@playwright/test'
import authSetup from '../fixtures/auth.setup'

test.use({ storageState: authSetup.storageState })

test.describe('资产管理模块', () => {
  test('资产列表页加载', async ({ page }) => {
    await page.goto('/oa/assets')

    // 验证页面标题
    await expect(page.locator('.card-header span')).toHaveText('资产管理')

    // 验证查询表单存在
    await expect(page.locator('.query-form')).toBeVisible()

    // 验证表格存在
    await expect(page.locator('.el-table')).toBeVisible()

    // 验证操作按钮存在
    await expect(page.getByRole('button', { name: '新增资产' })).toBeVisible()
    await expect(page.getByRole('button', { name: '批量导入' })).toBeVisible()
    await expect(page.getByRole('button', { name: '导出' })).toBeVisible()

    // 验证分页组件存在
    await expect(page.locator('.pagination .el-pagination')).toBeVisible()
  })

  test('新增资产表单', async ({ page }) => {
    await page.goto('/oa/assets/create')

    // 验证页面标题
    await expect(page.locator('.page-title')).toHaveText('新增资产')

    // 验证返回按钮
    await expect(page.locator('.el-page-header')).toBeVisible()

    // 验证表单字段存在
    await expect(page.locator('label').filter({ hasText: '资产名称' })).toBeVisible()
    await expect(page.locator('label').filter({ hasText: '资产分类' })).toBeVisible()
    await expect(page.locator('label').filter({ hasText: '资产编号' })).toBeVisible()
    await expect(page.locator('label').filter({ hasText: '品牌' })).toBeVisible()
    await expect(page.locator('label').filter({ hasText: '型号' })).toBeVisible()
    await expect(page.locator('label').filter({ hasText: '购入日期' })).toBeVisible()
    await expect(page.locator('label').filter({ hasText: '购入价格' })).toBeVisible()
    await expect(page.locator('label').filter({ hasText: '供应商' })).toBeVisible()

    // 验证操作按钮
    await expect(page.getByRole('button', { name: '保存' })).toBeVisible()
    await expect(page.getByRole('button', { name: '取消' })).toBeVisible()

    // 验证自动生成编号按钮
    await expect(page.getByRole('button', { name: '自动生成' })).toBeVisible()
  })

  test('资产详情页', async ({ page }) => {
    // 先访问列表页，然后点击查看按钮
    await page.goto('/oa/assets')

    // 等待表格加载
    await page.waitForSelector('.el-table')

    // 查找并点击第一个"查看"按钮
    const viewButtons = page.locator('.el-table').getByRole('button', { name: '查看' })
    const count = await viewButtons.count()

    if (count > 0) {
      await viewButtons.first().click()

      // 验证详情页加载
      await expect(page.locator('.asset-detail')).toBeVisible()

      // 验证基本信息卡片
      await expect(page.locator('.el-descriptions')).toBeVisible()

      // 验证操作按钮
      await expect(page.getByRole('button', { name: '返回列表' })).toBeVisible()
      await expect(page.getByRole('button', { name: '编辑' })).toBeVisible()

      // 验证借用历史记录表格
      await expect(page.locator('.info-card').last().locator('.el-table')).toBeVisible()
    } else {
      // 如果没有数据，直接访问详情页路由（使用模拟 ID）
      await page.goto('/oa/assets/test-id')
      // 页面应该仍然能渲染（即使数据为空）
      await expect(page.locator('.asset-detail')).toBeVisible()
    }
  })

  test('借用申请弹窗', async ({ page }) => {
    await page.goto('/oa/assets')

    // 等待表格加载
    await page.waitForSelector('.el-table')

    // 查找"更多"下拉按钮
    const moreButtons = page.locator('.el-table').getByRole('button', { name: /更多/ })
    const count = await moreButtons.count()

    if (count > 0) {
      // 点击第一个"更多"按钮
      await moreButtons.first().click()

      // 查找"领用"选项（可能不存在，取决于资产状态）
      const claimOption = page.locator('.el-dropdown-menu__item').filter({ hasText: '领用' })
      const claimCount = await claimOption.count()

      if (claimCount > 0) {
        await claimOption.first().click()

        // 验证借用申请弹窗打开
        await expect(page.locator('.el-dialog').filter({ hasText: '借用申请' })).toBeVisible()

        // 验证表单字段
        await expect(page.locator('label').filter({ hasText: '借用用途' })).toBeVisible()
        await expect(page.locator('label').filter({ hasText: '借用日期' })).toBeVisible()
        await expect(page.locator('label').filter({ hasText: '预计归还日期' })).toBeVisible()

        // 验证提交按钮
        await expect(page.locator('.el-dialog').filter({ hasText: '借用申请' }).getByRole('button', { name: '提交申请' })).toBeVisible()

        // 关闭弹窗
        await page.locator('.el-dialog').filter({ hasText: '借用申请' }).getByRole('button', { name: '取消' }).click()
      }
    }
  })
})
