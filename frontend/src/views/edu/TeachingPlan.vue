<template>
  <div class="teaching-plan">
    <el-card>
      <div class="toolbar">
        <el-form :inline="true" :model="searchForm">
          <el-form-item label="状态">
            <el-select v-model="searchForm.status" placeholder="请选择" clearable>
              <el-option label="草稿" value="draft" />
              <el-option label="已提交" value="submitted" />
              <el-option label="已审批" value="approved" />
              <el-option label="已拒绝" value="rejected" />
            </el-select>
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="handleSearch">搜索</el-button>
            <el-button type="success" @click="handleAdd">新增</el-button>
          </el-form-item>
        </el-form>
      </div>
      <el-table :data="tableData" v-loading="loading" stripe>
        <el-table-column prop="title" label="计划标题" min-width="150" />
        <el-table-column prop="academic_year" label="学年" width="100" />
        <el-table-column prop="semester" label="学期" width="80" />
        <el-table-column prop="status" label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">{{ getStatusText(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link @click="handleEdit(row)">编辑</el-button>
            <el-button v-if="row.status === 'draft'" type="success" link @click="handleSubmit(row)">提交</el-button>
            <el-button v-if="row.status === 'submitted'" type="warning" link @click="handleApprove(row)">审批</el-button>
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
        <el-form-item label="计划标题" prop="title"><el-input v-model="formData.title" /></el-form-item>
        <el-row :gutter="20">
          <el-col :span="12"><el-form-item label="教师ID"><el-input v-model="formData.teacher_id" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="课程ID"><el-input v-model="formData.course_id" /></el-form-item></el-col>
        </el-row>
        <el-form-item label="教学目标"><el-input v-model="formData.objectives" type="textarea" :rows="2" /></el-form-item>
        <el-form-item label="教学内容"><el-input v-model="formData.content" type="textarea" :rows="3" /></el-form-item>
        <el-form-item label="教学方法"><el-input v-model="formData.methodology" type="textarea" :rows="2" /></el-form-item>
        <el-row :gutter="20">
          <el-col :span="8"><el-form-item label="总课时"><el-input v-model="formData.total_periods" /></el-form-item></el-col>
          <el-col :span="8"><el-form-item label="学年"><el-input v-model="formData.academic_year" /></el-form-item></el-col>
          <el-col :span="8"><el-form-item label="学期"><el-input v-model="formData.semester" /></el-form-item></el-col>
        </el-row>
        <el-form-item label="备注"><el-input v-model="formData.remarks" type="textarea" :rows="2" /></el-form-item>
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
import { getTeachingPlanList, createTeachingPlan, updateTeachingPlan, deleteTeachingPlan, submitTeachingPlan, approveTeachingPlan } from '@/api/edu/teaching_plan'

const searchForm = reactive({ status: '' })
const pagination = reactive({ page: 1, pageSize: 20, total: 0 })
const tableData = ref<any[]>([])
const loading = ref(false)
const dialogVisible = ref(false)
const dialogTitle = ref('')
const formRef = ref()
const formData = reactive<any>({ id: '', teacher_id: '', course_id: '', title: '', objectives: '', content: '', methodology: '', total_periods: '', academic_year: '', semester: '', status: 'draft', remarks: '' })

const getStatusText = (v: string) => ({ draft: '草稿', submitted: '已提交', approved: '已审批', rejected: '已拒绝' }[v] || v)
const getStatusType = (v: string) => ({ draft: 'info', submitted: 'warning', approved: 'success', rejected: 'danger' }[v] || 'info')

const fetchData = async () => { loading.value = true; try { const res = await getTeachingPlanList({ status: searchForm.status, page: pagination.page, page_size: pagination.pageSize }); if (res.data?.items) { tableData.value = res.data.items; pagination.total = res.data.total || 0 } } catch (e) { console.error(e) } finally { loading.value = false } }
const handleSearch = () => { pagination.page = 1; fetchData() }
const handleAdd = () => { dialogTitle.value = '新增教学计划'; Object.assign(formData, { id: '', teacher_id: '', course_id: '', title: '', objectives: '', content: '', methodology: '', total_periods: '', academic_year: '', semester: '', status: 'draft', remarks: '' }); dialogVisible.value = true }
const handleEdit = (row: any) => { dialogTitle.value = '编辑教学计划'; Object.assign(formData, row); dialogVisible.value = true }
const handleDelete = async (row: any) => { try { await deleteTeachingPlan(row.id); ElMessage.success('删除成功'); fetchData() } catch (e) { console.error(e) } }
const handleSubmit = async (row: any) => { try { await submitTeachingPlan(row.id); ElMessage.success('提交成功'); fetchData() } catch (e) { console.error(e) } }
const handleApprove = async (row: any) => { try { await approveTeachingPlan(row.id, { approve: true, comment: '审批通过' }); ElMessage.success('审批成功'); fetchData() } catch (e) { console.error(e) } }
const handleSubmitForm = async () => { try { if (formData.id) { await updateTeachingPlan(formData.id, formData); ElMessage.success('更新成功') } else { await createTeachingPlan(formData); ElMessage.success('创建成功') }; dialogVisible.value = false; fetchData() } catch (e) { console.error(e) } }

onMounted(() => { fetchData() })
</script>

<style scoped>.teaching-plan { padding: 20px; }.pagination { margin-top: 20px; display: flex; justify-content: flex-end; }</style>