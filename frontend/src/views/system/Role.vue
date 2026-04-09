<template>
  <div class="role-management">
    <el-card>
      <div class="toolbar">
        <el-form :inline="true" :model="searchForm">
          <el-form-item label="关键词">
            <el-input v-model="searchForm.keyword" placeholder="角色名称" clearable />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="handleSearch">搜索</el-button>
            <el-button @click="handleReset">重置</el-button>
            <el-button type="success" @click="handleAdd">新增</el-button>
          </el-form-item>
        </el-form>
      </div>

      <el-table :data="tableData" v-loading="loading" stripe>
        <el-table-column prop="code" label="角色编码" width="120" />
        <el-table-column prop="name" label="角色名称" width="150" />
        <el-table-column prop="level" label="权限级别" width="100" />
        <el-table-column prop="data_scope" label="数据范围" width="120" />
        <el-table-column prop="description" label="描述" />
        <el-table-column prop="status" label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="row.status === 'active' ? 'success' : 'danger'">
              {{ row.status === 'active' ? '正常' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180" fixed="right">
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

    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="500px">
      <el-form ref="formRef" :model="formData" :rules="formRules" label-width="100px">
        <el-form-item label="角色编码" prop="code">
          <el-input v-model="formData.code" :disabled="!!formData.id" />
        </el-form-item>
        <el-form-item label="角色名称" prop="name">
          <el-input v-model="formData.name" />
        </el-form-item>
        <el-form-item label="权限级别" prop="level">
          <el-input-number v-model="formData.level" :min="1" :max="99" />
        </el-form-item>
        <el-form-item label="数据范围" prop="data_scope">
          <el-select v-model="formData.data_scope">
            <el-option label="全部数据" value="all" />
            <el-option label="本部门数据" value="dept" />
            <el-option label="仅本人数据" value="self" />
          </el-select>
        </el-form-item>
        <el-form-item label="描述" prop="description">
          <el-input v-model="formData.description" type="textarea" :rows="3" />
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
import { getRoleList, createRole, updateRole, deleteRole } from '@/api/system/role'

const loading = ref(false)
const tableData = ref([])
const searchForm = reactive({ keyword: '' })
const pagination = reactive({ page: 1, pageSize: 20, total: 0 })

const dialogVisible = ref(false)
const dialogTitle = ref('')
const formRef = ref<FormInstance>()
const formData = reactive<any>({ id: '', code: '', name: '', level: 1, data_scope: 'all', description: '', status: 'active' })

const formRules = {
  code: [{ required: true, message: '请输入角色编码', trigger: 'blur' }],
  name: [{ required: true, message: '请输入角色名称', trigger: 'blur' }]
}

const fetchData = async () => {
  loading.value = true
  try {
    const res = await getRoleList({ keyword: searchForm.keyword, page: pagination.page, page_size: pagination.pageSize })
    tableData.value = res.data.items
    pagination.total = res.data.total
  } catch (e) { console.error(e) }
  finally { loading.value = false }
}

const handleSearch = () => { pagination.page = 1; fetchData() }
const handleReset = () => { searchForm.keyword = ''; handleSearch() }

const handleAdd = () => {
  Object.assign(formData, { id: '', code: '', name: '', level: 1, data_scope: 'all', description: '', status: 'active' })
  dialogTitle.value = '新增角色'
  dialogVisible.value = true
}

const handleEdit = (row: any) => {
  Object.assign(formData, { ...row })
  dialogTitle.value = '编辑角色'
  dialogVisible.value = true
}

const handleSubmit = async () => {
  if (!formRef.value) return
  await formRef.value.validate()
  try {
    if (formData.id) { await updateRole(formData.id, formData); ElMessage.success('更新成功') }
    else { await createRole(formData); ElMessage.success('创建成功') }
    dialogVisible.value = false
    fetchData()
  } catch (e: any) { ElMessage.error(e.message || '操作失败') }
}

const handleDelete = async (row: any) => {
  try {
    await ElMessageBox.confirm('确定要删除该角色吗？', '提示', { type: 'warning' })
    await deleteRole(row.id)
    ElMessage.success('删除成功')
    fetchData()
  } catch (e: any) { if (e !== 'cancel') ElMessage.error(e.message || '删除失败') }
}

onMounted(() => { fetchData() })
</script>

<style scoped lang="scss">
.role-management {
  .toolbar { margin-bottom: 20px; }
  .pagination { margin-top: 20px; display: flex; justify-content: flex-end; }
}
</style>