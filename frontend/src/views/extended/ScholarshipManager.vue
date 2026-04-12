<template>
  <div class="scholarship-manager">
    <el-tabs v-model="activeSubTab">
      <el-tab-pane label="奖学金项目" name="projects">
        <div class="toolbar">
          <el-button type="primary" @click="handleAddProject">
            <el-icon><Plus /></el-icon>
            新建项目
          </el-button>
        </div>
        
        <el-table :data="projectList" v-loading="loading" stripe>
          <el-table-column prop="name" label="项目名称" min-width="200" />
          <el-table-column prop="scholarship_no" label="项目编号" width="150" />
          <el-table-column prop="scholarship_type" label="类型" width="100" align="center">
            <template #default="{ row }">
              <el-tag>{{ getTypeText(row.scholarship_type) }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="level" label="级别" width="100" align="center">
            <template #default="{ row }">
              <el-tag type="success">{{ getLevelText(row.level) }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="amount" label="金额(元)" width="100" align="center">
            <template #default="{ row }">
              ¥{{ row.amount.toFixed(0) }}
            </template>
          </el-table-column>
          <el-table-column prop="quota" label="名额" width="80" align="center" />
          <el-table-column prop="academic_year" label="学年" width="120" />
          <el-table-column prop="status" label="状态" width="100" align="center">
            <template #default="{ row }">
              <el-tag :type="row.status === 'open' ? 'success' : 'info'">
                {{ row.status === 'open' ? '开放申请' : '已截止' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="150">
            <template #default="{ row }">
              <el-button type="primary" link size="small">查看申请</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>
      
      <el-tab-pane label="申请管理" name="applications">
        <el-table :data="applicationList" v-loading="loading" stripe>
          <el-table-column prop="scholarship_id" label="奖学金ID" width="220" />
          <el-table-column prop="student_id" label="学生ID" width="150" />
          <el-table-column prop="academic_year" label="学年" width="120" />
          <el-table-column prop="gpa" label="GPA" width="80" align="center" />
          <el-table-column prop="rank" label="排名" width="80" align="center" />
          <el-table-column prop="status" label="状态" width="100" align="center">
            <template #default="{ row }">
              <el-tag :type="getStatusTagType(row.status)">
                {{ getStatusText(row.status) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="180">
            <template #default="{ row }">
              <el-button
                v-if="row.status === 'submitted'"
                type="success"
                link
                size="small"
                @click="handleApprove(row)"
              >
                审核
              </el-button>
              <el-button type="primary" link size="small">详情</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>
      
      <el-tab-pane label="贫困生认定" name="poor">
        <div class="toolbar">
          <el-button type="primary">
            <el-icon><Plus /></el-icon>
            新增认定
          </el-button>
        </div>
        
        <el-table :data="poorList" v-loading="loading" stripe>
          <el-table-column prop="student_id" label="学生ID" width="150" />
          <el-table-column prop="poor_level" label="贫困等级" width="100" align="center">
            <template #default="{ row }">
              <el-tag :type="row.poor_level === 'special' ? 'danger' : 'warning'">
                {{ row.poor_level === 'special' ? '特别困难' : '一般困难' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="poor_type" label="困难类型" width="150" />
          <el-table-column prop="academic_year" label="认定学年" width="120" />
          <el-table-column prop="status" label="状态" width="100" align="center">
            <template #default="{ row }">
              <el-tag :type="row.status === 'approved' ? 'success' : 'info'">
                {{ row.status === 'approved' ? '已认定' : row.status }}
              </el-tag>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import {
  getScholarships,
  getApplications
} from '@/api/extended'

const activeSubTab = ref('projects')
const loading = ref(false)
const projectList = ref<any[]>([])
const applicationList = ref<any[]>([])
const poorList = ref<any[]>([])

const loadProjects = async () => {
  loading.value = true
  try {
    const res = await getScholarships()
    if (res.code === 200) {
      projectList.value = res.data?.items || []
    }
  } catch (error) {
    console.error('加载失败:', error)
  } finally {
    loading.value = false
  }
}

const loadApplications = async () => {
  loading.value = true
  try {
    const res = await getApplications()
    if (res.code === 200) {
      applicationList.value = res.data?.items || []
    }
  } catch (error) {
    console.error('加载失败:', error)
  } finally {
    loading.value = false
  }
}

const handleAddProject = () => {
  console.log('新建项目')
}

const handleApprove = (row: any) => {
  console.log('审核', row.id)
}

const getTypeText = (type: string) => {
  const map: Record<string, string> = {
    scholarship: '奖学金',
    grant: '助学金',
    aid: '困难补助'
  }
  return map[type] || type
}

const getLevelText = (level: string) => {
  const map: Record<string, string> = {
    national: '国家级',
    school: '校级',
    society: '社会'
  }
  return map[level] || level
}

const getStatusText = (status: string) => {
  const map: Record<string, string> = {
    draft: '草稿',
    submitted: '已提交',
    reviewing: '审核中',
    approved: '已通过',
    rejected: '已拒绝'
  }
  return map[status] || status
}

const getStatusTagType = (status: string) => {
  const map: Record<string, string> = {
    draft: 'info',
    submitted: 'warning',
    reviewing: 'warning',
    approved: 'success',
    rejected: 'danger'
  }
  return map[status] || 'info'
}

onMounted(() => {
  loadProjects()
  loadApplications()
})
</script>

<style scoped lang="scss">
.scholarship-manager {
  .toolbar {
    margin-bottom: 16px;
  }
}
</style>
