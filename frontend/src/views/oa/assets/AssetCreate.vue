<template>
  <div class="asset-create">
    <el-card>
      <template #header>
        <div class="card-header">
          <el-page-header @back="handleBack" title="返回">
            <template #content>
              <span class="page-title">{{ isEdit ? '编辑资产' : '新增资产' }}</span>
            </template>
          </el-page-header>
        </div>
      </template>

      <el-form
        ref="formRef"
        :model="formData"
        :rules="formRules"
        label-width="120px"
        v-loading="pageLoading"
        style="max-width: 800px"
      >
        <el-divider content-position="left">基本信息</el-divider>

        <el-form-item label="资产名称" prop="name">
          <el-input v-model="formData.name" placeholder="请输入资产名称" maxlength="100" show-word-limit />
        </el-form-item>

        <el-form-item label="资产分类" prop="category_id">
          <el-select v-model="formData.category_id" placeholder="请选择资产分类" clearable style="width: 100%">
            <el-option
              v-for="cat in categoryList"
              :key="cat.id"
              :label="cat.name"
              :value="cat.id"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="资产编号" prop="asset_no">
          <el-input v-model="formData.asset_no" placeholder="自动生成或手动输入">
            <template #append>
              <el-button @click="generateAssetNo" :loading="generatingNo">自动生成</el-button>
            </template>
          </el-input>
        </el-form-item>

        <el-form-item label="条形码" prop="barcode">
          <el-input v-model="formData.barcode" placeholder="请输入条形码" />
        </el-form-item>

        <el-divider content-position="left">规格信息</el-divider>

        <el-form-item label="品牌" prop="brand">
          <el-input v-model="formData.brand" placeholder="请输入品牌" />
        </el-form-item>

        <el-form-item label="型号" prop="model">
          <el-input v-model="formData.model" placeholder="请输入型号" />
        </el-form-item>

        <el-form-item label="规格参数" prop="specifications">
          <el-input
            v-model="formData.specifications"
            type="textarea"
            :rows="4"
            placeholder="请输入规格参数（支持 Markdown 格式）"
          />
        </el-form-item>

        <el-divider content-position="left">采购信息</el-divider>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="购入日期" prop="purchase_date">
              <el-date-picker
                v-model="formData.purchase_date"
                type="date"
                placeholder="选择购入日期"
                value-format="YYYY-MM-DD"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="购入价格" prop="purchase_price">
              <el-input-number
                v-model="formData.purchase_price"
                :min="0"
                :precision="2"
                :step="100"
                placeholder="请输入价格"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item label="供应商" prop="supplier">
          <el-input v-model="formData.supplier" placeholder="请输入供应商" />
        </el-form-item>

        <el-form-item label="保修到期日" prop="warranty_expire_date">
          <el-date-picker
            v-model="formData.warranty_expire_date"
            type="date"
            placeholder="选择保修到期日"
            value-format="YYYY-MM-DD"
            style="width: 100%"
          />
        </el-form-item>

        <el-divider content-position="left">位置信息</el-divider>

        <el-form-item label="所在部门" prop="department_id">
          <el-select v-model="formData.department_id" placeholder="请选择所在部门" clearable style="width: 100%">
            <el-option
              v-for="dept in departmentList"
              :key="dept.id"
              :label="dept.name"
              :value="dept.id"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="存放位置" prop="location">
          <el-input v-model="formData.location" placeholder="请输入存放位置" />
        </el-form-item>

        <el-divider content-position="left">资产图片</el-divider>

        <el-form-item label="图片上传" prop="image_urls">
          <el-upload
            :auto-upload="false"
            :on-change="handleImageChange"
            :on-remove="handleImageRemove"
            :file-list="fileList"
            accept=".jpg,.jpeg,.png,.gif,.webp"
            list-type="picture-card"
            :limit="9"
          >
            <el-icon><Plus /></el-icon>
          </el-upload>
          <div class="form-tip">支持 jpg、png、gif、webp 格式，最多上传 9 张</div>
        </el-form-item>

        <el-form-item>
          <el-button type="primary" @click="handleSubmit" :loading="submitLoading">保存</el-button>
          <el-button @click="handleBack">取消</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import type { UploadFile } from 'element-plus'
import { assetApi, assetCategoryApi } from '@/api/oa/assets'
import { getAllDepartments } from '@/api/system/department'

const route = useRoute()
const router = useRouter()

const isEdit = computed(() => !!route.params.id)
const editId = computed(() => route.params.id as string)

const formRef = ref()
const pageLoading = ref(false)
const submitLoading = ref(false)
const generatingNo = ref(false)
const categoryList = ref<any[]>([])
const departmentList = ref<any[]>([])
const fileList = ref<UploadFile[]>([])

const formData = reactive({
  name: '',
  category_id: '',
  asset_no: '',
  barcode: '',
  brand: '',
  model: '',
  specifications: '',
  purchase_date: '',
  purchase_price: undefined as number | undefined,
  supplier: '',
  warranty_expire_date: '',
  department_id: '',
  location: '',
  image_urls: '' as string
})

const formRules = {
  name: [{ required: true, message: '请输入资产名称', trigger: 'blur' }],
  category_id: [{ required: true, message: '请选择资产分类', trigger: 'change' }]
}

// 加载分类列表
const loadCategories = async () => {
  try {
    const res = await assetCategoryApi.getList()
    categoryList.value = res.data?.list || []
  } catch (error) {
    console.error('加载分类失败', error)
  }
}

// 加载部门列表
const loadDepartments = async () => {
  try {
    const res = await getAllDepartments()
    departmentList.value = res.data || []
  } catch (error) {
    console.error('加载部门失败', error)
  }
}

// 自动生成资产编号
const generateAssetNo = async () => {
  generatingNo.value = true
  try {
    const now = new Date()
    const prefix = 'A'
    const dateStr = now.getFullYear().toString() +
      String(now.getMonth() + 1).padStart(2, '0') +
      String(now.getDate()).padStart(2, '0')
    const random = String(Math.floor(Math.random() * 10000)).padStart(4, '0')
    formData.asset_no = `${prefix}${dateStr}${random}`
  } catch (error) {
    ElMessage.error('生成编号失败')
  } finally {
    generatingNo.value = false
  }
}

// 图片上传处理
const handleImageChange = (file: UploadFile) => {
  // 预览模式下使用本地 URL
  if (file.url) {
    const urls = formData.image_urls ? JSON.parse(formData.image_urls) : []
    urls.push(file.url)
    formData.image_urls = JSON.stringify(urls)
  }
}

const handleImageRemove = (_file: UploadFile) => {
  // 简化处理：重新构建 image_urls
  const currentUrls: string[] = formData.image_urls ? JSON.parse(formData.image_urls) : []
  // 由于 el-upload 的 file-list 会自动管理，这里只需同步 formData
  const remainingUrls = fileList.value
    .filter(f => f.url)
    .map(f => f.url as string)
  formData.image_urls = JSON.stringify(remainingUrls)
}

// 加载编辑数据
const loadEditData = async () => {
  if (!editId.value) return
  pageLoading.value = true
  try {
    const res = await assetApi.getById(editId.value)
    const data = res.data || {}
    Object.assign(formData, {
      name: data.name || '',
      category_id: data.category_id || '',
      asset_no: data.asset_no || '',
      barcode: data.barcode || '',
      brand: data.brand || '',
      model: data.model || '',
      specifications: data.specifications || '',
      purchase_date: data.purchase_date || '',
      purchase_price: data.purchase_price || undefined,
      supplier: data.supplier || '',
      warranty_expire_date: data.warranty_expire_date || '',
      department_id: data.department_id || '',
      location: data.location || '',
      image_urls: data.image_urls || ''
    })

    // 解析已有图片
    if (data.image_urls) {
      let urls: string[] = []
      if (typeof data.image_urls === 'string') {
        try {
          urls = JSON.parse(data.image_urls)
        } catch {
          urls = []
        }
      } else if (Array.isArray(data.image_urls)) {
        urls = data.image_urls
      }
      fileList.value = urls.map((url, index) => ({
        name: `image_${index}`,
        url,
        uid: Date.now() + index
      } as UploadFile))
    }
  } catch (error) {
    ElMessage.error('加载资产数据失败')
  } finally {
    pageLoading.value = false
  }
}

// 提交表单
const handleSubmit = async () => {
  try {
    await formRef.value?.validate()
    submitLoading.value = true

    const submitData = { ...formData }

    if (isEdit.value) {
      await assetApi.update(editId.value, submitData)
      ElMessage.success('更新成功')
    } else {
      await assetApi.create(submitData)
      ElMessage.success('创建成功')
    }
    router.push('/oa/assets')
  } catch (error: any) {
    if (error !== false) {
      ElMessage.error(isEdit.value ? '更新失败' : '创建失败')
    }
  } finally {
    submitLoading.value = false
  }
}

const handleBack = () => {
  router.push('/oa/assets')
}

onMounted(() => {
  loadCategories()
  loadDepartments()
  if (isEdit.value) {
    loadEditData()
  }
})
</script>

<style scoped>
.asset-create {
  padding: 16px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.page-title {
  font-size: 16px;
  font-weight: 600;
}

.form-tip {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}
</style>
