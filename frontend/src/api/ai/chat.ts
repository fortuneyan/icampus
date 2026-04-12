/**
 * AI 对话与会话管理 API
 * 路径: /api/v1/ai/chat, /api/v1/ai/sessions, /api/v1/ai/config, /api/v1/ai/chat/stream
 */
import request from '@/utils/request'

export interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
  time?: string
}

export interface ChatSession {
  id: string
  title: string
  model: string
  created_at: string
}

// ---------------------------------------------------------------------------
// SSE 流式响应类型
// ---------------------------------------------------------------------------

export interface SSEChunk {
  type: 'session_id' | 'content' | 'done'
  value?: string
  session_id?: string
}

/** 获取会话列表 */
export function getChatSessions() {
  return request.get('/ai/sessions')
}

/** 创建新会话 */
export function createSession(data: { title: string; model?: string }) {
  return request.post('/ai/sessions', data)
}

/** 删除会话 */
export function deleteSession(sessionId: string) {
  return request.delete(`/ai/sessions/${sessionId}`)
}

/** 获取会话消息记录 */
export function getSessionMessages(sessionId: string) {
  return request.get(`/ai/sessions/${sessionId}/messages`)
}

/** 发送对话消息（非流式） */
export function sendMessage(data: {
  session_id?: string
  message: string
  model?: string
}) {
  return request.post('/ai/chat', data)
}

/**
 * 发送对话消息（流式 SSE）
 *
 * @param data - 请求参数
 * @param onChunk - 每个内容块回调（type=content 时触发）
 * @param onDone - 完成回调（type=done 时触发）
 * @param onSessionId - 会话 ID 回调（type=session_id 时触发）
 * @returns AbortController，用于取消请求
 *
 * @example
 * const controller = sendMessageStream(
 *   { message: '你好', model_type: 'deepseek' },
 *   (chunk) => { aiContent += chunk; render(); },
 *   () => { saveToHistory(); },
 *   (id) => { sessionId = id; }
 * );
 * // 取消: controller.abort()
 */
export function sendMessageStream(
  data: { session_id?: string; message: string; model_type?: string },
  onChunk: (content: string) => void,
  onDone?: (sessionId: string) => void,
  onSessionId?: (sessionId: string) => void
): AbortController {
  const controller = new AbortController()

  const token = localStorage.getItem('token') || ''

  fetch(`${import.meta.env.VITE_API_BASE_URL || ''}/api/v1/ai/chat/stream`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': token ? `Bearer ${token}` : '',
    },
    body: JSON.stringify(data),
    signal: controller.signal,
  })
    .then(async (response) => {
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`)
      }
      const reader = response.body!.getReader()
      const decoder = new TextDecoder('utf-8')
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })

        // 按 SSE 格式解析（data: {...}\n\n）
        const lines = buffer.split('\n')
        buffer = lines.pop() || '' // 保留不完整的行

        for (const line of lines) {
          if (!line.startsWith('data: ')) continue
          const dataStr = line.slice(6)
          try {
            const chunk: SSEChunk = JSON.parse(dataStr)
            if (chunk.type === 'session_id' && chunk.value) {
              onSessionId?.(chunk.value)
            } else if (chunk.type === 'content' && chunk.value) {
              onChunk(chunk.value)
            } else if (chunk.type === 'done') {
              onDone?.(chunk.session_id || '')
            }
          } catch {
            // 忽略解析错误
          }
        }
      }
    })
    .catch((err) => {
      if (err.name !== 'AbortError') {
        console.error('Stream error:', err)
        onChunk(`\n[错误] ${err.message}`)
        onDone?.('')
      }
    })

  return controller
}

/** 获取 AI 配置 */
export function getAIConfig() {
  return request.get('/ai/config')
}

/** 更新 AI 配置 */
export function updateAIConfig(data: {
  default_model?: string
  api_key?: string
}) {
  return request.put('/ai/config', data)
}

