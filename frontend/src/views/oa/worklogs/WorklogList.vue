<template>
  <div class="worklog-list">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>工作日志</span>
          <el-button type="primary" @click="handleCreate">写日志</el-button>
        </div>
      </template>

      <el-tabs v-model="activeTab" @tab-change="handleTabChange">
        <el-tab-pane label="我的日志" name="my" />
        <el-tab-pane label="下属日志" name="subordinate" />
        <el-tab-pane label="统计报表" name="statistics" />
      </el-tabs>

      <el-form :inline="true" :model="queryForm" class="query-form">
        <el-form-item label="日期范围">
          <el-date-picker
            v-model="queryForm.date_range"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            value-format="YYYY-MM-DD"
            clearable
          />
        </el-form-item>
        <el-form-item label="分类" v-if="activeTab !== 'statistics'">
          <el-select v-model="queryForm.category_id" placeholder="请选择分类" clearable>
            <el-option
              v-for="cat in categoryList"
              :key="cat.id"
              :label="cat.name"
              :value="cat.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleQuery">查询</el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>

      <div v-if="activeTab === 'statistics'" class="statistics-panel">
        <el-row :gutter="16">
          <el-col :span="6">
            <el-statistic title="本月日志数" :value="stats.monthly_count || 0" />
          </el-col>
          <el-col :span="6">
            <el-statistic title="本周日志数" :value="stats.weekly_count || 0" />
          </el-col>
          <el-col :span="6">
            <el-statistic title="总字数" :value="stats.total_words || 0" />
          </el-col>
          <el-col :span="6">
            <el-statistic title="连续打卡" :value="stats.streak_days || 0" suffix="天" />
          </el-col>
        </el-row>
      </div>

      <el-timeline v-else v-loading="loading">
        <el-timeline-item
          v-for="item in tableData"
          :key="item.id"
          :timestamp="item.created_at"
          placement="top"
        >
          <el-card>
            <template #header>
              <div class="log-header">
                <div class="log-title">
                  <span class="log-date">{{ item.log_date }}</span>
                  <el-tag v-if="item.category_name" size="small">{{ item.category_name }}</el-tag>
                </div>
                <div class="log-actions">
                  <el-button link type="primary" @click="handleEdit(item)">编辑</el-button>
                  <el-button link type="danger" @click="handleDelete(item)">删除</el-button>
                </div>
              </div>
            </template>
            <div class="log-content">
              <h4>{{ item.title }}</h4>
              <p>{{ item.content }}</p>
              <div v-if="item.attachments?.length" class="log-attachments">
                <el-icon><paperclip /></el-icon>
                <span>{{ item.attachments.length }} 个附件</span>
              </div>
            </div>
            <div class="log-footer">
              <div class="log-meta">
                <el-icon><view /></el-icon>
                <span>{{ item.view_count || 0 }}</span>
                <el-icon><star-filled /></el-icon>
                <span>{{ item.like_count || 0 }}</span>
                <el-icon><chat-dot-round /></el-icon>
                <span>{{ item.comment_count || 0 }}</span>
              </div>
              <div class="log-author" v-if="activeTab === 'subordinate'">
                {{ item.author_name }}
              </div>
            </div>
          </el-card>
        </el-timeline-item>
      </el-timeline>

      <div class="pagination" v-if="activeTab !== 'statistics'">
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

    <!-- 日志编辑弹窗 -->
    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="700px" @closed="resetForm">
      <el-form ref="formRef" :model="formData" :rules="formRules" label-width="80px">
        <el-form-item label="日期" prop="log_date">
          <el-date-picker
            v-model="formData.log_date"
            type="date"
            placeholder="选择日期"
            value-format="YYYY-MM-DD"
          />
        </el-form-item>
        <el-form-item label="分类" prop="category_id">
          <el-select v-model="formData.category_id" placeholder="请选择分类" clearable>
            <el-option
              v-for="cat in categoryList"
              :key="cat.id"
              :label="cat.name"
              :value="cat.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="标题" prop="title">
          <el-input v-model="formData.title" placeholder="请输入标题" />
        </el-form-item>
        <el-form-item label="内容" prop="content">
          <el-input v-model="formData.content" type="textarea" :rows="8" placeholder="请输入工作内容" />
        </el-form-item>
        <el-form-item label="附件">
          <el-upload
            :auto-upload="false"
            :limit="5"
            accept=".pdf,.doc,.docx,.xls,.xlsx,.jpg,.png"
          >
            <el-button type="primary">上传附件</el-button>
          </el-upload>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitLoading">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Paperclip, View, StarFilled, ChatDotRound } from '@element-plus/icons-vue'
import { worklogApi, worklogCategoryApi } from '@/api/oa/worklogs'

const loading = ref(false)
const dialogVisible = ref(false)
const dialogTitle = ref('写日志')
const submitLoading = ref(false)
const activeTab = ref('my')
const tableData = ref([])
const categoryList = ref([])
const stats = reactive({
  monthly_count: 0,
  weekly_count: 0,
  total_words: 0,
  streak_days: 0
})

const formRef = ref()

const queryForm = reactive({
  date_range: [],
  category_id: ''
})

const pagination = reactive({
  page: 1,
  pageSize: 10,
  total: 0
})

const formData = reactive({
  id: '',
  log_date: '',
  category_id: '',
  title: '',
  content: '',
  attachments: []
})

const formRules = {
  log_date: [{ required: true, message: '请选择日期', trigger: 'change' }],
  title: [{ required: true, message: '请输入标题', trigger: 'blur' }],
  content: [{ required: true, message: '请输入内容', trigger: 'blur' }]
}

const loadData = async () => {
  loading.value = true
  try {
    let res
    const params = {
      ...queryForm,
      page: pagination.page,
      pageSize: pagination.pageSize
    }
    if (activeTab.value === 'my') {
      res = await worklogApi.getMyList(params)
    } else if (activeTab.value === 'subordinate') {
      res = await worklogApi.getSubordinateList(params)
    } else {
      const statsRes = await worklogApi.getStatistics()
      Object.assign(stats, statsRes.data || {})
      loading.value = false
      return
    }
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
    const res = await worklogCategoryApi.getList()
    categoryList.value = res.data?.list || []
  } catch (error) {
    console.error('加载分类失败', error)
  }
}

const handleTabChange = () => {
  pagination.page = 1
  loadData()
}

const handleQuery = () => {
  pagination.page = 1
  loadData()
}

const handleReset = () => {
  queryForm.date_range = []
  queryForm.category_id = ''
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
  dialogTitle.value = '写日志'
  formData.id = ''
  formData.log_date = new Date().toISOString().split('T')[0]
  dialogVisible.value = true
}

const handleEdit = (row: any) => {
  dialogTitle.value = '编辑日志'
  Object.assign(formData, row)
  dialogVisible.value = true
}

const handleDelete = async (row: any) => {
  try {
    await ElMessageBox.confirm('确定要删除该日志吗？', '提示', {
      type: 'warning'
    })
    await worklogApi.delete(row.id)
    ElMessage.success('删除成功')
    loadData()
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

const resetForm = () => {
  formRef.value?.resetFields()
  Object.assign(formData, {
    id: '',
    log_date: '',
    category_id: '',
    title: '',
    content: '',
    attachments: []
  })
}

const handleSubmit = async () => {
  try {
    await formRef.value?.validate()
    submitLoading.value = true
    if (formData.id) {
      await worklogApi.update(formData.id, formData)
    } else {
      await worklogApi.create(formData)
    }
    ElMessage.success('保存成功')
    dialogVisible.value = false
    loadData()
  } catch (error: any) {
    if (error !== false) {
      ElMessage.error('保存失败')
    }
  } finally {
    submitLoading.value = false
  }
}

onMounted(() => {
  loadCategories()
  loadData()
})
</script>

<style scoped>
.worklog-list {
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

.statistics-panel {
  padding: 24px;
  background: #f5f7fa;
  border-radius: 4px;
  margin-bottom: 16px;
}

.log-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.log-title {
  display: flex;
  align-items: center;
  gap: 8px;
}

.log-date {
  font-weight: bold;
  font-size: 14px;
}

.log-content {
  margin: 12px 0;
}

.log-content h4 {
  margin: 0 0 8px 0;
  font-size: 15px;
}

.log-content p {
  margin: 0;
  color: #606266;
  line-height: 1.6;
}

.log-attachments {
  margin-top: 8px;
  color: #909399;
  font-size: 12px;
}

.log-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid #ebeef5;
}

.log-meta {
  display: flex;
  align-items: center;
  gap: 4px;
  color: #909399;
  font-size: 13px;
}

.log-meta span {
  margin-right: 12px;
}

.log-author {
  color: #606266;
  font-size: 13px;
}

.pagination {
  margin-top: 16px;
  display: flex;
  justify-content: flex-end;
}
</style>
