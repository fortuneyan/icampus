<template>
  <div class="asset-list">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>资产管理</span>
          <div>
            <el-button @click="handleImport">批量导入</el-button>
            <el-button @click="handleExport">导出</el-button>
            <el-button type="primary" @click="handleCreate">新增资产</el-button>
          </div>
        </div>
      </template>

      <el-form :inline="true" :model="queryForm" class="query-form">
        <el-form-item label="资产编号">
          <el-input v-model="queryForm.asset_no" placeholder="请输入资产编号" clearable />
        </el-form-item>
        <el-form-item label="资产名称">
          <el-input v-model="queryForm.name" placeholder="请输入资产名称" clearable />
        </el-form-item>
        <el-form-item label="分类">
          <el-select v-model="queryForm.category_id" placeholder="请选择分类" clearable>
            <el-option
              v-for="cat in categoryList"
              :key="cat.id"
              :label="cat.name"
              :value="cat.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="queryForm.status" placeholder="请选择状态" clearable>
            <el-option label="闲置" value="idle" />
            <el-option label="使用中" value="in_use" />
            <el-option label="维修中" value="repairing" />
            <el-option label="已报废" value="scrapped" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleQuery">查询</el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>

      <el-table :data="tableData" v-loading="loading" stripe>
        <el-table-column prop="asset_no" label="资产编号" width="120" />
        <el-table-column prop="name" label="资产名称" min-width="150" show-overflow-tooltip />
        <el-table-column prop="category_name" label="分类" width="100" />
        <el-table-column prop="model" label="规格型号" width="120" />
        <el-table-column prop="status" label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">{{ getStatusLabel(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="location" label="存放位置" width="120" />
        <el-table-column prop="custodian_name" label="保管人" width="100" />
        <el-table-column prop="purchase_date" label="购入日期" width="100" />
        <el-table-column prop="purchase_price" label="购入价格" width="100" align="right">
          <template #default="{ row }">
            {{ row.purchase_price ? `¥${row.purchase_price.toFixed(2)}` : '-' }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click="handleView(row)">查看</el-button>
            <el-button link type="primary" size="small" @click="handleEdit(row)">编辑</el-button>
            <el-dropdown trigger="click" @command="(cmd) => handleCommand(cmd, row)">
              <el-button link type="primary" size="small">
                更多<el-icon class="el-icon--right"><arrow-down /></el-icon>
              </el-button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="claim" v-if="row.status === 'idle'">领用</el-dropdown-item>
                  <el-dropdown-item command="return" v-if="row.status === 'in_use'">归还</el-dropdown-item>
                  <el-dropdown-item command="repair">报修</el-dropdown-item>
                  <el-dropdown-item command="scrap" v-if="row.status !== 'scrapped'">报废</el-dropdown-item>
                  <el-dropdown-item command="history">操作记录</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.pageSize"
          :total="pagination.total"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handlePageChange"
        />
      </div>
    </el-card>

    <!-- 借用申请弹窗 -->
    <BorrowForm
      v-model:visible="borrowFormVisible"
      :asset-id="currentAsset.id"
      :asset-name="currentAsset.name"
      @success="loadData"
    />

    <!-- 报修弹窗 -->
    <el-dialog v-model="repairDialogVisible" title="报修申请" width="500px" @closed="resetRepairForm">
      <el-form ref="repairFormRef" :model="repairForm" :rules="repairRules" label-width="100px">
        <el-form-item label="资产名称">
          <el-input :model-value="currentAsset.name" disabled />
        </el-form-item>
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

    <!-- 批量导入弹窗 -->
    <el-dialog v-model="importDialogVisible" title="批量导入资产" width="500px">
      <el-upload
        ref="importUploadRef"
        :auto-upload="false"
        :limit="1"
        accept=".xlsx,.xls,.csv"
        :on-change="handleImportFileChange"
        :on-exceed="handleImportExceed"
        drag
      >
        <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
        <div class="el-upload__text">
          将文件拖到此处，或 <em>点击上传</em>
        </div>
        <template #tip>
          <div class="el-upload__tip">
            仅支持 .xlsx、.xls、.csv 格式文件
          </div>
        </template>
      </el-upload>
      <template #footer>
        <el-button @click="importDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitImport" :loading="importLoading">确认导入</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ArrowDown, UploadFilled } from '@element-plus/icons-vue'
import type { UploadFile, UploadInstance } from 'element-plus'
import { assetApi, assetCategoryApi } from '@/api/oa/assets'
import BorrowForm from './BorrowForm.vue'

const router = useRouter()

const loading = ref(false)
const tableData = ref([])
const categoryList = ref([])

const queryForm = reactive({
  asset_no: '',
  name: '',
  category_id: '',
  status: ''
})

const pagination = reactive({
  page: 1,
  pageSize: 10,
  total: 0
})

const statusOptions = [
  { label: '闲置', value: 'idle', type: 'success' },
  { label: '使用中', value: 'in_use', type: 'primary' },
  { label: '维修中', value: 'repairing', type: 'warning' },
  { label: '已报废', value: 'scrapped', type: 'info' }
]

const getStatusLabel = (val: string) => statusOptions.find(o => o.value === val)?.label || val
const getStatusType = (val: string) => statusOptions.find(o => o.value === val)?.type || 'info'

const loadData = async () => {
  loading.value = true
  try {
    const res = await assetApi.getList({
      ...queryForm,
      page: pagination.page,
      pageSize: pagination.pageSize
    })
    tableData.value = res.data?.list || []
    pagination.total = res.data?.total || 0
  } catch (error) {
    ElMessage.error('加载数据失败')
  } finally {
    loading.value = false
  }
}

const loadCategories = async () => {
  try {
    const res = await assetCategoryApi.getList()
    categoryList.value = res.data?.list || []
  } catch (error) {
    console.error('加载分类失败', error)
  }
}

const handleQuery = () => {
  pagination.page = 1
  loadData()
}

const handleReset = () => {
  queryForm.asset_no = ''
  queryForm.name = ''
  queryForm.category_id = ''
  queryForm.status = ''
  handleQuery()
}

const handleSizeChange = () => {
  pagination.page = 1
  loadData()
}

const handlePageChange = () => {
  loadData()
}

const handleCreate = () => {
  router.push('/oa/assets/create')
}

const handleView = (row: any) => {
  router.push(`/oa/assets/${row.id}`)
}

const handleEdit = (row: any) => {
  router.push(`/oa/assets/${row.id}/edit`)
}

// 当前操作的资产
const currentAsset = ref<any>({ id: '', name: '' })

// 借用弹窗
const borrowFormVisible = ref(false)

// 报修弹窗
const repairDialogVisible = ref(false)
const repairLoading = ref(false)
const repairFormRef = ref()
const repairForm = reactive({
  reason: ''
})
const repairRules = {
  reason: [{ required: true, message: '请输入报修原因', trigger: 'blur' }]
}

const resetRepairForm = () => {
  repairFormRef.value?.resetFields()
  repairForm.reason = ''
}

const submitRepair = async () => {
  try {
    await repairFormRef.value?.validate()
    repairLoading.value = true
    await assetApi.repair(currentAsset.value.id, { reason: repairForm.reason })
    ElMessage.success('报修申请已提交')
    repairDialogVisible.value = false
    loadData()
  } catch (error: any) {
    if (error !== false) {
      ElMessage.error('报修失败')
    }
  } finally {
    repairLoading.value = false
  }
}

// 导入弹窗
const importDialogVisible = ref(false)
const importLoading = ref(false)
const importUploadRef = ref<UploadInstance>()
const importFile = ref<File | null>(null)

const handleImportFileChange = (file: UploadFile) => {
  importFile.value = file.raw || null
}

const handleImportExceed = () => {
  ElMessage.warning('只能上传一个文件，请先移除已选文件')
}

const submitImport = async () => {
  if (!importFile.value) {
    ElMessage.warning('请先选择文件')
    return
  }
  importLoading.value = true
  try {
    const formData = new FormData()
    formData.append('file', importFile.value)
    await assetApi.import(formData)
    ElMessage.success('导入成功')
    importDialogVisible.value = false
    loadData()
  } catch (error) {
    ElMessage.error('导入失败')
  } finally {
    importLoading.value = false
  }
}

const handleCommand = async (command: string, row: any) => {
  currentAsset.value = { id: row.id, name: row.name }
  switch (command) {
    case 'claim':
      borrowFormVisible.value = true
      break
    case 'return':
      try {
        await assetApi.return(row.id)
        ElMessage.success('归还成功')
        loadData()
      } catch (error) {
        ElMessage.error('归还失败')
      }
      break
    case 'repair':
      repairDialogVisible.value = true
      break
    case 'scrap':
      try {
        await ElMessageBox.confirm(
          `确认报废资产「${row.name}」？此操作不可恢复！`,
          '报废确认',
          {
            type: 'warning',
            confirmButtonText: '确认报废',
            confirmButtonClass: 'el-button--danger'
          }
        )
        await assetApi.scrap(row.id, {})
        ElMessage.success('资产已报废')
        loadData()
      } catch (error: any) {
        if (error !== 'cancel') {
          ElMessage.error('报废失败')
        }
      }
      break
    case 'history':
      router.push(`/oa/assets/${row.id}/history`)
      break
  }
}

const handleImport = () => {
  importFile.value = null
  importDialogVisible.value = true
}

const handleExport = async () => {
  try {
    const res = await assetApi.export({ ...queryForm })
    // 处理 Blob 下载
    const blob = new Blob([res as any], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' })
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `资产列表_${new Date().toISOString().slice(0, 10)}.xlsx`
    link.click()
    window.URL.revokeObjectURL(url)
    ElMessage.success('导出成功')
  } catch (error) {
    ElMessage.error('导出失败')
  }
}

onMounted(() => {
  loadCategories()
  loadData()
})
</script>

<style scoped>
.asset-list {
  padding: 16px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.query-form {
  margin-bottom: 16px;
}

.pagination {
  margin-top: 16px;
  display: flex;
  justify-content: flex-end;
}
</style>
