<template>
  <div class="ai-chat">
    <el-card class="chat-container">
      <div class="chat-header">
        <el-select v-model="currentModel" placeholder="选择AI模型" style="width: 150px">
          <el-option label="DeepSeek" value="deepseek" />
          <el-option label="通义千问" value="qwen" />
          <el-option label="OpenAI" value="openai" />
        </el-select>
        <el-button type="primary" link @click="handleNewSession">新建会话</el-button>
      </div>

      <div class="chat-content" ref="chatContentRef">
        <div v-for="(msg, index) in messages" :key="index"
             class="message" :class="msg.role">
          <div class="message-avatar">
            <el-icon v-if="msg.role === 'user'"><User /></el-icon>
            <el-icon v-else><Service /></el-icon>
          </div>
          <div class="message-content">
            <!-- assistant 消息支持 Markdown 渲染 -->
            <div v-if="msg.role === 'assistant'" class="message-text markdown-body" v-html="renderMarkdown(msg.content)" />
            <div v-else class="message-text">{{ msg.content }}</div>
            <div class="message-time">{{ msg.time }}</div>
          </div>
        </div>
        <div v-if="loading" class="message assistant">
          <div class="message-avatar"><el-icon><Service /></el-icon></div>
          <div class="message-content">
            <div class="message-text typing">
              <span class="typing-dots">
                <span></span><span></span><span></span>
              </span>
              正在思考中...
              <!-- 流式输出内容追加到打字中消息 -->
              <span v-if="streamingContent" class="streaming-text" v-html="renderMarkdown(streamingContent)" />
            </div>
          </div>
        </div>
      </div>

      <div class="chat-input">
        <el-input
          v-model="inputMessage"
          type="textarea"
          :rows="3"
          placeholder="输入消息... (Enter发送, Shift+Enter换行)"
          :disabled="loading"
          @keydown.enter.exact.prevent="handleSendMessage"
        />
        <el-button
          type="primary"
          @click="handleSendMessage"
          :loading="loading"
          :disabled="!inputMessage.trim() || loading"
        >
          {{ loading ? '生成中...' : '发送' }}
        </el-button>
      </div>
    </el-card>

    <el-card class="session-list">
      <template #header>
        <span>会话历史</span>
      </template>
      <el-scrollbar height="400px">
        <div v-for="sess in sessions" :key="sess.id"
             class="session-item"
             :class="{ active: sess.id === currentSessionId }"
             @click="handleSelectSession(sess)">
          <div class="session-title">{{ sess.title }}</div>
          <div class="session-time">{{ formatTime(sess.updated_at) }}</div>
        </div>
        <el-empty v-if="sessions.length === 0" description="暂无会话" :image-size="60" />
      </el-scrollbar>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import { User, Service } from '@element-plus/icons-vue'
import {
  getChatSessions,
  createSession,
  sendMessageStream,
  getSessionMessages,
} from '@/api/ai/chat'

// ---------------------------------------------------------------------------
// 状态
// ---------------------------------------------------------------------------
interface Msg {
  role: 'user' | 'assistant'
  content: string
  time: string
}

interface Session {
  id: string
  title: string
  model_type?: string
  updated_at: string
}

const currentModel = ref('deepseek')
const inputMessage = ref('')
const messages = ref<Msg[]>([])
const sessions = ref<Session[]>([])
const currentSessionId = ref('')
const loading = ref(false)
const streamingContent = ref('')   // 流式追加中的内容
const chatContentRef = ref<HTMLElement>()
let currentController: AbortController | null = null

// ---------------------------------------------------------------------------
// Markdown 渲染（基础实现，依赖 marked 或手动处理）
// ---------------------------------------------------------------------------
function renderMarkdown(text: string): string {
  if (!text) return ''
  // 简单转义 HTML，防止 XSS
  let html = text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
  // 粗体 **text**
  html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
  // 斜体 *text*
  html = html.replace(/\*(.+?)\*/g, '<em>$1</em>')
  // 代码 `code`
  html = html.replace(/`(.+?)`/g, '<code>$1</code>')
  // 换行
  html = html.replace(/\n/g, '<br>')
  return html
}

// ---------------------------------------------------------------------------
// 滚动到底部
// ---------------------------------------------------------------------------
function scrollToBottom() {
  nextTick(() => {
    if (chatContentRef.value) {
      chatContentRef.value.scrollTop = chatContentRef.value.scrollHeight
    }
  })
}

// ---------------------------------------------------------------------------
// 时间格式化
// ---------------------------------------------------------------------------
function formatTime(isoStr: string): string {
  if (!isoStr) return ''
  try {
    const d = new Date(isoStr)
    return d.toLocaleString('zh-CN', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })
  } catch {
    return isoStr
  }
}

// ---------------------------------------------------------------------------
// 新建会话
// ---------------------------------------------------------------------------
async function handleNewSession() {
  try {
    const res = await createSession({ title: '新对话', model: currentModel.value })
    const newSess: Session = {
      id: res.data?.id || res.data,
      title: '新对话',
      updated_at: new Date().toISOString(),
    }
    sessions.value.unshift(newSess)
    currentSessionId.value = newSess.id
    messages.value = []
    ElMessage.success('会话已创建')
  } catch (e: any) {
    ElMessage.error(e?.message || '创建会话失败')
  }
}

// ---------------------------------------------------------------------------
// 选择会话
// ---------------------------------------------------------------------------
async function handleSelectSession(sess: Session) {
  currentSessionId.value = sess.id
  try {
    const res = await getSessionMessages(sess.id)
    messages.value = (res.data || []).map((m: any) => ({
      role: m.role as 'user' | 'assistant',
      content: m.content,
      time: m.created_at ? formatTime(m.created_at) : '',
    }))
    scrollToBottom()
  } catch (e) {
    console.error(e)
  }
}

// ---------------------------------------------------------------------------
// 发送消息（流式）
// ---------------------------------------------------------------------------
function handleSendMessage() {
  if (!inputMessage.value.trim() || loading.value) return

  const userText = inputMessage.value.trim()
  inputMessage.value = ''

  // 用户消息立即追加
  messages.value.push({
    role: 'user',
    content: userText,
    time: new Date().toLocaleString(),
  })
  scrollToBottom()

  loading.value = true
  streamingContent.value = ''
  let assistantContent = ''

  // 取消上一个请求
  currentController?.abort()

  currentController = sendMessageStream(
    {
      session_id: currentSessionId.value || undefined,
      message: userText,
      model_type: currentModel.value,
    },
    // onChunk: 每次收到内容块
    (chunk) => {
      assistantContent += chunk
      streamingContent.value = assistantContent
      scrollToBottom()
    },
    // onDone: 流结束
    (sessionId) => {
      loading.value = false
      streamingContent.value = ''
      // 固定消息追加到历史
      messages.value.push({
        role: 'assistant',
        content: assistantContent || '[空响应]',
        time: new Date().toLocaleString(),
      })

      // 如果是新会话，记录 session_id
      if (sessionId && !currentSessionId.value) {
        currentSessionId.value = sessionId
        // 刷新会话列表
        loadSessions()
      }
      scrollToBottom()
    },
    // onSessionId: 收到会话 ID
    (sessionId) => {
      if (!currentSessionId.value) {
        currentSessionId.value = sessionId
        // 刷新会话列表
        loadSessions()
      }
    }
  )
}

// ---------------------------------------------------------------------------
// 加载会话列表
// ---------------------------------------------------------------------------
async function loadSessions() {
  try {
    const res = await getChatSessions()
    sessions.value = res.data || []
  } catch (e) {
    console.error(e)
  }
}

// ---------------------------------------------------------------------------
// 初始加载
// ---------------------------------------------------------------------------
onMounted(async () => {
  await loadSessions()
  if (sessions.value.length > 0) {
    currentSessionId.value = sessions.value[0].id
    await handleSelectSession(sessions.value[0])
  }
})
</script>

<style scoped lang="scss">
.ai-chat {
  display: flex;
  gap: 20px;
  height: calc(100vh - 100px);

  .chat-container {
    flex: 1;
    display: flex;
    flex-direction: column;

    .chat-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding-bottom: 15px;
      border-bottom: 1px solid #eee;
    }

    .chat-content {
      flex: 1;
      overflow-y: auto;
      padding: 20px 0;

      .message {
        display: flex;
        margin-bottom: 20px;

        &.user {
          flex-direction: row-reverse;

          .message-content {
            text-align: right;
          }
        }

        .message-avatar {
          width: 40px;
          height: 40px;
          border-radius: 50%;
          background: #409eff;
          display: flex;
          align-items: center;
          justify-content: center;
          color: #fff;
          margin: 0 10px;
          flex-shrink: 0;
        }

        .message-content {
          max-width: 70%;

          .message-text {
            padding: 10px 15px;
            border-radius: 8px;
            background: #f5f7fa;
            word-break: break-word;
          }

          .message-time {
            font-size: 12px;
            color: #999;
            margin-top: 5px;
          }
        }

        &.assistant .message-content .message-text {
          background: #e8f4ff;
        }
      }

      // 打字动画
      .typing {
        .typing-dots {
          display: inline-flex;
          gap: 3px;
          margin-right: 4px;
          vertical-align: middle;

          span {
            width: 6px;
            height: 6px;
            border-radius: 50%;
            background: #409eff;
            animation: bounce 1.4s ease-in-out infinite;

            &:nth-child(2) { animation-delay: 0.2s; }
            &:nth-child(3) { animation-delay: 0.4s; }
          }
        }
      }

      // 流式内容样式
      .streaming-text {
        display: inline;
      }
    }

    .chat-input {
      display: flex;
      gap: 10px;
      padding-top: 15px;
      border-top: 1px solid #eee;

      .el-textarea {
        flex: 1;
      }
    }
  }

  .session-list {
    width: 250px;

    .session-item {
      padding: 10px;
      border-bottom: 1px solid #eee;
      cursor: pointer;

      &:hover, &.active {
        background: #f5f7fa;
      }

      .session-title {
        font-size: 14px;
        margin-bottom: 5px;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
      }

      .session-time {
        font-size: 12px;
        color: #999;
      }
    }
  }
}

@keyframes bounce {
  0%, 80%, 100% { transform: translateY(0); }
  40% { transform: translateY(-6px); }
}
</style>
