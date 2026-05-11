<template>
  <div class="workflow-list">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>工作流管理</span>
          <el-button type="primary" @click="handleCreate">新建工作流</el-button>
        </div>
      </template>

      <el-form :inline="true" :model="queryForm" class="query-form">
        <el-form-item label="工作流名称">
          <el-input v-model="queryForm.name" placeholder="请输入工作流名称" clearable />
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="queryForm.status" placeholder="请选择状态" clearable>
            <el-option label="草稿" value="draft" />
            <el-option label="已发布" value="published" />
            <el-option label="已禁用" value="disabled" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleQuery">查询</el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>

      <el-table :data="tableData" v-loading="loading" stripe>
        <el-table-column prop="name" label="工作流名称" min-width="150" />
        <el-table-column prop="code" label="编码" width="120" />
        <el-table-column prop="category" label="分类" width="100">
          <template #default="{ row }">
            <el-tag>{{ getCategoryLabel(row.category) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">{{ getStatusLabel(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="instance_count" label="实例数" width="80" align="center" />
        <el-table-column prop="version" label="版本" width="60" align="center" />
        <el-table-column prop="created_at" label="创建时间" width="160">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click="handleView(row)">查看</el-button>
            <el-button link type="primary" size="small" @click="handleEdit(row)">编辑</el-button>
            <el-button link type="success" size="small" @click="handleDesign(row)">设计</el-button>
            <el-button link type="danger" size="small" @click="handleDelete(row)">删除</el-button>
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
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { workflowApi } from '@/api/oa/workflows'

const router = useRouter()

const loading = ref(false)
const tableData = ref([])
const queryForm = reactive({
  name: '',
  status: ''
})
const pagination = reactive({
  page: 1,
  pageSize: 10,
  total: 0
})

const categoryOptions = [
  { label: '请假', value: 'leave' },
  { label: '报销', value: 'reimburse' },
  { label: '采购', value: 'purchase' },
  { label: '用车', value: 'vehicle' },
  { label: '通用', value: 'general' }
]

const statusOptions = [
  { label: '草稿', value: 'draft', type: 'info' },
  { label: '已发布', value: 'published', type: 'success' },
  { label: '已禁用', value: 'disabled', type: 'danger' }
]

const getCategoryLabel = (val: string) => {
  return categoryOptions.find(o => o.value === val)?.label || val
}

const getStatusLabel = (val: string) => {
  return statusOptions.find(o => o.value === val)?.label || val
}

const getStatusType = (val: string) => {
  return statusOptions.find(o => o.value === val)?.type || 'info'
}

const formatDate = (val: string) => {
  if (!val) return '-'
  const date = new Date(val)
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  const hours = String(date.getHours()).padStart(2, '0')
  const minutes = String(date.getMinutes()).padStart(2, '0')
  return `${year}-${month}-${day} ${hours}:${minutes}`
}

const loadData = async () => {
  loading.value = true
  try {
    const res = await workflowApi.getList({
      ...queryForm,
      page: pagination.page,
      pageSize: pagination.pageSize
    })
    tableData.value = res.data?.items || res.data?.list || []
    pagination.total = res.data?.total || 0
  } catch (error) {
    ElMessage.error('加载数据失败')
  } finally {
    loading.value = false
  }
}

const handleQuery = () => {
  pagination.page = 1
  loadData()
}

const handleReset = () => {
  queryForm.name = ''
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
  router.push('/oa/workflows/create')
}

const handleView = (row: any) => {
  router.push(`/oa/workflows/${row.id}/view`)
}

const handleEdit = (row: any) => {
  router.push(`/oa/workflows/${row.id}/edit`)
}

const handleDesign = (row: any) => {
  router.push(`/oa/workflows/${row.id}/design`)
}

const handleDelete = async (row: any) => {
  try {
    await ElMessageBox.confirm('确定要删除该工作流吗？', '提示', {
      type: 'warning'
    })
    await workflowApi.delete(row.id)
    ElMessage.success('删除成功')
    loadData()
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

onMounted(() => {
  loadData()
})
</script>

<style scoped>
.workflow-list {
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
