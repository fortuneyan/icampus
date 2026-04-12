<template>
  <div class="dictionary-management">
    <el-row :gutter="20">
      <!-- 左侧：字典类型列表 -->
      <el-col :span="8">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>字典类型</span>
              <el-button type="primary" size="small" @click="handleAddType">
                <el-icon><Plus /></el-icon>
                新增
              </el-button>
            </div>
          </template>
          
          <el-input
            v-model="typeKeyword"
            placeholder="搜索字典类型"
            prefix-icon="Search"
            clearable
            style="margin-bottom: 16px"
          />
          
          <el-scrollbar height="calc(100vh - 280px)">
            <el-menu
              :default-active="currentTypeId"
              @select="handleTypeSelect"
            >
              <el-menu-item
                v-for="item in filteredTypeList"
                :key="item.id"
                :index="item.id"
              >
                <span>{{ item.name }}</span>
                <span style="margin-left: auto; color: #999; font-size: 12px">
                  {{ item.code }}
                </span>
              </el-menu-item>
            </el-menu>
          </el-scrollbar>
        </el-card>
      </el-col>
      
      <!-- 右侧：字典项列表 -->
      <el-col :span="16">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>字典项管理</span>
              <el-button
                type="primary"
                :disabled="!currentTypeId"
                @click="handleAddItem"
              >
                <el-icon><Plus /></el-icon>
                新增字典项
              </el-button>
            </div>
          </template>
          
          <el-table :data="dictItemList" stripe>
            <el-table-column prop="label" label="标签" width="150" />
            <el-table-column prop="value" label="值" width="150" />
            <el-table-column prop="sort_order" label="排序" width="80" align="center" />
            <el-table-column prop="status" label="状态" width="100" align="center">
              <template #default="{ row }">
                <el-tag :type="row.status === 'active' ? 'success' : 'info'" size="small">
                  {{ row.status === 'active' ? '启用' : '禁用' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="remark" label="备注" min-width="150" />
            <el-table-column label="操作" width="120" align="center" fixed="right">
              <template #default="{ row }">
                <el-button type="primary" link size="small" @click="handleEditItem(row)">
                  编辑
                </el-button>
                <el-button type="danger" link size="small" @click="handleDeleteItem(row)">
                  删除
                </el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
    </el-row>

    <!-- 字典类型对话框 -->
    <el-dialog
      v-model="typeDialogVisible"
      :title="typeDialogTitle"
      width="500px"
      @close="handleTypeDialogClose"
    >
      <el-form
        ref="typeFormRef"
        :model="typeFormData"
        :rules="typeFormRules"
        label-width="100px"
      >
        <el-form-item label="字典名称" prop="name">
          <el-input v-model="typeFormData.name" placeholder="请输入字典名称" />
        </el-form-item>
        <el-form-item label="字典编码" prop="code">
          <el-input
            v-model="typeFormData.code"
            placeholder="请输入字典编码"
            :disabled="isTypeEdit"
          />
        </el-form-item>
        <el-form-item label="描述" prop="description">
          <el-input
            v-model="typeFormData.description"
            type="textarea"
            :rows="3"
            placeholder="请输入描述"
          />
        </el-form-item>
        <el-form-item label="状态" prop="status">
          <el-radio-group v-model="typeFormData.status">
            <el-radio label="active">启用</el-radio>
            <el-radio label="inactive">禁用</el-radio>
          </el-radio-group>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="typeDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="typeSubmitLoading" @click="handleTypeSubmit">
          确定
        </el-button>
      </template>
    </el-dialog>

    <!-- 字典项对话框 -->
    <el-dialog
      v-model="itemDialogVisible"
      :title="itemDialogTitle"
      width="500px"
      @close="handleItemDialogClose"
    >
      <el-form
        ref="itemFormRef"
        :model="itemFormData"
        :rules="itemFormRules"
        label-width="100px"
      >
        <el-form-item label="标签" prop="label">
          <el-input v-model="itemFormData.label" placeholder="请输入字典项标签" />
        </el-form-item>
        <el-form-item label="值" prop="value">
          <el-input v-model="itemFormData.value" placeholder="请输入字典项值" />
        </el-form-item>
        <el-form-item label="排序" prop="sort_order">
          <el-input-number v-model="itemFormData.sort_order" :min="0" :max="999" />
        </el-form-item>
        <el-form-item label="备注" prop="remark">
          <el-input
            v-model="itemFormData.remark"
            type="textarea"
            :rows="2"
            placeholder="请输入备注"
          />
        </el-form-item>
        <el-form-item label="状态" prop="status">
          <el-radio-group v-model="itemFormData.status">
            <el-radio label="active">启用</el-radio>
            <el-radio label="inactive">禁用</el-radio>
          </el-radio-group>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="itemDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="itemSubmitLoading" @click="handleItemSubmit">
          确定
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox, FormInstance } from 'element-plus'
import { Plus, Search } from '@element-plus/icons-vue'
import {
  getDictTypeList,
  createDictType,
  updateDictType,
  deleteDictType,
  getDictItems,
  createDictItem,
  updateDictItem,
  deleteDictItem,
  type DictTypeItem,
  type DictItem,
  type DictTypeForm,
  type DictItemForm
} from '@/api/system/dictionary'

// ==================== 字典类型 ====================
const typeKeyword = ref('')
const typeList = ref<DictTypeItem[]>([])
const currentTypeId = ref('')
const typeDialogVisible = ref(false)
const typeDialogTitle = ref('')
const typeSubmitLoading = ref(false)
const typeFormRef = ref<FormInstance>()
const isTypeEdit = ref(false)

const typeFormData = reactive<DictTypeForm & { status: string }>({
  name: '',
  code: '',
  description: '',
  status: 'active'
})

const typeFormRules = {
  name: [{ required: true, message: '请输入字典名称', trigger: 'blur' }],
  code: [{ required: true, message: '请输入字典编码', trigger: 'blur' }]
}

const filteredTypeList = computed(() => {
  if (!typeKeyword.value) return typeList.value
  return typeList.value.filter(
    item => item.name.includes(typeKeyword.value) || item.code.includes(typeKeyword.value)
  )
})

const loadTypeList = async () => {
  try {
    const res = await getDictTypeList()
    if (res.code === 200) {
      typeList.value = res.data?.items || []
      if (typeList.value.length > 0 && !currentTypeId.value) {
        currentTypeId.value = typeList.value[0].id
        loadItemList()
      }
    }
  } catch (error) {
    console.error('加载字典类型列表失败:', error)
  }
}

const handleAddType = () => {
  typeDialogTitle.value = '新增字典类型'
  isTypeEdit.value = false
  resetTypeForm()
  typeDialogVisible.value = true
}

const handleTypeSelect = (id: string) => {
  currentTypeId.value = id
  loadItemList()
}

const handleTypeSubmit = async () => {
  if (!typeFormRef.value) return
  
  await typeFormRef.value.validate(async (valid) => {
    if (!valid) return
    
    typeSubmitLoading.value = true
    try {
      if (isTypeEdit.value) {
        await updateDictType(currentTypeId.value, typeFormData)
        ElMessage.success('更新成功')
      } else {
        await createDictType(typeFormData)
        ElMessage.success('创建成功')
      }
      typeDialogVisible.value = false
      loadTypeList()
    } catch (error) {
      console.error('保存字典类型失败:', error)
    } finally {
      typeSubmitLoading.value = false
    }
  })
}

const resetTypeForm = () => {
  Object.assign(typeFormData, {
    name: '',
    code: '',
    description: '',
    status: 'active'
  })
  typeFormRef.value?.resetFields()
}

const handleTypeDialogClose = () => {
  resetTypeForm()
}

// ==================== 字典项 ====================
const dictItemList = ref<DictItem[]>([])
const itemDialogVisible = ref(false)
const itemDialogTitle = ref('')
const itemSubmitLoading = ref(false)
const itemFormRef = ref<FormInstance>()
const isItemEdit = ref(false)
const currentItemId = ref('')

const itemFormData = reactive<DictItemForm>({
  type_id: '',
  label: '',
  value: '',
  sort_order: 0,
  status: 'active',
  remark: ''
})

const itemFormRules = {
  label: [{ required: true, message: '请输入标签', trigger: 'blur' }],
  value: [{ required: true, message: '请输入值', trigger: 'blur' }]
}

const loadItemList = async () => {
  if (!currentTypeId.value) return
  
  try {
    const res = await getDictItems({ type_id: currentTypeId.value })
    if (res.code === 200) {
      dictItemList.value = res.data || []
    }
  } catch (error) {
    console.error('加载字典项列表失败:', error)
  }
}

const handleAddItem = () => {
  itemDialogTitle.value = '新增字典项'
  isItemEdit.value = false
  itemFormData.type_id = currentTypeId.value
  resetItemForm()
  itemDialogVisible.value = true
}

const handleEditItem = (row: DictItem) => {
  itemDialogTitle.value = '编辑字典项'
  isItemEdit.value = true
  currentItemId.value = row.id
  Object.assign(itemFormData, {
    type_id: row.type_id,
    label: row.label,
    value: row.value,
    sort_order: row.sort_order,
    status: row.status,
    remark: row.remark || ''
  })
  itemDialogVisible.value = true
}

const handleDeleteItem = (row: DictItem) => {
  ElMessageBox.confirm(`确定要删除字典项"${row.label}"吗？`, '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(async () => {
    try {
      await deleteDictItem(row.id)
      ElMessage.success('删除成功')
      loadItemList()
    } catch (error) {
      console.error('删除字典项失败:', error)
    }
  }).catch(() => {})
}

const handleItemSubmit = async () => {
  if (!itemFormRef.value) return
  
  await itemFormRef.value.validate(async (valid) => {
    if (!valid) return
    
    itemSubmitLoading.value = true
    try {
      if (isItemEdit.value) {
        await updateDictItem(currentItemId.value, itemFormData)
        ElMessage.success('更新成功')
      } else {
        await createDictItem(itemFormData)
        ElMessage.success('创建成功')
      }
      itemDialogVisible.value = false
      loadItemList()
    } catch (error) {
      console.error('保存字典项失败:', error)
    } finally {
      itemSubmitLoading.value = false
    }
  })
}

const resetItemForm = () => {
  Object.assign(itemFormData, {
    type_id: '',
    label: '',
    value: '',
    sort_order: 0,
    status: 'active',
    remark: ''
  })
  itemFormRef.value?.resetFields()
}

const handleItemDialogClose = () => {
  resetItemForm()
}

onMounted(() => {
  loadTypeList()
})
</script>

<style scoped lang="scss">
.dictionary-management {
  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
  
  .el-menu-item {
    display: flex;
    align-items: center;
  }
}
</style>
