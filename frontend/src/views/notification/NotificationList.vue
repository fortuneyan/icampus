<template>
  <div class="notification-management">
    <el-card>
      <div class="toolbar">
        <el-form :inline="true" :model="searchForm">
          <el-form-item label="通知类型">
            <el-select v-model="searchForm.notification_type" placeholder="请选择" clearable>
              <el-option label="通知" value="notice" />
              <el-option label="公告" value="announcement" />
              <el-option label="作业" value="homework" />
            </el-select>
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="handleSearch">搜索</el-button>
            <el-button @click="handleReset">重置</el-button>
            <el-button type="success" @click="handleAdd">发布通知</el-button>
          </el-form-item>
        </el-form>
      </div>

      <el-table :data="tableData" v-loading="loading" stripe>
        <el-table-column prop="title" label="标题" width="200" />
        <el-table-column prop="notification_type" label="类型" width="100">
          <template #default="{ row }">
            <el-tag v-if="row.notification_type === 'notice'" type="info">通知</el-tag>
            <el-tag v-else-if="row.notification_type === 'announcement'" type="warning">公告</el-tag>
            <el-tag v-else type="success">作业</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="scope_type" label="推送范围" width="100">
          <template #default="{ row }">
            <span v-if="row.scope_type === 'all'">全部</span>
            <span v-else-if="row.scope_type === 'grade'">年级</span>
            <span v-else-if="row.scope_type === 'class'">班级</span>
            <span v-else>个人</span>
          </template>
        </el-table-column>
        <el-table-column prop="is_urgent" label="加急" width="80">
          <template #default="{ row }">
            <el-tag v-if="row.is_urgent" type="danger">是</el-tag>
            <span v-else>否</span>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag v-if="row.status === 'draft'" type="info">草稿</el-tag>
            <el-tag v-else-if="row.status === 'published'" type="success">已发布</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180" />
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link @click="handleEdit(row)">编辑</el-button>
            <el-button v-if="row.status === 'draft'" type="success" link @click="handleSend(row)">发送</el-button>
            <el-button type="danger" link @click="handleDelete(row)">删除</el-button>
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
        <el-form-item label="通知标题" prop="title">
          <el-input v-model="formData.title" placeholder="请输入通知标题" />
        </el-form-item>
        <el-form-item label="通知类型" prop="notification_type">
          <el-select v-model="formData.notification_type">
            <el-option label="通知" value="notice" />
            <el-option label="公告" value="announcement" />
            <el-option label="作业" value="homework" />
          </el-select>
        </el-form-item>
        <el-form-item label="推送范围" prop="scope_type">
          <el-select v-model="formData.scope_type" @change="handleScopeChange">
            <el-option label="全部" value="all" />
            <el-option label="按年级" value="grade" />
            <el-option label="按班级" value="class" />
            <el-option label="个人" value="individual" />
          </el-select>
        </el-form-item>
        <el-form-item v-if="formData.scope_type === 'grade'" label="选择年级" prop="scope_ids">
          <el-select v-model="formData.scope_ids" multiple placeholder="请选择年级">
            <el-option v-for="g in gradeOptions" :key="g.value" :label="g.label" :value="g.value" />
          </el-select>
        </el-form-item>
        <el-form-item v-if="formData.scope_type === 'class'" label="选择班级" prop="scope_ids">
          <el-select v-model="formData.scope_ids" multiple placeholder="请选择班级">
            <el-option v-for="c in classOptions" :key="c.value" :label="c.label" :value="c.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="加急" prop="is_urgent">
          <el-switch v-model="formData.is_urgent" />
        </el-form-item>
        <el-form-item label="通知内容" prop="content">
          <el-input v-model="formData.content" type="textarea" :rows="5" placeholder="请输入通知内容" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { FormInstance } from 'element-plus'
import {
  getNotificationAdminList,
  createNotification,
  updateNotification,
  deleteNotification,
  sendNotification
} from '@/api/notification'
import { getGradeOptions } from '@/api/edu/grade'
import { getClassOptions } from '@/api/edu/class'

const loading = ref(false)
const tableData = ref([])
const searchForm = reactive({ notification_type: '' })
const pagination = reactive({ page: 1, pageSize: 20, total: 0 })

const gradeOptions = ref<any[]>([])
const classOptions = ref<any[]>([])

const dialogVisible = ref(false)
const dialogTitle = ref('')
const formRef = ref<FormInstance>()
const formData = reactive<any>({
  id: '',
  title: '',
  content: '',
  notification_type: 'notice',
  scope_type: 'all',
  scope_ids: [],
  is_urgent: false
})

const formRules = {
  title: [{ required: true, message: '请输入通知标题', trigger: 'blur' }],
  content: [{ required: true, message: '请输入通知内容', trigger: 'blur' }]
}

const fetchData = async () => {
  loading.value = true
  try {
    const res = await getNotificationAdminList({
      ...searchForm,
      page: pagination.page,
      page_size: pagination.pageSize
    })
    tableData.value = res.data.items
    pagination.total = res.data.total
  } catch (e) { console.error(e) }
  finally { loading.value = false }
}

const fetchGrades = async () => {
  try {
    const res = await getGradeOptions()
    gradeOptions.value = res.data || []
  } catch (e) { console.error(e) }
}

const fetchClasses = async () => {
  try {
    const res = await getClassOptions()
    classOptions.value = res.data || []
  } catch (e) { console.error(e) }
}

const handleSearch = () => { pagination.page = 1; fetchData() }
const handleReset = () => { searchForm.notification_type = ''; handleSearch() }

const handleAdd = () => {
  Object.assign(formData, {
    id: '',
    title: '',
    content: '',
    notification_type: 'notice',
    scope_type: 'all',
    scope_ids: [],
    is_urgent: false
  })
  dialogTitle.value = '发布通知'
  dialogVisible.value = true
}

const handleEdit = (row: any) => {
  Object.assign(formData, {
    id: row.id,
    title: row.title,
    content: row.content,
    notification_type: row.notification_type,
    scope_type: row.scope_type,
    scope_ids: row.scope_ids || [],
    is_urgent: row.is_urgent
  })
  dialogTitle.value = '编辑通知'
  dialogVisible.value = true
}

const handleSubmit = async () => {
  if (!formRef.value) return
  await formRef.value.validate()
  try {
    const data = { ...formData }
    if (formData.id) {
      await updateNotification(formData.id, data)
      ElMessage.success('更新成功')
    } else {
      await createNotification(data)
      ElMessage.success('创建成功')
    }
    dialogVisible.value = false
    fetchData()
  } catch (e: any) { ElMessage.error(e.message || '操作失败') }
}

const handleSend = async (row: any) => {
  try {
    await ElMessageBox.confirm('确定要发送此通知吗？', '提示', { type: 'warning' })
    await sendNotification(row.id)
    ElMessage.success('发送成功')
    fetchData()
  } catch (e: any) { if (e !== 'cancel') ElMessage.error(e.message || '发送失败') }
}

const handleDelete = async (row: any) => {
  try {
    await ElMessageBox.confirm('确定要删除该通知吗？', '提示', { type: 'warning' })
    await deleteNotification(row.id)
    ElMessage.success('删除成功')
    fetchData()
  } catch (e: any) { if (e !== 'cancel') ElMessage.error(e.message || '删除失败') }
}

const handleScopeChange = () => {
  formData.scope_ids = []
}

onMounted(() => { fetchGrades(); fetchClasses(); fetchData() })
</script>

<style scoped lang="scss">
.notification-management {
  .toolbar { margin-bottom: 20px; }
  .pagination { margin-top: 20px; display: flex; justify-content: flex-end; }
}
</style>