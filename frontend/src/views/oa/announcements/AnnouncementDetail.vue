<template>
  <div class="announcement-detail" v-loading="loading">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>公告详情</span>
          <div class="header-actions">
            <el-button @click="handleBack">返回列表</el-button>
            <el-button
              v-if="detail.status === 'draft'"
              type="primary"
              @click="handleEdit"
            >
              编辑
            </el-button>
          </div>
        </div>
      </template>

      <div v-if="detail" class="detail-content">
        <!-- 标题区域 -->
        <div class="detail-title">
          <h1>{{ detail.title }}</h1>
          <div class="detail-meta">
            <el-tag v-if="detail.category_name" size="small">{{ detail.category_name }}</el-tag>
            <el-tag
              :type="getPriorityType(detail.priority)"
              size="small"
            >
              {{ getPriorityLabel(detail.priority) }}
            </el-tag>
            <el-tag
              :type="getStatusType(detail.status)"
              size="small"
            >
              {{ getStatusLabel(detail.status) }}
            </el-tag>
            <span class="meta-item" v-if="detail.published_at">
              <el-icon><Clock /></el-icon>
              {{ detail.published_at }}
            </span>
            <span class="meta-item" v-if="detail.author_name">
              <el-icon><User /></el-icon>
              {{ detail.author_name }}
            </span>
            <span class="meta-item">
              <el-icon><View /></el-icon>
              {{ detail.view_count || 0 }} 次阅读
            </span>
          </div>
        </div>

        <!-- 内容区域 -->
        <div class="detail-body">
          <MarkdownEditor
            :model-value="detail.content_md || ''"
            mode="preview"
            :show-toolbar="false"
            height="auto"
            :readonly="true"
          />
        </div>

        <!-- 附件区域 -->
        <div v-if="detail.attachments && detail.attachments.length" class="detail-attachments">
          <h3>附件</h3>
          <div class="attachment-list">
            <div
              v-for="file in detail.attachments"
              :key="file.id"
              class="attachment-item"
            >
              <el-icon><Document /></el-icon>
              <a :href="file.url" target="_blank" class="attachment-name">{{ file.name }}</a>
              <span class="attachment-size">{{ formatFileSize(file.size) }}</span>
            </div>
          </div>
        </div>

        <!-- 评论区 -->
        <div v-if="detail.allow_comment" class="detail-comments">
          <h3>评论 ({{ comments.length }})</h3>

          <!-- 评论输入 -->
          <div class="comment-input">
            <el-input
              v-model="commentContent"
              type="textarea"
              :rows="3"
              placeholder="请输入评论内容..."
            />
            <el-button
              type="primary"
              :loading="commentSubmitting"
              @click="handleSubmitComment"
              style="margin-top: 8px;"
            >
              发表评论
            </el-button>
          </div>

          <!-- 评论列表 -->
          <div class="comment-list">
            <div v-if="comments.length === 0" class="comment-empty">暂无评论</div>
            <div v-for="comment in comments" :key="comment.id" class="comment-item">
              <div class="comment-header">
                <span class="comment-author">{{ comment.author_name || '匿名用户' }}</span>
                <span class="comment-time">{{ comment.created_at }}</span>
              </div>
              <div class="comment-body">{{ comment.content }}</div>
            </div>
          </div>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Clock, User, View, Document } from '@element-plus/icons-vue'
import MarkdownEditor from '@/components/MarkdownEditor.vue'
import { announcementApi } from '@/api/oa/announcements'

const route = useRoute()
const router = useRouter()

const loading = ref(false)
const detail = ref<any>(null)
const comments = ref<any[]>([])
const commentContent = ref('')
const commentSubmitting = ref(false)

const priorityOptions = [
  { label: '普通', value: 'normal', type: 'info' },
  { label: '重要', value: 'important', type: 'warning' },
  { label: '紧急', value: 'urgent', type: 'danger' }
]

const statusOptions = [
  { label: '草稿', value: 'draft', type: 'info' },
  { label: '已发布', value: 'published', type: 'success' },
  { label: '已撤销', value: 'revoked', type: '' }
]

const getPriorityLabel = (val: string) => priorityOptions.find(o => o.value === val)?.label || val
const getPriorityType = (val: string) => priorityOptions.find(o => o.value === val)?.type || 'info'
const getStatusLabel = (val: string) => statusOptions.find(o => o.value === val)?.label || val
const getStatusType = (val: string) => statusOptions.find(o => o.value === val)?.type || 'info'

const formatFileSize = (size: number) => {
  if (!size) return ''
  if (size < 1024) return size + ' B'
  if (size < 1024 * 1024) return (size / 1024).toFixed(1) + ' KB'
  return (size / (1024 * 1024)).toFixed(1) + ' MB'
}

const loadDetail = async () => {
  const id = route.params.id as string
  if (!id) return
  loading.value = true
  try {
    const res = await announcementApi.getById(id)
    detail.value = res.data || res
  } catch (error) {
    ElMessage.error('加载公告详情失败')
  } finally {
    loading.value = false
  }
}

const markRead = async () => {
  const id = route.params.id as string
  if (!id) return
  try {
    await announcementApi.markRead(id)
  } catch (error) {
    // 标记已读失败不影响页面展示
  }
}

const loadComments = async () => {
  const id = route.params.id as string
  if (!id) return
  try {
    const res = await announcementApi.getComments(id)
    comments.value = res.data?.list || res.data || []
  } catch (error) {
    console.error('加载评论失败', error)
  }
}

const handleSubmitComment = async () => {
  if (!commentContent.value.trim()) {
    ElMessage.warning('请输入评论内容')
    return
  }
  const id = route.params.id as string
  commentSubmitting.value = true
  try {
    await announcementApi.addComment(id, { content: commentContent.value })
    ElMessage.success('评论成功')
    commentContent.value = ''
    loadComments()
  } catch (error) {
    ElMessage.error('评论失败')
  } finally {
    commentSubmitting.value = false
  }
}

const handleBack = () => {
  router.push('/oa/announcements')
}

const handleEdit = () => {
  const id = route.params.id as string
  router.push(`/oa/announcements/${id}/edit`)
}

onMounted(() => {
  loadDetail()
  markRead()
  loadComments()
})
</script>

<style scoped>
.announcement-detail {
  padding: 16px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-actions {
  display: flex;
  gap: 8px;
}

.detail-content {
  padding: 16px 0;
}

.detail-title h1 {
  font-size: 22px;
  font-weight: 600;
  margin: 0 0 12px;
  color: #303133;
}

.detail-meta {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
  margin-bottom: 24px;
  color: #909399;
  font-size: 14px;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 4px;
}

.detail-body {
  margin-bottom: 24px;
  border: 1px solid #ebeef5;
  border-radius: 4px;
  overflow: hidden;
}

.detail-attachments {
  margin-bottom: 24px;
}

.detail-attachments h3 {
  font-size: 16px;
  margin: 0 0 12px;
  color: #303133;
}

.attachment-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.attachment-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: #f5f7fa;
  border-radius: 4px;
}

.attachment-name {
  color: #409eff;
  text-decoration: none;
  flex: 1;
}

.attachment-name:hover {
  text-decoration: underline;
}

.attachment-size {
  color: #909399;
  font-size: 12px;
}

.detail-comments {
  border-top: 1px solid #ebeef5;
  padding-top: 24px;
}

.detail-comments h3 {
  font-size: 16px;
  margin: 0 0 16px;
  color: #303133;
}

.comment-input {
  margin-bottom: 24px;
}

.comment-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.comment-empty {
  text-align: center;
  color: #909399;
  padding: 24px 0;
}

.comment-item {
  padding: 12px;
  background: #f5f7fa;
  border-radius: 4px;
}

.comment-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.comment-author {
  font-weight: 500;
  color: #303133;
  font-size: 14px;
}

.comment-time {
  color: #909399;
  font-size: 12px;
}

.comment-body {
  color: #606266;
  font-size: 14px;
  line-height: 1.6;
}
</style>
