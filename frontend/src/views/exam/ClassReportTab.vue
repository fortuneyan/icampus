<template>
  <div class="class-report-tab">
    <a-table
      :columns="columns"
      :data-source="dataList"
      :loading="loading"
      row-key="class_id"
    >
      <template #bodyCell="{ column, record }">
        <template v-if="column.key === 'class_average'">
          <a-tag :color="getScoreColor(record.class_average)">
            {{ record.class_average }}
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
        </template>
      </template>
    </a-table>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'

const loading = ref(false)
const dataList = ref<any[]>([])

const columns = [
  { title: '班级ID', dataIndex: 'class_id', key: 'class_id', width: 100 },
  { title: '班级名称', dataIndex: 'class_name', key: 'class_name', width: 150 },
  { title: '学生数', dataIndex: 'total_students', key: 'total_students', width: 100 },
  { title: '班级平均分', dataIndex: 'class_average', key: 'class_average', width: 120 },
  { title: '及格率', dataIndex: 'pass_rate', key: 'pass_rate', width: 150 },
  { title: '优秀率', dataIndex: 'excellent_rate', key: 'excellent_rate', width: 100 },
  { title: '操作', key: 'action', fixed: 'right', width: 100 }
]

const getScoreColor = (score: number): string => {
  if (score >= 85) return 'green'
  if (score >= 75) return 'cyan'
  if (score >= 65) return 'blue'
  return 'orange'
}

const handleView = (record: any) => {
  console.log('查看班级详情:', record)
}

const loadData = async () => {
  loading.value = true
  // 模拟数据
  dataList.value = [
    { class_id: 1, class_name: '高一(1)班', total_students: 45, class_average: 78.5, pass_rate: 0.89, excellent_rate: 0.22 },
    { class_id: 2, class_name: '高一(2)班', total_students: 43, class_average: 82.3, pass_rate: 0.95, excellent_rate: 0.35 }
  ]
  loading.value = false
}

onMounted(() => {
  loadData()
})
</script>

<style scoped>
.class-report-tab {
  padding: 16px 0;
}
</style>
