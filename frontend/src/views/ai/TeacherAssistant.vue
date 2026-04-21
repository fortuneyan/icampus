<template>
  <div class="teacher-assistant">
    <el-row :gutter="20">
      <!-- 左侧：教案管理 + 题库预览 -->
      <el-col :span="14">
        <!-- 教案列表 -->
        <el-card class="mb-16">
          <template #header>
            <div class="card-header">
              <span>教案管理</span>
              <el-button type="primary" size="small" @click="switchToTab('generate')">
                <el-icon><Service /></el-icon>
                AI生成教案
              </el-button>
            </div>
          </template>

          <el-form :inline="true" :model="searchForm" class="search-form">
            <el-form-item label="关键词">
              <el-input v-model="searchForm.keyword" placeholder="教案标题" clearable />
            </el-form-item>
            <el-form-item label="年级">
              <el-input v-model="searchForm.grade_level" placeholder="如：高一" clearable />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="handleSearch">搜索</el-button>
              <el-button @click="handleReset">重置</el-button>
            </el-form-item>
          </el-form>

          <el-table :data="planList" v-loading="loading" stripe>
            <el-table-column prop="title" label="教案标题" min-width="150" />
            <el-table-column prop="course_name" label="课程" width="120" />
            <el-table-column prop="grade_level" label="年级" width="80" />
            <el-table-column prop="ai_generated" label="AI生成" width="80" align="center">
              <template #default="{ row }">
                <el-tag :type="row.ai_generated ? 'success' : 'info'" size="small">
                  {{ row.ai_generated ? '是' : '否' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="status" label="状态" width="80" align="center">
              <template #default="{ row }">
                <el-tag :type="row.status === 'published' ? 'success' : 'info'" size="small">
                  {{ row.status === 'published' ? '已发布' : '草稿' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="150" fixed="right">
              <template #default="{ row }">
                <el-button type="primary" link size="small" @click="handleView(row)">查看</el-button>
                <el-button type="danger" link size="small" @click="handleDelete(row)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>

          <div class="pagination">
            <el-pagination
              v-model:current-page="pagination.page"
              v-model:page-size="pagination.pageSize"
              :total="pagination.total"
              :page-sizes="[10, 20, 50]"
              layout="total, sizes, prev, pager, next"
              @size-change="fetchPlans"
              @current-change="fetchPlans"
            />
          </div>
        </el-card>

        <!-- 生成的题目预览 -->
        <el-card v-if="generatedQuestionSet" class="question-preview-card">
          <template #header>
            <div class="card-header">
              <span>生成的题目</span>
              <div>
                <el-button type="success" size="small" @click="handleSaveAllQuestions" :loading="savingAll">
                  保存全部 ({{ generatedQuestionSet.questions.length }})
                </el-button>
                <el-button type="danger" size="small" @click="generatedQuestionSet = null">清空</el-button>
              </div>
            </div>
          </template>

          <div class="question-set-info">
            <el-descriptions :column="3" size="small">
              <el-descriptions-item label="课程">{{ generatedQuestionSet.course_name }}</el-descriptions-item>
              <el-descriptions-item label="年级">{{ generatedQuestionSet.grade_level }}</el-descriptions-item>
              <el-descriptions-item label="课题">{{ generatedQuestionSet.topic }}</el-descriptions-item>
              <el-descriptions-item label="总题数">{{ generatedQuestionSet.total_count }}</el-descriptions-item>
              <el-descriptions-item label="已保存">{{ generatedQuestionSet.saved_count || 0 }}</el-descriptions-item>
            </el-descriptions>
          </div>

          <div class="question-list">
            <el-card
              v-for="(q, index) in generatedQuestionSet.questions"
              :key="index"
              class="question-item"
              :class="{ 'is-saved': q.saved }"
            >
              <template #header>
                <div class="question-header">
                  <span class="question-number">{{ index + 1 }}.</span>
                  <el-tag size="small" :type="getQuestionTypeTag(q.question_type)">
                    {{ getQuestionTypeLabel(q.question_type) }}
                  </el-tag>
                  <el-tag size="small" type="info">难度 {{ q.difficulty }}</el-tag>
                  <el-tag size="small" type="warning">{{ q.score }}分</el-tag>
                  <el-button
                    v-if="!q.saved"
                    type="primary"
                    link
                    size="small"
                    @click="handleSaveQuestion(index)"
                  >
                    保存
                  </el-button>
                  <el-tag v-else type="success" size="small">已保存</el-tag>
                </div>
              </template>

              <div class="question-content">
                <p class="question-text">{{ q.content }}</p>

                <!-- 选择题选项 -->
                <div v-if="q.options && q.options.length > 0" class="question-options">
                  <div
                    v-for="opt in q.options"
                    :key="opt.label"
                    class="option-item"
                    :class="{ 'is-correct': opt.is_correct }"
                  >
                    <span class="option-label">{{ opt.label }}.</span>
                    <span class="option-content">{{ opt.content }}</span>
                    <el-tag v-if="opt.is_correct" type="success" size="small" class="correct-tag">正确答案</el-tag>
                  </div>
                </div>

                <!-- 答案和解析 -->
                <div v-if="q.answer" class="question-answer">
                  <el-collapse>
                    <el-collapse-item title="查看答案" name="answer">
                      <div class="answer-content">{{ q.answer }}</div>
                    </el-collapse-item>
                  </el-collapse>
                </div>

                <!-- 知识点 -->
                <div v-if="q.knowledge_points && q.knowledge_points.length > 0" class="question-tags">
                  <el-tag
                    v-for="kp in q.knowledge_points"
                    :key="kp"
                    size="small"
                    class="mr-8"
                  >
                    {{ kp }}
                  </el-tag>
                </div>
              </div>
            </el-card>
          </div>
        </el-card>
      </el-col>

      <!-- 右侧：AI功能 -->
      <el-col :span="10">
        <el-card>
          <template #header>
            <span>AI教师助手</span>
          </template>

          <el-tabs v-model="activeTab">
            <el-tab-pane label="教案生成" name="generate">
              <el-form :model="generateForm" label-width="100px" class="generate-form">
                <el-form-item label="课程名称" required>
                  <el-input v-model="generateForm.course_name" placeholder="请输入课程名称" />
                </el-form-item>
                <el-form-item label="年级" required>
                  <el-input v-model="generateForm.grade_level" placeholder="如：高一" />
                </el-form-item>
                <el-form-item label="课题" required>
                  <el-input v-model="generateForm.topic" placeholder="请输入具体课题" />
                </el-form-item>
                <el-form-item label="时长">
                  <el-input-number v-model="generateForm.duration" :min="15" :max="120" />
                  <span style="margin-left: 8px">分钟</span>
                </el-form-item>
                <el-form-item label="特殊要求">
                  <el-input
                    v-model="generateForm.requirements"
                    type="textarea"
                    :rows="2"
                    placeholder="如有特殊要求请说明"
                  />
                </el-form-item>
                <el-form-item>
                  <el-button type="primary" :loading="generating" @click="handleGenerateSubmit">
                    生成教案
                  </el-button>
                </el-form-item>
              </el-form>
            </el-tab-pane>

            <el-tab-pane label="课件推荐" name="courseware">
              <el-form :model="coursewareForm" label-width="100px" class="generate-form">
                <el-form-item label="课程名称" required>
                  <el-input v-model="coursewareForm.course_name" placeholder="请输入课程名称" />
                </el-form-item>
                <el-form-item label="具体课题">
                  <el-input v-model="coursewareForm.topic" placeholder="请输入具体课题" />
                </el-form-item>
                <el-form-item label="年级">
                  <el-input v-model="coursewareForm.grade_level" placeholder="如：高一" />
                </el-form-item>
                <el-form-item>
                  <el-button type="primary" :loading="recommending" @click="handleRecommend">
                    获取推荐
                  </el-button>
                </el-form-item>
              </el-form>

              <div v-if="coursewareRecommendations.length > 0" class="recommendations">
                <h4>推荐课件：</h4>
                <el-card v-for="(item, index) in coursewareRecommendations" :key="index" class="recommend-item">
                  <template #header>
                    <span>{{ item.name }}</span>
                    <el-tag size="small" style="margin-left: 8px">{{ item.type }}</el-tag>
                  </template>
                  <p><strong>适用场景：</strong>{{ item.scenario }}</p>
                  <p><strong>说明：</strong>{{ item.description }}</p>
                </el-card>
              </div>
            </el-tab-pane>

            <!-- AI 出题 -->
            <el-tab-pane label="AI出题" name="questions">
              <el-form :model="questionForm" label-width="100px" class="generate-form">
                <el-form-item label="课程名称" required>
                  <el-input v-model="questionForm.course_name" placeholder="如：高中数学" />
                </el-form-item>
                <el-form-item label="年级" required>
                  <el-input v-model="questionForm.grade_level" placeholder="如：高一" />
                </el-form-item>
                <el-form-item label="课题" required>
                  <el-input v-model="questionForm.topic" placeholder="如：一元二次方程" />
                </el-form-item>
                <el-form-item label="题型" required>
                  <el-checkbox-group v-model="questionForm.question_types">
                    <el-checkbox value="single">单选题</el-checkbox>
                    <el-checkbox value="multiple">多选题</el-checkbox>
                    <el-checkbox value="fill">填空题</el-checkbox>
                    <el-checkbox value="essay">解答题</el-checkbox>
                    <el-checkbox value="calculation">计算题</el-checkbox>
                  </el-checkbox-group>
                </el-form-item>
                <el-form-item label="难度">
                  <el-slider
                    v-model="questionForm.difficulty"
                    :min="1"
                    :max="5"
                    :marks="difficultyMarks"
                    show-stops
                  />
                  <span class="difficulty-label">{{ getDifficultyLabel(questionForm.difficulty) }}</span>
                </el-form-item>
                <el-form-item label="题目数量">
                  <el-input-number
                    v-model="questionForm.count"
                    :min="1"
                    :max="50"
                    controls-position="right"
                  />
                </el-form-item>
                <el-form-item label="知识点">
                  <el-select
                    v-model="questionForm.knowledge_points"
                    multiple
                    filterable
                    allow-create
                    default-first-option
                    placeholder="输入后按回车添加"
                    style="width: 100%"
                  >
                  </el-select>
                </el-form-item>
                <el-form-item label="特殊要求">
                  <el-input
                    v-model="questionForm.requirements"
                    type="textarea"
                    :rows="2"
                    placeholder="如有题型、考点等特殊要求请说明"
                  />
                </el-form-item>
                <el-form-item>
                  <el-button type="primary" :loading="generatingQuestions" @click="handleGenerateQuestions">
                    AI出题
                  </el-button>
                  <el-button @click="handleResetQuestionForm">重置</el-button>
                </el-form-item>
              </el-form>
            </el-tab-pane>
          </el-tabs>
        </el-card>

        <!-- 生成的教案预览 -->
        <el-card v-if="generatedPlan" class="generated-preview">
          <template #header>
            <span>生成的教案</span>
            <el-button type="success" size="small" @click="handleSaveGenerated">保存教案</el-button>
          </template>
          <div class="plan-content">
            <h3>{{ generatedPlan.title || generatedPlan.plan?.title }}</h3>
            <div v-if="generatedPlan.plan?.teaching_objectives">
              <h4>教学目标</h4>
              <p>{{ generatedPlan.plan.teaching_objectives }}</p>
            </div>
            <div v-if="generatedPlan.plan?.teaching_keypoints">
              <h4>教学重难点</h4>
              <p>{{ generatedPlan.plan.teaching_keypoints }}</p>
            </div>
            <div v-if="generatedPlan.plan?.teaching_methods">
              <h4>教学方法</h4>
              <p>{{ generatedPlan.plan.teaching_methods }}</p>
            </div>
            <div v-if="generatedPlan.plan?.teaching_steps">
              <h4>教学过程</h4>
              <p>{{ generatedPlan.plan.teaching_steps }}</p>
            </div>
            <div v-if="generatedPlan.plan?.homework">
              <h4>作业布置</h4>
              <p>{{ generatedPlan.plan.homework }}</p>
            </div>
            <el-alert v-if="generatedPlan.note" :title="generatedPlan.note" type="info" show-icon />
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 教案详情对话框 -->
    <el-dialog v-model="detailVisible" title="教案详情" width="700px">
      <div v-if="currentPlan" class="plan-detail">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="课程">{{ currentPlan.course_name }}</el-descriptions-item>
          <el-descriptions-item label="年级">{{ currentPlan.grade_level }}</el-descriptions-item>
          <el-descriptions-item label="教案标题" :span="2">{{ currentPlan.title }}</el-descriptions-item>
          <el-descriptions-item label="AI生成">
            <el-tag :type="currentPlan.ai_generated ? 'success' : 'info'">
              {{ currentPlan.ai_generated ? '是' : '否' }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="currentPlan.status === 'published' ? 'success' : 'info'">
              {{ currentPlan.status === 'published' ? '已发布' : '草稿' }}
            </el-tag>
          </el-descriptions-item>
        </el-descriptions>

        <div v-if="currentPlan.teaching_objectives" class="detail-section">
          <h4>教学目标</h4>
          <p>{{ currentPlan.teaching_objectives }}</p>
        </div>
        <div v-if="currentPlan.teaching_keypoints" class="detail-section">
          <h4>教学重难点</h4>
          <p>{{ currentPlan.teaching_keypoints }}</p>
        </div>
        <div v-if="currentPlan.teaching_methods" class="detail-section">
          <h4>教学方法</h4>
          <p>{{ currentPlan.teaching_methods }}</p>
        </div>
        <div v-if="currentPlan.teaching_steps" class="detail-section">
          <h4>教学过程</h4>
          <p>{{ currentPlan.teaching_steps }}</p>
        </div>
        <div v-if="currentPlan.homework" class="detail-section">
          <h4>作业布置</h4>
          <p>{{ currentPlan.homework }}</p>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Service } from '@element-plus/icons-vue'
import {
  getLessonPlanList,
  getLessonPlanDetail,
  createLessonPlan,
  deleteLessonPlan,
  generateLessonPlan,
  recommendCourseware,
  generateQuestions,
  saveQuestion,
  saveQuestionsBatch,
  type LessonPlan,
  type LessonPlanGenerateRequest,
  type QuestionSet,
} from '@/api/ai/teacher'

const activeTab = ref('generate')
const searchForm = reactive({ keyword: '', grade_level: '' })
const pagination = reactive({ page: 1, pageSize: 20, total: 0 })
const planList = ref<LessonPlan[]>([])
const loading = ref(false)
const detailVisible = ref(false)
const currentPlan = ref<any>(null)

// 生成表单
const generateForm = reactive<LessonPlanGenerateRequest>({
  course_name: '',
  grade_level: '',
  topic: '',
  duration: 45,
  requirements: ''
})
const generating = ref(false)
const generatedPlan = ref<any>(null)

// 课件推荐表单
const coursewareForm = reactive({
  course_name: '',
  topic: '',
  grade_level: ''
})
const recommending = ref(false)
const coursewareRecommendations = ref<any[]>([])

// AI 出题表单
const questionForm = reactive({
  course_name: '',
  grade_level: '',
  topic: '',
  question_types: ['single'] as string[],
  difficulty: 2,
  count: 5,
  knowledge_points: [] as string[],
  requirements: ''
})
const generatingQuestions = ref(false)
const generatedQuestionSet = ref<QuestionSet | null>(null)
const savingAll = ref(false)

const difficultyMarks = {
  1: '简单',
  2: '中等',
  3: '较难',
  4: '困难',
  5: '极难'
}

const fetchPlans = async () => {
  loading.value = true
  try {
    const res = await getLessonPlanList({
      keyword: searchForm.keyword || undefined,
      grade_level: searchForm.grade_level || undefined,
      page: pagination.page,
      page_size: pagination.pageSize
    })
    if (res.code === 200 && res.data) {
      planList.value = res.data.items || []
      pagination.total = res.data.total || 0
    }
  } catch (error) {
    console.error('加载教案列表失败:', error)
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  pagination.page = 1
  fetchPlans()
}

const handleReset = () => {
  searchForm.keyword = ''
  searchForm.grade_level = ''
  pagination.page = 1
  fetchPlans()
}

const handleView = async (row: LessonPlan) => {
  try {
    const res = await getLessonPlanDetail(row.id)
    if (res.code === 200) {
      currentPlan.value = res.data
      detailVisible.value = true
    }
  } catch (error) {
    console.error('加载教案详情失败:', error)
  }
}

const handleDelete = async (row: LessonPlan) => {
  try {
    await deleteLessonPlan(row.id)
    ElMessage.success('删除成功')
    fetchPlans()
  } catch (error) {
    console.error('删除失败:', error)
  }
}

const switchToTab = (tab: string) => {
  activeTab.value = tab
}

const handleGenerateSubmit = async () => {
  if (!generateForm.course_name || !generateForm.topic) {
    ElMessage.warning('请填写课程名称和课题')
    return
  }

  generating.value = true
  try {
    const res = await generateLessonPlan(generateForm)
    if (res.code === 200) {
      generatedPlan.value = res.data
      ElMessage.success(res.data.note || '教案生成成功')
      fetchPlans()
    }
  } catch (error) {
    console.error('生成教案失败:', error)
  } finally {
    generating.value = false
  }
}

const handleRecommend = async () => {
  if (!coursewareForm.course_name) {
    ElMessage.warning('请填写课程名称')
    return
  }

  recommending.value = true
  try {
    const res = await recommendCourseware({
      course_name: coursewareForm.course_name,
      topic: coursewareForm.topic || undefined,
      grade_level: coursewareForm.grade_level || undefined
    })
    if (res.code === 200) {
      const data = res.data
      coursewareRecommendations.value = data.recommendations || []
      if (data.note) {
        ElMessage.info(data.note)
      }
    }
  } catch (error) {
    console.error('获取推荐失败:', error)
  } finally {
    recommending.value = false
  }
}

const handleSaveGenerated = async () => {
  if (!generatedPlan.value?.plan) {
    ElMessage.warning('没有可保存的教案')
    return
  }

  try {
    const planData = {
      ...generateForm,
      title: generatedPlan.value.plan.title || generateForm.topic,
      ...generatedPlan.value.plan,
      ai_generated: true
    }
    await createLessonPlan(planData)
    ElMessage.success('教案已保存')
    generatedPlan.value = null
    fetchPlans()
  } catch (error) {
    console.error('保存教案失败:', error)
  }
}

// AI 出题相关方法
const getDifficultyLabel = (level: number): string => {
  const labels: Record<number, string> = {
    1: '简单',
    2: '中等',
    3: '较难',
    4: '困难',
    5: '极难'
  }
  return labels[level] || '中等'
}

const getQuestionTypeLabel = (type: string): string => {
  const labels: Record<string, string> = {
    single: '单选',
    multiple: '多选',
    fill: '填空',
    essay: '解答',
    calculation: '计算'
  }
  return labels[type] || type
}

const getQuestionTypeTag = (type: string): string => {
  const tags: Record<string, string> = {
    single: 'primary',
    multiple: 'warning',
    fill: 'success',
    essay: 'info',
    calculation: 'danger'
  }
  return tags[type] || 'info'
}

const handleResetQuestionForm = () => {
  questionForm.course_name = ''
  questionForm.grade_level = ''
  questionForm.topic = ''
  questionForm.question_types = ['single']
  questionForm.difficulty = 2
  questionForm.count = 5
  questionForm.knowledge_points = []
  questionForm.requirements = ''
}

const handleGenerateQuestions = async () => {
  if (!questionForm.course_name || !questionForm.topic) {
    ElMessage.warning('请填写课程名称和课题')
    return
  }
  if (questionForm.question_types.length === 0) {
    ElMessage.warning('请至少选择一种题型')
    return
  }

  generatingQuestions.value = true
  try {
    const res = await generateQuestions({
      course_name: questionForm.course_name,
      grade_level: questionForm.grade_level,
      topic: questionForm.topic,
      question_types: questionForm.question_types,
      difficulty: questionForm.difficulty,
      count: questionForm.count,
      knowledge_points: questionForm.knowledge_points.length > 0 ? questionForm.knowledge_points : undefined,
      requirements: questionForm.requirements || undefined
    })

    if (res.code === 200) {
      generatedQuestionSet.value = res.data
      ElMessage.success(`成功生成 ${res.data.total_count} 道题目`)
    }
  } catch (error) {
    console.error('AI出题失败:', error)
    ElMessage.error('AI出题失败，请稍后重试')
  } finally {
    generatingQuestions.value = false
  }
}

const handleSaveQuestion = async (index: number) => {
  if (!generatedQuestionSet.value) return

  const q = generatedQuestionSet.value.questions[index]
  try {
    const res = await saveQuestion({
      content: q.content,
      question_type: q.question_type,
      options: q.options,
      answer: q.answer,
      analysis: q.analysis,
      difficulty: q.difficulty,
      score: q.score,
      knowledge_points: q.knowledge_points
    })

    if (res.code === 200) {
      q.saved = true
      q.saved_id = res.data.question_id
      generatedQuestionSet.value.saved_count = (generatedQuestionSet.value.saved_count || 0) + 1
      ElMessage.success('题目保存成功')
    }
  } catch (error) {
    console.error('保存题目失败:', error)
    ElMessage.error('保存失败，请稍后重试')
  }
}

const handleSaveAllQuestions = async () => {
  if (!generatedQuestionSet.value) return

  const unsavedQuestions = generatedQuestionSet.value.questions.filter((q: any) => !q.saved)
  if (unsavedQuestions.length === 0) {
    ElMessage.info('所有题目已保存')
    return
  }

  savingAll.value = true
  try {
    const res = await saveQuestionsBatch(
      unsavedQuestions.map((q: any) => ({
        content: q.content,
        question_type: q.question_type,
        options: q.options,
        answer: q.answer,
        analysis: q.analysis,
        difficulty: q.difficulty,
        score: q.score,
        knowledge_points: q.knowledge_points
      }))
    )

    if (res.code === 200) {
      const savedIds = res.data.question_ids as string[]
      let idx = 0
      generatedQuestionSet.value.questions.forEach((q: any) => {
        if (!q.saved && idx < savedIds.length) {
          q.saved = true
          q.saved_id = savedIds[idx++]
        }
      })
      generatedQuestionSet.value.saved_count = generatedQuestionSet.value.questions.filter((q: any) => q.saved).length
      ElMessage.success(`成功保存 ${savedIds.length} 道题目`)
    }
  } catch (error) {
    console.error('批量保存失败:', error)
    ElMessage.error('批量保存失败，请稍后重试')
  } finally {
    savingAll.value = false
  }
}

onMounted(() => {
  fetchPlans()
})
</script>

<style scoped lang="scss">
.teacher-assistant {
  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .mb-16 {
    margin-bottom: 16px;
  }

  .mr-8 {
    margin-right: 8px;
  }

  .search-form {
    margin-bottom: 16px;
  }

  .pagination {
    margin-top: 20px;
    display: flex;
    justify-content: flex-end;
  }

  .generate-form {
    margin-top: 16px;
  }

  .recommendations {
    margin-top: 20px;

    h4 {
      margin-bottom: 12px;
    }

    .recommend-item {
      margin-bottom: 12px;

      p {
        margin: 8px 0;
        color: #666;
      }
    }
  }

  .generated-preview {
    margin-top: 16px;

    .plan-content {
      max-height: 500px;
      overflow-y: auto;

      h3 {
        text-align: center;
        margin-bottom: 20px;
      }

      h4 {
        margin-top: 16px;
        margin-bottom: 8px;
        color: #409eff;
      }

      p {
        line-height: 1.8;
        white-space: pre-wrap;
      }
    }
  }

  .question-preview-card {
    .question-set-info {
      margin-bottom: 16px;
    }

    .question-list {
      max-height: 600px;
      overflow-y: auto;
    }

    .question-item {
      margin-bottom: 12px;

      &.is-saved {
        border-color: #67c23a;
      }

      .question-header {
        display: flex;
        align-items: center;
        gap: 8px;
      }

      .question-number {
        font-weight: bold;
        margin-right: 4px;
      }

      .question-content {
        .question-text {
          line-height: 1.8;
          margin-bottom: 12px;
        }

        .question-options {
          .option-item {
            padding: 8px 12px;
            margin-bottom: 6px;
            border-radius: 4px;
            background: #f5f7fa;

            &.is-correct {
              background: #f0f9eb;
              border: 1px solid #67c23a;
            }

            .option-label {
              font-weight: bold;
              margin-right: 8px;
            }

            .correct-tag {
              float: right;
            }
          }
        }

        .question-answer {
          margin-top: 12px;

          .answer-content {
            padding: 8px 12px;
            background: #ecf5ff;
            border-radius: 4px;
            line-height: 1.8;
          }
        }

        .question-tags {
          margin-top: 12px;
        }
      }
    }
  }

  .difficulty-label {
    margin-left: 12px;
    color: #909399;
  }

  .plan-detail {
    .detail-section {
      margin-top: 16px;

      h4 {
        margin-bottom: 8px;
        color: #409eff;
      }

      p {
        line-height: 1.8;
        white-space: pre-wrap;
      }
    }
  }
}
</style>
