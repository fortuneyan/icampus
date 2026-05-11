<template>
  <div class="resource-management">
    <el-card>
      <div class="toolbar">
        <el-form :inline="true" :model="searchForm">
          <el-form-item label="关键词">
            <el-input v-model="searchForm.keyword" placeholder="搜索资源" clearable />
          </el-form-item>
          <el-form-item label="类型">
            <el-select v-model="searchForm.resource_type" placeholder="请选择" clearable>
              <el-option label="视频" value="video" />
              <el-option label="文档" value="document" />
              <el-option label="图片" value="image" />
              <el-option label="音频" value="audio" />
            </el-select>
          </el-form-item>
          <el-form-item label="分类">
            <el-select v-model="searchForm.category_id" placeholder="请选择" clearable>
              <el-option v-for="c in categoryOptions" :key="c.value" :label="c.label" :value="c.value" />
            </el-select>
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="handleSearch">搜索</el-button>
            <el-button @click="handleReset">重置</el-button>
            <el-button type="success" @click="handleAdd">上传资源</el-button>
          </el-form-item>
        </el-form>
      </div>

      <el-table :data="tableData" v-loading="loading" stripe>
        <el-table-column prop="title" label="标题" min-width="200" />
        <el-table-column prop="resource_type" label="类型" width="100">
          <template #default="{ row }">
            <el-tag>{{ getTypeName(row.resource_type) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="category_name" label="分类" width="120" />
        <el-table-column prop="view_count" label="浏览" width="80" />
        <el-table-column prop="like_count" label="点赞" width="80" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.status === 'published' ? 'success' : 'warning'">
              {{ row.status === 'published' ? '已发布' : '待审核' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="上传时间" width="160">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link @click="handleView(row)">查看</el-button>
            <el-button type="success" link @click="handleAudit(row)" v-if="row.status === 'pending'">审核</el-button>
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
        <el-form-item label="标题" prop="title">
          <el-input v-model="formData.title" />
        </el-form-item>
        <el-form-item label="资源类型" prop="resource_type">
          <el-select v-model="formData.resource_type">
            <el-option label="视频" value="video" />
            <el-option label="文档" value="document" />
            <el-option label="图片" value="image" />
            <el-option label="音频" value="audio" />
          </el-select>
        </el-form-item>
        <el-form-item label="分类" prop="category_id">
          <el-select v-model="formData.category_id">
            <el-option v-for="c in categoryOptions" :key="c.value" :label="c.label" :value="c.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="描述" prop="description">
          <el-input v-model="formData.description" type="textarea" :rows="3" />
        </el-form-item>
        <el-form-item label="文件">
          <el-upload
            ref="uploadRef"
            class="upload-demo"
            drag
            action="/api/v1/resource/resources/upload"
            :headers="uploadHeaders"
            :auto-upload="false"
            :limit="1"
            :on-change="handleFileChange"
            :on-success="handleUploadSuccess"
            :on-error="handleUploadError"
          >
            <el-icon class="el-icon--upload"><upload-filled /></el-icon>
            <div class="el-upload__text">拖拽文件到此处或<em>点击上传</em></div>
          </el-upload>
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
import { UploadFilled } from '@element-plus/icons-vue'
import { getResourceList, createResource, deleteResource, auditResource, getCategoryOptions } from '@/api/resource'

const loading = ref(false)
const tableData = ref([])
const searchForm = reactive({ keyword: '', resource_type: '', category_id: '' })
const pagination = reactive({ page: 1, pageSize: 20, total: 0 })

// 上传请求头（携带 token）
const uploadHeaders = {
  Authorization: `Bearer ${localStorage.getItem('token') || ''}`
}

const categoryOptions = ref<any[]>([])

const dialogVisible = ref(false)
const dialogTitle = ref('')
const formRef = ref<FormInstance>()
const uploadRef = ref<any>(null)
const formData = reactive<any>({ id: '', title: '', resource_type: 'document', category_id: '', description: '', file_url: '' })
const hasSelectedFile = ref(false)

const formRules = {
  title: [{ required: true, message: '请输入标题', trigger: 'blur' }],
  resource_type: [{ required: true, message: '请选择类型', trigger: 'change' }]
}

const getTypeName = (type: string) => ({ video: '视频', document: '文档', image: '图片', audio: '音频' }[type] || type)

const formatDate = (val: string) => {
  if (!val) return '-'
  const date = new Date(val)
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  const hours = String(date.getHours()).padStart(2, '0')
  const minutes = String(date.getMinutes()).padStart(2, '0')
  return `${year}-${month}-${day} ${hours}:${minutes}`
}

const fetchData = async () => {
  loading.value = true
  try {
    const res = await getResourceList({ ...searchForm, page: pagination.page, page_size: pagination.pageSize })
    tableData.value = res.data.items
    pagination.total = res.data.total
  } catch (e) { console.error(e) }
  finally { loading.value = false }
}

const fetchCategories = async () => {
  try {
    const res = await getCategoryOptions()
    categoryOptions.value = res.data || []
  } catch (e) { console.error(e) }
}

const handleSearch = () => { pagination.page = 1; fetchData() }
const handleReset = () => { searchForm.keyword = ''; searchForm.resource_type = ''; searchForm.category_id = ''; handleSearch() }

const handleAdd = () => {
  Object.assign(formData, { id: '', title: '', resource_type: 'document', category_id: '', description: '', file_url: '' })
  hasSelectedFile.value = false
  // 清空上传组件的文件列表
  if (uploadRef.value) {
    uploadRef.value.clearFiles()
  }
  dialogTitle.value = '上传资源'
  dialogVisible.value = true
}

const handleView = (row: any) => { window.open(row.file_url, '_blank') }

const handleAudit = async (row: any) => {
  try {
    await ElMessageBox.confirm('确定审核通过该资源吗？', '提示', { type: 'info' })
    await auditResource(row.id, { status: 'published' })
    ElMessage.success('审核成功')
    fetchData()
  } catch (e: any) { if (e !== 'cancel') ElMessage.error(e.message || '操作失败') }
}

const handleFileChange = (file: any) => {
  hasSelectedFile.value = true
  // 提取文件名（不含扩展名）
  const fileName = file.name
  const nameWithoutExt = fileName.replace(/\.[^/.]+$/, '')
  const ext = fileName.split('.').pop()?.toLowerCase() || ''
  
  // 如果标题为空，自动填入文件名
  if (!formData.title) {
    formData.title = nameWithoutExt
  }
  
  // 根据扩展名自动识别资源类型
  const typeMap: Record<string, string> = {
    // 视频
    mp4: 'video', avi: 'video', mov: 'video', wmv: 'video', flv: 'video', mkv: 'video',
    // 音频
    mp3: 'audio', wav: 'audio', wma: 'audio', ogg: 'audio', aac: 'audio', flac: 'audio',
    // 图片
    jpg: 'image', jpeg: 'image', png: 'image', gif: 'image', bmp: 'image', webp: 'image', svg: 'image',
    // 文档
    pdf: 'document', doc: 'document', docx: 'document', xls: 'document', xlsx: 'document', 
    ppt: 'document', pptx: 'document', txt: 'document', rtf: 'document'
  }
  
  // 如果当前是默认的 document 类型，则根据扩展名自动切换
  if (formData.resource_type === 'document') {
    const detectedType = typeMap[ext]
    if (detectedType) {
      formData.resource_type = detectedType
    }
  }
  
  // 追加到描述中
  const fileInfo = `文件名：${fileName}`
  if (formData.description) {
    formData.description = formData.description + '\n' + fileInfo
  } else {
    formData.description = fileInfo
  }
}

const handleSubmit = async () => {
  if (!formRef.value) return
  await formRef.value.validate()
  
  // 如果有选择文件，先上传文件
  if (hasSelectedFile.value && uploadRef.value) {
    uploadRef.value.submit()
    return
  }
  
  // 没有文件直接创建资源
  await submitResource()
}

const submitResource = async () => {
  try {
    await createResource(formData)
    ElMessage.success('创建成功')
    dialogVisible.value = false
    hasSelectedFile.value = false
    fetchData()
  } catch (e: any) { ElMessage.error(e.message || '操作失败') }
}

const handleDelete = async (row: any) => {
  try {
    await ElMessageBox.confirm('确定要删除该资源吗？', '提示', { type: 'warning' })
    await deleteResource(row.id)
    ElMessage.success('删除成功')
    fetchData()
  } catch (e: any) { if (e !== 'cancel') ElMessage.error(e.message || '删除失败') }
}

const handleUploadSuccess = (response: any) => {
  formData.file_url = response.data.url
  ElMessage.success('文件上传成功')
  // 文件上传成功后，创建资源记录
  submitResource()
}

const handleUploadError = () => {
  ElMessage.error('上传失败')
}

onMounted(() => { fetchCategories(); fetchData() })
</script>

<style scoped lang="scss">
.resource-management {
  .toolbar { margin-bottom: 20px; }
  .pagination { margin-top: 20px; display: flex; justify-content: flex-end; }
}
</style>