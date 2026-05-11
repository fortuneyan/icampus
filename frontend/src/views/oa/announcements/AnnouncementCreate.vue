<template>
  <div class="announcement-create">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>发布公告</span>
          <el-button @click="handleBack">返回列表</el-button>
        </div>
      </template>

      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-width="100px"
        style="max-width: 800px;"
      >
        <el-form-item label="标题" prop="title">
          <el-input v-model="form.title" placeholder="请输入公告标题" maxlength="200" show-word-limit />
        </el-form-item>

        <el-form-item label="分类" prop="category_id">
          <el-select v-model="form.category_id" placeholder="请选择分类" clearable style="width: 100%;">
            <el-option
              v-for="cat in categoryList"
              :key="cat.id"
              :label="cat.name"
              :value="cat.id"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="优先级" prop="priority">
          <el-radio-group v-model="form.priority">
            <el-radio value="normal">普通</el-radio>
            <el-radio value="important">重要</el-radio>
            <el-radio value="urgent">紧急</el-radio>
          </el-radio-group>
        </el-form-item>

        <el-form-item label="内容" prop="content_md">
          <MarkdownEditor
            v-model="form.content_md"
            mode="split"
            placeholder="请输入公告内容（支持 Markdown）"
            height="400px"
          />
        </el-form-item>

        <el-form-item label="组织范围">
          <el-select
            v-model="form.department_ids"
            multiple
            placeholder="请选择发布范围（部门）"
            clearable
            style="width: 100%;"
          >
            <el-option
              v-for="dept in departmentList"
              :key="dept.id"
              :label="dept.name"
              :value="dept.id"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="定时发布">
          <el-date-picker
            v-model="form.scheduled_at"
            type="datetime"
            placeholder="选择定时发布时间（留空则立即发布）"
            value-format="YYYY-MM-DD HH:mm:ss"
            style="width: 100%;"
          />
        </el-form-item>

        <el-form-item label="允许评论">
          <el-switch v-model="form.allow_comment" />
        </el-form-item>

        <el-form-item label="附件">
          <el-upload
            action="/api/v1/oa/announcements/upload"
            :headers="uploadHeaders"
            :file-list="form.attachments"
            :on-success="handleUploadSuccess"
            :on-remove="handleUploadRemove"
            :limit="5"
            :on-exceed="handleExceed"
          >
            <el-button type="primary" plain>点击上传</el-button>
            <template #tip>
              <div class="upload-tip">支持上传文件，最多5个</div>
            </template>
          </el-upload>
        </el-form-item>

        <el-form-item>
          <el-button type="primary" :loading="submitting" @click="handlePublish">
            发布
          </el-button>
          <el-button :loading="submitting" @click="handleSaveDraft">
            保存草稿
          </el-button>
          <el-button @click="handleBack">取消</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import type { FormInstance, FormRules, UploadFile, UploadRawFile } from 'element-plus'
import MarkdownEditor from '@/components/MarkdownEditor.vue'
import { announcementApi, categoryApi } from '@/api/oa/announcements'

const router = useRouter()
const formRef = ref<FormInstance>()
const submitting = ref(false)
const categoryList = ref<any[]>([])
const departmentList = ref<any[]>([])

const uploadHeaders = reactive({
  Authorization: `Bearer ${localStorage.getItem('token') || ''}`
})

const form = reactive({
  title: '',
  category_id: '',
  priority: 'normal',
  content_md: '',
  department_ids: [] as string[],
  scheduled_at: '',
  allow_comment: true,
  attachments: [] as any[]
})

const rules = reactive<FormRules>({
  title: [
    { required: true, message: '请输入公告标题', trigger: 'blur' }
  ],
  content_md: [
    { required: true, message: '请输入公告内容', trigger: 'blur' }
  ]
})

const loadCategories = async () => {
  try {
    const res = await categoryApi.getList()
    categoryList.value = res.data?.list || res.data || []
  } catch (error) {
    console.error('加载分类失败', error)
  }
}

const loadDepartments = async () => {
  try {
    const { default: request } = await import('@/utils/request')
    const res = await request.get('/system/departments/tree')
    departmentList.value = res.data || []
  } catch (error) {
    console.error('加载部门列表失败', error)
  }
}

const handleUploadSuccess = (response: any, file: UploadFile, fileList: UploadFile[]) => {
  form.attachments = fileList.map(f => ({
    id: f.response?.data?.id || f.uid,
    name: f.name,
    url: f.response?.data?.url || f.url
  }))
}

const handleUploadRemove = (file: UploadFile, fileList: UploadFile[]) => {
  form.attachments = fileList.map(f => ({
    id: f.response?.data?.id || f.uid,
    name: f.name,
    url: f.response?.data?.url || f.url
  }))
}

const handleExceed = () => {
  ElMessage.warning('最多上传5个附件')
}

const handleSaveDraft = async () => {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return

  submitting.value = true
  try {
    const data = {
      ...form,
      status: 'draft'
    }
    await announcementApi.create(data)
    ElMessage.success('草稿保存成功')
    router.push('/oa/announcements')
  } catch (error) {
    ElMessage.error('保存草稿失败')
  } finally {
    submitting.value = false
  }
}

const handlePublish = async () => {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return

  submitting.value = true
  try {
    const data = {
      ...form,
      status: 'published'
    }
    const res = await announcementApi.create(data)
    const id = res.data?.id
    if (id) {
      await announcementApi.publish(id)
    }
    ElMessage.success('发布成功')
    router.push('/oa/announcements')
  } catch (error) {
    ElMessage.error('发布失败')
  } finally {
    submitting.value = false
  }
}

const handleBack = () => {
  router.push('/oa/announcements')
}

onMounted(() => {
  loadCategories()
  loadDepartments()
})
</script>

<style scoped>
.announcement-create {
  padding: 16px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.upload-tip {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}
</style>
