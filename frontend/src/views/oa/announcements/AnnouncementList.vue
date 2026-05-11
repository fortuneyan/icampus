<template>
  <div class="announcement-list">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>公告管理</span>
          <el-button type="primary" @click="handleCreate">发布公告</el-button>
        </div>
      </template>

      <el-form :inline="true" :model="queryForm" class="query-form">
        <el-form-item label="标题">
          <el-input v-model="queryForm.title" placeholder="请输入标题" clearable />
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
            <el-option label="草稿" value="draft" />
            <el-option label="已发布" value="published" />
            <el-option label="已撤销" value="revoked" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleQuery">查询</el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>

      <el-table :data="tableData" v-loading="loading" stripe>
        <el-table-column prop="title" label="标题" min-width="200" show-overflow-tooltip />
        <el-table-column prop="category_name" label="分类" width="100" />
        <el-table-column prop="priority" label="优先级" width="80" align="center">
          <template #default="{ row }">
            <el-tag :type="getPriorityType(row.priority)" size="small">
              {{ getPriorityLabel(row.priority) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="is_top" label="置顶" width="60" align="center">
          <template #default="{ row }">
            <el-tag v-if="row.is_top" type="warning" size="small">是</el-tag>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">{{ getStatusLabel(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="view_count" label="阅读" width="70" align="center" />
        <el-table-column prop="publisher_name" label="发布人" width="100" />
        <el-table-column prop="published_at" label="发布时间" width="160" />
        <el-table-column label="操作" width="220" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click="handleView(row)">查看</el-button>
            <el-button link type="primary" size="small" @click="handleEdit(row)">编辑</el-button>
            <el-button link type="success" size="small" @click="handlePublish(row)" v-if="row.status === 'draft'">
              发布
            </el-button>
            <el-button link type="warning" size="small" @click="handleRevoke(row)" v-if="row.status === 'published'">
              撤销
            </el-button>
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
import { announcementApi, categoryApi } from '@/api/oa/announcements'

const router = useRouter()

const loading = ref(false)
const tableData = ref([])
const categoryList = ref([])
const queryForm = reactive({
  title: '',
  category_id: '',
  status: ''
})
const pagination = reactive({
  page: 1,
  pageSize: 10,
  total: 0
})

const priorityOptions = [
  { label: '普通', value: 'normal', type: 'info' },
  { label: '重要', value: 'important', type: 'warning' },
  { label: '紧急', value: 'urgent', type: 'danger' }
]

const statusOptions = [
  { label: '草稿', value: 'draft', type: 'info' },
  { label: '已发布', value: 'published', type: 'success' },
  { label: '已撤销', value: 'revoked', type: '' }
]

const getPriorityLabel = (val: string) => priorityOptions.find(o => o.value === val)?.label || val
const getPriorityType = (val: string) => priorityOptions.find(o => o.value === val)?.type || 'info'
const getStatusLabel = (val: string) => statusOptions.find(o => o.value === val)?.label || val
const getStatusType = (val: string) => statusOptions.find(o => o.value === val)?.type || 'info'

const loadData = async () => {
  loading.value = true
  try {
    const res = await announcementApi.getList({
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
    const res = await categoryApi.getList()
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
  queryForm.title = ''
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
  router.push('/oa/announcements/create')
}

const handleView = (row: any) => {
  router.push(`/oa/announcements/${row.id}`)
}

const handleEdit = (row: any) => {
  router.push(`/oa/announcements/${row.id}/edit`)
}

const handlePublish = async (row: any) => {
  try {
    await announcementApi.publish(row.id)
    ElMessage.success('发布成功')
    loadData()
  } catch (error) {
    ElMessage.error('发布失败')
  }
}

const handleRevoke = async (row: any) => {
  try {
    await announcementApi.revoke(row.id)
    ElMessage.success('撤销成功')
    loadData()
  } catch (error) {
    ElMessage.error('撤销失败')
  }
}

const handleDelete = async (row: any) => {
  try {
    await ElMessageBox.confirm('确定要删除该公告吗？', '提示', {
      type: 'warning'
    })
    await announcementApi.delete(row.id)
    ElMessage.success('删除成功')
    loadData()
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

onMounted(() => {
  loadCategories()
  loadData()
})
</script>

<style scoped>
.announcement-list {
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
