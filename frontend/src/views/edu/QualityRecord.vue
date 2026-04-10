<template>
  <div class="quality-record">
    <el-card>
      <div class="toolbar">
        <el-form :inline="true" :model="searchForm">
          <el-form-item label="评价维度">
            <el-select v-model="searchForm.dimension" placeholder="请选择" clearable>
              <el-option label="思想品德" value="moral" />
              <el-option label="学业水平" value="academic" />
              <el-option label="身心健康" value="health" />
              <el-option label="艺术素养" value="art" />
              <el-option label="社会实践" value="practice" />
            </el-select>
          </el-form-item>
          <el-form-item label="状态">
            <el-select v-model="searchForm.status" placeholder="请选择" clearable>
              <el-option label="草稿" value="draft" />
              <el-option label="已提交" value="submitted" />
              <el-option label="已确认" value="confirmed" />
            </el-select>
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="handleSearch">搜索</el-button>
            <el-button @click="handleReset">重置</el-button>
            <el-button type="success" @click="handleAdd">新增</el-button>
          </el-form-item>
        </el-form>
      </div>

      <el-table :data="tableData" v-loading="loading" stripe>
        <el-table-column prop="student_id" label="学生ID" width="220" />
        <el-table-column prop="dimension" label="评价维度" width="100">
          <template #default="{ row }">
            {{ getDimensionText(row.dimension) }}
          </template>
        </el-table-column>
        <el-table-column prop="title" label="记录标题" min-width="150" />
        <el-table-column prop="self_rating" label="自评" width="60">
          <template #default="{ row }">
            {{ row.self_rating ? row.self_rating + '星' : '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="teacher_rating" label="师评" width="60">
          <template #default="{ row }">
            {{ row.teacher_rating ? row.teacher_rating + '星' : '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="final_rating" label="最终" width="60">
          <template #default="{ row }">
            {{ row.final_rating ? row.final_rating + '星' : '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="academic_year" label="学年" width="100" />
        <el-table-column prop="semester" label="学期" width="80" />
        <el-table-column prop="status" label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">{{ getStatusText(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link @click="handleEdit(row)">编辑</el-button>
            <el-button v-if="row.status === 'draft'" type="success" link @click="handleSubmit(row)">提交</el-button>
            <el-button v-if="row.status === 'submitted'" type="warning" link @click="handleConfirm(row)">确认</el-button>
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

    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="700px">
      <el-form ref="formRef" :model="formData" :rules="formRules" label-width="100px">
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="学生ID" prop="student_id">
              <el-input v-model="formData.student_id" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="评价维度" prop="dimension">
              <el-select v-model="formData.dimension" style="width: 100%">
                <el-option label="思想品德" value="moral" />
                <el-option label="学业水平" value="academic" />
                <el-option label="身心健康" value="health" />
                <el-option label="艺术素养" value="art" />
                <el-option label="社会实践" value="practice" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="记录标题" prop="title">
          <el-input v-model="formData.title" />
        </el-form-item>
        <el-form-item label="记录内容">
          <el-input v-model="formData.content" type="textarea" :rows="4" />
        </el-form-item>
        <el-form-item label="证明材料">
          <el-input v-model="formData.evidence_url" placeholder="图片或文件URL" />
        </el-form-item>
        <el-row :gutter="20">
          <el-col :span="8">
            <el-form-item label="自评">
              <el-rate v-model="formData.self_rating" :max="5" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="师评">
              <el-rate v-model="formData.teacher_rating" :max="5" :disabled="formData.status !== 'submitted'" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="最终">
              <el-rate v-model="formData.final_rating" :max="5" :disabled="formData.status !== 'submitted'" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="学年">
              <el-input v-model="formData.academic_year" placeholder="如: 2024-2025" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="学期">
              <el-select v-model="formData.semester" style="width: 100%">
                <el-option label="第一学期" value="第一学期" />
                <el-option label="第二学期" value="第二学期" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="备注">
          <el-input v-model="formData.remarks" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmitForm">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { getQualityRecordList, createQualityRecord, updateQualityRecord, deleteQualityRecord, submitQualityRecord, confirmQualityRecord } from '@/api/edu/quality_record'

const searchForm = reactive({
  dimension: '',
  status: ''
})

const pagination = reactive({ page: 1, pageSize: 20, total: 0 })
const tableData = ref<any[]>([])
const loading = ref(false)
const dialogVisible = ref(false)
const dialogTitle = ref('')
const formRef = ref()

const formData = reactive<any>({
  id: '', student_id: '', dimension: '', title: '', content: '',
  evidence_url: '', self_rating: 0, teacher_rating: 0, final_rating: 0,
  academic_year: '', semester: '', status: 'draft', remarks: ''
})

const formRules = {
  student_id: [{ required: true, message: '请输入学生ID', trigger: 'blur' }],
  dimension: [{ required: true, message: '请选择评价维度', trigger: 'change' }],
  title: [{ required: true, message: '请输入记录标题', trigger: 'blur' }]
}

const getDimensionText = (val: string) => {
  const map: Record<string, string> = { moral: '思想品德', academic: '学业水平', health: '身心健康', art: '艺术素养', practice: '社会实践' }
  return map[val] || val
}
const getStatusText = (val: string) => { const map: Record<string, string> = { draft: '草稿', submitted: '已提交', confirmed: '已确认' }; return map[val] || val }
const getStatusType = (val: string) => { const map: Record<string, string> = { draft: 'info', submitted: 'warning', confirmed: 'success' }; return map[val] || 'info' }

const fetchData = async () => {
  loading.value = true
  try {
    const res = await getQualityRecordList({ dimension: searchForm.dimension, status: searchForm.status, page: pagination.page, page_size: pagination.pageSize })
    if (res.data?.items) { tableData.value = res.data.items; pagination.total = res.data.total || 0 }
  } catch (e) { console.error(e) } finally { loading.value = false }
}

const handleSearch = () => { pagination.page = 1; fetchData() }
const handleReset = () => { searchForm.dimension = ''; searchForm.status = ''; pagination.page = 1; fetchData() }

const handleAdd = () => {
  dialogTitle.value = '新增综合素质记录'
  Object.assign(formData, { id: '', student_id: '', dimension: '', title: '', content: '', evidence_url: '', self_rating: 0, teacher_rating: 0, final_rating: 0, academic_year: '', semester: '', status: 'draft', remarks: '' })
  dialogVisible.value = true
}
const handleEdit = (row: any) => { dialogTitle.value = '编辑综合素质记录'; Object.assign(formData, row); dialogVisible.value = true }
const handleDelete = async (row: any) => { try { await deleteQualityRecord(row.id); ElMessage.success('删除成功'); fetchData() } catch (e) { console.error(e) } }

const handleSubmit = async (row: any) => { try { await submitQualityRecord(row.id); ElMessage.success('提交成功'); fetchData() } catch (e) { console.error(e) } }
const handleConfirm = async (row: any) => { try { await confirmQualityRecord(row.id, { teacher_rating: row.teacher_rating || 5, final_rating: row.final_rating || 5 }); ElMessage.success('确认成功'); fetchData() } catch (e) { console.error(e) } }

const handleSubmitForm = async () => {
  try {
    if (formData.id) { await updateQualityRecord(formData.id, formData); ElMessage.success('更新成功') }
    else { await createQualityRecord(formData); ElMessage.success('创建成功') }
    dialogVisible.value = false; fetchData()
  } catch (e) { console.error(e) }
}

onMounted(() => { fetchData() })
</script>

<style scoped>
.quality-record { padding: 20px; }
.pagination { margin-top: 20px; display: flex; justify-content: flex-end; }
</style>