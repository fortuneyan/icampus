<template>
  <div class="student-profile">
    <el-card>
      <div class="toolbar">
        <el-form :inline="true" :model="searchForm">
          <el-form-item label="关键词">
            <el-input v-model="searchForm.keyword" placeholder="学号" clearable />
          </el-form-item>
          <el-form-item label="状态">
            <el-select v-model="searchForm.status" placeholder="请选择" clearable>
              <el-option label="在读" value="active" />
              <el-option label="休学" value="suspended" />
              <el-option label="毕业" value="graduated" />
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
        <el-table-column prop="student_no" label="学号" width="120" />
        <el-table-column prop="guardian_name" label="监护人" width="100" />
        <el-table-column prop="guardian_phone" label="联系电话" width="130" />
        <el-table-column prop="province" label="省份" width="100" />
        <el-table-column prop="city" label="城市" width="100" />
        <el-table-column prop="student_status" label="学籍状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.student_status === 'active' ? 'success' : 'warning'">
              {{ getStatusText(row.student_status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="特殊标识" min-width="150">
          <template #default="{ row }">
            <el-tag v-if="row.is_left_behind" type="info" size="small">留守儿童</el-tag>
            <el-tag v-if="row.is_orphan" type="danger" size="small">孤儿</el-tag>
            <el-tag v-if="row.is_disabled" type="warning" size="small">残疾</el-tag>
            <el-tag v-if="row.is_poor" type="danger" size="small">贫困</el-tag>
          </template>
        </el-table-column>
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
            <el-form-item label="学号" prop="student_no">
              <el-input v-model="formData.student_no" />
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
            <el-form-item label="入学日期">
              <el-date-picker v-model="formData.enrollment_date" type="date" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="学籍状态">
              <el-select v-model="formData.student_status" style="width: 100%">
                <el-option label="在读" value="active" />
                <el-option label="休学" value="suspended" />
                <el-option label="毕业" value="graduated" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-divider>家庭信息</el-divider>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="监护人">
              <el-input v-model="formData.guardian_name" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="监护人电话">
              <el-input v-model="formData.guardian_phone" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="与监护人关系">
              <el-input v-model="formData.guardian_relation" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="监护人身份证">
              <el-input v-model="formData.guardian_id_card" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-divider>家庭住址</el-divider>
        <el-row :gutter="20">
          <el-col :span="8">
            <el-form-item label="省">
              <el-input v-model="formData.province" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="市">
              <el-input v-model="formData.city" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="区">
              <el-input v-model="formData.district" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="详细地址">
          <el-input v-model="formData.address" />
        </el-form-item>
        <el-divider>特殊标识</el-divider>
        <el-form-item>
          <el-checkbox v-model="formData.is_left_behind">留守儿童</el-checkbox>
          <el-checkbox v-model="formData.is_orphan">孤儿</el-checkbox>
          <el-checkbox v-model="formData.is_disabled">残疾</el-checkbox>
          <el-checkbox v-model="formData.is_poor">贫困</el-checkbox>
        </el-form-item>
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
import { getStudentProfileList, createStudentProfile, updateStudentProfile, deleteStudentProfile } from '@/api/edu/student_profile'

const searchForm = reactive({
  keyword: '',
  status: ''
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
  student_no: '',
  enrollment_date: '',
  graduation_date: '',
  student_status: 'active',
  guardian_name: '',
  guardian_phone: '',
  guardian_relation: '',
  guardian_id_card: '',
  province: '',
  city: '',
  district: '',
  address: '',
  is_left_behind: false,
  is_orphan: false,
  is_disabled: false,
  is_poor: false,
  remarks: ''
})

const formRules = {
  student_no: [{ required: true, message: '请输入学号', trigger: 'blur' }],
  user_id: [{ required: true, message: '请输入用户ID', trigger: 'blur' }]
}

const getStatusText = (status: string) => {
  const map: Record<string, string> = {
    active: '在读',
    suspended: '休学',
    graduated: '毕业'
  }
  return map[status] || status
}

const fetchData = async () => {
  loading.value = true
  try {
    const res = await getStudentProfileList({
      keyword: searchForm.keyword,
      status: searchForm.status,
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
  searchForm.status = ''
  pagination.page = 1
  fetchData()
}

const handleAdd = () => {
  dialogTitle.value = '新增学生扩展信息'
  Object.assign(formData, {
    id: '',
    user_id: '',
    student_no: '',
    enrollment_date: '',
    graduation_date: '',
    student_status: 'active',
    guardian_name: '',
    guardian_phone: '',
    guardian_relation: '',
    guardian_id_card: '',
    province: '',
    city: '',
    district: '',
    address: '',
    is_left_behind: false,
    is_orphan: false,
    is_disabled: false,
    is_poor: false,
    remarks: ''
  })
  dialogVisible.value = true
}

const handleEdit = (row: any) => {
  dialogTitle.value = '编辑学生扩展信息'
  Object.assign(formData, row)
  dialogVisible.value = true
}

const handleDelete = async (row: any) => {
  try {
    await deleteStudentProfile(row.user_id)
    ElMessage.success('删除成功')
    fetchData()
  } catch (error) {
    console.error(error)
  }
}

const handleSubmit = async () => {
  try {
    if (formData.id) {
      await updateStudentProfile(formData.user_id, formData)
      ElMessage.success('更新成功')
    } else {
      await createStudentProfile(formData)
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
.student-profile {
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