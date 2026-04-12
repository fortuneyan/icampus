<template>
  <div class="textbook-container">
    <!-- 页面标题 -->
    <div class="page-header">
      <h2>教材管理</h2>
      <div class="header-actions">
        <el-button type="primary" @click="handleAdd">
          <el-icon><Plus /></el-icon>
          新增教材
        </el-button>
        <el-button @click="handleExport">
          <el-icon><Download /></el-icon>
          导出
        </el-button>
      </div>
    </div>

    <!-- 搜索筛选 -->
    <el-card class="search-card">
      <el-form :inline="true" :model="searchForm">
        <el-form-item label="关键词">
          <el-input
            v-model="searchForm.keyword"
            placeholder="教材名称/ISBN/作者"
            clearable
            style="width: 180px"
          />
        </el-form-item>
        <el-form-item label="学科">
          <el-select v-model="searchForm.subject" placeholder="请选择" clearable style="width: 120px">
            <el-option
              v-for="item in SUBJECTS"
              :key="item.value"
              :label="item.label"
              :value="item.value"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="年级">
          <el-select v-model="searchForm.grade_level" placeholder="请选择" clearable style="width: 140px">
            <el-option
              v-for="item in GRADE_LEVELS"
              :key="item.value"
              :label="item.label"
              :value="item.value"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="searchForm.status" placeholder="请选择" clearable style="width: 120px">
            <el-option
              v-for="item in STATUS_LIST"
              :key="item.value"
              :label="item.label"
              :value="item.value"
            />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">搜索</el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 数据表格 -->
    <el-card class="table-card">
      <el-table
        v-loading="loading"
        :data="tableData"
        stripe
        border
        style="width: 100%"
      >
        <el-table-column type="index" label="序号" width="60" />
        <el-table-column prop="isbn" label="ISBN" width="140" />
        <el-table-column prop="title" label="教材名称" min-width="200" show-overflow-tooltip />
        <el-table-column prop="author" label="作者" width="120" show-overflow-tooltip />
        <el-table-column prop="subject" label="学科" width="100">
          <template #default="{ row }">
            {{ getSubjectLabel(row.subject) }}
          </template>
        </el-table-column>
        <el-table-column prop="grade_level" label="适用年级" width="100">
          <template #default="{ row }">
            {{ getGradeLabel(row.grade_level) }}
          </template>
        </el-table-column>
        <el-table-column prop="price" label="定价(元)" width="90">
          <template #default="{ row }">
            ¥{{ row.price?.toFixed(2) }}
          </template>
        </el-table-column>
        <el-table-column prop="stock_quantity" label="库存" width="80">
          <template #default="{ row }">
            <el-tag :type="row.stock_quantity <= row.min_stock ? 'danger' : 'success'" size="small">
              {{ row.stock_quantity }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="90">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)" size="small">
              {{ getStatusLabel(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link size="small" @click="handleView(row)">查看</el-button>
            <el-button type="primary" link size="small" @click="handleEdit(row)">编辑</el-button>
            <el-button type="danger" link size="small" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination-container">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.page_size"
          :total="pagination.total"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handlePageChange"
        />
      </div>
    </el-card>

    <!-- 新增/编辑弹窗 -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogTitle"
      width="700px"
      :close-on-click-modal="false"
    >
      <el-form
        ref="formRef"
        :model="formData"
        :rules="formRules"
        label-width="100px"
      >
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="ISBN" prop="isbn">
              <el-input v-model="formData.isbn" placeholder="请输入ISBN" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="教材名称" prop="title">
              <el-input v-model="formData.title" placeholder="请输入教材名称" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="副标题">
              <el-input v-model="formData.subtitle" placeholder="请输入副标题" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="作者">
              <el-input v-model="formData.author" placeholder="请输入作者" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="出版社">
              <el-input v-model="formData.publisher" placeholder="请输入出版社" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="学科" prop="subject">
              <el-select v-model="formData.subject" placeholder="请选择" style="width: 100%">
                <el-option
                  v-for="item in SUBJECTS"
                  :key="item.value"
                  :label="item.label"
                  :value="item.value"
                />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="适用年级">
              <el-select v-model="formData.grade_level" placeholder="请选择" style="width: 100%">
                <el-option
                  v-for="item in GRADE_LEVELS"
                  :key="item.value"
                  :label="item.label"
                  :value="item.value"
                />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="适用学期">
              <el-select v-model="formData.semester" placeholder="请选择" style="width: 100%">
                <el-option
                  v-for="item in SEMESTERS"
                  :key="item.value"
                  :label="item.label"
                  :value="item.value"
                />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="定价(元)">
              <el-input-number v-model="formData.price" :min="0" :precision="2" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="进价(元)">
              <el-input-number v-model="formData.cost_price" :min="0" :precision="2" style="width: 100%" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="库存数量">
              <el-input-number v-model="formData.stock_quantity" :min="0" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="最低库存">
              <el-input-number v-model="formData.min_stock" :min="0" style="width: 100%" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="版次">
              <el-input v-model="formData.edition" placeholder="如：第1版" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="状态">
              <el-select v-model="formData.status" placeholder="请选择" style="width: 100%">
                <el-option
                  v-for="item in STATUS_LIST"
                  :key="item.value"
                  :label="item.label"
                  :value="item.value"
                />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item label="教材简介">
          <el-input
            v-model="formData.description"
            type="textarea"
            :rows="3"
            placeholder="请输入教材简介"
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitLoading">
          确定
        </el-button>
      </template>
    </el-dialog>

    <!-- 查看详情弹窗 -->
    <el-dialog v-model="viewVisible" title="教材详情" width="600px">
      <el-descriptions :column="2" border>
        <el-descriptions-item label="ISBN">{{ viewData.isbn }}</el-descriptions-item>
        <el-descriptions-item label="教材名称">{{ viewData.title }}</el-descriptions-item>
        <el-descriptions-item label="副标题">{{ viewData.subtitle || '-' }}</el-descriptions-item>
        <el-descriptions-item label="作者">{{ viewData.author || '-' }}</el-descriptions-item>
        <el-descriptions-item label="出版社">{{ viewData.publisher || '-' }}</el-descriptions-item>
        <el-descriptions-item label="学科">{{ getSubjectLabel(viewData.subject) }}</el-descriptions-item>
        <el-descriptions-item label="适用年级">{{ getGradeLabel(viewData.grade_level) }}</el-descriptions-item>
        <el-descriptions-item label="适用学期">{{ getSemesterLabel(viewData.semester) }}</el-descriptions-item>
        <el-descriptions-item label="定价">¥{{ viewData.price?.toFixed(2) }}</el-descriptions-item>
        <el-descriptions-item label="进价">¥{{ viewData.cost_price?.toFixed(2) }}</el-descriptions-item>
        <el-descriptions-item label="库存">{{ viewData.stock_quantity }}</el-descriptions-item>
        <el-descriptions-item label="最低库存">{{ viewData.min_stock }}</el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="getStatusType(viewData.status)" size="small">
            {{ getStatusLabel(viewData.status) }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="版次">{{ viewData.edition || '-' }}</el-descriptions-item>
        <el-descriptions-item label="教材简介" :span="2">{{ viewData.description || '-' }}</el-descriptions-item>
      </el-descriptions>

      <template #footer>
        <el-button @click="viewVisible = false">关闭</el-button>
        <el-button type="primary" @click="handleEditFromView">编辑</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Download } from '@element-plus/icons-vue'
import type { FormInstance, FormRules } from 'element-plus'
import {
  getTextbookList,
  getTextbook,
  createTextbook,
  updateTextbook,
  deleteTextbook,
  SUBJECTS,
  GRADE_LEVELS,
  SEMESTERS,
  STATUS_LIST,
  type Textbook
} from '@/api/edu/textbook'

// 表格数据
const loading = ref(false)
const tableData = ref<Textbook[]>([])
const pagination = reactive({
  page: 1,
  page_size: 20,
  total: 0
})

// 搜索表单
const searchForm = reactive({
  keyword: '',
  subject: '',
  grade_level: '',
  status: ''
})

// 弹窗相关
const dialogVisible = ref(false)
const viewVisible = ref(false)
const dialogTitle = ref('')
const submitLoading = ref(false)
const formRef = ref<FormInstance>()

// 表单数据
const formData = reactive<Partial<Textbook>>({
  isbn: '',
  title: '',
  subtitle: '',
  author: '',
  publisher: '',
  subject: '',
  grade_level: '',
  semester: '',
  edition: '',
  price: 0,
  cost_price: 0,
  stock_quantity: 0,
  min_stock: 10,
  status: 'draft',
  description: ''
})

// 查看数据
const viewData = ref<Textbook>({})

// 表单验证规则
const formRules: FormRules = {
  isbn: [{ required: true, message: '请输入ISBN', trigger: 'blur' }],
  title: [{ required: true, message: '请输入教材名称', trigger: 'blur' }],
  subject: [{ required: true, message: '请选择学科', trigger: 'change' }]
}

// 获取列表数据
async function fetchData() {
  loading.value = true
  try {
    const params = {
      page: pagination.page,
      page_size: pagination.page_size,
      keyword: searchForm.keyword || undefined,
      subject: searchForm.subject || undefined,
      grade_level: searchForm.grade_level || undefined,
      status: searchForm.status || undefined
    }
    const res = await getTextbookList(params)
    tableData.value = res.items
    pagination.total = res.total
  } catch (error) {
    console.error('获取教材列表失败', error)
  } finally {
    loading.value = false
  }
}

// 搜索
function handleSearch() {
  pagination.page = 1
  fetchData()
}

// 重置
function handleReset() {
  searchForm.keyword = ''
  searchForm.subject = ''
  searchForm.grade_level = ''
  searchForm.status = ''
  pagination.page = 1
  fetchData()
}

// 分页
function handleSizeChange() {
  fetchData()
}

function handlePageChange() {
  fetchData()
}

// 新增
function handleAdd() {
  dialogTitle.value = '新增教材'
  resetForm()
  dialogVisible.value = true
}

// 编辑
function handleEdit(row: Textbook) {
  dialogTitle.value = '编辑教材'
  Object.assign(formData, row)
  dialogVisible.value = true
}

// 查看
function handleView(row: Textbook) {
  Object.assign(viewData, row)
  viewVisible.value = true
}

// 查看时编辑
function handleEditFromView() {
  handleEdit(viewData.value)
  viewVisible.value = false
}

// 删除
async function handleDelete(row: Textbook) {
  try {
    await ElMessageBox.confirm('确定删除该教材吗？', '提示', {
      type: 'warning'
    })
    await deleteTextbook(row.id!)
    ElMessage.success('删除成功')
    fetchData()
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

// 提交表单
async function handleSubmit() {
  if (!formRef.value) return

  await formRef.value.validate(async (valid) => {
    if (valid) {
      submitLoading.value = true
      try {
        if (formData.id) {
          await updateTextbook(formData.id, formData)
          ElMessage.success('更新成功')
        } else {
          await createTextbook(formData)
          ElMessage.success('创建成功')
        }
        dialogVisible.value = false
        fetchData()
      } catch (error) {
        console.error('保存失败', error)
        ElMessage.error('保存失败')
      } finally {
        submitLoading.value = false
      }
    }
  })
}

// 重置表单
function resetForm() {
  Object.assign(formData, {
    id: undefined,
    isbn: '',
    title: '',
    subtitle: '',
    author: '',
    publisher: '',
    subject: '',
    grade_level: '',
    semester: '',
    edition: '',
    price: 0,
    cost_price: 0,
    stock_quantity: 0,
    min_stock: 10,
    status: 'draft',
    description: ''
  })
}

// 导出
function handleExport() {
  ElMessage.info('导出功能开发中...')
}

// 辅助函数
function getSubjectLabel(value: string) {
  return SUBJECTS.find(s => s.value === value)?.label || value || '-'
}

function getGradeLabel(value: string) {
  return GRADE_LEVELS.find(g => g.value === value)?.label || value || '-'
}

function getSemesterLabel(value: string) {
  return SEMESTERS.find(s => s.value === value)?.label || value || '-'
}

function getStatusLabel(value: string) {
  return STATUS_LIST.find(s => s.value === value)?.label || value || '-'
}

function getStatusType(value: string) {
  switch (value) {
    case 'published': return 'success'
    case 'draft': return 'info'
    case 'out_of_stock': return 'warning'
    case 'discontinued': return 'danger'
    default: return 'info'
  }
}

// 初始化
onMounted(() => {
  fetchData()
})
</script>

<style scoped>
.textbook-container {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.page-header h2 {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
}

.header-actions {
  display: flex;
  gap: 10px;
}

.search-card {
  margin-bottom: 20px;
}

.table-card {
  margin-bottom: 20px;
}

.pagination-container {
  display: flex;
  justify-content: flex-end;
  margin-top: 20px;
}
</style>
