/**
 * @deprecated 此文件已迁移到 `@/api/ai/` 目录下，请从对应子模块导入
 *
 * - 对话相关: import { ... } from '@/api/ai/chat'
 * - 学习记录: import { ... } from '@/api/ai/learning_record'
 * - 教师助手: import { ... } from '@/api/ai/teacher'
 * - 学习诊断: import { ... } from '@/api/ai/diagnosis'
 * - 学习Agent: import learningAgentAPI from '@/api/ai/learning'
 *
 * 此文件保留以兼容现有引用，后续请逐步迁移。
 */

export * from './ai/chat'
export * from './ai/learning_record'
export * from './ai/teacher'
export * from './ai/diagnosis'
export { learningAgentAPI } from './ai/learning'
