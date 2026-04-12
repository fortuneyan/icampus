<template>
  <div class="dormitory-manager">
    <el-tabs v-model="activeSubTab">
      <el-tab-pane label="宿舍楼栋" name="buildings">
        <div class="toolbar">
          <el-button type="primary" @click="handleAddBuilding">
            <el-icon><Plus /></el-icon>
            添加楼栋
          </el-button>
        </div>
        
        <el-table :data="buildingList" v-loading="loading" stripe>
          <el-table-column prop="name" label="楼栋名称" width="150" />
          <el-table-column prop="building_no" label="楼栋编号" width="120" />
          <el-table-column prop="floor_count" label="楼层数" width="100" align="center" />
          <el-table-column prop="building_type" label="类型" width="100" align="center">
            <template #default="{ row }">
              <el-tag :type="row.building_type === 'male' ? 'primary' : 'warning'">
                {{ row.building_type === 'male' ? '男生楼' : '女生楼' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="status" label="状态" width="100" align="center">
            <template #default="{ row }">
              <el-tag :type="row.status === 'active' ? 'success' : 'info'">
                {{ row.status === 'active' ? '启用' : '禁用' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="120">
            <template #default="{ row }">
              <el-button type="primary" link size="small">查看房间</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>
      
      <el-tab-pane label="住宿分配" name="assignments">
        <div class="toolbar">
          <el-button type="primary" @click="handleAddAssignment">
            <el-icon><Plus /></el-icon>
            分配住宿
          </el-button>
        </div>
        
        <el-table :data="assignmentList" v-loading="loading" stripe>
          <el-table-column prop="student_id" label="学生ID" width="220" />
          <el-table-column prop="room_id" label="房间ID" width="220" />
          <el-table-column prop="bed_no" label="床位号" width="80" align="center" />
          <el-table-column prop="academic_year" label="学年" width="120" />
          <el-table-column prop="semester" label="学期" width="100" />
          <el-table-column prop="status" label="状态" width="100" align="center">
            <template #default="{ row }">
              <el-tag :type="row.status === 'active' ? 'success' : 'info'">
                {{ row.status === 'active' ? '在住' : '已退宿' }}
              </el-tag>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { Plus } from '@element-plus/icons-vue'
import {
  getDormitoryBuildings,
  createDormitoryBuilding,
  getDormitoryAssignments,
  createDormitoryAssignment
} from '@/api/extended'

const activeSubTab = ref('buildings')
const loading = ref(false)
const buildingList = ref<any[]>([])
const assignmentList = ref<any[]>([])

const loadBuildings = async () => {
  loading.value = true
  try {
    const res = await getDormitoryBuildings()
    if (res.code === 200) {
      buildingList.value = res.data?.items || []
    }
  } catch (error) {
    console.error('加载数据失败:', error)
  } finally {
    loading.value = false
  }
}

const loadAssignments = async () => {
  loading.value = true
  try {
    const res = await getDormitoryAssignments()
    if (res.code === 200) {
      assignmentList.value = res.data?.items || []
    }
  } catch (error) {
    console.error('加载数据失败:', error)
  } finally {
    loading.value = false
  }
}

const handleAddBuilding = () => {
  // TODO: 打开添加对话框
  console.log('添加楼栋')
}

const handleAddAssignment = () => {
  // TODO: 打开分配对话框
  console.log('分配住宿')
}

onMounted(() => {
  loadBuildings()
})
</script>

<style scoped lang="scss">
.dormitory-manager {
  .toolbar {
    margin-bottom: 16px;
  }
}
</style>
