<template>
  <div class="md-editor" :data-theme="theme">
    <!-- 工具栏 -->
    <div v-if="showToolbar" class="md-toolbar">
      <div class="toolbar-group">
        <button class="tool-btn" title="清空" @click="clearEditor">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="18" height="18" rx="2"/><line x1="9" y1="9" x2="15" y2="15"/><line x1="15" y1="9" x2="9" y2="15"/></svg>
        </button>
        <button class="tool-btn" title="插入表格" @click="insertTable">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="4 7 4 4 20 4 20 7"/><line x1="9" y1="20" x2="15" y2="20"/><line x1="12" y1="4" x2="12" y2="20"/></svg>
        </button>
        <button class="tool-btn" title="插入代码块" @click="insertCodeBlock">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="16 18 22 12 16 6"/><polyline points="8 6 2 12 8 18"/></svg>
        </button>
      </div>
      <div class="toolbar-divider"></div>
      <div class="toolbar-group">
        <button class="tool-btn" title="标题" @click="insertHeading">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="8" y1="6" x2="21" y2="6"/><line x1="8" y1="12" x2="21" y2="12"/><line x1="8" y1="18" x2="21" y2="18"/><line x1="3" y1="6" x2="3.01" y2="6"/><line x1="3" y1="12" x2="3.01" y2="12"/><line x1="3" y1="18" x2="3.01" y2="18"/></svg>
        </button>
        <button class="tool-btn" title="粗体" @click="insertBold">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M6 4h8a4 4 0 0 1 4 4 4 4 0 0 1-4 4H6z"/><path d="M6 12h9a4 4 0 0 1 4 4 4 4 0 0 1-4 4H6z"/></svg>
        </button>
        <button class="tool-btn" title="斜体" @click="insertItalic">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="19" y1="4" x2="10" y2="4"/><line x1="14" y1="20" x2="5" y2="20"/><line x1="15" y1="4" x2="9" y2="20"/></svg>
        </button>
        <button class="tool-btn" title="链接" @click="insertLink">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/></svg>
        </button>
        <button class="tool-btn" title="列表" @click="insertList">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="8" y1="6" x2="21" y2="6"/><line x1="8" y1="12" x2="21" y2="12"/><line x1="8" y1="18" x2="21" y2="18"/><line x1="3" y1="6" x2="3.01" y2="6"/><line x1="3" y1="12" x2="3.01" y2="12"/><line x1="3" y1="18" x2="3.01" y2="18"/></svg>
        </button>
      </div>
      <div class="toolbar-divider"></div>
      <!-- 视图模式切换 -->
      <div class="mode-toggle-group">
        <button
          class="mode-btn"
          :class="{ active: internalMode === 'edit' }"
          title="编辑"
          @click="internalMode = 'edit'"
        >
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>
        </button>
        <button
          class="mode-btn"
          :class="{ active: internalMode === 'preview' }"
          title="预览"
          @click="internalMode = 'preview'"
        >
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>
        </button>
        <button
          class="mode-btn"
          :class="{ active: internalMode === 'split' }"
          title="分屏"
          @click="internalMode = 'split'"
        >
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="18" height="18" rx="2"/><line x1="12" y1="3" x2="12" y2="21"/></svg>
        </button>
      </div>
      <div class="toolbar-divider"></div>
      <!-- 主题切换 -->
      <button class="tool-btn theme-btn" title="切换主题" @click="toggleTheme">
        <svg v-if="theme === 'dark'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>
        <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/></svg>
      </button>
      <!-- 状态栏 -->
      <div class="toolbar-status">
        <span class="cursor-pos">{{ cursorPosition }}</span>
        <span class="word-count">{{ wordCount }}</span>
      </div>
    </div>

    <!-- 内容区域 -->
    <div class="md-content" :style="{ height: editorHeight }">
      <!-- 编辑面板 -->
      <div v-show="internalMode === 'edit' || internalMode === 'split'" class="pane editor-pane">
        <div class="editor-wrapper">
          <div ref="lineNumbersRef" class="line-numbers">
            <span
              v-for="n in lineCount"
              :key="n"
              :class="{ 'active-line': n === currentLine }"
            >{{ n }}</span>
          </div>
          <textarea
            ref="editorRef"
            class="editor"
            :value="modelValue"
            :placeholder="placeholder"
            :readonly="readonly"
            @input="onInput"
            @keyup="updateCursorInfo"
            @mouseup="updateCursorInfo"
            @click="updateCursorInfo"
            @scroll="syncLineScroll"
            @keydown="onKeydown"
          />
        </div>
      </div>

      <!-- 分屏分隔线 -->
      <div v-if="internalMode === 'split'" class="split-divider"></div>

      <!-- 预览面板 -->
      <div v-show="internalMode === 'preview' || internalMode === 'split'" class="pane preview-pane">
        <div ref="previewRef" class="preview" v-html="renderedHtml"></div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { marked } from 'marked'

// ==================== Props & Emits ====================

const props = withDefaults(defineProps<{
  modelValue: string
  mode?: 'edit' | 'preview' | 'split'
  placeholder?: string
  height?: string
  readonly?: boolean
  showToolbar?: boolean
  showMindMap?: boolean
  theme?: 'dark' | 'light'
}>(), {
  modelValue: '',
  mode: 'split',
  placeholder: '使用 Markdown 编写...',
  height: '500px',
  readonly: false,
  showToolbar: true,
  showMindMap: false,
  theme: 'dark',
})

const emit = defineEmits<{
  'update:modelValue': [value: string]
  'change': [value: string]
  'save': [value: string]
}>()

// ==================== Refs ====================

const editorRef = ref<HTMLTextAreaElement | null>(null)
const lineNumbersRef = ref<HTMLDivElement | null>(null)
const previewRef = ref<HTMLDivElement | null>(null)

const internalMode = ref<'edit' | 'preview' | 'split'>(props.mode)
const internalTheme = ref<'dark' | 'light'>(props.theme)
const currentLine = ref(1)
const currentCol = ref(1)

// ==================== Computed ====================

const editorHeight = computed(() => props.height)

const lineCount = computed(() => {
  if (!props.modelValue) return 1
  return props.modelValue.split('\n').length
})

const cursorPosition = computed(() => `行 ${currentLine.value}，列 ${currentCol.value}`)

const wordCount = computed(() => {
  return `${props.modelValue.length} 字`
})

const renderedHtml = computed(() => {
  if (!props.modelValue) return ''
  try {
    return marked.parse(props.modelValue) as string
  } catch (e: any) {
    return `<p style="color:red;">解析错误: ${e.message}</p>`
  }
})

// ==================== Watchers ====================

watch(() => props.mode, (val) => {
  internalMode.value = val
})

watch(() => props.theme, (val) => {
  internalTheme.value = val
})

// ==================== Methods ====================

/** 编辑器输入处理 */
function onInput(e: Event) {
  const target = e.target as HTMLTextAreaElement
  const value = target.value
  emit('update:modelValue', value)
  emit('change', value)
  updateCursorInfo()
}

/** 键盘事件（Tab 缩进、Ctrl+S 保存） */
function onKeydown(e: KeyboardEvent) {
  const textarea = editorRef.value
  if (!textarea) return

  // Tab 键插入缩进
  if (e.key === 'Tab') {
    e.preventDefault()
    const start = textarea.selectionStart
    const end = textarea.selectionEnd
    const value = textarea.value
    const newValue = value.substring(0, start) + '    ' + value.substring(end)
    emit('update:modelValue', newValue)
    nextTick(() => {
      textarea.selectionStart = textarea.selectionEnd = start + 4
    })
    return
  }

  // Ctrl+S / Cmd+S 保存
  if ((e.ctrlKey || e.metaKey) && e.key === 's') {
    e.preventDefault()
    emit('save', props.modelValue)
  }
}

/** 更新光标位置信息 */
function updateCursorInfo() {
  const textarea = editorRef.value
  if (!textarea) return
  const value = textarea.value
  const pos = textarea.selectionStart || 0
  const lines = value.substring(0, pos).split('\n')
  currentLine.value = lines.length
  currentCol.value = lines[lines.length - 1].length + 1
}

/** 同步行号滚动 */
function syncLineScroll() {
  const textarea = editorRef.value
  const lineNums = lineNumbersRef.value
  if (textarea && lineNums) {
    lineNums.scrollTop = textarea.scrollTop
  }
}

/** 在光标位置插入文本 */
function insertAtCursor(text: string) {
  const textarea = editorRef.value
  if (!textarea || props.readonly) return
  const start = textarea.selectionStart
  const end = textarea.selectionEnd
  const value = textarea.value
  const newValue = value.substring(0, start) + text + value.substring(end)
  emit('update:modelValue', newValue)
  emit('change', newValue)
  nextTick(() => {
    textarea.selectionStart = textarea.selectionEnd = start + text.length
    textarea.focus()
  })
}

/** 清空编辑器 */
function clearEditor() {
  if (props.readonly) return
  emit('update:modelValue', '')
  emit('change', '')
}

/** 插入标题 */
function insertHeading() {
  insertAtCursor('\n## 标题\n')
}

/** 插入粗体 */
function insertBold() {
  insertAtCursor('**粗体**')
}

/** 插入斜体 */
function insertItalic() {
  insertAtCursor('*斜体*')
}

/** 插入链接 */
function insertLink() {
  insertAtCursor('[链接](https://example.com)')
}

/** 插入列表 */
function insertList() {
  insertAtCursor('\n- 列表项1\n- 列表项2\n- 列表项3\n')
}

/** 插入代码块 */
function insertCodeBlock() {
  insertAtCursor('\n```javascript\n// 代码\n```\n')
}

/** 插入表格 */
function insertTable() {
  insertAtCursor('\n| 标题1 | 标题2 | 标题3 |\n| ------ | ------ | ------ |\n| 内容1 | 内容2 | 内容3 |\n')
}

/** 切换主题 */
function toggleTheme() {
  internalTheme.value = internalTheme.value === 'dark' ? 'light' : 'dark'
}

// ==================== Lifecycle ====================

onMounted(() => {
  updateCursorInfo()
})

onBeforeUnmount(() => {
  // 清理
})
</script>

<style scoped>
/* ========== 主题变量 ========== */
.md-editor[data-theme="dark"] {
  --bg-base: #0f1117;
  --bg-panel: #1e222b;
  --bg-editor: #181b23;
  --bg-elevated: #262a35;
  --border: #2d3340;
  --text-primary: #e8eaed;
  --text-muted: #9ca3af;
  --text-dim: #6b7280;
  --text-linenum: #3d4455;
  --accent: #f59e0b;
  --accent-text: #0f1117;
  --transition: background 0.25s, color 0.25s, border-color 0.25s;
}

.md-editor[data-theme="light"] {
  --bg-base: #f5f6fa;
  --bg-panel: #ffffff;
  --bg-editor: #fafbfc;
  --bg-elevated: #eef0f4;
  --border: #d1d5db;
  --text-primary: #1a1d23;
  --text-muted: #4b5563;
  --text-dim: #9ca3af;
  --text-linenum: #b0b8c8;
  --accent: #d97706;
  --accent-text: #ffffff;
  --transition: background 0.25s, color 0.25s, border-color 0.25s;
}

/* ========== 编辑器容器 ========== */
.md-editor {
  display: flex;
  flex-direction: column;
  background: var(--bg-base);
  color: var(--text-primary);
  border: 1px solid var(--border);
  border-radius: 8px;
  overflow: hidden;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', sans-serif;
  transition: var(--transition);
}

/* ========== 工具栏 ========== */
.md-toolbar {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 16px;
  background: var(--bg-panel);
  flex-shrink: 0;
  border-bottom: 1px solid var(--border);
}

.toolbar-group {
  display: flex;
  gap: 4px;
}

.tool-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 34px;
  height: 34px;
  border-radius: 6px;
  background: var(--bg-elevated);
  border: 1px solid var(--border);
  color: var(--text-muted);
  cursor: pointer;
  transition: all 0.2s;
  padding: 0;
}

.tool-btn svg {
  width: 16px;
  height: 16px;
}

.tool-btn:hover {
  background: var(--bg-panel);
  color: var(--accent);
  border-color: var(--accent);
}

.tool-btn.theme-btn {
  width: 30px;
  height: 30px;
}

.toolbar-divider {
  width: 1px;
  height: 22px;
  background: var(--border);
  margin: 0 6px;
}

/* ========== 模式切换 ========== */
.mode-toggle-group {
  display: flex;
  gap: 4px;
}

.mode-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 30px;
  height: 30px;
  border-radius: 6px;
  background: var(--bg-elevated);
  border: 1px solid var(--border);
  color: var(--text-muted);
  cursor: pointer;
  transition: all 0.2s;
  padding: 0;
}

.mode-btn svg {
  width: 15px;
  height: 15px;
}

.mode-btn.active {
  background: var(--accent);
  border-color: var(--accent);
  color: var(--accent-text);
}

.mode-btn:hover:not(.active) {
  background: var(--border);
  color: var(--text-primary);
}

/* ========== 状态栏 ========== */
.toolbar-status {
  margin-left: auto;
  display: flex;
  gap: 10px;
  align-items: center;
}

.word-count {
  font-size: 12px;
  color: var(--text-dim);
  padding: 3px 10px;
  background: var(--bg-elevated);
  border-radius: 10px;
  white-space: nowrap;
}

.cursor-pos {
  font-size: 12px;
  color: var(--text-dim);
  padding: 3px 10px;
  background: var(--bg-elevated);
  border-radius: 10px;
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
  white-space: nowrap;
}

/* ========== 内容区域 ========== */
.md-content {
  flex: 1;
  display: flex;
  overflow: hidden;
  min-width: 0;
}

.pane {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.editor-pane {
  background: var(--bg-editor);
}

.preview-pane {
  background: var(--bg-editor);
}

.split-divider {
  width: 1px;
  background: var(--border);
  flex-shrink: 0;
}

/* ========== 编辑器 ========== */
.editor-wrapper {
  display: flex;
  flex: 1;
  min-width: 0;
  overflow: hidden;
  background: var(--bg-editor);
  height: 100%;
}

.line-numbers {
  flex-shrink: 0;
  align-self: stretch;
  width: 48px;
  padding: 16px 0;
  background: var(--bg-editor);
  border-right: 1px solid var(--border);
  overflow: hidden;
  user-select: none;
  text-align: right;
  transition: var(--transition);
}

.line-numbers span {
  display: block;
  padding-right: 10px;
  font-size: 13px;
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
  line-height: 1.6;
  height: 20.8px;
  color: var(--text-linenum);
  transition: color 0.1s;
}

.line-numbers span.active-line {
  color: var(--accent);
  font-weight: 600;
}

.editor {
  flex: 1;
  min-width: 0;
  align-self: stretch;
  padding: 16px 16px 16px 12px;
  background: var(--bg-editor);
  border: none;
  color: var(--text-primary);
  font-size: 13px;
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
  line-height: 1.6;
  resize: none;
  outline: none;
  tab-size: 4;
  white-space: pre;
  overflow-wrap: normal;
  overflow-x: auto;
  overflow-y: auto;
  transition: var(--transition);
}

.editor:focus {
  outline: none;
}

.editor::placeholder {
  color: var(--text-dim);
}

/* ========== 预览区 ========== */
.preview {
  min-width: 0;
  padding: 20px;
  background: var(--bg-editor);
  color: var(--text-muted);
  line-height: 1.8;
  overflow-y: auto;
  height: 100%;
  transition: var(--transition);
}

.preview :deep(h1) {
  font-size: 24px;
  color: var(--accent);
  margin-bottom: 16px;
  border-bottom: 1px solid var(--border);
  padding-bottom: 8px;
}

.preview :deep(h2) {
  font-size: 20px;
  color: var(--text-primary);
  margin: 16px 0 12px;
}

.preview :deep(h3) {
  font-size: 16px;
  color: var(--text-primary);
  margin: 12px 0 8px;
}

.preview :deep(h4) {
  font-size: 14px;
  color: var(--text-primary);
  margin: 10px 0 6px;
}

.preview :deep(p) {
  margin-bottom: 12px;
  white-space: pre-wrap;
  word-wrap: break-word;
}

.preview :deep(ul),
.preview :deep(ol) {
  margin: 8px 0;
  padding-left: 24px;
}

.preview :deep(li) {
  margin-bottom: 4px;
}

.preview :deep(code) {
  background: var(--bg-elevated);
  padding: 2px 6px;
  border-radius: 4px;
  font-family: 'Consolas', monospace;
  color: var(--text-primary);
  font-size: 0.9em;
}

.preview :deep(pre) {
  background: var(--bg-elevated);
  padding: 12px;
  border-radius: 8px;
  overflow-x: auto;
}

.preview :deep(pre code) {
  background: transparent;
  padding: 0;
}

.preview :deep(table) {
  width: 100%;
  border-collapse: collapse;
  margin: 12px 0;
}

.preview :deep(th),
.preview :deep(td) {
  border: 1px solid var(--border);
  padding: 8px 12px;
  text-align: left;
}

.preview :deep(th) {
  background: var(--bg-elevated);
  color: var(--text-primary);
}

.preview :deep(blockquote) {
  border-left: 4px solid var(--accent);
  padding-left: 16px;
  margin: 12px 0;
  color: var(--text-dim);
}

.preview :deep(a) {
  color: var(--accent);
}

.preview :deep(img) {
  max-width: 100%;
}

.preview :deep(hr) {
  border: none;
  border-top: 1px solid var(--border);
  margin: 16px 0;
}
</style>
