<template>
  <div class="teacher-profile">
    <el-card>
      <div class="toolbar">
        <el-form :inline="true" :model="searchForm">
          <el-form-item label="关键词">
            <el-input v-model="searchForm.keyword" placeholder="工号" clearable />
          </el-form-item>
          <el-form-item label="科目">
            <el-select v-model="searchForm.subject" placeholder="请选择" clearable>
              <el-option label="语文" value="语文" />
              <el-option label="数学" value="数学" />
              <el-option label="英语" value="英语" />
              <el-option label="物理" value="物理" />
              <el-option label="化学" value="化学" />
              <el-option label="生物" value="生物" />
              <el-option label="历史" value="历史" />
              <el-option label="地理" value="地理" />
              <el-option label="政治" value="政治" />
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
        <el-table-column prop="employee_no" label="工号" width="100" />
        <el-table-column prop="position" label="岗位" width="120" />
        <el-table-column prop="title" label="职称" width="100" />
        <el-table-column prop="subject" label="任教科目" width="100" />
        <el-table-column prop="teaching_grade" label="任教年级" width="100" />
        <el-table-column prop="employment_type" label="用工类型" width="100">
          <template #default="{ row }">
            <el-tag>{{ getEmploymentType(row.employment_type) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="education" label="学历" width="80" />
        <el-table-column prop="emergency_phone" label="紧急联系电话" width="140" />
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link @click="handleEdit(row)">编辑</el-button>
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
            <el-form-item label="工号" prop="employee_no">
              <el-input v-model="formData.employee_no" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="用户ID" prop="user_id">
              <el-input v-model="formData.user_id" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="入职日期">
              <el-date-picker v-model="formData.hire_date" type="date" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="用工类型">
              <el-select v-model="formData.employment_type" style="width: 100%">
                <el-option label="正式编制" value="full_time" />
                <el-option label="合同制" value="contract" />
                <el-option label="临时工" value="temporary" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="岗位">
              <el-input v-model="formData.position" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="职称">
              <el-select v-model="formData.title" style="width: 100%">
                <el-option label="正高级" value="正高级" />
                <el-option label="高级" value="高级" />
                <el-option label="一级" value="一级" />
                <el-option label="二级" value="二级" />
                <el-option label="三级" value="三级" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="任教科目">
              <el-select v-model="formData.subject" style="width: 100%">
                <el-option label="语文" value="语文" />
                <el-option label="数学" value="数学" />
                <el-option label="英语" value="英语" />
                <el-option label="物理" value="物理" />
                <el-option label="化学" value="化学" />
                <el-option label="生物" value="生物" />
                <el-option label="历史" value="历史" />
                <el-option label="地理" value="地理" />
                <el-option label="政治" value="政治" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="任教年级">
              <el-input v-model="formData.teaching_grade" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-divider>资质信息</el-divider>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="学历">
              <el-select v-model="formData.education" style="width: 100%">
                <el-option label="博士" value="博士" />
                <el-option label="硕士" value="硕士" />
                <el-option label="本科" value="本科" />
                <el-option label="大专" value="大专" />
                <el-option label="中专" value="中专" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="学位">
              <el-select v-model="formData.degree" style="width: 100%">
                <el-option label="博士学位" value="博士学位" />
                <el-option label="硕士学位" value="硕士学位" />
                <el-option label="学士学位" value="学士学位" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="教师资格证">
          <el-input v-model="formData.teacher_certificate" />
        </el-form-item>
        <el-divider>紧急联系人</el-divider>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="联系人">
              <el-input v-model="formData.emergency_contact" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="联系电话">
              <el-input v-model="formData.emergency_phone" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="备注">
          <el-input v-model="formData.remarks" type="textarea" :rows="2" />
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
import { ElMessage } from 'element-plus'
import { getTeacherProfileList, createTeacherProfile, updateTeacherProfile, deleteTeacherProfile } from '@/api/system/teacher_profile'

const searchForm = reactive({
  keyword: '',
  subject: ''
})

const pagination = reactive({
  page: 1,
  pageSize: 20,
  total: 0
})

const tableData = ref<any[]>([])
const loading = ref(false)
const dialogVisible = ref(false)
const dialogTitle = ref('')
const formRef = ref()

const formData = reactive<any>({
  id: '',
  user_id: '',
  employee_no: '',
  hire_date: '',
  position: '',
  title: '',
  employment_type: 'full_time',
  subject: '',
  teaching_grade: '',
  teacher_certificate: '',
  education: '',
  degree: '',
  emergency_contact: '',
  emergency_phone: '',
  remarks: ''
})

const formRules = {
  employee_no: [{ required: true, message: '请输入工号', trigger: 'blur' }],
  user_id: [{ required: true, message: '请输入用户ID', trigger: 'blur' }]
}

const getEmploymentType = (type: string) => {
  const map: Record<string, string> = {
    full_time: '正式编制',
    contract: '合同制',
    temporary: '临时工'
  }
  return map[type] || type
}

const fetchData = async () => {
  loading.value = true
  try {
    const res = await getTeacherProfileList({
      keyword: searchForm.keyword,
      subject: searchForm.subject,
      page: pagination.page,
      page_size: pagination.pageSize
    })
    if (res.data?.items) {
      tableData.value = res.data.items
      pagination.total = res.data.total || 0
    }
  } catch (error) {
    console.error(error)
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  pagination.page = 1
  fetchData()
}

const handleReset = () => {
  searchForm.keyword = ''
  searchForm.subject = ''
  pagination.page = 1
  fetchData()
}

const handleAdd = () => {
  dialogTitle.value = '新增教师扩展信息'
  Object.assign(formData, {
    id: '',
    user_id: '',
    employee_no: '',
    hire_date: '',
    position: '',
    title: '',
    employment_type: 'full_time',
    subject: '',
    teaching_grade: '',
    teacher_certificate: '',
    education: '',
    degree: '',
    emergency_contact: '',
    emergency_phone: '',
    remarks: ''
  })
  dialogVisible.value = true
}

const handleEdit = (row: any) => {
  dialogTitle.value = '编辑教师扩展信息'
  Object.assign(formData, row)
  dialogVisible.value = true
}

const handleDelete = async (row: any) => {
  try {
    await deleteTeacherProfile(row.user_id)
    ElMessage.success('删除成功')
    fetchData()
  } catch (error) {
    console.error(error)
  }
}

const handleSubmit = async () => {
  try {
    if (formData.id) {
      await updateTeacherProfile(formData.user_id, formData)
      ElMessage.success('更新成功')
    } else {
      await createTeacherProfile(formData)
      ElMessage.success('创建成功')
    }
    dialogVisible.value = false
    fetchData()
  } catch (error) {
    console.error(error)
  }
}

onMounted(() => {
  fetchData()
})
</script>

<style scoped>
.teacher-profile {
  padding: 20px;
}
.toolbar {
  margin-bottom: 20px;
}
.pagination {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}
</style>