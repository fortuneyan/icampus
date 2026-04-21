<template>
  <div class="public-apply">
    <el-card class="apply-card">
      <template #header>
        <div class="card-header">
          <el-icon size="20"><EditPen /></el-icon>
          <span>{{ plan?.name || '在线报名' }}</span>
        </div>
      </template>

      <el-steps :active="step" finish-status="success" align-center>
        <el-step title="填写信息" />
        <el-step title="确认提交" />
        <el-step title="完成" />
      </el-steps>

      <el-form v-if="step === 0" ref="formRef" :model="formData" :rules="formRules" label-width="100px" class="apply-form">
        <el-form-item label="学生姓名" prop="student_name">
          <el-input v-model="formData.student_name" placeholder="请输入学生姓名" />
        </el-form-item>
        <el-form-item label="性别" prop="gender">
          <el-radio-group v-model="formData.gender">
            <el-radio value="male">男</el-radio>
            <el-radio value="female">女</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="出生日期" prop="birth_date">
          <el-date-picker v-model="formData.birth_date" type="date" placeholder="选择日期" value-format="YYYY-MM-DD" style="width: 100%" />
        </el-form-item>
        <el-form-item label="联系电话" prop="phone">
          <el-input v-model="formData.phone" placeholder="请输入联系电话" />
        </el-form-item>
        <el-form-item label="监护人" prop="guardian_name">
          <el-input v-model="formData.guardian_name" placeholder="请输入监护人姓名" />
        </el-form-item>
        <el-form-item label="监护人电话" prop="guardian_phone">
          <el-input v-model="formData.guardian_phone" placeholder="请输入监护人联系电话" />
        </el-form-item>
        <el-form-item label="身份证号">
          <el-input v-model="formData.id_card" placeholder="请输入学生身份证号" />
        </el-form-item>
        <el-form-item label="家庭地址">
          <el-input v-model="formData.address" placeholder="请输入家庭住址" />
        </el-form-item>
        <el-form-item label="就读学校">
          <el-input v-model="formData.current_school" placeholder="请输入当前就读学校" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleNext">下一步</el-button>
        </el-form-item>
      </el-form>

      <div v-else-if="step === 1" class="confirm-section">
        <el-descriptions :column="1" border>
          <el-descriptions-item label="学生姓名">{{ formData.student_name }}</el-descriptions-item>
          <el-descriptions-item label="性别">{{ formData.gender === 'male' ? '男' : '女' }}</el-descriptions-item>
          <el-descriptions-item label="出生日期">{{ formData.birth_date }}</el-descriptions-item>
          <el-descriptions-item label="联系电话">{{ formData.phone }}</el-descriptions-item>
          <el-descriptions-item label="监护人">{{ formData.guardian_name }}</el-descriptions-item>
          <el-descriptions-item label="监护人电话">{{ formData.guardian_phone }}</el-descriptions-item>
          <el-descriptions-item label="就读学校">{{ formData.current_school }}</el-descriptions-item>
        </el-descriptions>
        <div class="confirm-actions">
          <el-button @click="step = 0">上一步</el-button>
          <el-button type="primary" @click="handleSubmit" :loading="submitting">确认提交</el-button>
        </div>
      </div>

      <div v-else class="success-section">
        <el-result icon="success" title="提交成功">
          <template #sub-title>
            <p>报名信息已提交成功！</p>
            <p>您的联系电话: {{ formData.phone }}</p>
            <p>请留意我们的通知。</p>
          </template>
          <template #extra>
            <el-button type="primary" @click="checkStatus">查询报名状态</el-button>
            <el-button @click="resetForm">重新报名</el-button>
          </template>
        </el-result>
      </div>
    </el-card>

    <el-dialog v-model="statusDialogVisible" title="报名状态查询" width="400px">
      <el-descriptions v-if="applicationStatus" :column="1" border>
        <el-descriptions-item label="学生姓名">{{ applicationStatus.student_name }}</el-descriptions-item>
        <el-descriptions-item label="报名状态">
          <el-tag v-if="applicationStatus.status === 'pending'" type="warning">待审核</el-tag>
          <el-tag v-else-if="applicationStatus.status === 'contacted'" type="info">已联系</el-tag>
          <el-tag v-else-if="applicationStatus.status === 'interviewed'" type="primary">已面试</el-tag>
          <el-tag v-else-if="applicationStatus.status === 'admitted'" type="success">已录取</el-tag>
          <el-tag v-else type="info">{{ applicationStatus.status }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item v-if="applicationStatus.enrollment_batch" label="录取批次">
          {{ applicationStatus.enrollment_batch }}
        </el-descriptions-item>
      </el-descriptions>
      <el-empty v-else description="未找到报名信息" />
      <template #footer>
        <el-button @click="statusDialogVisible = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { publicApply, checkApplicationStatus, getPublicPlan } from '@/api/recruitment'

const route = useRoute()
const step = ref(0)
const submitting = ref(false)
const statusDialogVisible = ref(false)
const applicationStatus = ref<any>(null)
const formRef = ref()

const plan = ref<any>(null)
const formData = reactive({
  student_name: '',
  gender: '',
  birth_date: '',
  phone: '',
  guardian_name: '',
  guardian_phone: '',
  id_card: '',
  address: '',
  current_school: ''
})

const formRules = {
  student_name: [{ required: true, message: '请输入学生姓名', trigger: 'blur' }],
  phone: [{ required: true, message: '请输入联系电话', trigger: 'blur' }]
}

const handleNext = async () => {
  if (!formRef.value) return
  await formRef.value.validate(async (valid) => {
    if (valid) {
      step.value = 1
    }
  })
}

const handleSubmit = async () => {
  submitting.value = true
  try {
    await publicApply(formData as any)
    ElMessage.success('报名信息提交成功')
    step.value = 2
  } catch (e: any) {
    ElMessage.error(e.message || '提交失败')
  } finally {
    submitting.value = false
  }
}

const checkStatus = async () => {
  if (!formData.phone) {
    ElMessage.warning('请输入查询的手机号')
    return
  }
  try {
    const res = await checkApplicationStatus(formData.phone)
    applicationStatus.value = res.data
    statusDialogVisible.value = true
  } catch (e) {
    ElMessage.error('查询失败')
  }
}

const resetForm = () => {
  step.value = 0
  Object.assign(formData, {
    student_name: '',
    gender: '',
    birth_date: '',
    phone: '',
    guardian_name: '',
    guardian_phone: '',
    id_card: '',
    address: '',
    current_school: ''
  })
}

onMounted(async () => {
  const planId = route.query.plan as string
  if (planId) {
    try {
      const res = await getPublicPlan(planId)
      plan.value = res.data
    } catch (e) {
      console.error('获取招生计划失败', e)
    }
  }
})
</script>

<style scoped>
.public-apply {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 40px 20px;
  display: flex;
  justify-content: center;
  align-items: flex-start;
}

.apply-card {
  width: 100%;
  max-width: 600px;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 18px;
  font-weight: bold;
}

.apply-form {
  margin-top: 30px;
}

.confirm-section {
  margin-top: 30px;
}

.confirm-actions {
  margin-top: 30px;
  display: flex;
  justify-content: center;
  gap: 20px;
}

.success-section {
  margin-top: 30px;
}
</style>