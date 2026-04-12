<template>
  <div class="scheduling-container">
    <!-- 页面标题 -->
    <div class="page-header">
      <h2>智能排课</h2>
      <div class="header-actions">
        <a-button @click="loadPlans">
          <template #icon><ReloadOutlined /></template>
          刷新
        </a-button>
        <a-button type="primary" @click="showCreateModal = true">
          <template #icon><PlusOutlined /></template>
          新建排课计划
        </a-button>
      </div>
    </div>

    <!-- 筛选条件 -->
    <a-card class="filter-card">
      <a-form layout="inline" :model="filterForm">
        <a-form-item label="学年">
          <a-select
            v-model:value="filterForm.academic_year"
            :options="ACADEMIC_YEAR_OPTIONS"
            placeholder="选择学年"
            style="width: 150px"
            allow-clear
            @change="loadPlans"
          />
        </a-form-item>
        <a-form-item label="学期">
          <a-select
            v-model:value="filterForm.semester"
            :options="SEMESTER_OPTIONS"
            placeholder="选择学期"
            style="width: 120px"
            allow-clear
            @change="loadPlans"
          />
        </a-form-item>
        <a-form-item label="状态">
          <a-select
            v-model:value="filterForm.status"
            :options="STATUS_OPTIONS"
            placeholder="选择状态"
            style="width: 120px"
            allow-clear
            @change="loadPlans"
          />
        </a-form-item>
      </a-form>
    </a-card>

    <!-- 排课计划列表 -->
    <a-card title="排课计划" class="plans-card">
      <template #extra>
        <span class="total-count">共 {{ plans.length }} 个计划</span>
      </template>
      <a-table
        :columns="planColumns"
        :data-source="plans"
        :loading="loading"
        :pagination="pagination"
        @change="handleTableChange"
        row-key="id"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'name'">
            <a @click="viewPlanDetail(record)">{{ record.name }}</a>
          </template>
          <template v-else-if="column.key === 'status'">
            <a-tag :color="getStatusColor(record.status)">
              {{ getStatusLabel(record.status) }}
            </a-tag>
          </template>
          <template v-else-if="column.key === 'score'">
            <a-progress
              :percent="record.score"
              size="small"
              :status="record.score >= 90 ? 'success' : record.score >= 70 ? 'normal' : 'exception'"
            />
          </template>
          <template v-else-if="column.key === 'action'">
            <a-space>
              <a @click="viewPlanDetail(record)">查看</a>
              <a-divider type="vertical" />
              <a-dropdown>
                <a>更多</a>
                <template #overlay>
                  <a-menu>
                    <a-menu-item key="optimize" @click="handleOptimize(record)" v-if="record.status === 'draft'">
                      智能优化
                    </a-menu-item>
                    <a-menu-item key="conflicts" @click="checkConflicts(record)">
                      检测冲突
                    </a-menu-item>
                    <a-menu-item key="publish" @click="handlePublish(record)" v-if="record.status === 'optimized'">
                      发布计划
                    </a-menu-item>
                    <a-menu-divider />
                    <a-menu-item key="delete" danger @click="handleDelete(record)">
                      删除
                    </a-menu-item>
                  </a-menu>
                </template>
              </a-dropdown>
            </a-space>
          </template>
        </template>
      </a-table>
    </a-card>

    <!-- 课表视图 -->
    <a-card title="课表视图" class="schedule-card" v-if="currentPlan">
      <template #extra>
        <a-space>
          <a-select
            v-model:value="viewClassId"
            placeholder="选择班级"
            style="width: 120px"
            :options="classOptions"
            @change="loadScheduleTable"
          />
          <a-select
            v-model:value="viewTeacherId"
            placeholder="选择教师"
            style="width: 120px"
            :options="teacherOptions"
            @change="loadScheduleTable"
          />
        </a-space>
      </template>

      <div class="schedule-table">
        <table class=" timetable">
          <thead>
            <tr>
              <th class="time-column">时间</th>
              <th v-for="day in 5" :key="day">{{ getDayLabel(day) }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="period in 10" :key="period">
              <td class="time-column">{{ getPeriodLabel(period) }}</td>
              <td v-for="day in 5" :key="day">
                <div
                  v-for="(assignment, idx) in getScheduleCell(day, period)"
                  :key="idx"
                  class="course-cell"
                  :class="{ locked: assignment.is_locked }"
                  @click="editAssignment(assignment)"
                >
                  <div class="course-name">{{ assignment.course_name }}</div>
                  <div class="course-info">
                    {{ assignment.teacher_name }}
                    <span v-if="assignment.classroom_name"> · {{ assignment.classroom_name }}</span>
                  </div>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </a-card>

    <!-- 创建计划弹窗 -->
    <a-modal
      v-model:open="showCreateModal"
      title="新建排课计划"
      width="700px"
      @ok="handleCreatePlan"
      @cancel="showCreateModal = false"
    >
      <a-form
        ref="createFormRef"
        layout="vertical"
        :model="createForm"
      >
        <a-form-item label="计划名称" name="name" :rules="[{ required: true, message: '请输入计划名称' }]">
          <a-input v-model:value="createForm.name" placeholder="例如：2024-2025学年第一学期排课计划" />
        </a-form-item>
        <a-row :gutter="16">
          <a-col :span="12">
            <a-form-item label="学年" name="academic_year" :rules="[{ required: true, message: '请选择学年' }]">
              <a-select v-model:value="createForm.academic_year" :options="ACADEMIC_YEAR_OPTIONS" />
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="学期" name="semester" :rules="[{ required: true, message: '请选择学期' }]">
              <a-select v-model:value="createForm.semester" :options="SEMESTER_OPTIONS" />
            </a-form-item>
          </a-col>
        </a-row>
        <a-row :gutter="16">
          <a-col :span="12">
            <a-form-item label="开始日期" name="start_date" :rules="[{ required: true, message: '请选择开始日期' }]">
              <a-date-picker v-model:value="createForm.start_date" format="YYYY-MM-DD" style="width: 100%" />
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="结束日期" name="end_date" :rules="[{ required: true, message: '请选择结束日期' }]">
              <a-date-picker v-model:value="createForm.end_date" format="YYYY-MM-DD" style="width: 100%" />
            </a-form-item>
          </a-col>
        </a-row>
      </a-form>
    </a-modal>

    <!-- 冲突检测结果弹窗 -->
    <a-modal
      v-model:open="showConflictModal"
      title="冲突检测结果"
      width="600px"
      :footer="null"
    >
      <div v-if="conflictResult">
        <a-result
          :status="conflictResult.can_publish ? 'success' : 'warning'"
          :title="conflictResult.can_publish ? '无冲突' : '存在冲突'"
          :sub-title="`共检测到 ${conflictResult.total_conflicts} 个冲突`"
        >
          <template #extra>
            <a-list v-if="conflictResult.conflicts.length > 0" :data-source="conflictResult.conflicts">
              <template #renderItem="{ item }">
                <a-list-item>
                  <a-list-item-meta>
                    <template #title>
                      <a-tag :color="getSeverityColor(item.severity)">
                        {{ getSeverityLabel(item.severity) }}
                      </a-tag>
                      <a-tag>{{ getConflictTypeLabel(item.type) }}</a-tag>
                    </template>
                    <template #description>
                      {{ item.description }}
                      <div v-if="item.suggestion" class="suggestion">
                        建议：{{ item.suggestion }}
                      </div>
                    </template>
                  </a-list-item-meta>
                </a-list-item>
              </template>
            </a-list>
          </template>
        </a-result>
      </div>
    </a-modal>

    <!-- 课程分配编辑弹窗 -->
    <a-modal
      v-model:open="showAssignmentModal"
      title="编辑课程分配"
      @ok="handleSaveAssignment"
      @cancel="showAssignmentModal = false"
    >
      <a-form layout="vertical" v-if="currentAssignment">
        <a-form-item label="课程">
          {{ currentAssignment.course_name }}
        </a-form-item>
        <a-form-item label="教师">
          {{ currentAssignment.teacher_name }}
        </a-form-item>
        <a-form-item label="班级">
          {{ currentAssignment.class_name }}
        </a-form-item>
        <a-row :gutter="16">
          <a-col :span="12">
            <a-form-item label="星期" name="new_day">
              <a-select v-model:value="assignmentForm.new_day" :options="DAY_OPTIONS" />
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="节次" name="new_period">
              <a-select v-model:value="assignmentForm.new_period" :options="PERIOD_OPTIONS" />
            </a-form-item>
          </a-col>
        </a-row>
        <a-form-item label="教室" name="new_classroom_id">
          <a-select v-model:value="assignmentForm.new_classroom_id" :options="classroomOptions" placeholder="选择教室" allow-clear />
        </a-form-item>
      </a-form>
    </a-modal>

    <!-- 优化进度弹窗 -->
    <a-modal
      v-model:open="showOptimizeModal"
      title="智能优化中..."
      :footer="null"
      :maskClosable="false"
      :closable="false"
    >
      <a-progress :percent="optimizeProgress" status="active" />
      <p class="optimize-info">正在优化排课方案，请稍候...</p>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue';
import {
  ReloadOutlined,
  PlusOutlined,
} from '@ant-design/icons-vue';
import { message } from 'ant-design-vue';
import type { TableProps } from 'ant-design-vue';
import dayjs from 'dayjs';
import * as echarts from 'echarts';
import {
  getPlans,
  getPlan,
  createPlan,
  optimizePlan,
  detectConflicts,
  adjustAssignment,
  publishPlan,
  getScheduleTable,
  getClasses,
  getTeachers,
  getClassrooms,
  getDayLabel,
  getPeriodLabel,
  getStatusLabel,
  getStatusColor,
  getSeverityLabel,
  getSeverityColor,
  getConflictTypeLabel,
  getConflictTypeLabel as getConflictLabel,
  ACADEMIC_YEAR_OPTIONS,
  SEMESTER_OPTIONS,
  STATUS_OPTIONS,
  DAY_OPTIONS,
  PERIOD_OPTIONS,
} from '@/api/edu/scheduling';
import type { SchedulingPlan, CourseAssignment, Conflict, ScheduleTable } from '@/api/edu/scheduling';

// ============== Refs ==============

// ============== State ==============
const loading = ref(false);
const plans = ref<SchedulingPlan[]>([]);
const currentPlan = ref<SchedulingPlan | null>(null);
const scheduleTable = ref<ScheduleTable | null>(null);

const filterForm = reactive({
  academic_year: '2024-2025',
  semester: undefined,
  status: undefined,
});

const pagination = reactive({
  current: 1,
  pageSize: 10,
  total: 0,
});

const showCreateModal = ref(false);
const createForm = reactive({
  name: '',
  academic_year: '2024-2025',
  semester: '第一学期',
  start_date: null as any,
  end_date: null as any,
});

const showConflictModal = ref(false);
const conflictResult = ref<{
  total_conflicts: number;
  conflicts: Conflict[];
  can_publish: boolean;
} | null>(null);

const showAssignmentModal = ref(false);
const currentAssignment = ref<CourseAssignment | null>(null);
const assignmentForm = reactive({
  new_day: 1,
  new_period: 1,
  new_classroom_id: undefined as number | undefined,
});

const showOptimizeModal = ref(false);
const optimizeProgress = ref(0);

const viewClassId = ref<number | undefined>(undefined);
const viewTeacherId = ref<number | undefined>(undefined);

const classes = ref<{ id: number; name: string }[]>([]);
const teachers = ref<{ id: number; name: string }[]>([]);
const classrooms = ref<{ id: number; name: string }[]>([]);

const classOptions = computed(() =>
  classes.value.map(c => ({ value: c.id, label: c.name }))
);

const teacherOptions = computed(() =>
  teachers.value.map(t => ({ value: t.id, label: t.name }))
);

const classroomOptions = computed(() =>
  classrooms.value.map(c => ({ value: c.id, label: c.name }))
);

// ============== Columns ==============
const planColumns = [
  { title: '计划名称', key: 'name', width: 300 },
  { title: '学年', dataIndex: 'academic_year', width: 120 },
  { title: '学期', dataIndex: 'semester', width: 100 },
  { title: '状态', key: 'status', width: 100 },
  { title: '评分', key: 'score', width: 150 },
  { title: '课程数', dataIndex: 'assignments', width: 80 },
  { title: '操作', key: 'action', width: 150, fixed: 'right' },
];

// ============== Methods ==============
const loadPlans = async () => {
  loading.value = true;
  try {
    const response = await getPlans({
      academic_year: filterForm.academic_year || undefined,
      semester: filterForm.semester || undefined,
      status: filterForm.status || undefined,
      page: pagination.current,
      page_size: pagination.pageSize,
    });

    if (response.success && response.data) {
      plans.value = response.data.plans;
      pagination.total = response.data.pagination.total;
    }
  } catch (error) {
    console.error('加载排课计划失败:', error);
  } finally {
    loading.value = false;
  }
};

const viewPlanDetail = async (plan: SchedulingPlan) => {
  try {
    const response = await getPlan(plan.id);
    if (response.success && response.data) {
      currentPlan.value = response.data;
      await loadScheduleTable();
    }
  } catch (error) {
    console.error('加载计划详情失败:', error);
  }
};

const loadScheduleTable = async () => {
  if (!currentPlan.value) return;

  try {
    const response = await getScheduleTable(currentPlan.value.id, {
      class_id: viewClassId.value,
      teacher_id: viewTeacherId.value,
    });

    if (response.success && response.data) {
      scheduleTable.value = response.data;
    }
  } catch (error) {
    console.error('加载课表失败:', error);
  }
};

const loadReferenceData = async () => {
  try {
    const [classRes, teacherRes, classroomRes] = await Promise.all([
      getClasses(),
      getTeachers(),
      getClassrooms(),
    ]);

    if (classRes.success && classRes.data) {
      classes.value = classRes.data;
    }
    if (teacherRes.success && teacherRes.data) {
      teachers.value = teacherRes.data;
    }
    if (classroomRes.success && classroomRes.data) {
      classrooms.value = classroomRes.data;
    }
  } catch (error) {
    console.error('加载参考数据失败:', error);
  }
};

const handleCreatePlan = async () => {
  try {
    const response = await createPlan({
      name: createForm.name,
      academic_year: createForm.academic_year,
      semester: createForm.semester,
      start_date: createForm.start_date?.format('YYYY-MM-DD'),
      end_date: createForm.end_date?.format('YYYY-MM-DD'),
    });

    if (response.success) {
      message.success('创建成功');
      showCreateModal.value = false;
      loadPlans();
    }
  } catch (error) {
    console.error('创建失败:', error);
  }
};

const handleOptimize = async (plan: SchedulingPlan) => {
  showOptimizeModal.value = true;
  optimizeProgress.value = 0;

  // 模拟进度
  const interval = setInterval(() => {
    if (optimizeProgress.value < 90) {
      optimizeProgress.value += Math.random() * 10;
    }
  }, 500);

  try {
    const response = await optimizePlan(plan.id, {
      max_iterations: 1000,
      time_limit: 60,
    });

    clearInterval(interval);
    optimizeProgress.value = 100;

    if (response.success) {
      message.success('优化完成');
      loadPlans();
      if (currentPlan.value?.id === plan.id) {
        viewPlanDetail(plan);
      }
    }
  } catch (error) {
    console.error('优化失败:', error);
    message.error('优化失败');
  } finally {
    clearInterval(interval);
    setTimeout(() => {
      showOptimizeModal.value = false;
      optimizeProgress.value = 0;
    }, 1000);
  }
};

const checkConflicts = async (plan: SchedulingPlan) => {
  try {
    const response = await detectConflicts(plan.id);
    if (response.success && response.data) {
      conflictResult.value = response.data;
      showConflictModal.value = true;
    }
  } catch (error) {
    console.error('检测冲突失败:', error);
  }
};

const handlePublish = async (plan: SchedulingPlan) => {
  try {
    const response = await publishPlan(plan.id);
    if (response.success) {
      message.success('发布成功');
      loadPlans();
    }
  } catch (error: any) {
    message.error(error.message || '发布失败');
  }
};

const handleDelete = async (plan: SchedulingPlan) => {
  // 确认删除
  message.info('删除功能待实现');
};

const handleTableChange: TableProps['onChange'] = (pag) => {
  pagination.current = pag.current || 1;
  pagination.pageSize = pag.pageSize || 10;
  loadPlans();
};

const getScheduleCell = (day: number, period: number): CourseAssignment[] => {
  if (!scheduleTable.value?.grid) return [];
  return scheduleTable.value.grid[day]?.[period] || [];
};

const editAssignment = (assignment: CourseAssignment) => {
  currentAssignment.value = assignment;
  if (assignment.time_slot) {
    assignmentForm.new_day = assignment.time_slot.day_of_week;
    assignmentForm.new_period = assignment.time_slot.period;
  }
  assignmentForm.new_classroom_id = assignment.classroom_id;
  showAssignmentModal.value = true;
};

const handleSaveAssignment = async () => {
  if (!currentPlan.value || !currentAssignment.value) return;

  try {
    const response = await adjustAssignment(currentPlan.value.id, {
      assignment_id: currentAssignment.value.id,
      new_day: assignmentForm.new_day,
      new_period: assignmentForm.new_period,
      new_classroom_id: assignmentForm.new_classroom_id,
    });

    if (response.success) {
      message.success('调整成功');
      showAssignmentModal.value = false;
      loadScheduleTable();
    }
  } catch (error) {
    console.error('调整失败:', error);
  }
};

// ============== Lifecycle ==============
onMounted(() => {
  loadPlans();
  loadReferenceData();
});
</script>

<style scoped>
.scheduling-container {
  padding: 24px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.page-header h2 {
  margin: 0;
}

.header-actions {
  display: flex;
  gap: 12px;
}

.filter-card {
  margin-bottom: 16px;
}

.plans-card {
  margin-bottom: 16px;
}

.total-count {
  color: #999;
}

.schedule-card {
  margin-bottom: 16px;
}

.schedule-table {
  overflow-x: auto;
}

.timetable {
  width: 100%;
  border-collapse: collapse;
  table-layout: fixed;
}

.timetable th,
.timetable td {
  border: 1px solid #e8e8e8;
  padding: 8px;
  text-align: center;
  vertical-align: top;
}

.timetable th {
  background: #fafafa;
  font-weight: 500;
}

.time-column {
  width: 80px;
  background: #fafafa;
}

.course-cell {
  padding: 4px 8px;
  margin-bottom: 4px;
  background: #e6f7ff;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
  text-align: left;
}

.course-cell:hover {
  background: #bae7ff;
}

.course-cell.locked {
  background: #fff1b8;
  border: 1px dashed #faad14;
}

.course-name {
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.course-info {
  color: #666;
  font-size: 11px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.suggestion {
  margin-top: 4px;
  color: #1890ff;
  font-size: 12px;
}

.optimize-info {
  text-align: center;
  margin-top: 16px;
  color: #666;
}
</style>
