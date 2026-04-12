<template>
  <div class="card-manager">
    <el-tabs v-model="activeSubTab">
      <el-tab-pane label="校园卡" name="cards">
        <el-form :inline="true" :model="searchForm" class="search-form">
          <el-form-item label="卡号">
            <el-input v-model="searchForm.keyword" placeholder="请输入卡号" clearable />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="handleSearch">搜索</el-button>
            <el-button type="primary" @click="handleAddCard">
              <el-icon><Plus /></el-icon>
              办卡
            </el-button>
          </el-form-item>
        </el-form>
        
        <el-table :data="cardList" v-loading="loading" stripe>
          <el-table-column prop="card_no" label="卡号" width="150" />
          <el-table-column prop="student_id" label="关联学生" width="150" />
          <el-table-column prop="card_type" label="卡类型" width="100" align="center">
            <template #default="{ row }">
              <el-tag>{{ row.card_type === 'student' ? '学生卡' : '教师卡' }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="balance" label="余额(元)" width="100" align="center">
            <template #default="{ row }">
              <span :style="{ color: row.balance > 0 ? '#67c23a' : '#f56c6c' }">
                ¥{{ row.balance.toFixed(2) }}
              </span>
            </template>
          </el-table-column>
          <el-table-column prop="status" label="状态" width="100" align="center">
            <template #default="{ row }">
              <el-tag :type="getCardStatusType(row.status)">
                {{ getCardStatusText(row.status) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="issue_date" label="发卡日期" width="120" />
          <el-table-column label="操作" width="180">
            <template #default="{ row }">
              <el-button type="primary" link size="small" @click="handleRecharge(row)">
                充值
              </el-button>
              <el-button type="danger" link size="small" @click="handleLoss(row)">
                挂失
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>
      
      <el-tab-pane label="交易记录" name="transactions">
        <el-table :data="transactionList" v-loading="loading" stripe>
          <el-table-column prop="card_id" label="卡号" width="150" />
          <el-table-column prop="transaction_type" label="类型" width="100" align="center">
            <template #default="{ row }">
              <el-tag :type="row.transaction_type === 'recharge' ? 'success' : 'warning'">
                {{ row.transaction_type === 'recharge' ? '充值' : '消费' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="amount" label="金额(元)" width="100" align="center">
            <template #default="{ row }">
              <span :style="{ color: row.transaction_type === 'recharge' ? '#67c23a' : '#f56c6c' }">
                {{ row.transaction_type === 'recharge' ? '+' : '-' }}¥{{ Math.abs(row.amount).toFixed(2) }}
              </span>
            </template>
          </el-table-column>
          <el-table-column prop="balance_after" label="余额" width="100" align="center">
            <template #default="{ row }">
              ¥{{ row.balance_after.toFixed(2) }}
            </template>
          </el-table-column>
          <el-table-column prop="merchant_name" label="商户" width="150" />
          <el-table-column prop="location" label="地点" width="150" />
          <el-table-column prop="created_at" label="时间" width="180" />
        </el-table>
      </el-tab-pane>
      
      <el-tab-pane label="门禁记录" name="access">
        <el-table :data="accessList" v-loading="loading" stripe>
          <el-table-column prop="card_id" label="卡号" width="150" />
          <el-table-column prop="door_name" label="门禁点" width="150" />
          <el-table-column prop="location" label="位置" width="150" />
          <el-table-column prop="access_type" label="类型" width="100" align="center">
            <template #default="{ row }">
              <el-tag>{{ row.access_type === 'enter' ? '进入' : '离开' }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="access_result" label="结果" width="100" align="center">
            <template #default="{ row }">
              <el-tag :type="row.access_result === 'allow' ? 'success' : 'danger'">
                {{ row.access_result === 'allow' ? '通过' : '拒绝' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="created_at" label="时间" width="180" />
        </el-table>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { getCards, rechargeCard, getTransactions, getAccessRecords } from '@/api/extended'

const activeSubTab = ref('cards')
const loading = ref(false)
const searchForm = reactive({ keyword: '', card_type: '' })
const cardList = ref<any[]>([])
const transactionList = ref<any[]>([])
const accessList = ref<any[]>([])

const loadCards = async () => {
  loading.value = true
  try {
    const res = await getCards({ keyword: searchForm.keyword || undefined })
    if (res.code === 200) {
      cardList.value = res.data?.items || []
    }
  } catch (error) {
    console.error('加载失败:', error)
  } finally {
    loading.value = false
  }
}

const loadTransactions = async () => {
  loading.value = true
  try {
    const res = await getTransactions()
    if (res.code === 200) {
      transactionList.value = res.data?.items || []
    }
  } catch (error) {
    console.error('加载失败:', error)
  } finally {
    loading.value = false
  }
}

const loadAccess = async () => {
  loading.value = true
  try {
    const res = await getAccessRecords()
    if (res.code === 200) {
      accessList.value = res.data?.items || []
    }
  } catch (error) {
    console.error('加载失败:', error)
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  loadCards()
}

const handleAddCard = () => {
  console.log('办理新卡')
}

const handleRecharge = (row: any) => {
  console.log('充值', row.id)
}

const handleLoss = (row: any) => {
  console.log('挂失', row.id)
}

const getCardStatusText = (status: string) => {
  const map: Record<string, string> = {
    active: '正常',
    lost: '已挂失',
    disabled: '已禁用'
  }
  return map[status] || status
}

const getCardStatusType = (status: string) => {
  const map: Record<string, string> = {
    active: 'success',
    lost: 'warning',
    disabled: 'info'
  }
  return map[status] || 'info'
}

onMounted(() => {
  loadCards()
})
</script>

<style scoped lang="scss">
.card-manager {
  .search-form {
    margin-bottom: 16px;
  }
}
</style>
