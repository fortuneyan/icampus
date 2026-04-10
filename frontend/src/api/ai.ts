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

export function getChatSessions() {
  return request.get('/ai/sessions')
}

export function createSession(data: { title: string; model?: string }) {
  return request.post('/ai/sessions', data)
}

export function deleteSession(sessionId: string) {
  return request.delete(`/ai/sessions/${sessionId}`)
}

export function getSessionMessages(sessionId: string) {
  return request.get(`/ai/sessions/${sessionId}/messages`)
}

export function sendMessage(data: { session_id?: string; message: string; model?: string }) {
  return request.post('/ai/chat', data)
}

export function getAIConfig() {
  return request.get('/ai/config')
}

export function updateAIConfig(data: { default_model?: string; api_key?: string }) {
  return request.put('/ai/config', data)
}