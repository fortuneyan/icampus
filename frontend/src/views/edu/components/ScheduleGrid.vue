<template>
  <div class="schedule-grid">
    <table class="timetable">
      <thead>
        <tr>
          <th class="time-header">时间</th>
          <th v-for="day in schedule.days" :key="day.day_index">
            {{ day.day_name }}
          </th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="periodIdx in 10" :key="periodIdx">
          <td class="time-cell">第{{ periodIdx }}节</td>
          <td
            v-for="day in schedule.days"
            :key="day.day_index"
            class="schedule-cell"
            :class="{ 'has-course': getCell(day, periodIdx).course_name }"
            @click="handleCellClick(day.day_index, periodIdx, getCell(day, periodIdx))"
            @dragover.prevent
            @drop="handleDrop($event, day.day_index, periodIdx)"
          >
            <div
              v-if="getCell(day, periodIdx).course_name"
              class="course-card"
              :class="{
                'is-locked': getCell(day, periodIdx).is_locked,
                'is-dragging': draggingId === getCell(day, periodIdx).result_id
              }"
              draggable="true"
              @dragstart="handleDragStart($event, getCell(day, periodIdx))"
              @dragend="handleDragEnd"
            >
              <div class="course-name">{{ getCell(day, periodIdx).course_name }}</div>
              <div class="course-info">
                <span>{{ getCell(day, periodIdx).teacher_name }}</span>
                <span v-if="getCell(day, periodIdx).room_name" class="room">
                  · {{ getCell(day, periodIdx).room_name }}
                </span>
              </div>
              <div class="lock-icon" v-if="getCell(day, periodIdx).is_locked">
                <el-icon><Lock /></el-icon>
              </div>
            </div>
            <div v-else class="empty-cell">
              <span class="add-hint">+</span>
            </div>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { Lock } from '@element-plus/icons-vue';
import type { ScheduleCell, ClassSchedule, TeacherSchedule } from '@/api/edu/scheduling';

interface Props {
  schedule: ClassSchedule | TeacherSchedule;
  type: 'class' | 'teacher';
}

const props = defineProps<Props>();

const emit = defineEmits<{
  (e: 'cell-click', data: { dayIndex: number; periodIndex: number; cell: ScheduleCell }): void;
  (e: 'drag-adjust', data: { resultId: string; newDayIndex: number; newPeriodIndex: number }): void;
}>();

const draggingId = ref<string | null>(null);

const getCell = (day: { periods: ScheduleCell[] }, periodIdx: number): ScheduleCell => {
  return day.periods[periodIdx - 1] || {
    course_name: '',
    teacher_name: '',
    room_name: '',
    is_locked: false,
    create_type: '',
  };
};

const handleCellClick = (dayIndex: number, periodIndex: number, cell: ScheduleCell) => {
  emit('cell-click', { dayIndex, periodIndex, cell });
};

const handleDragStart = (event: DragEvent, cell: ScheduleCell) => {
  if (!cell.result_id) {
    event.preventDefault();
    return;
  }
  draggingId.value = cell.result_id;
  event.dataTransfer?.setData('text/plain', JSON.stringify({
    resultId: cell.result_id,
    dayIndex: cell.course_id ? props.schedule.days.findIndex(d =>
      d.periods.some(p => p.result_id === cell.result_id)
    ) + 1 : 1,
    periodIndex: cell.course_id ? 1 : 1,
  }));
};

const handleDragEnd = () => {
  draggingId.value = null;
};

const handleDrop = (event: DragEvent, newDayIndex: number, newPeriodIndex: number) => {
  event.preventDefault();
  const data = event.dataTransfer?.getData('text/plain');
  if (!data) return;

  try {
    const parsed = JSON.parse(data);
    if (parsed.resultId) {
      emit('drag-adjust', {
        resultId: parsed.resultId,
        newDayIndex,
        newPeriodIndex,
      });
    }
  } catch (error) {
    console.error('Parse drag data error:', error);
  }
  draggingId.value = null;
};
</script>

<style scoped>
.schedule-grid {
  overflow-x: auto;
}

.timetable {
  width: 100%;
  border-collapse: collapse;
  table-layout: fixed;
}

.timetable th,
.timetable td {
  border: 1px solid #dcdfe6;
  padding: 8px;
  text-align: center;
  vertical-align: middle;
  min-height: 60px;
}

.time-header,
.time-cell {
  width: 80px;
  background: #f5f7fa;
  font-weight: 500;
  color: #606266;
}

.schedule-cell {
  background: #fff;
  cursor: pointer;
  transition: background-color 0.2s;
}

.schedule-cell:hover {
  background: #f5f7fa;
}

.schedule-cell.has-course {
  background: #ecf5ff;
}

.schedule-cell.has-course:hover {
  background: #d9ecff;
}

.course-card {
  position: relative;
  padding: 8px;
  background: #fff;
  border-radius: 4px;
  border-left: 3px solid #409eff;
  cursor: grab;
  text-align: left;
  font-size: 13px;
}

.course-card:active {
  cursor: grabbing;
}

.course-card.is-locked {
  background: #fdf6ec;
  border-left-color: #e6a23c;
}

.course-card.is-dragging {
  opacity: 0.5;
}

.course-name {
  font-weight: 600;
  color: #303133;
  margin-bottom: 4px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.course-info {
  color: #909399;
  font-size: 12px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.course-info .room {
  color: #c0c4cc;
}

.lock-icon {
  position: absolute;
  top: 4px;
  right: 4px;
  color: #e6a23c;
  font-size: 12px;
}

.empty-cell {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  min-height: 44px;
}

.add-hint {
  color: #c0c4cc;
  font-size: 20px;
  opacity: 0;
  transition: opacity 0.2s;
}

.schedule-cell:hover .add-hint {
  opacity: 1;
}
</style>
