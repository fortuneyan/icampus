<template>
  <div class="learning-record">
    <el-card>
      <div class="toolbar">
        <el-form :inline="true" :model="searchForm">
          <el-form-item label="资源类型">
            <el-select v-model="searchForm.resource_type" placeholder="请选择" clearable>
              <el-option label="视频" value="video" />
              <el-option label="文档" value="document" />
              <el-option label="课件" value="courseware" />
              <el-option label="作业" value="homework" />
            </el-select>
          </el-form-item>
          <el-form-item label="行为类型">
            <el-select v-model="searchForm.action_type" placeholder="请选择" clearable>
              <el-option label="观看" value="view" />
              <el-option label="下载" value="download" />
              <el-option label="收藏" value="favorite" />
              <el-option label="完成" value="complete" />
            </el-select>
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="handleSearch">搜索</el-button>
            <el-button type="success" @click="handleAdd">添加记录</el-button>
          </el-form-item>
        </el-form>
      </div>

      <el-row :gutter="20" class="stats-row">
        <el-col :span="6">
          <el-card shadow="hover">
            <div class="stat-item">
              <el-icon :size="40" color="#409eff"><Timer /></el-icon>
              <div class="stat-info">
                <span class="stat-value">{{ statistics.total_duration || 0 }}分钟</span>
                <span class="stat-label">总学习时长</span>
              </div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card shadow="hover">
            <div class="stat-item">
              <el-icon :size="40" color="#67c23a"><Document /></el-icon>
              <div class="stat-info">
                <span class="stat-value">{{ statistics.total_count || 0 }}</span>
                <span class="stat-label">学习记录数</span>
              </div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card shadow="hover">
            <div class="stat-item">
              <el-icon :size="40" color="#e6a23c"><DataLine /></el-icon>
              <div class="stat-info">
                <span class="stat-value">{{ statistics.days || 0 }}天</span>
                <span class="stat-label">学习天数</span>
              </div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card shadow="hover">
            <div class="stat-item">
              <el-icon :size="40" color="#f56c6c"><Star /></el-icon>
              <div class="stat-info">
                <span class="stat-value">{{ actionStats }}</span>
                <span class="stat-label">行为类型</span>
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>

      <el-table :data="tableData" v-loading="loading" stripe>
        <el-table-column prop="resource_name" label="资源名称" min-width="150" />
        <el-table-column prop="resource_type" label="资源类型" width="100">
          <template #default="{ row }">
            <el-tag>{{ getTypeText(row.resource_type) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="action_type" label="行为类型" width="100">
          <template #default="{ row }">
            <el-tag :type="getActionTypeTag(row.action_type)">{{ getActionText(row.action_type) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="duration" label="时长(分钟)" width="100" />
        <el-table-column prop="progress" label="进度" width="100">
          <template #default="{ row }">
            {{ (row.progress * 100).toFixed(0) }}%
          </template>
        </el-table-column>
        <el-table-column prop="score" label="得分" width="80">
          <template #default="{ row }">
            {{ row.score || '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="学习时间" width="180" />
      </el-table>

      <div class="pagination">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.pageSize"
          :total="pagination.total"
          :page-sizes="[10, 20, 50]"
          layout="total, sizes, prev, pager, next"
          @size-change="fetchData"
          @current-change="fetchData"
        />
      </div>
    </el-card>

    <el-dialog v-model="dialogVisible" title="添加学习记录" width="500px">
      <el-form ref="formRef" :model="formData" :rules="formRules" label-width="100px">
        <el-form-item label="资源类型" prop="resource_type">
          <el-select v-model="formData.resource_type">
            <el-option label="视频" value="video" />
            <el-option label="文档" value="document" />
            <el-option label="课件" value="courseware" />
            <el-option label="作业" value="homework" />
          </el-select>
        </el-form-item>
        <el-form-item label="资源名称" prop="resource_name">
          <el-input v-model="formData.resource_name" />
        </el-form-item>
        <el-form-item label="行为类型" prop="action_type">
          <el-select v-model="formData.action_type">
            <el-option label="观看" value="view" />
            <el-option label="下载" value="download" />
            <el-option label="收藏" value="favorite" />
            <el-option label="完成" value="complete" />
          </el-select>
        </el-form-item>
        <el-form-item label="时长(分钟)" prop="duration">
          <el-input-number v-model="formData.duration" :min="0" />
        </el-form-item>
        <el-form-item label="进度" prop="progress">
          <el-slider v-model="formData.progress" :min="0" :max="1" :step="0.1" show-stops />
        </el-form-item>
        <el-form-item label="得分" prop="score">
          <el-input-number v-model="formData.score" :min="0" :max="100" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage } from 'element-plus'
import type { FormInstance } from 'element-plus'
import { Timer, Document, DataLine, Star } from '@element-plus/icons-vue'
import { getLearningRecords, createLearningRecord, getLearningStatistics } from '@/api/ai/learning_record'

const loading = ref(false)
const tableData = ref([])
const searchForm = reactive({ resource_type: '', action_type: '' })
const pagination = reactive({ page: 1, pageSize: 20, total: 0 })

const statistics = ref<any>({})
const actionStats = ref('0')

const dialogVisible = ref(false)
const formRef = ref<FormInstance>()
const formData = reactive<any>({ resource_type: 'video', resource_name: '', action_type: 'view', duration: 0, progress: 0, score: undefined })

const formRules = {
  resource_type: [{ required: true, message: '请选择资源类型', trigger: 'change' }],
  action_type: [{ required: true, message: '请选择行为类型', trigger: 'change' }],
}

const getTypeText = (v: string) => ({ video: '视频', document: '文档', courseware: '课件', homework: '作业' }[v] || v)
const getActionText = (v: string) => ({ view: '观看', download: '下载', favorite: '收藏', complete: '完成' }[v] || v)
const getActionTypeTag = (v: string) => ({ view: 'primary', download: 'success', favorite: 'warning', complete: 'info' }[v] || '')

const fetchData = async () => {
  loading.value = true
  try {
    const res = await getLearningRecords({ ...searchForm, page: pagination.page, page_size: pagination.pageSize })
    tableData.value = res.data?.items || []
    pagination.total = res.data?.total || 0
  } catch (e) { console.error(e) }
  finally { loading.value = false }
}

const fetchStatistics = async () => {
  try {
    const res = await getLearningStatistics(30)
    statistics.value = res.data || {}
    actionStats.value = Object.keys(statistics.value.action_stats || {}).length.toString()
  } catch (e) { console.error(e) }
}

const handleSearch = () => { pagination.page = 1; fetchData() }
const handleAdd = () => {
  Object.assign(formData, { resource_type: 'video', resource_name: '', action_type: 'view', duration: 0, progress: 0, score: undefined })
  dialogVisible.value = true
}

const handleSubmit = async () => {
  if (!formRef.value) return
  await formRef.value.validate()
  try {
    await createLearningRecord(formData)
    ElMessage.success('添加成功')
    dialogVisible.value = false
    fetchData()
    fetchStatistics()
  } catch (e: any) { ElMessage.error(e.message || '操作失败') }
}

onMounted(() => { fetchData(); fetchStatistics() })
</script>

<style scoped lang="scss">
.learning-record {
  .toolbar { margin-bottom: 20px; }
  .stats-row { margin-bottom: 20px; }
  .pagination { margin-top: 20px; display: flex; justify-content: flex-end; }
  .stat-item { display: flex; align-items: center; gap: 20px; .stat-info { display: flex; flex-direction: column; .stat-value { font-size: 24px; font-weight: bold; color: #333; } .stat-label { font-size: 14px; color: #999; } } }
}
</style>