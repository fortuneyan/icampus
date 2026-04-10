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
            <el-icon v-else><Robot /></el-icon>
          </div>
          <div class="message-content">
            <div class="message-text">{{ msg.content }}</div>
            <div class="message-time">{{ msg.time }}</div>
          </div>
        </div>
        <div v-if="loading" class="message assistant">
          <div class="message-avatar"><el-icon><Robot /></el-icon></div>
          <div class="message-content">
            <div class="message-text typing">正在思考中...</div>
          </div>
        </div>
      </div>
      
      <div class="chat-input">
        <el-input
          v-model="inputMessage"
          type="textarea"
          :rows="3"
          placeholder="输入消息... (Enter发送, Shift+Enter换行)"
          @keydown.enter="handleSendMessage"
        />
        <el-button type="primary" @click="handleSendMessage" :loading="loading" :disabled="!inputMessage.trim()">
          发送
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
          <div class="session-time">{{ sess.time }}</div>
        </div>
      </el-scrollbar>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import { User, Robot } from '@element-plus/icons-vue'
import { getChatSessions, createSession, sendMessage, getSessionMessages } from '@/api/ai'

const currentModel = ref('deepseek')
const inputMessage = ref('')
const messages = ref<any[]>([])
const sessions = ref<any[]>([])
const currentSessionId = ref('')
const loading = ref(false)
const chatContentRef = ref<HTMLElement>()

const scrollToBottom = () => {
  nextTick(() => {
    if (chatContentRef.value) {
      chatContentRef.value.scrollTop = chatContentRef.value.scrollHeight
    }
  })
}

const handleNewSession = async () => {
  try {
    const res = await createSession({ title: '新会话', model: currentModel.value })
    sessions.value.unshift({ id: res.data.id, title: '新会话', time: new Date().toLocaleString() })
    currentSessionId.value = res.data.id
    messages.value = []
    ElMessage.success('创建成功')
  } catch (e: any) { ElMessage.error(e.message || '创建失败') }
}

const handleSelectSession = async (sess: any) => {
  currentSessionId.value = sess.id
  try {
    const res = await getSessionMessages(sess.id)
    messages.value = res.data || []
    scrollToBottom()
  } catch (e: any) { console.error(e) }
}

const handleSendMessage = async () => {
  if (!inputMessage.value.trim() || loading.value) return
  
  const userMessage = inputMessage.value.trim()
  inputMessage.value = ''
  
  messages.value.push({
    role: 'user',
    content: userMessage,
    time: new Date().toLocaleString()
  })
  loading.value = true
  scrollToBottom()
  
  try {
    const res = await sendMessage({
      session_id: currentSessionId.value || undefined,
      message: userMessage,
      model: currentModel.value
    })
    messages.value.push({
      role: 'assistant',
      content: res.data?.content || res.data?.message || '回答已生成',
      time: new Date().toLocaleString()
    })
    if (!currentSessionId.value && res.data?.session_id) {
      currentSessionId.value = res.data.session_id
      const sessRes = await getChatSessions()
      sessions.value = sessRes.data || []
    }
  } catch (e: any) {
    ElMessage.error(e.message || '发送失败')
    messages.value.push({
      role: 'assistant',
      content: '抱歉，发生了一些错误，请稍后重试。',
      time: new Date().toLocaleString()
    })
  } finally {
    loading.value = false
    scrollToBottom()
  }
}

onMounted(async () => {
  try {
    const res = await getChatSessions()
    sessions.value = res.data || []
    if (sessions.value.length > 0) {
      currentSessionId.value = sessions.value[0].id
      const msgRes = await getSessionMessages(currentSessionId.value)
      messages.value = msgRes.data || []
    }
  } catch (e: any) { console.error(e) }
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
        }
        
        .message-content {
          max-width: 70%;
          
          .message-text {
            padding: 10px 15px;
            border-radius: 8px;
            background: #f5f7fa;
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
      }
      
      .session-time {
        font-size: 12px;
        color: #999;
      }
    }
  }
}
</style>