# 智慧校园管理平台 - 目录规划与开发计划

> 文档版本：v1.0  
> 更新时间：2026-04-12  
> 状态：Phase 1-5 全部完成，当前为 Phase 6 AI 模块深化开发

---

## 一、项目现状速览

### 技术栈
| 层次 | 技术 |
|------|------|
| 后端框架 | Python FastAPI 0.115 + SQLAlchemy 2.0 |
| 数据库 | PostgreSQL (asyncpg) + SQLite (本地开发) |
| 前端框架 | Vue 3.4 + Element Plus 2.6 + TypeScript |
| 状态管理 | Pinia |
| 路由 | Vue Router 4 |
| HTTP 客户端 | Axios |
| AI 服务 | LangChain + DeepSeek/Qwen/OpenAI |
| 构建工具 | Vite 5 |

### 整体完成率：~82%（Phase 1-5 全部交付）

---

## 二、目录结构全景（规范版）

> **规则说明**  
> - 后端 API：`/api/v1/{module}/...` 为基础管理接口  
> - 后端 AI API：`/api/v1/ai/{module}/...` 为 AI 功能接口（独立 Router 挂载）  
> - 前端视图：`views/{module}/` 与后端 `module` 一一对应  
> - 前端 AI 视图：`views/ai/` 统一 `/ai/` 路由前缀  

```
smart-campus/
├── backend/
│   ├── app/
│   │   ├── main.py                    # FastAPI 入口（双 Router 挂载）
│   │   ├── api/
│   │   │   └── v1/
│   │   │       ├── __init__.py        # 导出 api_router + ai_api_router
│   │   │       │
│   │   │       ├── ── 基础管理路由 (/api/v1/) ──
│   │   │       ├── auth/              # 认证：登录/登出/刷新token
│   │   │       ├── system/            # 系统：用户/角色/部门/日志/字典/地区/加密
│   │   │       ├── edu/               # 教务：课程/班级/年级/学生/成绩/课表/排课/选课...
│   │   │       ├── exam/              # 考试：考试管理/成绩报表
│   │   │       ├── attendance/        # 考勤：打卡/规则/统计报表
│   │   │       ├── notice/            # 通知公告
│   │   │       ├── message/           # 消息中心/订阅
│   │   │       ├── resource/          # 教学资源/收藏/推荐
│   │   │       ├── dashboard/         # 仪表盘概览
│   │   │       ├── report/            # 学生报告
│   │   │       ├── settings/          # 系统设置
│   │   │       ├── student/           # 学生扩展：毕业管理/成长记录
│   │   │       ├── extended/          # 扩展业务：宿舍/图书/一卡通/奖助学金
│   │   │       │
│   │   │       └── ── AI 功能路由 (/api/v1/ai/) ──
│   │   │           └── ai/
│   │   │               ├── __init__.py
│   │   │               ├── chat.py              # AI 对话 & 会话管理
│   │   │               ├── learning_records.py  # 学习记录追踪
│   │   │               ├── learning_diagnosis.py# 学习诊断 & 个性化推荐
│   │   │               └── teacher_assistant.py # 教师助手：教案/课件推荐
│   │   │
│   │   ├── models/                    # 48 个 SQLAlchemy ORM 模型
│   │   ├── schemas/                   # 20 个 Pydantic 数据模式
│   │   ├── services/                  # 29 个业务逻辑层
│   │   ├── core/                      # 核心配置：config/db/security/session/logger
│   │   └── middleware/                # 中间件：csrf/rate_limit/xss
│   │
│   ├── tests/                         # 后端测试（60+ 测试文件，500+ 用例）
│   ├── scripts/                       # 数据库初始化脚本
│   ├── requirements.txt
│   └── .env / .env.example
│
├── frontend/
│   ├── src/
│   │   ├── main.ts                    # 应用入口
│   │   ├── App.vue
│   │   ├── router/
│   │   │   └── index.ts               # 路由配置（双前缀：/ 基础 & /ai/ AI）
│   │   │
│   │   ├── stores/
│   │   │   └── user.ts                # Pinia 用户状态
│   │   │
│   │   ├── utils/
│   │   │   └── request.ts             # Axios 实例
│   │   │
│   │   ├── api/
│   │   │   ├── ── 基础管理 API ──
│   │   │   ├── auth.ts                # 认证
│   │   │   ├── dashboard.ts           # 仪表盘
│   │   │   ├── notice.ts              # 通知公告
│   │   │   ├── exam.ts                # 考试（旧，兼容）
│   │   │   ├── resource.ts            # 资源（旧，兼容）
│   │   │   ├── student.ts             # 学生（旧，兼容）
│   │   │   ├── extended.ts            # 扩展业务
│   │   │   ├── settings.ts            # 系统设置
│   │   │   ├── attendance.ts          # 考勤（旧，兼容）
│   │   │   ├── system/                # 系统管理：user/role/department/log/dictionary
│   │   │   ├── edu/                   # 教务管理：course/class/grade/schedule/scheduling...
│   │   │   ├── exam/                  # 考试管理：report
│   │   │   ├── attendance/            # 考勤管理：attendance_stats
│   │   │   ├── resource/              # 资源管理：favorite/recommend
│   │   │   ├── student/               # 学生管理：graduation
│   │   │   │
│   │   │   └── ── AI 功能 API (/api/v1/ai/) ──
│   │   │       ├── ai.ts              # 旧版（@deprecated 兼容转发）
│   │   │       ├── teacher.ts         # 旧版（@deprecated 兼容转发）
│   │   │       └── ai/
│   │   │           ├── index.ts       # 统一导出入口
│   │   │           ├── chat.ts        # AI 对话 & 会话管理
│   │   │           ├── teacher.ts     # 教师助手
│   │   │           ├── diagnosis.ts   # 学习诊断
│   │   │           ├── learning.ts    # 学习 Agent（完整实现）
│   │   │           └── learning_record.ts # 学习记录
│   │   │
│   │   └── views/
│   │       ├── Layout.vue             # 主布局
│   │       ├── ── 基础管理视图 ──
│   │       ├── auth/                  # 登录页
│   │       ├── system/                # 系统管理视图（Dashboard/User/Role/Dept/Log...）
│   │       ├── edu/                   # 教务管理视图（Class/Course/Schedule/Scheduling...）
│   │       ├── exam/                  # 考试管理视图（Exam/Report及子Tab）
│   │       ├── attendance/            # 考勤管理视图（Attendance/AttendanceStats）
│   │       ├── notice/                # 通知公告视图
│   │       ├── resource/              # 资源管理视图
│   │       ├── settings/              # 系统设置视图
│   │       ├── student/               # 学生管理视图（Graduation/GrowthRecord）
│   │       ├── extended/              # 扩展业务视图（宿舍/图书/一卡通/奖助学金）
│   │       │
│   │       └── ── AI 功能视图 (/ai/ 路由前缀) ──
│   │           └── ai/
│   │               ├── Chat.vue           # AI 对话（路由: /ai/chat）
│   │               ├── LearningAgent.vue  # 学习助手（路由: /ai/learning-agent）
│   │               ├── LearningPath.vue   # 学习路径（路由: /ai/learning-path）
│   │               ├── LearningRecord.vue # 学习记录（路由: /ai/learning-records）
│   │               └── TeacherAssistant.vue # 教师助手（路由: /ai/teacher-assistant）
│   │
│   ├── tests/                         # 前端测试
│   ├── package.json
│   ├── vite.config.ts
│   └── tsconfig.json
│
├── docs/                              # 设计文档 & 测试报告
├── tests/                             # 集成测试
├── docker-compose.yml
└── README.md
```

---

## 三、路由对照表

### 3.1 后端 API 路由（完整版）

#### 基础管理路由（`api_router`，挂载于 `/api/v1`）

| 模块 | 路由前缀 | 说明 |
|------|----------|------|
| 认证 | `/api/v1/auth/` | 登录/登出/刷新 |
| 系统管理 | `/api/v1/system/` | 用户/角色/部门/日志/字典 |
| 教务管理 | `/api/v1/edu/` | 课程/班级/排课/选课等 |
| 考试管理 | `/api/v1/exam/` | 考试/成绩报表 |
| 考勤管理 | `/api/v1/attendance/` | 打卡/规则/统计 |
| 通知公告 | `/api/v1/notice/` | CRUD |
| 消息中心 | `/api/v1/message/` | 消息/订阅 |
| 教学资源 | `/api/v1/resource/` | 上传/检索/推荐 |
| 仪表盘 | `/api/v1/dashboard/` | 数据概览 |
| 报表 | `/api/v1/report/` | 学生报告 |
| 系统设置 | `/api/v1/settings/` | 配置管理 |
| 学生扩展 | `/api/v1/student/` | 毕业/成长记录 |
| 扩展业务 | `/api/v1/extended/` | 宿舍/图书/一卡通/奖助学金 |

#### AI 功能路由（`ai_api_router`，挂载于 `/api/v1`）

| 模块 | 路由前缀 | 说明 |
|------|----------|------|
| AI 对话 | `/api/v1/ai/chat/` | 会话管理、流式对话 |
| 学习记录 | `/api/v1/ai/learning-records/` | 行为追踪 |
| 学习诊断 | `/api/v1/ai/diagnosis/` | 能力画像/推荐 |
| 教师助手 | `/api/v1/ai/teacher/` | 教案/课件生成 |

### 3.2 前端路由（完整版）

#### 基础管理路由

| 路由路径 | 组件 | 说明 |
|----------|------|------|
| `/login` | `auth/Login.vue` | 登录 |
| `/dashboard` | `system/Dashboard.vue` | 仪表盘 |
| `/system/users` | `system/User.vue` | 用户管理 |
| `/system/roles` | `system/Role.vue` | 角色管理 |
| `/system/departments` | `system/Department.vue` | 部门管理 |
| `/system/logs/operation` | `system/OperationLog.vue` | 操作日志 |
| `/system/logs/login` | `system/LoginLog.vue` | 登录日志 |
| `/system/teacher-profiles` | `system/TeacherProfile.vue` | 教师档案 |
| `/edu/students` | `edu/Student.vue` | 学生管理 |
| `/edu/grades` | `edu/Grade.vue` | 年级管理 |
| `/edu/classes` | `edu/Class.vue` | 班级管理 |
| `/edu/courses` | `edu/Course.vue` | 课程管理 |
| `/edu/scores` | `edu/Score.vue` | 成绩管理 |
| `/edu/schedules` | `edu/Schedule.vue` | 课表管理 |
| `/edu/classrooms` | `edu/Classroom.vue` | 教室管理 |
| `/edu/student-profiles` | `edu/StudentProfile.vue` | 学籍档案 |
| `/edu/quality-records` | `edu/QualityRecord.vue` | 综合素质 |
| `/edu/teaching-plans` | `edu/TeachingPlan.vue` | 教学计划 |
| `/edu/lesson-plans` | `edu/LessonPlan.vue` | 教案管理 |
| `/edu/research-projects` | `edu/Research.vue` | 教研项目 |
| `/resource/list` | `resource/Resource.vue` | 资源列表 |
| `/resource/favorites` | `resource/Favorites.vue` | 我的收藏 |
| `/resource/recommend` | `resource/Recommend.vue` | 推荐资源 |
| `/exam/list` | `exam/Exam.vue` | 考试管理 |
| `/attendance/list` | `attendance/Attendance.vue` | 考勤记录 |
| `/notice/list` | `notice/Notice.vue` | 通知公告 |
| `/settings` | `settings/Settings.vue` | 系统设置 |

#### AI 功能路由（`meta.aiFeature: true`）

| 路由路径 | 组件 | 对应后端 API |
|----------|------|--------------|
| `/ai/chat` | `ai/Chat.vue` | `/api/v1/ai/chat/` |
| `/ai/learning-agent` | `ai/LearningAgent.vue` | `/api/v1/ai/learning-records/` |
| `/ai/learning-path` | `ai/LearningPath.vue` | `/api/v1/ai/diagnosis/` |
| `/ai/learning-records` | `ai/LearningRecord.vue` | `/api/v1/ai/learning-records/` |
| `/ai/teacher-assistant` | `ai/TeacherAssistant.vue` | `/api/v1/ai/teacher/` |

---

## 四、当前完成状态汇总

### 4.1 后端完成度

| 模块 | 文件数 | 完成率 | 说明 |
|------|--------|--------|------|
| models | 48 个 | ✅ 100% | 全部 ORM 模型完成 |
| schemas | 20 个 | ✅ ~90% | 部分 AI schemas 待扩展 |
| services | 29 个 | ✅ ~90% | AI service 逻辑待增强 |
| api/v1（基础） | 13 模块 | ✅ ~95% | 系统监控类待补全 |
| api/v1/ai（AI） | 4 文件 | 🔄 ~70% | 接口完整，内部逻辑待强化 |
| tests | 60+ 文件 | ✅ 500+ 用例通过 | |

### 4.2 前端完成度

| 模块 | 视图文件数 | API 文件数 | 完成率 |
|------|-----------|-----------|--------|
| auth | 1 | 1 | ✅ 100% |
| system | 8 | 7 | ✅ 95% |
| edu | 16 | 16 | ✅ 95% |
| exam | 7 | 2 | ✅ 95% |
| attendance | 2 | 2 | ✅ 90% |
| notice | 1 | 1 | ✅ 90% |
| resource | 3 | 3 | ✅ 90% |
| settings | 1 | 1 | ✅ 95% |
| student | 3 | 1 | ✅ 95% |
| extended | 5 | 1 | ✅ 100% |
| **ai** | **5** | **6** | **🔄 70%** |

---

## 五、Phase 6 开发计划：AI 模块深化

> 现有 AI 功能已实现接口层，Phase 6 聚焦**后端逻辑增强**、**前端体验打磨**和**系统监控补全**。

### 5.1 任务清单

| 任务 ID | 功能 | 优先级 | 预估工时 | 涉及目录 |
|---------|------|--------|----------|----------|
| T10 | AI 对话增强（流式/历史/会话管理） | **P0** | 2天 | `api/v1/ai/chat.py` + `views/ai/Chat.vue` |
| T11 | 学习诊断深化（能力画像+知识图谱） | **P0** | 3天 | `api/v1/ai/learning_diagnosis.py` + `views/ai/LearningAgent.vue` |
| T12 | 教师助手增强（AI 出题+教案生成） | **P1** | 2天 | `api/v1/ai/teacher_assistant.py` + `views/ai/TeacherAssistant.vue` |
| T13 | 系统监控补全（在线用户/定时任务/服务/缓存） | **P1** | 2天 | `api/v1/system/` + `views/system/` |
| T14 | 学习路径可视化优化 | **P2** | 1天 | `views/ai/LearningPath.vue` |
| T15 | 前端 AI 侧边栏导航整合 | **P2** | 1天 | `views/Layout.vue` |

### 5.2 分阶段执行计划

#### Phase 6-A：AI 核心功能（第1-5天）

**T10 - AI 对话增强**
```
后端：
  backend/app/api/v1/ai/chat.py          ← 增加流式 SSE、会话持久化
  backend/app/services/ai_service.py     ← 多模型路由逻辑增强
  backend/app/models/ai_model.py         ← 会话历史模型完善

前端：
  frontend/src/views/ai/Chat.vue         ← Markdown 渲染、打字机效果
  frontend/src/api/ai/chat.ts            ← EventSource 流式接入
```

**T11 - 学习诊断深化**
```
后端：
  backend/app/api/v1/ai/learning_diagnosis.py  ← 能力雷达图接口
  backend/app/services/ai_service.py           ← 知识点图谱计算

前端：
  frontend/src/views/ai/LearningAgent.vue      ← ECharts 能力雷达图
  frontend/src/api/ai/diagnosis.ts             ← 诊断接口完善
```

#### Phase 6-B：教师助手 & 监控（第6-9天）

**T12 - 教师助手增强**
```
后端：
  backend/app/api/v1/ai/teacher_assistant.py  ← AI 出题、教案模板生成
  backend/app/schemas/ai.py                   ← 出题请求/响应 Schema

前端：
  frontend/src/views/ai/TeacherAssistant.vue  ← 出题面板、教案编辑器
  frontend/src/api/ai/teacher.ts              ← 出题接口调用
```

**T13 - 系统监控补全**
```
后端（新建）：
  backend/app/api/v1/system/online_users.py   ← 在线用户
  backend/app/api/v1/system/scheduler.py      ← 定时任务
  backend/app/api/v1/system/monitor.py        ← 服务监控
  backend/app/api/v1/system/cache.py          ← 缓存监控

前端（新建）：
  frontend/src/views/system/OnlineUser.vue    ← 路由: /system/online-users
  frontend/src/views/system/Scheduler.vue     ← 路由: /system/scheduler
  frontend/src/views/system/Monitor.vue       ← 路由: /system/monitor
  frontend/src/views/system/Cache.vue         ← 路由: /system/cache
  frontend/src/api/system/monitor.ts          ← 监控 API
```

#### Phase 6-C：体验优化（第10-11天）

**T14 - 学习路径可视化**
```
前端：
  frontend/src/views/ai/LearningPath.vue      ← D3.js/ECharts 路径图
```

**T15 - 布局导航整合**
```
前端：
  frontend/src/views/Layout.vue               ← 侧边栏 AI 分组、角标提示
  frontend/src/router/index.ts                ← 补充 T13 新增路由
```

---

## 六、新增文件清单（Phase 6）

### 6.1 后端新增文件（8个）

| 文件路径 | 任务 | 说明 |
|----------|------|------|
| `backend/app/api/v1/system/online_users.py` | T13 | 在线用户监控 API |
| `backend/app/api/v1/system/scheduler.py` | T13 | 定时任务管理 API |
| `backend/app/api/v1/system/monitor.py` | T13 | 服务监控 API |
| `backend/app/api/v1/system/cache.py` | T13 | 缓存监控 API |
| `backend/tests/test_task11_online_users.py` | T13 | 在线用户测试 |
| `backend/tests/test_task12_scheduler.py` | T13 | 定时任务测试 |
| `backend/tests/test_task13_service_monitor.py` | T13 | 服务监控测试 |
| `backend/tests/test_task14_cache_monitor.py` | T13 | 缓存监控测试 |

### 6.2 前端新增文件（9个）

| 文件路径 | 任务 | 路由 |
|----------|------|------|
| `frontend/src/views/system/OnlineUser.vue` | T13 | `/system/online-users` |
| `frontend/src/views/system/Scheduler.vue` | T13 | `/system/scheduler` |
| `frontend/src/views/system/Monitor.vue` | T13 | `/system/monitor` |
| `frontend/src/views/system/Cache.vue` | T13 | `/system/cache` |
| `frontend/src/api/system/monitor.ts` | T13 | — |
| `frontend/src/api/system/online_user.ts` | T13 | — |
| `frontend/src/api/system/scheduler.ts` | T13 | — |

---

## 七、命名规范

### 7.1 后端命名规范

| 层次 | 命名方式 | 示例 |
|------|----------|------|
| 文件名 | snake_case | `teacher_assistant.py` |
| 类名 | PascalCase | `TeacherAssistant` |
| 函数名 | snake_case | `get_lesson_plan` |
| API 路径 | kebab-case | `/api/v1/ai/teacher-assistant/` |
| 基础管理路由 | `/api/v1/{module}/` | `/api/v1/edu/` |
| AI 功能路由 | `/api/v1/ai/{module}/` | `/api/v1/ai/chat/` |

### 7.2 前端命名规范

| 层次 | 命名方式 | 示例 |
|------|----------|------|
| 视图文件 | PascalCase | `TeacherAssistant.vue` |
| API 文件 | snake_case | `teacher.ts` |
| 路由名称 | PascalCase | `TeacherAssistant` |
| 基础路由路径 | `/{module}/{page}` | `/edu/classes` |
| AI 路由路径 | `/ai/{feature}` | `/ai/teacher-assistant` |
| `meta.module` | 模块标识 | `'ai'` / `'edu'` |
| AI 页面标记 | `meta.aiFeature` | `true` |

---

## 八、开发工作流

### 8.1 新增功能标准步骤

```
1. 后端
   ├── 新建 models/{name}.py           ← ORM 模型
   ├── 新建 schemas/{name}.py          ← Pydantic Schema
   ├── 新建 services/{name}_service.py ← 业务逻辑
   ├── 新建 api/v1/{module}/{name}.py  ← FastAPI Router
   └── 注册到 api/v1/__init__.py       ← 加入 api_router 或 ai_api_router

2. 前端
   ├── 新建 api/{module}/{name}.ts     ← Axios 请求封装
   ├── 新建 views/{module}/{Name}.vue  ← 页面组件
   └── 注册到 router/index.ts          ← 加入路由配置

3. 测试
   ├── 新建 backend/tests/test_{name}.py
   └── 新建 frontend/tests/unit/{name}.test.ts
```

### 8.2 AI 功能专属步骤

```
后端 AI 接口：
  ├── 在 api/v1/ai/ 下新建 {name}.py
  ├── 路由路径格式：/api/v1/ai/{name}/
  └── 注册到 api/v1/ai/__init__.py → 汇入 ai_api_router

前端 AI 页面：
  ├── 在 views/ai/ 下新建 {Name}.vue
  ├── 在 api/ai/ 下新建 {name}.ts
  ├── 路由路径格式：/ai/{feature}
  └── meta 必须包含：{ module: 'ai', aiFeature: true }
```

---

## 九、里程碑计划

| 里程碑 | 内容 | 目标日期 |
|--------|------|----------|
| **M1** | Phase 1-5 全部交付（T1-T9） | ✅ 2026-04-10 完成 |
| **M2** | AI 路由分离重构（前后端目录规范化） | ✅ 2026-04-12 完成 |
| **M3** | Phase 6-A：AI 对话 + 学习诊断深化（T10/T11） | 2026-04-14 |
| **M4** | Phase 6-B：教师助手 + 系统监控（T12/T13） | 2026-04-18 |
| **M5** | Phase 6-C：体验优化 + 路由完善（T14/T15） | 2026-04-20 |
| **M6** | 全量测试 + 联调 + 部署准备 | 2026-04-22 |

---

*文档维护人：开发团队*  
*最后更新：2026-04-12*
