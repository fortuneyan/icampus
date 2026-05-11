<template>
  <div class="worklog-editor">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>{{ isEdit ? '编辑日志' : '撰写日志' }}</span>
          <el-button @click="handleBack">返回</el-button>
        </div>
      </template>

      <el-form
        ref="formRef"
        :model="form"
        :rules="formRules"
        label-width="120px"
        style="max-width: 900px;"
        v-loading="pageLoading"
      >
        <el-form-item label="日志类型" prop="log_type">
          <el-radio-group v-model="form.log_type" @change="handleTypeChange">
            <el-radio value="daily">日报</el-radio>
            <el-radio value="weekly">周报</el-radio>
            <el-radio value="monthly">月报</el-radio>
          </el-radio-group>
        </el-form-item>

        <el-form-item label="周期开始日期" prop="period_start">
          <el-date-picker
            v-model="form.period_start"
            type="date"
            placeholder="选择开始日期"
            value-format="YYYY-MM-DD"
            style="width: 100%;"
          />
        </el-form-item>

        <el-form-item label="周期结束日期" prop="period_end">
          <el-date-picker
            v-model="form.period_end"
            type="date"
            placeholder="选择结束日期"
            value-format="YYYY-MM-DD"
            style="width: 100%;"
          />
        </el-form-item>

        <el-form-item label="本周期总结" prop="summary">
          <MarkdownEditor
            v-model="form.summary"
            mode="split"
            placeholder="请输入本周期工作总结（支持 Markdown）"
            height="300px"
          />
        </el-form-item>

        <el-form-item label="下周期计划" prop="plan">
          <MarkdownEditor
            v-model="form.plan"
            mode="split"
            placeholder="请输入下周期工作计划（支持 Markdown）"
            height="300px"
          />
        </el-form-item>

        <el-form-item label="附件">
          <el-upload
            :auto-upload="false"
            :limit="5"
            accept=".pdf,.doc,.docx,.xls,.xlsx,.jpg,.png"
            :file-list="form.attachments"
            :on-change="handleFileChange"
            :on-remove="handleFileRemove"
          >
            <el-button type="primary">上传附件</el-button>
            <template #tip>
              <div class="upload-tip">支持 pdf/doc/docx/xls/xlsx/jpg/png 格式，最多 5 个文件</div>
            </template>
          </el-upload>
        </el-form-item>

        <el-form-item>
          <el-button type="default" @click="handleSaveDraft" :loading="submitLoading">保存草稿</el-button>
          <el-button type="primary" @click="handleSubmit" :loading="submitLoading">提交审核</el-button>
          <el-button @click="handleBack">返回</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import MarkdownEditor from '@/components/MarkdownEditor.vue'
import { worklogApi } from '@/api/oa/worklogs'

const route = useRoute()
const router = useRouter()

const formRef = ref()
const pageLoading = ref(false)
const submitLoading = ref(false)

const isEdit = computed(() => !!route.params.id)

const form = reactive({
  log_type: 'weekly',
  period_start: '',
  period_end: '',
  summary: '',
  plan: '',
  attachments: [] as any[]
})

const formRules = {
  log_type: [{ required: true, message: '请选择日志类型', trigger: 'change' }],
  period_start: [{ required: true, message: '请选择周期开始日期', trigger: 'change' }],
  period_end: [{ required: true, message: '请选择周期结束日期', trigger: 'change' }],
  summary: [{ required: true, message: '请输入本周期总结', trigger: 'blur' }],
  plan: [{ required: true, message: '请输入下周期计划', trigger: 'blur' }]
}

/** 获取本周的日期范围 */
function getWeekRange(): { start: string; end: string } {
  const now = new Date()
  const day = now.getDay()
  const monday = new Date(now)
  monday.setDate(now.getDate() - (day === 0 ? 6 : day - 1))
  const sunday = new Date(monday)
  sunday.setDate(monday.getDate() + 6)
  const format = (d: Date) => d.toISOString().split('T')[0]
  return { start: format(monday), end: format(sunday) }
}

/** 获取本月日期范围 */
function getMonthRange(): { start: string; end: string } {
  const now = new Date()
  const start = new Date(now.getFullYear(), now.getMonth(), 1)
  const end = new Date(now.getFullYear(), now.getMonth() + 1, 0)
  const format = (d: Date) => d.toISOString().split('T')[0]
  return { start: format(start), end: format(end) }
}

/** 日志类型变更时自动计算周期 */
function handleTypeChange(type: string) {
  if (isEdit.value) return
  if (type === 'weekly') {
    const range = getWeekRange()
    form.period_start = range.start
    form.period_end = range.end
  } else if (type === 'monthly') {
    const range = getMonthRange()
    form.period_start = range.start
    form.period_end = range.end
  } else {
    form.period_start = new Date().toISOString().split('T')[0]
    form.period_end = new Date().toISOString().split('T')[0]
  }
}

/** 附件变更 */
function handleFileChange(file: any, fileList: any[]) {
  form.attachments = fileList
}

/** 附件移除 */
function handleFileRemove(file: any, fileList: any[]) {
  form.attachments = fileList
}

/** 保存草稿 */
async function handleSaveDraft() {
  try {
    await formRef.value?.validate()
    submitLoading.value = true
    const data = {
      log_type: form.log_type,
      period_start: form.period_start,
      period_end: form.period_end,
      summary: form.summary,
      plan: form.plan,
      status: 'DRAFT'
    }
    if (isEdit.value) {
      await worklogApi.update(route.params.id as string, data)
    } else {
      await worklogApi.create(data)
    }
    ElMessage.success('草稿保存成功')
  } catch (error: any) {
    if (error !== false) {
      ElMessage.error('保存草稿失败')
    }
  } finally {
    submitLoading.value = false
  }
}

/** 提交审核 */
async function handleSubmit() {
  try {
    await formRef.value?.validate()
    submitLoading.value = true
    const data = {
      log_type: form.log_type,
      period_start: form.period_start,
      period_end: form.period_end,
      summary: form.summary,
      plan: form.plan,
      status: 'SUBMITTED'
    }
    if (isEdit.value) {
      await worklogApi.update(route.params.id as string, data)
    } else {
      const res = await worklogApi.create(data)
      // 提交审核
      if (res.data?.id) {
        await worklogApi.submit(res.data.id)
      }
    }
    ElMessage.success('提交审核成功')
    router.push('/oa/worklogs')
  } catch (error: any) {
    if (error !== false) {
      ElMessage.error('提交审核失败')
    }
  } finally {
    submitLoading.value = false
  }
}

/** 返回 */
function handleBack() {
  router.push('/oa/worklogs')
}

/** 加载编辑数据 */
async function loadWorklog() {
  if (!isEdit.value) return
  pageLoading.value = true
  try {
    const res = await worklogApi.getById(route.params.id as string)
    const data = res.data
    if (data) {
      form.log_type = data.log_type || 'weekly'
      form.period_start = data.period_start || ''
      form.period_end = data.period_end || ''
      form.summary = data.summary || ''
      form.plan = data.plan || ''
      form.attachments = data.attachments || []
    }
  } catch (error) {
    ElMessage.error('加载日志数据失败')
  } finally {
    pageLoading.value = false
  }
}

onMounted(() => {
  if (isEdit.value) {
    loadWorklog()
  } else {
    // 新建模式默认周报，自动计算本周范围
    const range = getWeekRange()
    form.period_start = range.start
    form.period_end = range.end
  }
})
</script>

<style scoped>
.worklog-editor {
  padding: 16px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.upload-tip {
  color: #909399;
  font-size: 12px;
  margin-top: 4px;
}
</style>
