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
            <el-menu-item index="security">
              <el-icon><Lock /></el-icon>
              <span>安全设置</span>
            </el-menu-item>
            <el-menu-item index="notification">
              <el-icon><Bell /></el-icon>
              <span>通知设置</span>
            </el-menu-item>
            <el-menu-item index="about">
              <el-icon><Info /></el-icon>
              <span>关于系统</span>
            </el-menu-item>
          </el-menu>
        </el-card>
      </el-col>
      
      <el-col :span="18">
        <el-card v-if="activeMenu === 'basic'">
          <template #header>基本设置</template>
          <el-form :model="basicForm" label-width="120px">
            <el-form-item label="系统名称">
              <el-input v-model="basicForm.system_name" />
            </el-form-item>
            <el-form-item label="学校名称">
              <el-input v-model="basicForm.school_name" />
            </el-form-item>
            <el-form-item label="学年制">
              <el-select v-model="basicForm.academic_year_system">
                <el-option label="秋季入学" value="autumn" />
                <el-option label="春季入学" value="spring" />
              </el-select>
            </el-form-item>
            <el-form-item label="学期数">
              <el-input-number v-model="basicForm.semester_count" :min="2" :max="4" />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="handleSaveBasic">保存</el-button>
            </el-form-item>
          </el-form>
        </el-card>
        
        <el-card v-if="activeMenu === 'security'">
          <template #header>安全设置</template>
          <el-form :model="securityForm" label-width="120px">
            <el-form-item label="密码强度">
              <el-select v-model="securityForm.password_strength">
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
              <el-button type="primary" @click="handleSaveSecurity">保存</el-button>
            </el-form-item>
          </el-form>
        </el-card>
        
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
              <el-button type="primary" @click="handleSaveNotification">保存</el-button>
            </el-form-item>
          </el-form>
        </el-card>
        
        <el-card v-if="activeMenu === 'about'">
          <template #header>关于系统</template>
          <el-descriptions :column="1" border>
            <el-descriptions-item label="系统名称">智慧校园管理平台</el-descriptions-item>
            <el-descriptions-item label="版本号">v1.0.0</el-descriptions-item>
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
import { ref, reactive } from 'vue'
import { ElMessage } from 'element-plus'
import { Setting, Lock, Bell, Info } from '@element-plus/icons-vue'

const activeMenu = ref('basic')

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

const handleMenuSelect = (index: string) => {
  activeMenu.value = index
}

const handleSaveBasic = () => {
  ElMessage.success('基本设置已保存')
}

const handleSaveSecurity = () => {
  ElMessage.success('安全设置已保存')
}

const handleSaveNotification = () => {
  ElMessage.success('通知设置已保存')
}
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
</style>