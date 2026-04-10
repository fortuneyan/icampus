<template>
  <div class="research-project">
    <el-card>
      <div class="toolbar">
        <el-form :inline="true" :model="searchForm">
          <el-form-item label="状态">
            <el-select v-model="searchForm.status" placeholder="请选择" clearable>
              <el-option label="待审核" value="pending" />
              <el-option label="已提交" value="submitted" />
              <el-option label="已通过" value="approved" />
              <el-option label="已结题" value="completed" />
            </el-select>
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="handleSearch">搜索</el-button>
            <el-button type="success" @click="handleAdd">新增</el-button>
          </el-form-item>
        </el-form>
      </div>
      <el-table :data="tableData" v-loading="loading" stripe>
        <el-table-column prop="project_no" label="课题编号" width="120" />
        <el-table-column prop="title" label="课题名称" min-width="180" />
        <el-table-column prop="project_type" label="类型" width="100" />
        <el-table-column prop="status" label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">{{ getStatusText(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="start_date" label="开始日期" width="100" />
        <el-table-column prop="end_date" label="结束日期" width="100" />
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link @click="handleEdit(row)">编辑</el-button>
            <el-button v-if="row.status === 'pending'" type="success" link @click="handleSubmit(row)">提交</el-button>
            <el-button v-if="row.status === 'approved'" type="warning" link @click="handleComplete(row)">结题</el-button>
            <el-button type="danger" link @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
      <div class="pagination">
        <el-pagination v-model:current-page="pagination.page" v-model:page-size="pagination.pageSize" :total="pagination.total" :page-sizes="[10, 20, 50]" layout="total, sizes, prev, pager, next" @size-change="fetchData" @current-change="fetchData" />
      </div>
    </el-card>
    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="700px">
      <el-form ref="formRef" :model="formData" label-width="100px">
        <el-row :gutter="20">
          <el-col :span="12"><el-form-item label="课题编号"><el-input v-model="formData.project_no" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="课题名称"><el-input v-model="formData.title" /></el-form-item></el-col>
        </el-row>
        <el-form-item label="课题背景"><el-input v-model="formData.background" type="textarea" :rows="2" /></el-form-item>
        <el-form-item label="研究目标"><el-input v-model="formData.objectives" type="textarea" :rows="2" /></el-form-item>
        <el-form-item label="研究内容"><el-input v-model="formData.content" type="textarea" :rows="2" /></el-form-item>
        <el-form-item label="研究方法"><el-input v-model="formData.methods" type="textarea" :rows="2" /></el-form-item>
        <el-form-item label="预期成果"><el-input v-model="formData.expected_results" type="textarea" :rows="2" /></el-form-item>
        <el-row :gutter="20">
          <el-col :span="12"><el-form-item label="负责人ID"><el-input v-model="formData.leader_id" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="经费预算"><el-input v-model="formData.funding" /></el-form-item></el-col>
        </el-row>
        <el-form-item label="成员"><el-input v-model="formData.members" type="textarea" :rows="2" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmitForm">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { getResearchProjectList, createResearchProject, updateResearchProject, deleteResearchProject, submitResearchProject, completeResearchProject } from '@/api/edu/research'

const searchForm = reactive({ status: '' })
const pagination = reactive({ page: 1, pageSize: 20, total: 0 })
const tableData = ref<any[]>([])
const loading = ref(false)
const dialogVisible = ref(false)
const dialogTitle = ref('')
const formRef = ref()
const formData = reactive<any>({ id: '', leader_id: '', project_no: '', title: '', project_type: '', background: '', objectives: '', content: '', methods: '', expected_results: '', funding: '', members: '', status: 'pending' })

const getStatusText = (v: string) => ({ pending: '待审核', submitted: '已提交', approved: '已通过', rejected: '已拒绝', completed: '已结题' }[v] || v)
const getStatusType = (v: string) => ({ pending: 'info', submitted: 'warning', approved: 'success', rejected: 'danger', completed: 'success' }[v] || 'info')

const fetchData = async () => { loading.value = true; try { const res = await getResearchProjectList({ status: searchForm.status, page: pagination.page, page_size: pagination.pageSize }); if (res.data?.items) { tableData.value = res.data.items; pagination.total = res.data.total || 0 } } catch (e) { console.error(e) } finally { loading.value = false } }
const handleSearch = () => { pagination.page = 1; fetchData() }
const handleAdd = () => { dialogTitle.value = '新增教研课题'; Object.assign(formData, { id: '', leader_id: '', project_no: '', title: '', project_type: '', background: '', objectives: '', content: '', methods: '', expected_results: '', funding: '', members: '', status: 'pending' }); dialogVisible.value = true }
const handleEdit = (row: any) => { dialogTitle.value = '编辑教研课题'; Object.assign(formData, row); dialogVisible.value = true }
const handleDelete = async (row: any) => { try { await deleteResearchProject(row.id); ElMessage.success('删除成功'); fetchData() } catch (e) { console.error(e) } }
const handleSubmit = async (row: any) => { try { await submitResearchProject(row.id); ElMessage.success('提交成功'); fetchData() } catch (e) { console.error(e) } }
const handleComplete = async (row: any) => { try { await completeResearchProject(row.id); ElMessage.success('结题成功'); fetchData() } catch (e) { console.error(e) } }
const handleSubmitForm = async () => { try { if (formData.id) { await updateResearchProject(formData.id, formData); ElMessage.success('更新成功') } else { await createResearchProject(formData); ElMessage.success('创建成功') }; dialogVisible.value = false; fetchData() } catch (e) { console.error(e) } }

onMounted(() => { fetchData() })
</script>

<style scoped>.research-project { padding: 20px; }.pagination { margin-top: 20px; display: flex; justify-content: flex-end; }</style>