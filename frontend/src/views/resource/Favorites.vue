<template>
  <div class="resource-favorites">
    <el-card>
      <div class="toolbar">
        <el-form :inline="true" :model="searchForm">
          <el-form-item label="资源类型">
            <el-select v-model="searchForm.resource_type" placeholder="请选择" clearable>
              <el-option label="视频" value="video" />
              <el-option label="文档" value="document" />
              <el-option label="图片" value="image" />
              <el-option label="课件" value="courseware" />
            </el-select>
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="handleSearch">搜索</el-button>
          </el-form-item>
        </el-form>
      </div>
      <el-table :data="tableData" v-loading="loading" stripe>
        <el-table-column prop="resource_name" label="资源名称" min-width="200" />
        <el-table-column prop="resource_type" label="类型" width="100">
          <template #default="{ row }">
            <el-tag>{{ getTypeText(row.resource_type) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="收藏时间" width="160">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="120" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link @click="handleView(row)">查看</el-button>
            <el-button type="danger" link @click="handleDelete(row)">取消</el-button>
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
import { ElMessage } from 'element-plus'
import { getFavorites, removeFavorite } from '@/api/resource/favorite'

const searchForm = reactive({ resource_type: '' })
const pagination = reactive({ page: 1, pageSize: 20, total: 0 })
const tableData = ref<any[]>([])
const loading = ref(false)

const getTypeText = (v: string) => ({ video: '视频', document: '文档', image: '图片', courseware: '课件' }[v] || v)

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

const fetchData = async () => { loading.value = true; try { const res = await getFavorites({ resource_type: searchForm.resource_type, page: pagination.page, page_size: pagination.pageSize }); if (res.data?.items) { tableData.value = res.data.items; pagination.total = res.data.total || 0 } } catch (e) { console.error(e) } finally { loading.value = false } }
const handleSearch = () => { pagination.page = 1; fetchData() }
const handleDelete = async (row: any) => { try { await removeFavorite(row.resource_id); ElMessage.success('取消收藏成功'); fetchData() } catch (e) { console.error(e) } }
const handleView = (row: any) => { window.open(`/resource/list?id=${row.resource_id}`) }

onMounted(() => { fetchData() })
</script>

<style scoped>.resource-favorites { padding: 20px; }.pagination { margin-top: 20px; display: flex; justify-content: flex-end; }</style>