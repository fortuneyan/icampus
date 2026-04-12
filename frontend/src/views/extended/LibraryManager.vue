<template>
  <div class="library-manager">
    <el-tabs v-model="activeSubTab">
      <el-tab-pane label="图书管理" name="books">
        <el-form :inline="true" :model="searchForm" class="search-form">
          <el-form-item label="关键词">
            <el-input v-model="searchForm.keyword" placeholder="书名/作者" clearable />
          </el-form-item>
          <el-form-item label="分类">
            <el-select v-model="searchForm.category" placeholder="请选择" clearable>
              <el-option label="文学" value="literature" />
              <el-option label="科学" value="science" />
              <el-option label="历史" value="history" />
            </el-select>
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="handleSearch">搜索</el-button>
            <el-button type="primary" @click="handleAddBook">
              <el-icon><Plus /></el-icon>
              添加图书
            </el-button>
          </el-form-item>
        </el-form>
        
        <el-table :data="bookList" v-loading="loading" stripe>
          <el-table-column prop="title" label="书名" min-width="200" />
          <el-table-column prop="author" label="作者" width="150" />
          <el-table-column prop="isbn" label="ISBN" width="150" />
          <el-table-column prop="category" label="分类" width="100" />
          <el-table-column prop="total_copies" label="总数" width="80" align="center" />
          <el-table-column prop="available_copies" label="可借" width="80" align="center">
            <template #default="{ row }">
              <span :style="{ color: row.available_copies > 0 ? '#67c23a' : '#f56c6c' }">
                {{ row.available_copies }}
              </span>
            </template>
          </el-table-column>
          <el-table-column prop="status" label="状态" width="100" align="center">
            <template #default="{ row }">
              <el-tag :type="row.status === 'active' ? 'success' : 'info'">
                {{ row.status === 'active' ? '在库' : '其他' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="120">
            <template #default="{ row }">
              <el-button type="primary" link size="small">编辑</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>
      
      <el-tab-pane label="借阅管理" name="borrows">
        <el-table :data="borrowList" v-loading="loading" stripe>
          <el-table-column prop="student_id" label="学号" width="150" />
          <el-table-column prop="book_id" label="图书ID" width="220" />
          <el-table-column prop="borrow_date" label="借阅日期" width="120" />
          <el-table-column prop="due_date" label="应还日期" width="120" />
          <el-table-column prop="return_date" label="实际归还" width="120" />
          <el-table-column prop="status" label="状态" width="100" align="center">
            <template #default="{ row }">
              <el-tag :type="getStatusType(row.status)">
                {{ getStatusText(row.status) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="120">
            <template #default="{ row }">
              <el-button
                v-if="row.status === 'borrowed'"
                type="success"
                link
                size="small"
                @click="handleReturn(row)"
              >
                归还
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import {
  getBooks,
  getBorrows,
  returnBook
} from '@/api/extended'

const activeSubTab = ref('books')
const loading = ref(false)
const searchForm = reactive({ keyword: '', category: '' })
const bookList = ref<any[]>([])
const borrowList = ref<any[]>([])

const loadBooks = async () => {
  loading.value = true
  try {
    const res = await getBooks({
      keyword: searchForm.keyword || undefined,
      category: searchForm.category || undefined
    })
    if (res.code === 200) {
      bookList.value = res.data?.items || []
    }
  } catch (error) {
    console.error('加载失败:', error)
  } finally {
    loading.value = false
  }
}

const loadBorrows = async () => {
  loading.value = true
  try {
    const res = await getBorrows()
    if (res.code === 200) {
      borrowList.value = res.data?.items || []
    }
  } catch (error) {
    console.error('加载失败:', error)
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  loadBooks()
}

const handleAddBook = () => {
  console.log('添加图书')
}

const handleReturn = async (row: any) => {
  try {
    await returnBook(row.id)
    ElMessage.success('归还成功')
    loadBorrows()
  } catch (error) {
    console.error('归还失败:', error)
  }
}

const getStatusText = (status: string) => {
  const map: Record<string, string> = {
    borrowed: '借阅中',
    returned: '已归还',
    overdue: '逾期'
  }
  return map[status] || status
}

const getStatusType = (status: string) => {
  const map: Record<string, string> = {
    borrowed: 'warning',
    returned: 'success',
    overdue: 'danger'
  }
  return map[status] || 'info'
}

onMounted(() => {
  loadBooks()
  loadBorrows()
})
</script>

<style scoped lang="scss">
.library-manager {
  .search-form {
    margin-bottom: 16px;
  }
}
</style>
