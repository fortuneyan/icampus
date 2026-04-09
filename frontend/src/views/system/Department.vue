<template>
  <div class="dept-management">
    <el-card>
      <div class="toolbar">
        <el-button type="success" @click="handleAdd">新增部门</el-button>
      </div>

      <el-table :data="tableData" v-loading="loading" row-key="id" default-expand-all :tree-props="{ children: 'children' }">
        <el-table-column prop="name" label="部门名称" width="200" />
        <el-table-column prop="code" label="部门编码" width="150" />
        <el-table-column prop="sort_order" label="排序" width="80" />
        <el-table-column prop="status" label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="row.status === 'active' ? 'success' : 'danger'">
              {{ row.status === 'active' ? '正常' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link @click="handleAddChild(row)">新增子部门</el-button>
            <el-button type="primary" link @click="handleEdit(row)">编辑</el-button>
            <el-button type="danger" link @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="500px">
      <el-form ref="formRef" :model="formData" :rules="formRules" label-width="100px">
        <el-form-item label="上级部门" prop="parent_id">
          <el-tree-select v-model="formData.parent_id" :data="treeData" :props="{ label: 'label', value: 'value', children: 'children' }" check-strictly placeholder="请选择上级部门" clearable />
        </el-form-item>
        <el-form-item label="部门名称" prop="name">
          <el-input v-model="formData.name" />
        </el-form-item>
        <el-form-item label="部门编码" prop="code">
          <el-input v-model="formData.code" />
        </el-form-item>
        <el-form-item label="排序" prop="sort_order">
          <el-input-number v-model="formData.sort_order" :min="0" />
        </el-form-item>
        <el-form-item label="联系电话" prop="phone">
          <el-input v-model="formData.phone" />
        </el-form-item>
        <el-form-item label="邮箱" prop="email">
          <el-input v-model="formData.email" />
        </el-form-item>
        <el-form-item label="描述" prop="description">
          <el-input v-model="formData.description" type="textarea" :rows="2" />
        </el-form-item>
        <el-form-item label="状态" prop="status">
          <el-select v-model="formData.status">
            <el-option label="正常" value="active" />
            <el-option label="禁用" value="inactive" />
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
import { getDepartmentTree, createDepartment, updateDepartment, deleteDepartment } from '@/api/system/department'

const loading = ref(false)
const tableData = ref([])
const treeData = ref([{ value: '', label: '顶级部门', children: [] }])
const searchForm = reactive({})

const dialogVisible = ref(false)
const dialogTitle = ref('')
const formRef = ref<FormInstance>()
const formData = reactive<any>({ id: '', parent_id: '', name: '', code: '', sort_order: 0, phone: '', email: '', description: '', status: 'active' })

const formRules = {
  name: [{ required: true, message: '请输入部门名称', trigger: 'blur' }]
}

const fetchData = async () => {
  loading.value = true
  try {
    const res = await getDepartmentTree()
    tableData.value = res.data || []
    treeData.value = [{ value: '', label: '顶级部门', children: res.data || [] }]
  } catch (e) { console.error(e) }
  finally { loading.value = false }
}

const handleAdd = () => {
  Object.assign(formData, { id: '', parent_id: '', name: '', code: '', sort_order: 0, phone: '', email: '', description: '', status: 'active' })
  dialogTitle.value = '新增部门'
  dialogVisible.value = true
}

const handleAddChild = (row: any) => {
  Object.assign(formData, { id: '', parent_id: row.id, name: '', code: '', sort_order: 0, phone: '', email: '', description: '', status: 'active' })
  dialogTitle.value = '新增子部门'
  dialogVisible.value = true
}

const handleEdit = (row: any) => {
  Object.assign(formData, { ...row, parent_id: row.parent_id || '' })
  dialogTitle.value = '编辑部门'
  dialogVisible.value = true
}

const handleSubmit = async () => {
  if (!formRef.value) return
  await formRef.value.validate()
  try {
    const data = { ...formData }
    if (!data.parent_id) delete data.parent_id
    if (formData.id) { await updateDepartment(formData.id, data); ElMessage.success('更新成功') }
    else { await createDepartment(data); ElMessage.success('创建成功') }
    dialogVisible.value = false
    fetchData()
  } catch (e: any) { ElMessage.error(e.message || '操作失败') }
}

const handleDelete = async (row: any) => {
  try {
    await ElMessageBox.confirm('确定要删除该部门吗？', '提示', { type: 'warning' })
    await deleteDepartment(row.id)
    ElMessage.success('删除成功')
    fetchData()
  } catch (e: any) { if (e !== 'cancel') ElMessage.error(e.message || '删除失败') }
}

onMounted(() => { fetchData() })
</script>

<style scoped lang="scss">
.dept-management {
  .toolbar { margin-bottom: 20px; }
}
</style>