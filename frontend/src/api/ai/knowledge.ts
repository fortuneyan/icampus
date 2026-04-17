/**
 * Knowledge Base API - 知识库管理
 * 
 * 对应后端接口: /api/v1/ai/knowledge-bases
 */

import request from '@/utils/request'

export interface KnowledgeBase {
  id: string
  name: string
  description: string
  document_count: number
  created_at?: string
}

export interface RetrievalResult {
  content: string
  source: string
  score: number
  metadata: Record<string, any>
}

export function createKnowledgeBase(name: string, description?: string) {
  return request.post<any, { data: KnowledgeBase }>('/ai/knowledge-bases', {
    name,
    description: description || '',
  })
}

export function getKnowledgeBases(params?: { page?: number; page_size?: number }) {
  return request.get<any, { data: { items: KnowledgeBase[] } }>('/ai/knowledge-bases', { params })
}

export function getKnowledgeBase(knowledgeBaseId: string) {
  return request.get<any, { data: KnowledgeBase }>(`/ai/knowledge-bases/${knowledgeBaseId}`)
}

export function deleteKnowledgeBase(knowledgeBaseId: string) {
  return request.delete(`/ai/knowledge-bases/${knowledgeBaseId}`)
}

export function addDocument(knowledgeBaseId: string, file: File) {
  const formData = new FormData()
  formData.append('file', file)
  return request.post<any, { data: any }>(`/ai/knowledge-bases/${knowledgeBaseId}/documents`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}

export function addTexts(knowledgeBaseId: string, texts: string[]) {
  return request.post<any, { data: any }>(`/ai/knowledge-bases/${knowledgeBaseId}/texts`, texts)
}

export function retrieve(knowledgeBaseId: string, query: string, top_k?: number) {
  return request.post<any, { data: { results: RetrievalResult[] } }>('/ai/retrieval', {
    knowledge_base_id: knowledgeBaseId,
    query,
    top_k: top_k || 5,
  })
}

export function augmentChat(knowledgeBaseId: string, query: string, history?: string[], top_k?: number) {
  return request.post<any, { data: any }>(`/ai/knowledge-bases/${knowledgeBaseId}/chat`, {
    query,
    history: history ? JSON.stringify(history) : '',
    top_k: top_k || 3,
  })
}

export default {
  createKnowledgeBase,
  getKnowledgeBases,
  getKnowledgeBase,
  deleteKnowledgeBase,
  addDocument,
  addTexts,
  retrieve,
  augmentChat,
}