<template>
  <div class="student-report-tab">
    <!-- 搜索栏 -->
    <div class="search-bar">
      <a-form layout="inline" :model="searchForm">
        <a-form-item label="学号">
          <a-input v-model:value="searchForm.student_id" placeholder="请输入学号" />
        </a-form-item>
        <a-form-item label="学年">
          <a-select v-model:value="searchForm.academic_year" style="width: 150px">
            <a-select-option value="2025-2026">2025-2026</a-select-option>
            <a-select-option value="2024-2025">2024-2025</a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item>
          <a-button type="primary" @click="handleSearch">
            <template #icon><SearchOutlined /></template>
            查询
          </a-button>
        </a-form-item>
      </a-form>
    </div>

    <!-- 数据表格 -->
    <a-table
      :columns="columns"
      :data-source="dataList"
      :loading="loading"
      :pagination="pagination"
      @change="handleTableChange"
      row-key="student_id"
    >
      <template #bodyCell="{ column, record }">
        <template v-if="column.key === 'average_score'">
          <a-tag :color="getScoreColor(record.average_score)">
            {{ record.average_score }}
          </a-tag>
        </template>
        <template v-else-if="column.key === 'pass_rate'">
          <a-progress
            :percent="record.pass_rate * 100"
            size="small"
            :status="record.pass_rate >= 0.6 ? 'success' : 'normal'"
          />
        </template>
        <template v-else-if="column.key === 'action'">
          <a-button type="link" size="small" @click="handleView(record)">
            详情
          </a-button>
          <a-button type="link" size="small" @click="handleTrend(record)">
            趋势
          </a-button>
        </template>
      </template>
    </a-table>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { SearchOutlined } from '@ant-design/icons-vue'
import type { TableProps } from 'ant-design-vue'

// 事件
const emit = defineEmits(['view-detail'])

// 数据
const loading = ref(false)
const dataList = ref<any[]>([])

const searchForm = reactive({
  student_id: '',
  academic_year: '2025-2026',
  semester: 1
})

const pagination = reactive({
  current: 1,
  pageSize: 20,
  total: 0
})

const columns = [
  { title: '学号', dataIndex: 'student_id', key: 'student_id', width: 120 },
  { title: '姓名', dataIndex: 'student_name', key: 'student_name', width: 100 },
  { title: '平均分', dataIndex: 'average_score', key: 'average_score', width: 100 },
  { title: 'GPA', dataIndex: 'gpa', key: 'gpa', width: 80 },
  { title: '课程数', dataIndex: 'total_courses', key: 'total_courses', width: 80 },
  { title: '及格率', dataIndex: 'pass_rate', key: 'pass_rate', width: 150 },
  { title: '班级排名', dataIndex: 'class_rank', key: 'class_rank', width: 100 },
  { title: '操作', key: 'action', fixed: 'right', width: 120 }
]

// 获取分数颜色
const getScoreColor = (score: number): string => {
  if (score >= 90) return 'green'
  if (score >= 80) return 'cyan'
  if (score >= 70) return 'blue'
  if (score >= 60) return 'orange'
  return 'red'
}

// 搜索
const handleSearch = () => {
  pagination.current = 1
  loadData()
}

// 表格变化
const handleTableChange: TableProps['onChange'] = (pag) => {
  pagination.current = pag.current || 1
  pagination.pageSize = pag.pageSize || 20
  loadData()
}

// 查看详情
const handleView = (record: any) => {
  emit('view-detail', record.student_id)
}

// 查看趋势
const handleTrend = (record: any) => {
  // TODO: 跳转到趋势分析
}

// 加载数据
const loadData = async () => {
  loading.value = true
  // TODO: 调用API获取数据
  // 模拟数据
  dataList.value = [
    {
      student_id: 1001,
      student_name: '张三',
      average_score: 85.5,
      gpa: 3.2,
      total_courses: 8,
      pass_rate: 0.875,
      class_rank: 5
    }
  ]
  pagination.total = 1
  loading.value = false
}

onMounted(() => {
  loadData()
})
</script>

<style scoped>
.student-report-tab {
  padding: 16px 0;
}

.search-bar {
  margin-bottom: 16px;
}
</style>
