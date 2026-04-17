<template>
  <div class="growth-record">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>学生成长档案</span>
          <el-button type="primary" @click="handleAdd">
            <el-icon><Plus /></el-icon>
            新增记录
          </el-button>
        </div>
      </template>

      <el-form :inline="true" :model="searchForm" class="search-form">
        <el-form-item label="记录类型">
          <el-select v-model="searchForm.record_type" placeholder="请选择" clearable>
            <el-option label="照片" value="photo" />
            <el-option label="视频" value="video" />
            <el-option label="荣誉" value="honor" />
            <el-option label="活动" value="activity" />
            <el-option label="评语" value="comment" />
          </el-select>
        </el-form-item>
        <el-form-item label="学年">
          <el-input v-model="searchForm.academic_year" placeholder="如: 2024-2025" clearable />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">搜索</el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>

      <el-table :data="tableData" v-loading="loading" stripe>
        <el-table-column prop="record_type" label="类型" width="100">
          <template #default="{ row }">
            <el-tag :type="getTypeTag(row.record_type)">{{ getTypeText(row.record_type) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="title" label="标题" min-width="200" />
        <el-table-column prop="content" label="内容" min-width="200" show-overflow-tooltip />
        <el-table-column prop="academic_year" label="学年" width="100" />
        <el-table-column prop="semester" label="学期" width="80" />
        <el-table-column prop="is_public" label="公开" width="80" align="center">
          <template #default="{ row }">
            <el-tag :type="row.is_public ? 'success' : 'info'" size="small">
              {{ row.is_public ? '是' : '否' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="is_featured" label="精选" width="80" align="center">
          <template #default="{ row }">
            <el-tag :type="row.is_featured ? 'warning' : 'info'" size="small">
              {{ row.is_featured ? '是' : '否' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="80" align="center">
          <template #default="{ row }">
            <el-tag :type="row.status === 'published' ? 'success' : 'info'" size="small">
              {{ row.status === 'published' ? '已发布' : '草稿' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link size="small" @click="handleEdit(row)">编辑</el-button>
            <el-button type="danger" link size="small" @click="handleDelete(row)">删除</el-button>
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

    <!-- 新增/编辑对话框 -->
    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="700px" @close="handleDialogClose">
      <el-form ref="formRef" :model="formData" :rules="formRules" label-width="100px">
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="学生ID" prop="student_id">
              <el-input v-model="formData.student_id" placeholder="请输入学生ID" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="记录类型" prop="record_type">
              <el-select v-model="formData.record_type" style="width: 100%">
                <el-option label="照片" value="photo" />
                <el-option label="视频" value="video" />
                <el-option label="荣誉" value="honor" />
                <el-option label="活动" value="activity" />
                <el-option label="评语" value="comment" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="标题" prop="title">
          <el-input v-model="formData.title" placeholder="请输入标题" />
        </el-form-item>
        <el-form-item label="内容">
          <el-input v-model="formData.content" type="textarea" :rows="4" placeholder="请输入内容" />
        </el-form-item>
        <el-form-item label="附件URL">
          <el-input v-model="formData.attachment_url" placeholder="图片或视频URL" />
        </el-form-item>
        <el-form-item label="标签">
          <el-input v-model="formData.tags" placeholder="多个标签用逗号分隔" />
        </el-form-item>
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
        <el-form-item label="记录日期">
          <el-date-picker
            v-model="formData.record_date"
            type="datetime"
            placeholder="选择日期时间"
            style="width: 100%"
          />
        </el-form-item>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="对家长可见">
              <el-switch v-model="formData.is_public" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="精选">
              <el-switch v-model="formData.is_featured" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="状态">
          <el-radio-group v-model="formData.status">
            <el-radio value="draft">草稿</el-radio>
            <el-radio value="published">发布</el-radio>
          </el-radio-group>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitLoading" @click="handleSubmit">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox, FormInstance } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import {
  getGrowthRecordList,
  createGrowthRecord,
  updateGrowthRecord,
  deleteGrowthRecord,
  type GrowthRecord
} from '@/api/student'

const searchForm = reactive({
  record_type: '',
  academic_year: ''
})

const pagination = reactive({ page: 1, pageSize: 20, total: 0 })
const tableData = ref<GrowthRecord[]>([])
const loading = ref(false)
const dialogVisible = ref(false)
const dialogTitle = ref('')
const submitLoading = ref(false)
const formRef = ref<FormInstance>()
const isEdit = ref(false)
const currentId = ref('')

const formData = reactive({
  student_id: '',
  record_type: 'photo',
  title: '',
  content: '',
  attachment_url: '',
  tags: '',
  academic_year: '',
  semester: '',
  record_date: '',
  is_public: false,
  is_featured: false,
  status: 'draft'
})

const formRules = {
  student_id: [{ required: true, message: '请输入学生ID', trigger: 'blur' }],
  record_type: [{ required: true, message: '请选择记录类型', trigger: 'change' }],
  title: [{ required: true, message: '请输入标题', trigger: 'blur' }]
}

const getTypeText = (val: string) => {
  const map: Record<string, string> = {
    photo: '照片',
    video: '视频',
    honor: '荣誉',
    activity: '活动',
    comment: '评语'
  }
  return map[val] || val
}

const getTypeTag = (val: string) => {
  const map: Record<string, string> = {
    photo: '',
    video: 'success',
    honor: 'warning',
    activity: 'info',
    comment: 'danger'
  }
  return map[val] || ''
}

const fetchData = async () => {
  loading.value = true
  try {
    const res = await getGrowthRecordList({
      record_type: searchForm.record_type || undefined,
      academic_year: searchForm.academic_year || undefined,
      page: pagination.page,
      page_size: pagination.pageSize
    })
    if (res.code === 200 && res.data) {
      tableData.value = res.data.items || []
      pagination.total = res.data.total || 0
    }
  } catch (error) {
    console.error('加载数据失败:', error)
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  pagination.page = 1
  fetchData()
}

const handleReset = () => {
  searchForm.record_type = ''
  searchForm.academic_year = ''
  pagination.page = 1
  fetchData()
}

const handleAdd = () => {
  dialogTitle.value = '新增成长记录'
  isEdit.value = false
  resetForm()
  dialogVisible.value = true
}

const handleEdit = (row: GrowthRecord) => {
  dialogTitle.value = '编辑成长记录'
  isEdit.value = true
  currentId.value = row.id
  Object.assign(formData, {
    student_id: row.student_id,
    record_type: row.record_type,
    title: row.title,
    content: row.content || '',
    attachment_url: row.attachment_url || '',
    tags: row.tags || '',
    academic_year: row.academic_year || '',
    semester: row.semester || '',
    is_public: row.is_public,
    is_featured: row.is_featured,
    status: row.status
  })
  dialogVisible.value = true
}

const handleDelete = (row: GrowthRecord) => {
  ElMessageBox.confirm(`确定要删除成长记录"${row.title}"吗？`, '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(async () => {
    try {
      await deleteGrowthRecord(row.id)
      ElMessage.success('删除成功')
      fetchData()
    } catch (error) {
      console.error('删除失败:', error)
    }
  }).catch(() => {})
}

const handleSubmit = async () => {
  if (!formRef.value) return
  
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    
    submitLoading.value = true
    try {
      const data = { ...formData }
      if (data.record_date instanceof Date) {
        data.record_date = data.record_date.toISOString()
      }
      
      if (isEdit.value) {
        await updateGrowthRecord(currentId.value, data)
        ElMessage.success('更新成功')
      } else {
        await createGrowthRecord(data)
        ElMessage.success('创建成功')
      }
      dialogVisible.value = false
      fetchData()
    } catch (error) {
      console.error('保存失败:', error)
    } finally {
      submitLoading.value = false
    }
  })
}

const resetForm = () => {
  Object.assign(formData, {
    student_id: '',
    record_type: 'photo',
    title: '',
    content: '',
    attachment_url: '',
    tags: '',
    academic_year: '',
    semester: '',
    record_date: '',
    is_public: false,
    is_featured: false,
    status: 'draft'
  })
  formRef.value?.resetFields()
}

const handleDialogClose = () => {
  resetForm()
}

onMounted(() => {
  fetchData()
})
</script>

<style scoped lang="scss">
.growth-record {
  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
  
  .search-form {
    margin-bottom: 16px;
  }
  
  .pagination {
    margin-top: 20px;
    display: flex;
    justify-content: flex-end;
  }
}
</style>
