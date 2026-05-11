<template>
  <div class="asset-detail">
    <el-card v-loading="loading">
      <template #header>
        <div class="card-header">
          <el-page-header @back="handleBack" title="返回">
            <template #content>
              <span class="page-title">资产详情</span>
            </template>
          </el-page-header>
          <div class="header-actions">
            <el-button @click="handleBack">返回列表</el-button>
            <el-button type="primary" @click="handleEdit">编辑</el-button>
            <el-button type="success" v-if="detail.status === 'idle'" @click="handleBorrow">领用</el-button>
            <el-button type="warning" v-if="detail.status === 'in_use'" @click="handleReturn">归还</el-button>
            <el-button type="warning" plain @click="handleRepair">报修</el-button>
            <el-button type="danger" plain v-if="detail.status !== 'scrapped'" @click="handleScrap">报废</el-button>
          </div>
        </div>
      </template>

      <template v-if="detail.id">
        <!-- 状态标签 -->
        <div class="status-bar">
          <span class="status-label">当前状态：</span>
          <el-tag :type="getStatusType(detail.status)" size="large">{{ getStatusLabel(detail.status) }}</el-tag>
        </div>

        <el-row :gutter="24">
          <!-- 左侧：基本信息 -->
          <el-col :span="16">
            <el-card shadow="never" class="info-card">
              <template #header>
                <span>基本信息</span>
              </template>
              <el-descriptions :column="2" border>
                <el-descriptions-item label="资产编号">{{ detail.asset_no }}</el-descriptions-item>
                <el-descriptions-item label="资产名称">{{ detail.name }}</el-descriptions-item>
                <el-descriptions-item label="资产分类">{{ detail.category_name || '-' }}</el-descriptions-item>
                <el-descriptions-item label="品牌">{{ detail.brand || '-' }}</el-descriptions-item>
                <el-descriptions-item label="型号">{{ detail.model || '-' }}</el-descriptions-item>
                <el-descriptions-item label="条形码">{{ detail.barcode || '-' }}</el-descriptions-item>
                <el-descriptions-item label="购入日期">{{ detail.purchase_date || '-' }}</el-descriptions-item>
                <el-descriptions-item label="购入价格">
                  {{ detail.purchase_price ? `¥${detail.purchase_price.toFixed(2)}` : '-' }}
                </el-descriptions-item>
                <el-descriptions-item label="供应商">{{ detail.supplier || '-' }}</el-descriptions-item>
                <el-descriptions-item label="保修到期日">{{ detail.warranty_expire_date || '-' }}</el-descriptions-item>
                <el-descriptions-item label="规格参数" :span="2">
                  <div v-if="detail.specifications" class="spec-content" v-html="renderMarkdown(detail.specifications)"></div>
                  <span v-else>-</span>
                </el-descriptions-item>
              </el-descriptions>
            </el-card>

            <!-- 位置信息 -->
            <el-card shadow="never" class="info-card">
              <template #header>
                <span>位置信息</span>
              </template>
              <el-descriptions :column="3" border>
                <el-descriptions-item label="所在部门">{{ detail.department_name || '-' }}</el-descriptions-item>
                <el-descriptions-item label="存放位置">{{ detail.location || '-' }}</el-descriptions-item>
                <el-descriptions-item label="保管人">{{ detail.custodian_name || '-' }}</el-descriptions-item>
              </el-descriptions>
            </el-card>
          </el-col>

          <!-- 右侧：图片展示 -->
          <el-col :span="8">
            <el-card shadow="never" class="info-card">
              <template #header>
                <span>资产图片</span>
              </template>
              <div class="image-gallery" v-if="imageUrls.length > 0">
                <el-image
                  v-for="(url, index) in imageUrls"
                  :key="index"
                  :src="url"
                  :preview-src-list="imageUrls"
                  :initial-index="index"
                  fit="cover"
                  class="asset-image"
                />
              </div>
              <el-empty v-else description="暂无图片" :image-size="80" />
            </el-card>
          </el-col>
        </el-row>

        <!-- 借用历史记录 -->
        <el-card shadow="never" class="info-card">
          <template #header>
            <span>借用历史记录</span>
          </template>
          <el-table :data="historyList" v-loading="historyLoading" stripe>
            <el-table-column prop="operation_type" label="操作类型" width="100">
              <template #default="{ row }">
                <el-tag :type="getOperationType(row.operation_type)" size="small">
                  {{ getOperationLabel(row.operation_type) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="operator_name" label="操作人" width="100" />
            <el-table-column prop="purpose" label="用途/说明" min-width="180" show-overflow-tooltip />
            <el-table-column prop="created_at" label="操作时间" width="170" />
          </el-table>
          <div class="pagination" v-if="historyTotal > 0">
            <el-pagination
              v-model:current-page="historyPage"
              :page-size="10"
              :total="historyTotal"
              layout="total, prev, pager, next"
              @current-change="loadHistory"
            />
          </div>
        </el-card>
      </template>
    </el-card>

    <!-- 借用申请弹窗 -->
    <BorrowForm
      v-model:visible="borrowFormVisible"
      :asset-id="detail.id"
      :asset-name="detail.name"
      @success="loadDetail"
    />

    <!-- 报修弹窗 -->
    <el-dialog v-model="repairDialogVisible" title="报修申请" width="500px" @closed="resetRepairForm">
      <el-form ref="repairFormRef" :model="repairForm" :rules="repairRules" label-width="100px">
        <el-form-item label="报修原因" prop="reason">
          <el-input
            v-model="repairForm.reason"
            type="textarea"
            :rows="3"
            placeholder="请输入报修原因"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="repairDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitRepair" :loading="repairLoading">提交</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { assetApi, assetOperationApi } from '@/api/oa/assets'
import BorrowForm from './BorrowForm.vue'

const route = useRoute()
const router = useRouter()

const assetId = computed(() => route.params.id as string)

const loading = ref(false)
const detail = ref<any>({})

const statusOptions = [
  { label: '闲置', value: 'idle', type: 'success' },
  { label: '使用中', value: 'in_use', type: 'primary' },
  { label: '维修中', value: 'repairing', type: 'warning' },
  { label: '已报废', value: 'scrapped', type: 'info' }
]

const getStatusLabel = (val: string) => statusOptions.find(o => o.value === val)?.label || val
const getStatusType = (val: string) => statusOptions.find(o => o.value === val)?.type || 'info'

const operationOptions = [
  { label: '领用', value: 'claim', type: 'primary' },
  { label: '归还', value: 'return', type: 'success' },
  { label: '报修', value: 'repair', type: 'warning' },
  { label: '报废', value: 'scrap', type: 'danger' },
  { label: '调拨', value: 'transfer', type: '' },
  { label: '入库', value: 'stock_in', type: 'info' }
]

const getOperationLabel = (val: string) => operationOptions.find(o => o.value === val)?.label || val
const getOperationType = (val: string) => operationOptions.find(o => o.value === val)?.type || 'info'

// 图片展示
const imageUrls = computed(() => {
  if (detail.value.image_urls) {
    if (Array.isArray(detail.value.image_urls)) {
      return detail.value.image_urls
    }
    try {
      const parsed = JSON.parse(detail.value.image_urls)
      return Array.isArray(parsed) ? parsed : []
    } catch {
      return []
    }
  }
  return []
})

// 简单 Markdown 渲染（支持换行和加粗）
const renderMarkdown = (text: string) => {
  if (!text) return ''
  return text
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\n/g, '<br/>')
}

// 借用历史
const historyList = ref([])
const historyLoading = ref(false)
const historyPage = ref(1)
const historyTotal = ref(0)

const loadHistory = async () => {
  if (!assetId.value) return
  historyLoading.value = true
  try {
    const res = await assetApi.getHistory(assetId.value, {
      page: historyPage.value,
      pageSize: 10
    })
    historyList.value = res.data?.list || []
    historyTotal.value = res.data?.total || 0
  } catch (error) {
    console.error('加载历史记录失败', error)
  } finally {
    historyLoading.value = false
  }
}

// 加载详情
const loadDetail = async () => {
  if (!assetId.value) return
  loading.value = true
  try {
    const res = await assetApi.getById(assetId.value)
    detail.value = res.data || {}
  } catch (error) {
    ElMessage.error('加载资产详情失败')
  } finally {
    loading.value = false
  }
}

// 操作按钮
const handleBack = () => {
  router.push('/oa/assets')
}

const handleEdit = () => {
  router.push(`/oa/assets/${assetId.value}/edit`)
}

// 借用
const borrowFormVisible = ref(false)
const handleBorrow = () => {
  borrowFormVisible.value = true
}

// 归还
const handleReturn = async () => {
  try {
    await ElMessageBox.confirm('确认归还该资产？', '归还确认', {
      type: 'warning'
    })
    await assetApi.return(assetId.value)
    ElMessage.success('归还成功')
    loadDetail()
    loadHistory()
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error('归还失败')
    }
  }
}

// 报修
const repairDialogVisible = ref(false)
const repairLoading = ref(false)
const repairFormRef = ref()
const repairForm = reactive({
  reason: ''
})
const repairRules = {
  reason: [{ required: true, message: '请输入报修原因', trigger: 'blur' }]
}

const handleRepair = () => {
  repairDialogVisible.value = true
}

const resetRepairForm = () => {
  repairFormRef.value?.resetFields()
  repairForm.reason = ''
}

const submitRepair = async () => {
  try {
    await repairFormRef.value?.validate()
    repairLoading.value = true
    await assetApi.repair(assetId.value, { reason: repairForm.reason })
    ElMessage.success('报修申请已提交')
    repairDialogVisible.value = false
    loadDetail()
    loadHistory()
  } catch (error: any) {
    if (error !== false) {
      ElMessage.error('报修失败')
    }
  } finally {
    repairLoading.value = false
  }
}

// 报废
const handleScrap = async () => {
  try {
    await ElMessageBox.confirm('确认报废该资产？此操作不可恢复！', '报废确认', {
      type: 'warning',
      confirmButtonText: '确认报废',
      confirmButtonClass: 'el-button--danger'
    })
    await assetApi.scrap(assetId.value, {})
    ElMessage.success('资产已报废')
    loadDetail()
    loadHistory()
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error('报废失败')
    }
  }
}

onMounted(() => {
  loadDetail()
  loadHistory()
})
</script>

<style scoped>
.asset-detail {
  padding: 16px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-actions {
  display: flex;
  gap: 8px;
}

.status-bar {
  margin-bottom: 20px;
  display: flex;
  align-items: center;
}

.status-label {
  font-size: 14px;
  color: #606266;
  margin-right: 8px;
}

.info-card {
  margin-bottom: 16px;
}

.spec-content {
  line-height: 1.6;
  color: #303133;
}

.image-gallery {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.asset-image {
  width: 100%;
  height: 160px;
  border-radius: 4px;
}

.pagination {
  margin-top: 16px;
  display: flex;
  justify-content: flex-end;
}
</style>
