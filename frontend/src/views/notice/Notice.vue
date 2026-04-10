<template>
  <div class="notice-management">
    <el-card>
      <div class="toolbar">
        <el-form :inline="true" :model="searchForm">
          <el-form-item label="标题">
            <el-input v-model="searchForm.keyword" placeholder="请输入" clearable />
          </el-form-item>
          <el-form-item label="类型">
            <el-select v-model="searchForm.notice_type" placeholder="请选择" clearable>
              <el-option label="系统通知" value="system" />
              <el-option label="班级通知" value="class" />
              <el-option label="个人通知" value="personal" />
            </el-select>
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="handleSearch">搜索</el-button>
            <el-button type="success" @click="handleAdd">发布通知</el-button>
          </el-form-item>
        </el-form>
      </div>

      <el-table :data="tableData" v-loading="loading" stripe @row-click="handleRowClick">
        <el-table-column prop="title" label="标题" min-width="200" />
        <el-table-column prop="notice_type" label="类型" width="100">
          <template #default="{ row }">
            <el-tag>{{ getTypeName(row.notice_type) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="priority" label="优先级" width="100">
          <template #default="{ row }">
            <el-tag :type="getPriorityType(row.priority)">{{ row.priority }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="is_read" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.is_read ? 'info' : 'success'">{{ row.is_read ? '已读' : '未读' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="published_at" label="发布时间" width="180" />
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link @click.stop="handleView(row)">查看</el-button>
            <el-button type="danger" link @click.stop="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.pageSize"
          :total="pagination.total"
          :page-sizes="[10, 20, 50]"
          layout="total, sizes, prev, pager, next"
          @size-change="fetchData"
          @current-change="fetchData"
        />
      </div>
    </el-card>

    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="700px">
      <el-form ref="formRef" :model="formData" :rules="formRules" label-width="100px">
        <el-form-item label="标题" prop="title">
          <el-input v-model="formData.title" />
        </el-form-item>
        <el-form-item label="类型" prop="notice_type">
          <el-select v-model="formData.notice_type">
            <el-option label="系统通知" value="system" />
            <el-option label="班级通知" value="class" />
            <el-option label="个人通知" value="personal" />
          </el-select>
        </el-form-item>
        <el-form-item label="优先级" prop="priority">
          <el-select v-model="formData.priority">
            <el-option label="普通" value="normal" />
            <el-option label="重要" value="important" />
            <el-option label="紧急" value="urgent" />
          </el-select>
        </el-form-item>
        <el-form-item label="内容" prop="content">
          <el-input v-model="formData.content" type="textarea" :rows="8" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit">发布</el-button>
      </template>
    </el-dialog>

    <el-drawer v-model="drawerVisible" :title="currentNotice?.title" size="60%">
      <div class="notice-content">
        <div class="notice-meta">
          <el-tag>{{ getTypeName(currentNotice?.notice_type || '') }}</el-tag>
          <span>{{ currentNotice?.published_at }}</span>
        </div>
        <div class="notice-body">{{ currentNotice?.content }}</div>
      </div>
      <template #footer>
        <el-button type="primary" @click="handleMarkRead">标记已读</el-button>
      </template>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { FormInstance } from 'element-plus'
import { getNoticeList, createNotice, deleteNotice, markRead } from '@/api/notice'

const loading = ref(false)
const tableData = ref([])
const searchForm = reactive({ keyword: '', notice_type: '' })
const pagination = reactive({ page: 1, pageSize: 20, total: 0 })

const dialogVisible = ref(false)
const drawerVisible = ref(false)
const dialogTitle = ref('')
const formRef = ref<FormInstance>()
const formData = reactive<any>({ id: '', title: '', notice_type: 'system', priority: 'normal', content: '' })
const currentNotice = ref<any>(null)

const formRules = {
  title: [{ required: true, message: '请输入标题', trigger: 'blur' }],
  content: [{ required: true, message: '请输入内容', trigger: 'blur' }]
}

const getTypeName = (type: string) => ({ system: '系统', class: '班级', personal: '个人' }[type] || type)
const getPriorityType = (priority: string) => ({ normal: '', important: 'warning', urgent: 'danger' }[priority] || '')

const fetchData = async () => {
  loading.value = true
  try {
    const res = await getNoticeList({ ...searchForm, page: pagination.page, page_size: pagination.pageSize })
    tableData.value = res.data.items || []
    pagination.total = res.data.total || 0
  } catch (e) { console.error(e) }
  finally { loading.value = false }
}

const handleSearch = () => { pagination.page = 1; fetchData() }

const handleAdd = () => {
  Object.assign(formData, { id: '', title: '', notice_type: 'system', priority: 'normal', content: '' })
  dialogTitle.value = '发布通知'
  dialogVisible.value = true
}

const handleView = (row: any) => {
  currentNotice.value = row
  drawerVisible.value = true
}

const handleRowClick = (row: any) => { handleView(row) }

const handleMarkRead = async () => {
  try {
    if (currentNotice.value?.id) {
      await markRead(currentNotice.value.id)
      ElMessage.success('已标记为已读')
      fetchData()
    }
    drawerVisible.value = false
  } catch (e: any) { ElMessage.error(e.message || '操作失败') }
}

const handleSubmit = async () => {
  if (!formRef.value) return
  await formRef.value.validate()
  try {
    await createNotice(formData)
    ElMessage.success('发布成功')
    dialogVisible.value = false
    fetchData()
  } catch (e: any) { ElMessage.error(e.message || '操作失败') }
}

const handleDelete = async (row: any) => {
  try {
    await ElMessageBox.confirm('确定要删除该通知吗？', '提示', { type: 'warning' })
    await deleteNotice(row.id)
    ElMessage.success('删除成功')
    fetchData()
  } catch (e: any) { if (e !== 'cancel') ElMessage.error(e.message || '删除失败') }
}

onMounted(() => { fetchData() })
</script>

<style scoped lang="scss">
.notice-management {
  .toolbar { margin-bottom: 20px; }
  .pagination { margin-top: 20px; display: flex; justify-content: flex-end; }
  
  .notice-content {
    .notice-meta {
      display: flex;
      gap: 15px;
      margin-bottom: 20px;
      color: #666;
    }
    .notice-body {
      line-height: 1.8;
      white-space: pre-wrap;
    }
  }
}
</style>