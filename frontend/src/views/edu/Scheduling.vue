<template>
  <div class="scheduling-container">
    <!-- 页面标题 -->
    <div class="page-header">
      <h2>智能排课</h2>
      <div class="header-actions">
        <el-button @click="loadData">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
        <el-button type="primary" @click="showSemesterDialog = true">
          <el-icon><Plus /></el-icon>
          新建学期
        </el-button>
      </div>
    </div>

    <!-- 学期选择 -->
    <el-card class="filter-card" shadow="never">
      <el-form :inline="true" :model="filterForm">
        <el-form-item label="学期">
          <el-select v-model="filterForm.semesterId" placeholder="选择学期" style="width: 200px" @change="loadCycles">
            <el-option v-for="s in semesters" :key="s.id" :label="s.name" :value="s.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="周次组合">
          <div style="display: flex; gap: 8px; align-items: center;">
            <el-select v-model="filterForm.cycleId" placeholder="选择周次" style="width: 200px" @change="loadResults">
              <el-option v-for="c in cycles" :key="c.id" :label="`${c.start_date} ~ ${c.end_date}${c.is_current ? ' ★' : ''}`" :value="c.id" />
            </el-select>
            <el-button size="small" @click="showCycleDialog = true">
              <el-icon><Plus /></el-icon>
              新建
            </el-button>
          </div>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 主操作区 -->
    <el-card class="main-card" shadow="never">
      <template #header>
        <div class="card-header">
          <span>排课管理</span>
          <div class="header-actions">
            <el-button size="small" @click="showCalendarDialog = true">
              <el-icon><Calendar /></el-icon>
              日历映射
            </el-button>
            <el-button size="small" @click="showConstraintDialog = true">
              <el-icon><Setting /></el-icon>
              约束规则
            </el-button>
            <el-button size="small" @click="showEventDialog = true">
              <el-icon><Bell /></el-icon>
              批量事件
            </el-button>
            <el-button size="small" type="primary" @click="showPlanDialog = true">
              <el-icon><Plus /></el-icon>
              课程规划
            </el-button>
          </div>
        </div>
      </template>

      <!-- 标签页 -->
      <el-tabs v-model="activeTab" @tab-change="handleTabChange">
        <el-tab-pane label="班级课表" name="class">
          <div class="schedule-toolbar">
            <el-select v-model="viewClassId" placeholder="选择班级" style="width: 200px" @change="loadClassSchedule">
              <el-option v-for="c in classes" :key="c.id" :label="c.name" :value="c.id" />
            </el-select>
            <el-button @click="showManualAddDialog = true" type="primary" size="small">
              手动添加
            </el-button>
          </div>
          <ScheduleGrid
            v-if="classSchedule"
            :schedule="classSchedule"
            type="class"
            @cell-click="handleCellClick"
            @drag-adjust="handleDragAdjust"
          />
        </el-tab-pane>

        <el-tab-pane label="教师课表" name="teacher">
          <div class="schedule-toolbar">
            <el-select v-model="viewTeacherId" placeholder="选择教师" style="width: 200px" @change="loadTeacherSchedule">
              <el-option v-for="t in teachers" :key="t.id" :label="t.name" :value="t.id" />
            </el-select>
          </div>
          <ScheduleGrid
            v-if="teacherSchedule"
            :schedule="teacherSchedule"
            type="teacher"
            @cell-click="handleCellClick"
            @drag-adjust="handleDragAdjust"
          />
        </el-tab-pane>

        <el-tab-pane label="调课管理" name="patch">
          <div class="schedule-toolbar">
            <el-date-picker
              v-model="patchDate"
              type="date"
              placeholder="选择日期"
              format="YYYY-MM-DD"
              value-format="YYYY-MM-DD"
              @change="loadPatches"
            />
            <el-button @click="showPatchDialog = true" type="primary" size="small">
              添加调课
            </el-button>
          </div>
          <el-table :data="patches" stripe>
            <el-table-column prop="natural_date" label="日期" width="120" />
            <el-table-column prop="class_id" label="班级" width="150">
              <template #default="{ row }">
                {{ getClassName(row.class_id) }}
              </template>
            </el-table-column>
            <el-table-column prop="day_index" label="节次" width="80">
              <template #default="{ row }">
                第{{ row.period_index }}节
              </template>
            </el-table-column>
            <el-table-column prop="patch_type" label="类型" width="100">
              <template #default="{ row }">
                <el-tag :type="getPatchTypeColor(row.patch_type)" size="small">
                  {{ getPatchTypeLabel(row.patch_type) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="status" label="状态" width="80">
              <template #default="{ row }">
                <el-tag :type="row.status === 'active' ? 'success' : 'info'" size="small">
                  {{ row.status === 'active' ? '生效' : '已取消' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="reason" label="原因" />
            <el-table-column label="操作" width="120">
              <template #default="{ row }">
                <el-button v-if="row.status === 'active'" link type="danger" size="small" @click="cancelPatch(row.id)">
                  取消
                </el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>

        <el-tab-pane label="冲突检测" name="conflict">
          <div class="schedule-toolbar">
            <el-button @click="checkConflicts" type="warning" size="small">
              <el-icon><Search /></el-icon>
              检测冲突
            </el-button>
          </div>
          <el-table v-if="conflicts.length > 0" :data="conflicts" stripe>
            <el-table-column prop="conflict_type" label="类型" width="150">
              <template #default="{ row }">
                <el-tag :type="getConflictTypeColor(row.conflict_type)" size="small">
                  {{ getConflictTypeLabel(row.conflict_type) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="severity" label="严重程度" width="100">
              <template #default="{ row }">
                <el-tag :type="getSeverityColor(row.severity)" size="small">
                  {{ getSeverityLabel(row.severity) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="message" label="描述" />
          </el-table>
          <el-empty v-else-if="conflictChecked" description="未检测到冲突" />
        </el-tab-pane>
      </el-tabs>
    </el-card>

    <!-- 创建学期对话框 -->
    <el-dialog v-model="showSemesterDialog" title="创建学期" width="500px">
      <el-form :model="semesterForm" label-width="100px">
        <el-form-item label="学期名称">
          <el-input v-model="semesterForm.name" placeholder="例如：2024年秋季学期" />
        </el-form-item>
        <el-form-item label="学年">
          <el-input v-model="semesterForm.academic_year" placeholder="例如：2024-2025" />
        </el-form-item>
        <el-form-item label="学期">
          <el-select v-model="semesterForm.semester" style="width: 100%">
            <el-option :value="1" label="第一学期" />
            <el-option :value="2" label="第二学期" />
          </el-select>
        </el-form-item>
        <el-form-item label="开始日期">
          <el-date-picker v-model="semesterForm.start_date" type="date" format="YYYY-MM-DD" value-format="YYYY-MM-DD" style="width: 100%" />
        </el-form-item>
        <el-form-item label="结束日期">
          <el-date-picker v-model="semesterForm.end_date" type="date" format="YYYY-MM-DD" value-format="YYYY-MM-DD" style="width: 100%" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showSemesterDialog = false">取消</el-button>
        <el-button type="primary" @click="handleCreateSemester">确定</el-button>
      </template>
    </el-dialog>

    <!-- 创建周次组合对话框 -->
    <el-dialog v-model="showCycleDialog" title="创建周次组合" width="500px">
      <el-form :model="cycleForm" label-width="100px">
        <el-form-item label="组合ID">
          <el-input v-model="cycleForm.id" placeholder="例如：W01_04" />
        </el-form-item>
        <el-form-item label="开始日期">
          <el-date-picker v-model="cycleForm.start_date" type="date" format="YYYY-MM-DD" value-format="YYYY-MM-DD" style="width: 100%" />
        </el-form-item>
        <el-form-item label="结束日期">
          <el-date-picker v-model="cycleForm.end_date" type="date" format="YYYY-MM-DD" value-format="YYYY-MM-DD" style="width: 100%" />
        </el-form-item>
        <el-form-item label="设为当前">
          <el-switch v-model="cycleForm.is_current" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCycleDialog = false">取消</el-button>
        <el-button type="primary" @click="handleCreateCycle">确定</el-button>
      </template>
    </el-dialog>

    <!-- 日历映射对话框 -->
    <el-dialog v-model="showCalendarDialog" title="日历映射" width="600px">
      <el-form :model="calendarForm" label-width="120px">
        <el-form-item label="自然日期">
          <el-date-picker v-model="calendarForm.natural_date" type="date" format="YYYY-MM-DD" value-format="YYYY-MM-DD" style="width: 100%" />
        </el-form-item>
        <el-form-item label="执行星期">
          <el-select v-model="calendarForm.exec_day" style="width: 100%">
            <el-option v-for="d in DAY_OPTIONS" :key="d.value" :label="d.label" :value="d.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="是否工作日">
          <el-switch v-model="calendarForm.is_workday" />
        </el-form-item>
        <el-form-item label="是否放假">
          <el-switch v-model="calendarForm.is_holiday" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCalendarDialog = false">取消</el-button>
        <el-button type="primary" @click="handleCreateCalendarMap">确定</el-button>
      </template>
    </el-dialog>

    <!-- 课程规划对话框 -->
    <el-dialog v-model="showPlanDialog" title="课程规划" width="600px">
      <el-form :model="planForm" label-width="100px">
        <el-form-item label="班级">
          <el-select v-model="planForm.class_id" style="width: 100%">
            <el-option v-for="c in classes" :key="c.id" :label="c.name" :value="c.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="教师">
          <el-select v-model="planForm.teacher_id" style="width: 100%">
            <el-option v-for="t in teachers" :key="t.id" :label="t.name" :value="t.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="课程">
          <el-select v-model="planForm.course_id" style="width: 100%">
            <el-option v-for="c in filteredCourses" :key="c.id" :label="getCourseLabel(c)" :value="c.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="周次组合">
          <el-select v-model="planForm.cycle_id" style="width: 100%" placeholder="请选择周次组合">
            <el-option v-for="c in cycles" :key="c.id" :label="`${c.start_date} ~ ${c.end_date}${c.is_current ? ' ★' : ''}`" :value="c.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="总课时">
          <el-input-number v-model="planForm.total_hours" :min="1" :max="20" />
        </el-form-item>
        <el-form-item label="需要连排">
          <el-switch v-model="planForm.is_continuous" />
        </el-form-item>
        <el-form-item v-if="planForm.is_continuous" label="连排节数">
          <el-input-number v-model="planForm.continuous_length" :min="2" :max="4" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showPlanDialog = false">取消</el-button>
        <el-button type="primary" @click="handleCreatePlan">确定</el-button>
      </template>
    </el-dialog>

    <!-- 约束规则对话框 -->
    <el-dialog v-model="showConstraintDialog" title="约束规则" width="600px">
      <el-form :model="constraintForm" label-width="100px">
        <el-form-item label="约束名称">
          <el-input v-model="constraintForm.name" />
        </el-form-item>
        <el-form-item label="约束类型">
          <el-select v-model="constraintForm.constraint_type" style="width: 100%">
            <el-option v-for="t in CONSTRAINT_TYPE_OPTIONS" :key="t.value" :label="t.label" :value="t.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="constraintForm.description" type="textarea" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showConstraintDialog = false">取消</el-button>
        <el-button type="primary" @click="handleCreateConstraint">确定</el-button>
      </template>
    </el-dialog>

    <!-- 批量事件对话框 -->
    <el-dialog v-model="showEventDialog" title="批量事件" width="600px">
      <el-form :model="eventForm" label-width="100px">
        <el-form-item label="事件名称">
          <el-input v-model="eventForm.name" />
        </el-form-item>
        <el-form-item label="事件类型">
          <el-select v-model="eventForm.event_type" style="width: 100%">
            <el-option v-for="t in EVENT_TYPE_OPTIONS" :key="t.value" :label="t.label" :value="t.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="开始日期">
          <el-date-picker v-model="eventForm.start_date" type="date" format="YYYY-MM-DD" value-format="YYYY-MM-DD" style="width: 100%" />
        </el-form-item>
        <el-form-item label="结束日期">
          <el-date-picker v-model="eventForm.end_date" type="date" format="YYYY-MM-DD" value-format="YYYY-MM-DD" style="width: 100%" />
        </el-form-item>
        <el-form-item label="影响范围">
          <el-select v-model="eventForm.scope" style="width: 100%">
            <el-option value="all" label="全校" />
            <el-option value="grade" label="年级" />
            <el-option value="class" label="班级" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showEventDialog = false">取消</el-button>
        <el-button type="primary" @click="handleCreateEvent">确定</el-button>
      </template>
    </el-dialog>

    <!-- 手动添加排课对话框 -->
    <el-dialog v-model="showManualAddDialog" title="手动添加排课" width="500px">
      <el-form :model="manualForm" label-width="100px">
        <el-form-item label="班级">
          <el-select v-model="manualForm.class_id" style="width: 100%">
            <el-option v-for="c in classes" :key="c.id" :label="c.name" :value="c.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="教师">
          <el-select v-model="manualForm.teacher_id" style="width: 100%">
            <el-option v-for="t in teachers" :key="t.id" :label="t.name" :value="t.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="课程">
          <el-select v-model="manualForm.course_id" style="width: 100%">
            <el-option v-for="c in filteredCourses" :key="c.id" :label="getCourseLabel(c)" :value="c.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="周次组合">
          <el-select v-model="manualForm.cycle_id" style="width: 100%" placeholder="请选择周次组合">
            <el-option v-for="c in cycles" :key="c.id" :label="`${c.start_date} ~ ${c.end_date}${c.is_current ? ' ★' : ''}`" :value="c.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="教室">
          <el-select v-model="manualForm.room_id" style="width: 100%" clearable>
            <el-option v-for="r in classrooms" :key="r.id" :label="r.name" :value="r.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="星期">
          <el-select v-model="manualForm.day_index" style="width: 100%">
            <el-option v-for="d in DAY_OPTIONS" :key="d.value" :label="d.label" :value="d.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="节次">
          <el-select v-model="manualForm.period_index" style="width: 100%">
            <el-option v-for="p in PERIOD_OPTIONS" :key="p.value" :label="p.label" :value="p.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="锁定">
          <el-switch v-model="manualForm.is_locked" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showManualAddDialog = false">取消</el-button>
        <el-button type="primary" @click="handleManualAdd">确定</el-button>
      </template>
    </el-dialog>

    <!-- 调课对话框 -->
    <el-dialog v-model="showPatchDialog" title="添加调课" width="500px">
      <el-form :model="patchForm" label-width="100px">
        <el-form-item label="日期">
          <el-date-picker v-model="patchForm.natural_date" type="date" format="YYYY-MM-DD" value-format="YYYY-MM-DD" style="width: 100%" />
        </el-form-item>
        <el-form-item label="班级">
          <el-select v-model="patchForm.class_id" style="width: 100%">
            <el-option v-for="c in classes" :key="c.id" :label="c.name" :value="c.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="节次">
          <el-select v-model="patchForm.period_index" style="width: 100%">
            <el-option v-for="p in PERIOD_OPTIONS" :key="p.value" :label="p.label" :value="p.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="调课类型">
          <el-select v-model="patchForm.patch_type" style="width: 100%">
            <el-option v-for="t in PATCH_TYPE_OPTIONS" :key="t.value" :label="t.label" :value="t.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="代课教师" v-if="patchForm.patch_type === 'substitute'">
          <el-select v-model="patchForm.patch_teacher_id" style="width: 100%">
            <el-option v-for="t in teachers" :key="t.id" :label="t.name" :value="t.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="原因">
          <el-input v-model="patchForm.reason" type="textarea" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showPatchDialog = false">取消</el-button>
        <el-button type="primary" @click="handleCreatePatch">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch, onMounted } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import { Refresh, Plus, Calendar, Setting, Bell, Search } from '@element-plus/icons-vue';
import ScheduleGrid from './components/ScheduleGrid.vue';
import {
  getSemesters,
  createSemester,
  getCycles,
  createCycle,
  setCurrentCycle,
  getCalendarMaps,
  getCalendarMap,
  createCalendarMap,
  getResults,
  createResult,
  deleteResults,
  getPatches,
  createPatch,
  cancelPatch as cancelPatchApi,
  checkConflicts as checkConflictsApi,
  getClassSchedule,
  getTeacherSchedule,
  dragAdjust as dragAdjustApi,
  getPlans,
  createPlan,
  getConstraints,
  createConstraint,
  getEvents,
  createEvent,
  getClassesForScheduling,
  getCoursesForScheduling,
  getTeachersForScheduling,
  getClassroomsForScheduling,
  getDayLabel,
  getPeriodLabel,
  getStatusLabel,
  getStatusColor,
  getSeverityLabel,
  getSeverityColor,
  getConflictTypeLabel,
  DAY_OPTIONS,
  PERIOD_OPTIONS,
  CONSTRAINT_TYPE_OPTIONS,
  EVENT_TYPE_OPTIONS,
  PATCH_TYPE_OPTIONS,
} from '@/api/edu/scheduling';

import type {
  Semester, Cycle, CalendarMap, Plan, Result, Patch, Conflict,
  ClassSchedule, TeacherSchedule, ClassInfo, CourseInfo, TeacherInfo, ClassroomInfo, Constraint, Event
} from '@/api/edu/scheduling';

// 状态
const activeTab = ref('class');
const loading = ref(false);
const semesters = ref<Semester[]>([]);
const cycles = ref<Cycle[]>([]);
const classes = ref<ClassInfo[]>([]);
const courses = ref<CourseInfo[]>([]);
const teachers = ref<TeacherInfo[]>([]);
const classrooms = ref<ClassroomInfo[]>([]);
const patches = ref<Patch[]>([]);
const conflicts = ref<Conflict[]>([]);
const conflictChecked = ref(false);

const filterForm = reactive({
  semesterId: '',
  cycleId: '',
});

const viewClassId = ref('');
const viewTeacherId = ref('');
const patchDate = ref('');

const classSchedule = ref<ClassSchedule | null>(null);
const teacherSchedule = ref<TeacherSchedule | null>(null);

// 对话框状态
const showSemesterDialog = ref(false);
const showCycleDialog = ref(false);
const showCalendarDialog = ref(false);
const showPlanDialog = ref(false);
const showConstraintDialog = ref(false);
const showEventDialog = ref(false);
const showManualAddDialog = ref(false);
const showPatchDialog = ref(false);

// 表单数据
const semesterForm = reactive({
  name: '',
  academic_year: '',
  semester: 1,
  start_date: '',
  end_date: '',
});

const cycleForm = reactive({
  id: '',
  semester_id: '',
  start_date: '',
  end_date: '',
  is_current: true,
});

const calendarForm = reactive({
  natural_date: '',
  exec_day: 1,
  is_workday: true,
  is_holiday: false,
});

const planForm = reactive({
  class_id: '',
  teacher_id: '',
  course_id: '',
  total_hours: 1,
  is_continuous: false,
  continuous_length: 2,
  cycle_id: '',
});

const constraintForm = reactive({
  name: '',
  constraint_type: 'HARD',
  description: '',
});

const eventForm = reactive({
  name: '',
  event_type: 'sports_meet',
  start_date: '',
  end_date: '',
  scope: 'all',
});

const manualForm = reactive({
  class_id: '',
  teacher_id: '',
  course_id: '',
  room_id: '',
  day_index: 1,
  period_index: 1,
  is_locked: false,
  cycle_id: '',
});

const patchForm = reactive({
  natural_date: '',
  class_id: '',
  period_index: 1,
  patch_type: 'swap',
  patch_teacher_id: '',
  reason: '',
});

// 加载数据
const loadData = async () => {
  loading.value = true;
  try {
    await Promise.all([
      loadSemesters(),
      loadReferenceData(),
    ]);
  } finally {
    loading.value = false;
  }
};

const loadSemesters = async () => {
  try {
    const res = await getSemesters();
    if (res.code === 200 && res.data) {
      semesters.value = res.data.semesters || [];
      if (semesters.value.length > 0 && !filterForm.semesterId) {
        filterForm.semesterId = semesters.value[0].id;
        loadCycles();
      }
    }
  } catch (error) {
    console.error('加载学期失败:', error);
  }
};

const loadCycles = async () => {
  if (!filterForm.semesterId) return;
  try {
    const res = await getCycles(filterForm.semesterId);
    if (res.code === 200 && res.data) {
      cycles.value = res.data.cycles || [];
      if (cycles.value.length > 0) {
        filterForm.cycleId = cycles.value[0].id;
        loadResults();
      }
    }
  } catch (error) {
    console.error('加载周次组合失败:', error);
  }
};

const loadResults = async () => {
  if (!filterForm.cycleId) return;
  await loadClassSchedule();
};

const loadReferenceData = async () => {
  try {
    const [classRes, courseRes, teacherRes, classroomRes] = await Promise.all([
      getClassesForScheduling(),
      getCoursesForScheduling(),
      getTeachersForScheduling(),
      getClassroomsForScheduling(),
    ]);

    if (classRes.code === 200 && classRes.data) {
      classes.value = classRes.data.classes || [];
    }
    if (courseRes.code === 200 && courseRes.data) {
      courses.value = courseRes.data.courses || [];
    }
    if (teacherRes.code === 200 && teacherRes.data) {
      teachers.value = teacherRes.data.teachers || [];
    }
    if (classroomRes.code === 200 && classroomRes.data) {
      classrooms.value = classroomRes.data.classrooms || [];
    }
  } catch (error) {
    console.error('加载参考数据失败:', error);
  }
};

const loadClassSchedule = async () => {
  if (!filterForm.cycleId || !viewClassId.value) return;
  try {
    const res = await getClassSchedule({
      class_id: viewClassId.value,
      cycle_id: filterForm.cycleId,
    });
    if (res.code === 200 && res.data) {
      classSchedule.value = res.data;
    }
  } catch (error) {
    console.error('加载班级课表失败:', error);
  }
};

const loadTeacherSchedule = async () => {
  if (!filterForm.cycleId || !viewTeacherId.value) return;
  try {
    const res = await getTeacherSchedule({
      teacher_id: viewTeacherId.value,
      cycle_id: filterForm.cycleId,
    });
    if (res.code === 200 && res.data) {
      teacherSchedule.value = res.data;
    }
  } catch (error) {
    console.error('加载教师课表失败:', error);
  }
};

const loadPatches = async () => {
  if (!patchDate.value) return;
  try {
    const res = await getPatches({ natural_date: patchDate.value });
    if (res.code === 200 && res.data) {
      patches.value = res.data.patches || [];
    }
  } catch (error) {
    console.error('加载调课记录失败:', error);
  }
};

// 处理函数
const handleTabChange = (tab: string) => {
  if (tab === 'class' && viewClassId.value) {
    loadClassSchedule();
  } else if (tab === 'teacher' && viewTeacherId.value) {
    loadTeacherSchedule();
  } else if (tab === 'patch' && patchDate.value) {
    loadPatches();
  }
};

const handleCellClick = (data: { dayIndex: number; periodIndex: number; cell: any }) => {
  console.log('Cell clicked:', data);
};

const handleDragAdjust = async (data: { resultId: string; newDayIndex: number; newPeriodIndex: number }) => {
  try {
    const res = await dragAdjustApi({
      result_id: data.resultId,
      new_day_index: data.newDayIndex,
      new_period_index: data.newPeriodIndex,
      check_conflict: true,
    });
    if (res.code === 200 && res.data) {
      if (res.data.success) {
        ElMessage.success('调整成功');
        if (activeTab.value === 'class') {
          loadClassSchedule();
        } else if (activeTab.value === 'teacher') {
          loadTeacherSchedule();
        }
      } else {
        ElMessage.warning(res.data.message || '调整失败');
      }
    }
  } catch (error) {
    console.error('拖拽调整失败:', error);
    ElMessage.error('调整失败');
  }
};

const handleCreateSemester = async () => {
  try {
    const res = await createSemester(semesterForm);
    if (res.code === 200) {
      ElMessage.success('创建成功');
      showSemesterDialog.value = false;
      loadSemesters();
    }
  } catch (error) {
    console.error('创建学期失败:', error);
  }
};

const handleCreateCycle = async () => {
  if (!filterForm.semesterId) {
    ElMessage.warning('请先选择学期');
    return;
  }
  try {
    const res = await createCycle({
      ...cycleForm,
      semester_id: filterForm.semesterId,
    });
    if (res.code === 200) {
      ElMessage.success('创建成功');
      showCycleDialog.value = false;
      // 重置表单
      cycleForm.id = '';
      cycleForm.semester_id = filterForm.semesterId;
      cycleForm.start_date = '';
      cycleForm.end_date = '';
      cycleForm.is_current = true;
      loadCycles();
    }
  } catch (error) {
    console.error('创建周次组合失败:', error);
  }
};

const handleCreateCalendarMap = async () => {
  if (!filterForm.cycleId) {
    ElMessage.warning('请先选择周次组合');
    return;
  }
  try {
    const res = await createCalendarMap({
      ...calendarForm,
      cycle_id: filterForm.cycleId,
    });
    if (res.code === 200) {
      ElMessage.success('创建成功');
      showCalendarDialog.value = false;
    }
  } catch (error) {
    console.error('创建日历映射失败:', error);
  }
};

const handleCreatePlan = async () => {
  if (!planForm.cycle_id) {
    ElMessage.warning('请先选择周次组合');
    return;
  }
  try {
    const res = await createPlan(planForm);
    if (res.code === 200) {
      ElMessage.success('创建成功');
      showPlanDialog.value = false;
    }
  } catch (error) {
    console.error('创建课程规划失败:', error);
  }
};

const handleCreateConstraint = async () => {
  try {
    const res = await createConstraint(constraintForm);
    if (res.code === 200) {
      ElMessage.success('创建成功');
      showConstraintDialog.value = false;
    }
  } catch (error) {
    console.error('创建约束失败:', error);
  }
};

const handleCreateEvent = async () => {
  if (!filterForm.semesterId) {
    ElMessage.warning('请先选择学期');
    return;
  }
  try {
    const res = await createEvent({
      ...eventForm,
      semester_id: filterForm.semesterId,
    });
    if (res.code === 200) {
      ElMessage.success('创建成功');
      showEventDialog.value = false;
    }
  } catch (error) {
    console.error('创建事件失败:', error);
  }
};

const handleManualAdd = async () => {
  if (!manualForm.cycle_id) {
    ElMessage.warning('请先选择周次组合');
    return;
  }
  try {
    const res = await createResult({
      ...manualForm,
      room_id: manualForm.room_id || undefined,
      create_type: 'manual',
    });
    if (res.code === 200) {
      ElMessage.success('添加成功');
      showManualAddDialog.value = false;
      if (viewClassId.value) {
        loadClassSchedule();
      }
    }
  } catch (error) {
    console.error('手动添加排课失败:', error);
  }
};

const handleCreatePatch = async () => {
  try {
    const res = await createPatch({
      ...patchForm,
      day_index: 1, // 默认周一
    });
    if (res.code === 200) {
      ElMessage.success('添加成功');
      showPatchDialog.value = false;
      if (patchDate.value) {
        loadPatches();
      }
    }
  } catch (error) {
    console.error('创建调课失败:', error);
  }
};

const cancelPatch = async (patchId: string) => {
  try {
    await ElMessageBox.confirm('确定要取消这条调课吗?', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    });
    const res = await cancelPatchApi(patchId);
    if (res.code === 200) {
      ElMessage.success('取消成功');
      loadPatches();
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('取消调课失败:', error);
    }
  }
};

const checkConflicts = async () => {
  if (!filterForm.cycleId) {
    ElMessage.warning('请先选择周次组合');
    return;
  }
  try {
    const res = await checkConflictsApi({ cycle_id: filterForm.cycleId });
    if (res.code === 200 && res.data) {
      conflicts.value = res.data.conflicts || [];
      conflictChecked.value = true;
      if (conflicts.value.length === 0) {
        ElMessage.success('未检测到冲突');
      } else {
        ElMessage.warning(`检测到 ${conflicts.value.length} 个冲突`);
      }
    }
  } catch (error) {
    console.error('检测冲突失败:', error);
  }
};

// 辅助函数
const getClassName = (classId: string): string => {
  const cls = classes.value.find(c => c.id === classId);
  return cls?.name || classId;
};

const getPatchTypeColor = (type: string): string => {
  const colors: Record<string, string> = {
    swap: 'primary',
    substitute: 'warning',
    cancel: 'danger',
    self_study: 'info',
  };
  return colors[type] || 'info';
};

const getPatchTypeLabel = (type: string): string => {
  const labels: Record<string, string> = {
    swap: '换课',
    substitute: '代课',
    cancel: '停课',
    self_study: '转自习',
  };
  return labels[type] || type;
};

const getConflictTypeColor = (type: string): string => {
  const colors: Record<string, string> = {
    teacher_conflict: 'danger',
    class_conflict: 'warning',
    room_conflict: 'warning',
  };
  return colors[type] || 'info';
};

// 辅助函数：将年级级别数字转换为中文名称
const getGradeLevelName = (level: number): string => {
  const names: Record<number, string> = {
    7: '初一', 8: '初二', 9: '初三',
    10: '高一', 11: '高二', 12: '高三',
  };
  return names[level] || `年级${level}`;
};

// 辅助函数：获取课程显示标签（包含适用年级信息）
const getCourseLabel = (course: CourseInfo): string => {
  const base = `${course.name}（${course.code}）`;
  if (course.grade_levels && course.grade_levels.length > 0) {
    const grades = course.grade_levels.map(getGradeLevelName).join('、');
    return `${base} - 适用: ${grades}`;
  }
  return base;
};

// 计算属性：根据对话框中选择的班级年级过滤课程
const filteredCourses = computed(() => {
  // 从 planForm 或 manualForm 中获取当前选择的班级 ID
  const selectedClassId = planForm.class_id || manualForm.class_id;

  // 如果没有选择班级，返回所有课程
  if (!selectedClassId) {
    return courses.value;
  }

  // 找到选中的班级
  const selectedClass = classes.value.find(c => c.id === selectedClassId);
  if (!selectedClass || !selectedClass.grade_level) {
    return courses.value;  // 班级无年级信息，返回所有课程
  }

  const classGradeLevel = selectedClass.grade_level;

  // 过滤：只返回适用年级包含当前班级年级的课程，或未指定年级的课程
  return courses.value.filter(course => {
    // 如果课程未指定适用年级，显示
    if (!course.grade_levels || course.grade_levels.length === 0) {
      return true;
    }
    // 如果课程指定了适用年级，检查是否包含当前班级年级
    return course.grade_levels.includes(classGradeLevel);
  });
});

// 监听对话框打开，自动预设学期ID
watch(showCycleDialog, (newVal) => {
  if (newVal) {
    cycleForm.semester_id = filterForm.semesterId || '';
  }
});

// 初始化
onMounted(() => {
  loadData();
});
</script>

<style scoped>
.scheduling-container {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
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

.main-card {
  margin-bottom: 16px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.schedule-toolbar {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
}
</style>
