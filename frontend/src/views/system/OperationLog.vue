<template>
  <div class="operation-log">
    <el-card>
      <div class="toolbar">
        <el-form :inline="true" :model="searchForm">
          <el-form-item label="模块">
            <el-select v-model="searchForm.module" placeholder="请选择" clearable>
              <el-option label="系统管理" value="system" />
              <el-option label="教务管理" value="edu" />
              <el-option label="资源管理" value="resource" />
            </el-select>
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="handleSearch">搜索</el-button>
          </el-form-item>
        </el-form>
      </div>
      <el-table :data="tableData" v-loading="loading" stripe>
        <el-table-column prop="username" label="操作人" width="100" />
        <el-table-column prop="module" label="模块" width="100" />
        <el-table-column prop="action" label="操作" width="100" />
        <el-table-column prop="operation" label="操作描述" min-width="150" />
        <el-table-column prop="method" label="方法" width="60" />
        <el-table-column prop="path" label="路径" min-width="150" />
        <el-table-column prop="ip_address" label="IP" width="120" />
        <el-table-column prop="status_code" label="状态" width="60" />
        <el-table-column prop="created_at" label="时间" width="160">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
      </el-table>
      <div class="pagination">
        <el-pagination v-model:current-page="pagination.page" v-model:page-size="pagination.pageSize" :total="pagination.total" :page-sizes="[10, 20, 50]" layout="total, sizes, prev, pager, next" @size-change="fetchData" @current-change="fetchData" />
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { getOperationLogs } from '@/api/system/log'

const searchForm = reactive({ module: '' })
const pagination = reactive({ page: 1, pageSize: 20, total: 0 })
const tableData = ref<any[]>([])
const loading = ref(false)

const fetchData = async () => { loading.value = true; try { const res = await getOperationLogs({ module: searchForm.module, page: pagination.page, page_size: pagination.pageSize }); if (res.data?.items) { tableData.value = res.data.items; pagination.total = res.data.total || 0 } } catch (e) { console.error(e) } finally { loading.value = false } }

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

const handleSearch = () => { pagination.page = 1; fetchData() }

onMounted(() => { fetchData() })
</script>

<style scoped>.operation-log { padding: 20px; }.pagination { margin-top: 20px; display: flex; justify-content: flex-end; }</style>