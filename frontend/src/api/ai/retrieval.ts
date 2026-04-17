/**
 * Retrieval API - RAG语义检索
 * 
 * 对应后端接口: /api/v1/ai/retrieval
 */

import request from '@/utils/request'
import type { RetrievalResult } from './knowledge'

export function retrieve(knowledgeBaseId: string, query: string, top_k: number = 5) {
  return request.post<any, { data: { results: RetrievalResult[] } }>('/ai/retrieval', {
    knowledge_base_id: knowledgeBaseId,
    query,
    top_k,
  })
}

export function augmentChat(knowledgeBaseId: string, query: string, history?: Array<{role: string, content: string}>, top_k: number = 3) {
  return request.post<any, { data: any }>('/ai/retrieval/augment', {
    knowledge_base_id: knowledgeBaseId,
    query,
    history: history ? JSON.stringify(history) : '[]',
    top_k,
  })
}

export default {
  retrieve,
  augmentChat,
}