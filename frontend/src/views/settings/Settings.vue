<template>
  <div class="settings-page">
    <el-row :gutter="20">
      <el-col :span="6">
        <el-card>
          <el-menu :default-active="activeMenu" @select="handleMenuSelect">
            <el-menu-item index="basic">
              <el-icon><Setting /></el-icon>
              <span>基本设置</span>
            </el-menu-item>
            <el-menu-item index="academic">
              <el-icon><Reading /></el-icon>
              <span>学制设置</span>
            </el-menu-item>
            <el-menu-item index="security">
              <el-icon><Lock /></el-icon>
              <span>安全设置</span>
            </el-menu-item>
            <el-menu-item index="notification">
              <el-icon><Bell /></el-icon>
              <span>通知设置</span>
            </el-menu-item>
            <el-menu-item index="about">
              <el-icon><InfoFilled /></el-icon>
              <span>关于系统</span>
            </el-menu-item>
          </el-menu>
        </el-card>
      </el-col>
      
      <el-col :span="18">
        <!-- 基本设置 -->
        <el-card v-if="activeMenu === 'basic'">
          <template #header>基本设置</template>
          <el-form :model="basicForm" label-width="120px">
            <el-form-item label="系统名称">
              <el-input v-model="basicForm.system_name" placeholder="请输入系统名称" />
            </el-form-item>
            <el-form-item label="学校名称">
              <el-input v-model="basicForm.school_name" placeholder="请输入学校名称" />
            </el-form-item>
            <el-form-item label="学年制">
              <el-select v-model="basicForm.academic_year_system" placeholder="请选择学年制">
                <el-option label="秋季入学" value="autumn" />
                <el-option label="春季入学" value="spring" />
              </el-select>
            </el-form-item>
            <el-form-item label="学期数">
              <el-input-number v-model="basicForm.semester_count" :min="2" :max="4" />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" :loading="basicLoading" @click="handleSaveBasic">保存</el-button>
            </el-form-item>
          </el-form>
        </el-card>
        
        <!-- 学制设置 -->
        <el-card v-if="activeMenu === 'academic'">
          <template #header>学制设置</template>
          <el-form :model="academicForm" label-width="120px">
            <el-form-item label="学制类型">
              <el-select v-model="academicForm.school_type" placeholder="请选择学制类型" @change="handleSchoolTypeChange">
                <el-option label="普通高中" value="regular_high" />
                <el-option label="职业高中" value="vocational_high" />
                <el-option label="普通初中" value="regular_junior" />
                <el-option label="小学" value="primary" />
                <el-option label="自定义" value="custom" />
              </el-select>
            </el-form-item>
            <el-form-item label="学制年数">
              <el-input-number v-model="academicForm.years" :min="1" :max="academicForm.school_type === 'custom' ? 15 : 6" @change="handleYearsChange" />
              <span style="margin-left: 10px">年</span>
            </el-form-item>
            <el-form-item label="年级设置">
              <div class="grade-list">
                <div v-for="(grade, index) in academicForm.grades" :key="index" class="grade-item">
                  <span class="grade-label">第{{ index + 1 }}年级：</span>
                  <el-input v-model="academicForm.grades[index]" placeholder="年级名称" style="width: 150px" />
                  <el-button type="danger" :icon="Delete" circle @click="removeGrade(index)" style="margin-left: 8px" />
                </div>
                <el-button type="primary" plain @click="addGrade">添加年级</el-button>
              </div>
            </el-form-item>
            <el-form-item>
              <el-button type="primary" :loading="academicLoading" @click="handleSaveAcademic">保存</el-button>
            </el-form-item>
          </el-form>
        </el-card>
        
        <!-- 安全设置 -->
        <el-card v-if="activeMenu === 'security'">
          <template #header>安全设置</template>
          <el-form :model="securityForm" label-width="120px">
            <el-form-item label="密码强度">
              <el-select v-model="securityForm.password_strength" placeholder="请选择密码强度">
                <el-option label="低" value="low" />
                <el-option label="中" value="medium" />
                <el-option label="高" value="high" />
              </el-select>
            </el-form-item>
            <el-form-item label="登录失败锁定">
              <el-input-number v-model="securityForm.max_login_attempts" :min="3" :max="10" />
              <span style="margin-left: 10px">次</span>
            </el-form-item>
            <el-form-item label="会话超时">
              <el-input-number v-model="securityForm.session_timeout" :min="15" :max="120" />
              <span style="margin-left: 10px">分钟</span>
            </el-form-item>
            <el-form-item>
              <el-button type="primary" :loading="securityLoading" @click="handleSaveSecurity">保存</el-button>
            </el-form-item>
          </el-form>
        </el-card>
        
        <!-- 通知设置 -->
        <el-card v-if="activeMenu === 'notification'">
          <template #header>通知设置</template>
          <el-form :model="notificationForm" label-width="150px">
            <el-form-item label="邮件通知">
              <el-switch v-model="notificationForm.email_enabled" />
            </el-form-item>
            <el-form-item label="短信通知">
              <el-switch v-model="notificationForm.sms_enabled" />
            </el-form-item>
            <el-form-item label="系统消息">
              <el-switch v-model="notificationForm.system_enabled" />
            </el-form-item>
            <el-form-item label="成绩发布通知家长">
              <el-switch v-model="notificationForm.score_notify_parent" />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" :loading="notificationLoading" @click="handleSaveNotification">保存</el-button>
            </el-form-item>
          </el-form>
        </el-card>
        
        <!-- 关于系统 -->
        <el-card v-if="activeMenu === 'about'">
          <template #header>关于系统</template>
          <el-skeleton :rows="5" v-if="systemInfoLoading" />
          <el-descriptions v-else :column="1" border>
            <el-descriptions-item label="系统名称">{{ systemInfo.app_name || '智慧校园管理平台' }}</el-descriptions-item>
            <el-descriptions-item label="版本号">{{ systemInfo.app_version || 'v1.0.0' }}</el-descriptions-item>
            <el-descriptions-item label="技术栈">Python FastAPI + Vue3 + PostgreSQL</el-descriptions-item>
            <el-descriptions-item label="开发日期">2026-04-09</el-descriptions-item>
            <el-descriptions-item label="依据标准">JY/T 0641-2022, JY/T 0650-2022, JY/T 0643-2025, JY/T 0661-2025</el-descriptions-item>
          </el-descriptions>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Setting, Lock, Bell, InfoFilled, Reading, Delete } from '@element-plus/icons-vue'
import { getConfig, updateConfig, getSystemInfo } from '@/api/settings'

const activeMenu = ref('basic')
const basicLoading = ref(false)
const securityLoading = ref(false)
const notificationLoading = ref(false)
const academicLoading = ref(false)
const systemInfoLoading = ref(false)

const systemInfo = reactive<Record<string, string>>({})

const basicForm = reactive({
  system_name: '智慧校园管理平台',
  school_name: '',
  academic_year_system: 'autumn',
  semester_count: 2
})

const securityForm = reactive({
  password_strength: 'medium',
  max_login_attempts: 5,
  session_timeout: 60
})

const notificationForm = reactive({
  email_enabled: true,
  sms_enabled: false,
  system_enabled: true,
  score_notify_parent: true
})

const schoolTypeConfig: Record<string, { years: number; grades: string[] }> = {
  regular_high: { years: 3, grades: ['高一', '高二', '高三'] },
  vocational_high: { years: 3, grades: ['职一', '职二', '职三'] },
  regular_junior: { years: 3, grades: ['初一', '初二', '初三'] },
  primary: { years: 6, grades: ['一年级', '二年级', '三年级', '四年级', '五年级', '六年级'] },
  custom: { years: 3, grades: ['一年级', '二年级', '三年级'] }
}

const academicForm = reactive({
  school_type: 'regular_high',
  years: 3,
  grades: ['高一', '高二', '高三']
})

const handleSchoolTypeChange = (type: string) => {
  const config = schoolTypeConfig[type]
  if (config) {
    academicForm.years = config.years
    academicForm.grades = [...config.grades]
  }
}

const handleYearsChange = (years: number) => {
  const currentGrades = academicForm.grades.length
  if (years > currentGrades) {
    for (let i = currentGrades; i < years; i++) {
      academicForm.grades.push(`${i + 1}年级`)
    }
  } else if (years < currentGrades) {
    academicForm.grades = academicForm.grades.slice(0, years)
  }
}

const addGrade = () => {
  if (academicForm.grades.length < academicForm.years) {
    academicForm.grades.push(`${academicForm.grades.length + 1}年级`)
  }
}

const removeGrade = (index: number) => {
  if (academicForm.grades.length > 1) {
    academicForm.grades.splice(index, 1)
    academicForm.years = academicForm.grades.length
  }
}

const handleMenuSelect = (index: string) => {
  activeMenu.value = index
  if (index === 'about' && Object.keys(systemInfo).length === 0) {
    loadSystemInfo()
  }
}

// 加载配置
const loadConfig = async () => {
  try {
    const res = await getConfig()
    if (res.code === 200 && res.data) {
      const configs = Array.isArray(res.data) ? res.data : [res.data]
      configs.forEach((item: any) => {
        if (item.setting_key) {
          // 根据key映射到表单
          switch (item.setting_key) {
            case 'system_name':
              basicForm.system_name = item.setting_value
              break
            case 'school_name':
              basicForm.school_name = item.setting_value
              break
            case 'academic_year_system':
              basicForm.academic_year_system = item.setting_value
              break
            case 'semester_count':
              basicForm.semester_count = parseInt(item.setting_value) || 2
              break
          }
        }
      })
    }
  } catch (error) {
    console.error('加载配置失败:', error)
  }
}

// 保存基本设置
const handleSaveBasic = async () => {
  basicLoading.value = true
  try {
    await updateConfig({ setting_key: 'system_name', setting_value: basicForm.system_name, value_type: 'string' })
    await updateConfig({ setting_key: 'school_name', setting_value: basicForm.school_name, value_type: 'string' })
    await updateConfig({ setting_key: 'academic_year_system', setting_value: basicForm.academic_year_system, value_type: 'string' })
    await updateConfig({ setting_key: 'semester_count', setting_value: String(basicForm.semester_count), value_type: 'int' })
    ElMessage.success('基本设置已保存')
  } catch (error) {
    console.error('保存失败:', error)
  } finally {
    basicLoading.value = false
  }
}

// 保存安全设置
const handleSaveSecurity = async () => {
  securityLoading.value = true
  try {
    await updateConfig({ setting_key: 'password_strength', setting_value: securityForm.password_strength, value_type: 'string' })
    await updateConfig({ setting_key: 'max_login_attempts', setting_value: String(securityForm.max_login_attempts), value_type: 'int' })
    await updateConfig({ setting_key: 'session_timeout', setting_value: String(securityForm.session_timeout), value_type: 'int' })
    ElMessage.success('安全设置已保存')
  } catch (error) {
    console.error('保存失败:', error)
  } finally {
    securityLoading.value = false
  }
}

// 保存通知设置
const handleSaveNotification = async () => {
  notificationLoading.value = true
  try {
    await updateConfig({ setting_key: 'email_enabled', setting_value: String(notificationForm.email_enabled), value_type: 'boolean' })
    await updateConfig({ setting_key: 'sms_enabled', setting_value: String(notificationForm.sms_enabled), value_type: 'boolean' })
    await updateConfig({ setting_key: 'system_enabled', setting_value: String(notificationForm.system_enabled), value_type: 'boolean' })
    await updateConfig({ setting_key: 'score_notify_parent', setting_value: String(notificationForm.score_notify_parent), value_type: 'boolean' })
    ElMessage.success('通知设置已保存')
  } catch (error) {
    console.error('保存失败:', error)
  } finally {
    notificationLoading.value = false
  }
}

// 加载学制设置
const loadAcademicConfig = async () => {
  try {
    const res = await getConfig()
    if (res.code === 200 && res.data) {
      const configs = Array.isArray(res.data) ? res.data : [res.data]
      let loadedYears = 3
      let loadedGrades: string[] = []
      configs.forEach((item: any) => {
        if (item.setting_key === 'school_type') {
          academicForm.school_type = item.setting_value || 'regular_high'
        }
        if (item.setting_key === 'academic_years') {
          loadedYears = parseInt(item.setting_value) || 3
        }
        if (item.setting_key === 'grade_names') {
          loadedGrades = item.setting_value ? item.setting_value.split(',') : []
        }
      })
      if (loadedGrades.length > 0) {
        academicForm.years = loadedYears
        academicForm.grades = loadedGrades
      } else {
        handleSchoolTypeChange(academicForm.school_type)
      }
    }
  } catch (error) {
    console.error('加载学制配置失败:', error)
  }
}

// 保存学制设置
const handleSaveAcademic = async () => {
  academicLoading.value = true
  try {
    await updateConfig({ setting_key: 'school_type', setting_value: academicForm.school_type, value_type: 'string' })
    await updateConfig({ setting_key: 'academic_years', setting_value: String(academicForm.years), value_type: 'int' })
    await updateConfig({ setting_key: 'grade_names', setting_value: academicForm.grades.join(','), value_type: 'string' })
    ElMessage.success('学制设置已保存')
  } catch (error) {
    console.error('保存失败:', error)
  } finally {
    academicLoading.value = false
  }
}

// 加载系统信息
const loadSystemInfo = async () => {
  systemInfoLoading.value = true
  try {
    const res = await getSystemInfo()
    if (res.code === 200) {
      Object.assign(systemInfo, res.data)
    }
  } catch (error) {
    console.error('加载系统信息失败:', error)
  } finally {
    systemInfoLoading.value = false
  }
}

onMounted(() => {
  loadConfig()
  loadAcademicConfig()
})
</script>

<style scoped lang="scss">
.settings-page {
  .el-col:first-child {
    .el-menu-item {
      height: 50px;
      line-height: 50px;
    }
  }
}
.grade-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.grade-item {
  display: flex;
  align-items: center;
}
.grade-label {
  width: 80px;
  color: #606266;
}
</style>
