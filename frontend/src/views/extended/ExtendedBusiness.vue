<template>
  <div class="extended-business">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>扩展业务管理</span>
        </div>
      </template>
      
      <el-tabs v-model="activeTab">
        <el-tab-pane label="宿舍管理" name="dormitory">
          <DormitoryManager />
        </el-tab-pane>
        <el-tab-pane label="图书管理" name="library">
          <LibraryManager />
        </el-tab-pane>
        <el-tab-pane label="一卡通" name="card">
          <CardManager />
        </el-tab-pane>
        <el-tab-pane label="奖助学金" name="scholarship">
          <ScholarshipManager />
        </el-tab-pane>
      </el-tabs>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import DormitoryManager from './DormitoryManager.vue'
import LibraryManager from './LibraryManager.vue'
import CardManager from './CardManager.vue'
import ScholarshipManager from './ScholarshipManager.vue'

const activeTab = ref('dormitory')
</script>

<style scoped lang="scss">
.extended-business {
  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
}
</style>
