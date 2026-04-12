/**
 * AI 模块 API 统一入口
 *
 * 所有 AI 相关接口调用均从此文件导入，对应后端路由前缀 /api/v1/ai/
 *
 * 子模块：
 *   chat          - AI 对话与会话管理   (/ai/chat, /ai/sessions, /ai/config)
 *   learning      - 学习 Agent 会话     (/ai/learning/...)
 *   learning_record - 学习记录追踪      (/ai/learning-records)
 *   teacher       - 教师助手            (/ai/teacher/...)
 *   diagnosis     - 学习诊断与推荐      (/ai/learning/diagnosis, /ai/learning/recommendations)
 */

export * from './chat'
export * from './learning_record'
export * from './teacher'
export * from './diagnosis'
export * as learningAgentAPI from './learning'
