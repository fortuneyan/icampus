<template>
  <div class="exam-management">
    <el-card>
      <div class="toolbar">
        <el-form :inline="true" :model="searchForm">
          <el-form-item label="考试名称">
            <el-input v-model="searchForm.keyword" placeholder="请输入" clearable />
          </el-form-item>
          <el-form-item label="考试类型">
            <el-select v-model="searchForm.exam_type" placeholder="请选择" clearable>
              <el-option label="期中考试" value="midterm" />
              <el-option label="期末考试" value="final" />
              <el-option label="月考" value="monthly" />
              <el-option label="模拟考试" value="mock" />
            </el-select>
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="handleSearch">搜索</el-button>
            <el-button @click="handleReset">重置</el-button>
            <el-button type="success" @click="handleAdd">创建考试</el-button>
          </el-form-item>
        </el-form>
      </div>

      <el-table :data="tableData" v-loading="loading" stripe>
        <el-table-column prop="title" label="考试名称" min-width="150" />
        <el-table-column prop="exam_type" label="类型" width="100">
          <template #default="{ row }">
            <el-tag>{{ getTypeName(row.exam_type) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="academic_year" label="学年" width="120" />
        <el-table-column prop="semester" label="学期" width="100" />
        <el-table-column prop="duration" label="时长(分钟)" width="100" />
        <el-table-column prop="total_score" label="总分" width="80" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">
              {{ getStatusName(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link @click="handleEdit(row)">编辑</el-button>
            <el-button type="success" link @click="handleArrange(row)" v-if="row.status === 'draft'">安排</el-button>
            <el-button type="danger" link @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
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

    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="600px">
      <el-form ref="formRef" :model="formData" :rules="formRules" label-width="100px">
        <el-form-item label="考试名称" prop="title">
          <el-input v-model="formData.title" />
        </el-form-item>
        <el-form-item label="考试类型" prop="exam_type">
          <el-select v-model="formData.exam_type">
            <el-option label="期中考试" value="midterm" />
            <el-option label="期末考试" value="final" />
            <el-option label="月考" value="monthly" />
            <el-option label="模拟考试" value="mock" />
          </el-select>
        </el-form-item>
        <el-form-item label="学年" prop="academic_year">
          <el-input v-model="formData.academic_year" placeholder="如: 2025-2026" />
        </el-form-item>
        <el-form-item label="学期" prop="semester">
          <el-select v-model="formData.semester">
            <el-option label="第一学期" value="第一学期" />
            <el-option label="第二学期" value="第二学期" />
          </el-select>
        </el-form-item>
        <el-form-item label="时长(分钟)" prop="duration">
          <el-input-number v-model="formData.duration" :min="30" :max="180" />
        </el-form-item>
        <el-form-item label="总分" prop="total_score">
          <el-input-number v-model="formData.total_score" :min="0" :max="200" />
        </el-form-item>
        <el-form-item label="状态" prop="status">
          <el-select v-model="formData.status">
            <el-option label="草稿" value="draft" />
            <el-option label="已发布" value="published" />
            <el-option label="进行中" value="ongoing" />
            <el-option label="已结束" value="completed" />
          </el-select>
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
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { FormInstance } from 'element-plus'
import { getExamList, createExam, updateExam, deleteExam } from '@/api/exam'

const loading = ref(false)
const tableData = ref([])
const searchForm = reactive({ keyword: '', exam_type: '' })
const pagination = reactive({ page: 1, pageSize: 20, total: 0 })

const dialogVisible = ref(false)
const dialogTitle = ref('')
const formRef = ref<FormInstance>()
const formData = reactive<any>({ id: '', title: '', exam_type: 'midterm', academic_year: '', semester: '第一学期', duration: 120, total_score: 100, status: 'draft' })

const formRules = {
  title: [{ required: true, message: '请输入考试名称', trigger: 'blur' }],
  exam_type: [{ required: true, message: '请选择考试类型', trigger: 'change' }]
}

const getTypeName = (type: string) => ({ midterm: '期中', final: '期末', monthly: '月考', mock: '模拟' }[type] || type)
const getStatusName = (status: string) => ({ draft: '草稿', published: '已发布', ongoing: '进行中', completed: '已结束' }[status] || status)
const getStatusType = (status: string) => ({ draft: 'info', published: 'success', ongoing: 'warning', completed: 'info' }[status] || 'info')

const fetchData = async () => {
  loading.value = true
  try {
    const res = await getExamList({ ...searchForm, page: pagination.page, page_size: pagination.pageSize })
    tableData.value = res.data.items || []
    pagination.total = res.data.total || 0
  } catch (e) { console.error(e) }
  finally { loading.value = false }
}

const handleSearch = () => { pagination.page = 1; fetchData() }
const handleReset = () => { searchForm.keyword = ''; searchForm.exam_type = ''; handleSearch() }

const handleAdd = () => {
  Object.assign(formData, { id: '', title: '', exam_type: 'midterm', academic_year: '', semester: '第一学期', duration: 120, total_score: 100, status: 'draft' })
  dialogTitle.value = '创建考试'
  dialogVisible.value = true
}

const handleEdit = (row: any) => {
  Object.assign(formData, { ...row })
  dialogTitle.value = '编辑考试'
  dialogVisible.value = true
}

const handleArrange = (row: any) => {
  ElMessage.info('考试安排功能开发中')
}

const handleSubmit = async () => {
  if (!formRef.value) return
  await formRef.value.validate()
  try {
    if (formData.id) { await updateExam(formData.id, formData); ElMessage.success('更新成功') }
    else { await createExam(formData); ElMessage.success('创建成功') }
    dialogVisible.value = false
    fetchData()
  } catch (e: any) { ElMessage.error(e.message || '操作失败') }
}

const handleDelete = async (row: any) => {
  try {
    await ElMessageBox.confirm('确定要删除该考试吗？', '提示', { type: 'warning' })
    await deleteExam(row.id)
    ElMessage.success('删除成功')
    fetchData()
  } catch (e: any) { if (e !== 'cancel') ElMessage.error(e.message || '删除失败') }
}

onMounted(() => { fetchData() })
</script>

<style scoped lang="scss">
.exam-management {
  .toolbar { margin-bottom: 20px; }
  .pagination { margin-top: 20px; display: flex; justify-content: flex-end; }
}
</style>