<template>
  <div class="lesson-plan">
    <el-card>
      <div class="toolbar">
        <el-form :inline="true" :model="searchForm">
          <el-form-item label="状态">
            <el-select v-model="searchForm.status" placeholder="请选择" clearable>
              <el-option label="草稿" value="draft" />
              <el-option label="已提交" value="submitted" />
              <el-option label="已审批" value="approved" />
            </el-select>
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="handleSearch">搜索</el-button>
            <el-button type="success" @click="handleAdd">新增</el-button>
          </el-form-item>
        </el-form>
      </div>
      <el-table :data="tableData" v-loading="loading" stripe>
        <el-table-column prop="title" label="教案标题" min-width="150" />
        <el-table-column prop="lesson_type" label="课型" width="100" />
        <el-table-column prop="teaching_duration" label="课时" width="80" />
        <el-table-column prop="status" label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">{{ getStatusText(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link @click="handleEdit(row)">编辑</el-button>
            <el-button v-if="row.status === 'draft'" type="success" link @click="handleSubmit(row)">提交</el-button>
            <el-button type="danger" link @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
      <div class="pagination">
        <el-pagination v-model:current-page="pagination.page" v-model:page-size="pagination.pageSize" :total="pagination.total" :page-sizes="[10, 20, 50]" layout="total, sizes, prev, pager, next" @size-change="fetchData" @current-change="fetchData" />
      </div>
    </el-card>
    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="800px">
      <el-form ref="formRef" :model="formData" label-width="100px">
        <el-row :gutter="20">
          <el-col :span="12"><el-form-item label="教案标题"><el-input v-model="formData.title" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="课型"><el-input v-model="formData.lesson_type" /></el-form-item></el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12"><el-form-item label="教师ID"><el-input v-model="formData.teacher_id" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="课时"><el-input v-model="formData.teaching_duration" /></el-form-item></el-col>
        </el-row>
        <el-form-item label="教学目标"><el-input v-model="formData.objectives" type="textarea" :rows="2" /></el-form-item>
        <el-form-item label="重点"><el-input v-model="formData.key_points" type="textarea" :rows="2" /></el-form-item>
        <el-form-item label="难点"><el-input v-model="formData.difficult_points" type="textarea" :rows="2" /></el-form-item>
        <el-form-item label="教学步骤"><el-input v-model="formData.teaching_steps" type="textarea" :rows="4" /></el-form-item>
        <el-form-item label="作业"><el-input v-model="formData.homework" type="textarea" :rows="2" /></el-form-item>
        <el-form-item label="教学反思"><el-input v-model="formData.reflection" type="textarea" :rows="2" /></el-form-item>
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
import { getLessonPlanList, createLessonPlan, updateLessonPlan, deleteLessonPlan, submitLessonPlan } from '@/api/edu/lesson_plan'

const searchForm = reactive({ status: '' })
const pagination = reactive({ page: 1, pageSize: 20, total: 0 })
const tableData = ref<any[]>([])
const loading = ref(false)
const dialogVisible = ref(false)
const dialogTitle = ref('')
const formRef = ref()
const formData = reactive<any>({ id: '', teacher_id: '', course_id: '', title: '', lesson_type: '', teaching_duration: '', objectives: '', key_points: '', difficult_points: '', teaching_steps: '', homework: '', reflection: '', status: 'draft' })

const getStatusText = (v: string) => ({ draft: '草稿', submitted: '已提交', approved: '已审批' }[v] || v)
const getStatusType = (v: string) => ({ draft: 'info', submitted: 'warning', approved: 'success' }[v] || 'info')

const fetchData = async () => { loading.value = true; try { const res = await getLessonPlanList({ status: searchForm.status, page: pagination.page, page_size: pagination.pageSize }); if (res.data?.items) { tableData.value = res.data.items; pagination.total = res.data.total || 0 } } catch (e) { console.error(e) } finally { loading.value = false } }
const handleSearch = () => { pagination.page = 1; fetchData() }
const handleAdd = () => { dialogTitle.value = '新增教案'; Object.assign(formData, { id: '', teacher_id: '', course_id: '', title: '', lesson_type: '', teaching_duration: '', objectives: '', key_points: '', difficult_points: '', teaching_steps: '', homework: '', reflection: '', status: 'draft' }); dialogVisible.value = true }
const handleEdit = (row: any) => { dialogTitle.value = '编辑教案'; Object.assign(formData, row); dialogVisible.value = true }
const handleDelete = async (row: any) => { try { await deleteLessonPlan(row.id); ElMessage.success('删除成功'); fetchData() } catch (e) { console.error(e) } }
const handleSubmit = async (row: any) => { try { await submitLessonPlan(row.id); ElMessage.success('提交成功'); fetchData() } catch (e) { console.error(e) } }
const handleSubmitForm = async () => { try { if (formData.id) { await updateLessonPlan(formData.id, formData); ElMessage.success('更新成功') } else { await createLessonPlan(formData); ElMessage.success('创建成功') }; dialogVisible.value = false; fetchData() } catch (e) { console.error(e) } }

onMounted(() => { fetchData() })
</script>

<style scoped>.lesson-plan { padding: 20px; }.pagination { margin-top: 20px; display: flex; justify-content: flex-end; }</style>