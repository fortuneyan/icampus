<template>
  <div class="menu-management">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>菜单管理</span>
          <el-button type="primary" @click="handleAdd">
            <el-icon><Plus /></el-icon>
            新增菜单
          </el-button>
        </div>
      </template>

      <el-table
        :data="menuList"
        row-key="id"
        :tree-props="{ children: 'children', hasChildren: 'hasChildren' }"
        default-expand-all
        stripe
      >
        <el-table-column prop="title" label="菜单名称" width="200">
          <template #default="{ row }">
            <el-icon v-if="row.icon"><component :is="row.icon" /></el-icon>
            <span style="margin-left: 8px">{{ row.title }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="name" label="路由名称" width="150" />
        <el-table-column prop="path" label="路由路径" width="200" />
        <el-table-column prop="component" label="组件路径" min-width="200" />
        <el-table-column prop="sort_order" label="排序" width="80" align="center" />
        <el-table-column prop="visible" label="状态" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="row.visible ? 'success' : 'info'" size="small">
              {{ row.visible ? '显示' : '隐藏' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180" align="center" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link size="small" @click="handleEdit(row)">
              编辑
            </el-button>
            <el-button type="danger" link size="small" @click="handleDelete(row)">
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 新增/编辑对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogTitle"
      width="600px"
      @close="handleDialogClose"
    >
      <el-form
        ref="formRef"
        :model="formData"
        :rules="formRules"
        label-width="100px"
      >
        <el-form-item label="上级菜单" prop="parent_id">
          <el-tree-select
            v-model="formData.parent_id"
            :data="menuTreeData"
            :props="{ label: 'title', value: 'id', children: 'children' }"
            check-strictly
            clearable
            placeholder="请选择上级菜单"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="菜单名称" prop="title">
          <el-input v-model="formData.title" placeholder="请输入菜单名称" />
        </el-form-item>
        <el-form-item label="路由名称" prop="name">
          <el-input v-model="formData.name" placeholder="请输入路由名称" />
        </el-form-item>
        <el-form-item label="路由路径" prop="path">
          <el-input v-model="formData.path" placeholder="请输入路由路径" />
        </el-form-item>
        <el-form-item label="组件路径" prop="component">
          <el-input v-model="formData.component" placeholder="请输入组件路径" />
        </el-form-item>
        <el-form-item label="菜单图标" prop="icon">
          <el-input v-model="formData.icon" placeholder="请输入图标名称" />
        </el-form-item>
        <el-form-item label="排序" prop="sort_order">
          <el-input-number v-model="formData.sort_order" :min="0" :max="999" />
        </el-form-item>
        <el-form-item label="权限标识" prop="permission_code">
          <el-input v-model="formData.permission_code" placeholder="请输入权限标识" />
        </el-form-item>
        <el-form-item label="显示状态" prop="visible">
          <el-radio-group v-model="formData.visible">
            <el-radio :value="true">显示</el-radio>
            <el-radio :value="false">隐藏</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="启用状态" prop="enabled">
          <el-switch v-model="formData.enabled" />
        </el-form-item>
        <el-form-item label="缓存页面" prop="keep_alive">
          <el-switch v-model="formData.keep_alive" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitLoading" @click="handleSubmit">
          确定
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox, FormInstance } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import {
  getMenuTree,
  createMenu,
  updateMenu,
  deleteMenu
} from '@/api/system/role'

interface MenuItem {
  id: string
  parent_id?: string
  name: string
  title: string
  icon?: string
  path?: string
  component?: string
  sort_order: number
  visible: boolean
  enabled: boolean
  keep_alive: boolean
  permission_code?: string
  children?: MenuItem[]
}

const menuList = ref<MenuItem[]>([])
const menuTreeData = ref<MenuItem[]>([])
const dialogVisible = ref(false)
const dialogTitle = ref('')
const submitLoading = ref(false)
const formRef = ref<FormInstance>()
const isEdit = ref(false)
const currentId = ref('')

const formData = reactive({
  parent_id: undefined as string | undefined,
  name: '',
  title: '',
  icon: '',
  path: '',
  component: '',
  sort_order: 0,
  visible: true,
  enabled: true,
  keep_alive: true,
  permission_code: ''
})

const formRules = {
  title: [{ required: true, message: '请输入菜单名称', trigger: 'blur' }],
  name: [{ required: true, message: '请输入路由名称', trigger: 'blur' }]
}

// 加载菜单列表
const loadMenuList = async () => {
  try {
    const res = await getMenuTree()
    if (res.code === 200) {
      menuList.value = res.data || []
      // 生成树形选择器数据
      menuTreeData.value = [
        { id: '', title: '根菜单', name: '', sort_order: 0, visible: true, enabled: true, keep_alive: true, children: res.data || [] }
      ]
    }
  } catch (error) {
    console.error('加载菜单列表失败:', error)
  }
}

// 新增菜单
const handleAdd = () => {
  dialogTitle.value = '新增菜单'
  isEdit.value = false
  resetForm()
  dialogVisible.value = true
}

// 编辑菜单
const handleEdit = (row: MenuItem) => {
  dialogTitle.value = '编辑菜单'
  isEdit.value = true
  currentId.value = row.id
  Object.assign(formData, {
    parent_id: row.parent_id,
    name: row.name,
    title: row.title,
    icon: row.icon || '',
    path: row.path || '',
    component: row.component || '',
    sort_order: row.sort_order,
    visible: row.visible,
    enabled: row.enabled,
    keep_alive: row.keep_alive,
    permission_code: row.permission_code || ''
  })
  dialogVisible.value = true
}

// 删除菜单
const handleDelete = (row: MenuItem) => {
  ElMessageBox.confirm(`确定要删除菜单"${row.title}"吗？`, '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(async () => {
    try {
      await deleteMenu(row.id)
      ElMessage.success('删除成功')
      loadMenuList()
    } catch (error) {
      console.error('删除菜单失败:', error)
    }
  }).catch(() => {})
}

// 提交表单
const handleSubmit = async () => {
  if (!formRef.value) return
  
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    
    submitLoading.value = true
    try {
      const data = { ...formData }
      if (data.parent_id === '') {
        data.parent_id = undefined
      }
      
      if (isEdit.value) {
        await updateMenu(currentId.value, data)
        ElMessage.success('更新成功')
      } else {
        await createMenu(data)
        ElMessage.success('创建成功')
      }
      dialogVisible.value = false
      loadMenuList()
    } catch (error) {
      console.error('保存菜单失败:', error)
    } finally {
      submitLoading.value = false
    }
  })
}

// 重置表单
const resetForm = () => {
  Object.assign(formData, {
    parent_id: undefined,
    name: '',
    title: '',
    icon: '',
    path: '',
    component: '',
    sort_order: 0,
    visible: true,
    enabled: true,
    keep_alive: true,
    permission_code: ''
  })
  formRef.value?.resetFields()
}

// 对话框关闭
const handleDialogClose = () => {
  resetForm()
}

onMounted(() => {
  loadMenuList()
})
</script>

<style scoped lang="scss">
.menu-management {
  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
}
</style>
