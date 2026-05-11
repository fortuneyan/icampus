<template>
  <div class="project-list">
    <el-card>
      <template #header>
        <div class="card-header">
          <span class="header-title">项目管理</span>
          <div class="header-actions">
            <el-input
              v-model="queryParams.keyword"
              placeholder="搜索项目名称"
              clearable
              style="width: 200px"
              @clear="handleSearch"
              @keyup.enter="handleSearch"
            />
            <el-select
              v-model="queryParams.status"
              placeholder="项目状态"
              clearable
              style="width: 140px"
              @change="handleSearch"
            >
              <el-option label="进行中" value="active" />
              <el-option label="已归档" value="archived" />
            </el-select>
            <el-button type="primary" @click="handleCreate">
              <el-icon><plus /></el-icon>
              新建项目
            </el-button>
          </div>
        </div>
      </template>

      <div v-loading="loading" class="project-grid">
        <el-empty v-if="!loading && projectList.length === 0" description="暂无项目" />
        <div
          v-for="project in projectList"
          :key="project.id"
          class="project-card"
        >
          <div class="card-top">
            <el-tag
              :type="project.status === 'active' ? 'success' : 'info'"
              size="small"
            >
              {{ project.status === 'active' ? '进行中' : '已归档' }}
            </el-tag>
            <el-dropdown trigger="click" @command="(cmd: string) => handleCommand(cmd, project)">
              <el-button link>
                <el-icon><more-filled /></el-icon>
              </el-button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="view">
                    <el-icon><view /></el-icon> 查看看板
                  </el-dropdown-item>
                  <el-dropdown-item command="edit">
                    <el-icon><edit /></el-icon> 编辑项目
                  </el-dropdown-item>
                  <el-dropdown-item v-if="project.status === 'active'" command="archive">
                    <el-icon><folder-checked /></el-icon> 归档项目
                  </el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
          <div class="card-body">
            <h3 class="project-name" @click="handleViewBoard(project)">{{ project.name }}</h3>
            <p class="project-desc" v-if="project.description">
              {{ project.description.length > 80 ? project.description.slice(0, 80) + '...' : project.description }}
            </p>
            <div class="project-info">
              <div class="info-item" v-if="project.owner">
                <el-icon><user /></el-icon>
                <span>{{ project.owner_name || project.owner }}</span>
              </div>
              <div class="info-item" v-if="project.start_date">
                <el-icon><calendar /></el-icon>
                <span>{{ project.start_date }} ~ {{ project.end_date || '未设定' }}</span>
              </div>
            </div>
            <div class="project-stats">
              <div class="stat-item">
                <el-icon><document /></el-icon>
                <span>{{ project.task_count || 0 }} 个任务</span>
              </div>
              <div class="stat-item" v-if="project.completed_task_count !== undefined">
                <el-icon><check /></el-icon>
                <span>{{ project.completed_task_count }} 已完成</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="pagination-wrapper" v-if="total > queryParams.page_size">
        <el-pagination
          v-model:current-page="queryParams.page"
          v-model:page-size="queryParams.page_size"
          :total="total"
          :page-sizes="[12, 24, 36]"
          layout="total, sizes, prev, pager, next"
          @size-change="loadProjects"
          @current-change="loadProjects"
        />
      </div>
    </el-card>

    <!-- 新建/编辑项目弹窗 -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? '编辑项目' : '新建项目'"
      width="520px"
      destroy-on-close
    >
      <el-form
        ref="formRef"
        :model="formData"
        :rules="formRules"
        label-width="90px"
        label-position="right"
      >
        <el-form-item label="项目名称" prop="name">
          <el-input v-model="formData.name" placeholder="请输入项目名称" maxlength="50" show-word-limit />
        </el-form-item>
        <el-form-item label="项目描述" prop="description">
          <el-input
            v-model="formData.description"
            type="textarea"
            placeholder="请输入项目描述"
            :rows="4"
            maxlength="500"
            show-word-limit
          />
        </el-form-item>
        <el-form-item label="负责人" prop="owner">
          <el-select
            v-model="formData.owner"
            placeholder="请选择负责人"
            filterable
            style="width: 100%"
          >
            <el-option
              v-for="user in userList"
              :key="user.id"
              :label="user.real_name || user.username"
              :value="user.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="开始日期" prop="start_date">
          <el-date-picker
            v-model="formData.start_date"
            type="date"
            placeholder="请选择开始日期"
            value-format="YYYY-MM-DD"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="结束日期" prop="end_date">
          <el-date-picker
            v-model="formData.end_date"
            type="date"
            placeholder="请选择结束日期"
            value-format="YYYY-MM-DD"
            style="width: 100%"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitLoading" @click="handleSubmit">
          {{ isEdit ? '保存' : '创建' }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import {
  Plus, MoreFilled, View, Edit, FolderChecked,
  User, Calendar, Document, Check
} from '@element-plus/icons-vue'
import { taskBoardApi, taskCardApi } from '@/api/oa/tasks'
import { getUserList } from '@/api/system/user'

const router = useRouter()

const loading = ref(false)
const submitLoading = ref(false)
const projectList = ref<any[]>([])
const total = ref(0)
const userList = ref<any[]>([])

const queryParams = reactive({
  keyword: '',
  status: '',
  page: 1,
  page_size: 12,
})

const dialogVisible = ref(false)
const isEdit = ref(false)
const editingId = ref('')
const formRef = ref<FormInstance>()

const formData = reactive({
  name: '',
  description: '',
  owner: '',
  start_date: '',
  end_date: '',
})

const formRules: FormRules = {
  name: [{ required: true, message: '请输入项目名称', trigger: 'blur' }],
}

const loadProjects = async () => {
  loading.value = true
  try {
    const params: any = {
      page: queryParams.page,
      page_size: queryParams.page_size,
    }
    if (queryParams.keyword) params.keyword = queryParams.keyword
    if (queryParams.status) params.status = queryParams.status
    const res = await taskBoardApi.getBoardList(params)
    projectList.value = res.data?.list || res.data || []
    total.value = res.data?.total || 0
  } catch (error) {
    ElMessage.error('加载项目列表失败')
  } finally {
    loading.value = false
  }
}

const loadUsers = async () => {
  try {
    const res = await getUserList({ page: 1, page_size: 100 })
    userList.value = res.data?.list || res.data || []
  } catch (error) {
    // 静默处理
  }
}

const handleSearch = () => {
  queryParams.page = 1
  loadProjects()
}

const resetForm = () => {
  formData.name = ''
  formData.description = ''
  formData.owner = ''
  formData.start_date = ''
  formData.end_date = ''
  isEdit.value = false
  editingId.value = ''
}

const handleCreate = () => {
  resetForm()
  dialogVisible.value = true
}

const handleEdit = (project: any) => {
  isEdit.value = true
  editingId.value = project.id
  formData.name = project.name || ''
  formData.description = project.description || ''
  formData.owner = project.owner || ''
  formData.start_date = project.start_date || ''
  formData.end_date = project.end_date || ''
  dialogVisible.value = true
}

const handleSubmit = async () => {
  if (!formRef.value) return
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    submitLoading.value = true
    try {
      if (isEdit.value) {
        await taskBoardApi.updateBoard(editingId.value, { ...formData })
        ElMessage.success('项目更新成功')
      } else {
        await taskBoardApi.createBoard({ ...formData })
        ElMessage.success('项目创建成功')
      }
      dialogVisible.value = false
      loadProjects()
    } catch (error) {
      ElMessage.error(isEdit.value ? '更新失败' : '创建失败')
    } finally {
      submitLoading.value = false
    }
  })
}

const handleViewBoard = (project: any) => {
  router.push(`/oa/task-board?board_id=${project.id}`)
}

const handleArchive = async (project: any) => {
  try {
    await ElMessageBox.confirm('确定要归档该项目吗？归档后项目将变为只读状态。', '提示', {
      type: 'warning',
    })
    await taskBoardApi.updateBoard(project.id, { status: 'archived' })
    ElMessage.success('项目已归档')
    loadProjects()
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error('归档失败')
    }
  }
}

const handleCommand = (command: string, project: any) => {
  switch (command) {
    case 'view':
      handleViewBoard(project)
      break
    case 'edit':
      handleEdit(project)
      break
    case 'archive':
      handleArchive(project)
      break
  }
}

onMounted(() => {
  loadProjects()
  loadUsers()
})
</script>

<style scoped>
.project-list {
  padding: 16px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-title {
  font-size: 18px;
  font-weight: 600;
}

.header-actions {
  display: flex;
  gap: 12px;
  align-items: center;
}

.project-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 16px;
  min-height: 200px;
}

.project-card {
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  padding: 16px;
  background: #fff;
  transition: box-shadow 0.2s, border-color 0.2s;
  cursor: default;
}

.project-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  border-color: #c0c4cc;
}

.card-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.card-body {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.project-name {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
  margin: 0;
  cursor: pointer;
  transition: color 0.2s;
}

.project-name:hover {
  color: #409eff;
}

.project-desc {
  font-size: 13px;
  color: #909399;
  line-height: 1.5;
  margin: 0;
}

.project-info {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.info-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: #606266;
}

.info-item .el-icon {
  color: #909399;
}

.project-stats {
  display: flex;
  gap: 16px;
  padding-top: 10px;
  border-top: 1px solid #f2f6fc;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: #909399;
}

.stat-item .el-icon {
  color: #67c23a;
}

.pagination-wrapper {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}
</style>
