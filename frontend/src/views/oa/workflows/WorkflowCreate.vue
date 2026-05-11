<template>
  <div class="workflow-create">
    <el-card>
      <template #header>
        <div class="card-header">
          <el-page-header @back="handleBack" title="返回">
            <template #content>
              <span class="page-title">{{ isEdit ? '编辑工作流' : '新建工作流' }}</span>
            </template>
          </el-page-header>
        </div>
      </template>

      <el-steps :active="activeStep" finish-status="success" class="workflow-steps">
        <el-step title="基本信息" description="填写工作流基本属性" />
        <el-step title="流程设计" description="设计审批节点和流程" />
        <el-step title="表单配置" description="配置发起审批时的表单字段" />
        <el-step title="权限设置" description="配置权限和选项" />
      </el-steps>

      <div class="step-content">
        <!-- 步骤1: 基本信息 -->
        <div v-show="activeStep === 0" class="step-panel">
          <el-form ref="basicFormRef" :model="basicForm" :rules="basicRules" label-width="120px">
            <el-form-item label="工作流名称" prop="name">
              <el-input v-model="basicForm.name" placeholder="请输入工作流名称" maxlength="100" show-word-limit />
            </el-form-item>
            <el-form-item label="工作流编码" prop="code" v-if="!isEdit">
              <el-input v-model="basicForm.code" placeholder="请输入唯一编码，如 leave_request" maxlength="50" />
              <div class="form-tip">编码只能包含字母、数字和下划线，用于系统内部标识</div>
            </el-form-item>
            <el-form-item label="工作流分类" prop="category">
              <el-select v-model="basicForm.category" placeholder="请选择分类">
                <el-option label="请假类" value="leave" />
                <el-option label="报销类" value="reimburse" />
                <el-option label="采购类" value="purchase" />
                <el-option label="用车类" value="vehicle" />
                <el-option label="人事类" value="hr" />
                <el-option label="通用类" value="general" />
              </el-select>
            </el-form-item>
            <el-form-item label="业务类型" prop="business_type">
              <el-input v-model="basicForm.business_type" placeholder="请输入关联业务类型" maxlength="50" />
              <div class="form-tip">用于关联具体业务数据，如 leave、reimburse 等</div>
            </el-form-item>
            <el-form-item label="描述" prop="description">
              <el-input v-model="basicForm.description" type="textarea" :rows="4" placeholder="请输入工作流描述" maxlength="500" show-word-limit />
            </el-form-item>
            <el-form-item label="版本号" prop="version" v-if="isEdit">
              <el-input-number v-model="basicForm.version" :min="1" :max="99" />
              <div class="form-tip">每次发布新版本需要递增版本号</div>
            </el-form-item>
          </el-form>
        </div>

        <!-- 步骤2: 流程设计 -->
        <div v-show="activeStep === 1" class="step-panel">
          <div class="flow-design-header">
            <el-button type="primary" @click="handleAddNode('START')" plain>
              <el-icon><Plus /></el-icon> 添加开始节点
            </el-button>
            <el-button type="primary" @click="handleAddNode('APPROVAL')" plain>
              <el-icon><Plus /></el-icon> 添加审批节点
            </el-button>
            <el-button type="primary" @click="handleAddNode('CONDITION')" plain>
              <el-icon><Plus /></el-icon> 添加条件节点
            </el-button>
            <el-button type="primary" @click="handleAddNode('CC')" plain>
              <el-icon><Plus /></el-icon> 添加抄送节点
            </el-button>
            <el-button type="primary" @click="handleAddNode('END')" plain>
              <el-icon><Plus /></el-icon> 添加结束节点
            </el-button>
          </div>

          <div class="flow-canvas" ref="flowCanvasRef">
            <div class="flow-nodes">
              <div
                v-for="(node, index) in flowNodes"
                :key="node.id"
                class="flow-node"
                :class="[`node-${node.node_type.toLowerCase()}`, { 'node-selected': selectedNodeId === node.id }]"
                :style="{ left: node.x + 'px', top: node.y + 'px' }"
                @click="handleSelectNode(node)"
              >
                <div class="node-icon">
                  <el-icon v-if="node.node_type === 'START'"><VideoPlay /></el-icon>
                  <el-icon v-else-if="node.node_type === 'END'"><CircleCheck /></el-icon>
                  <el-icon v-else-if="node.node_type === 'APPROVAL'"><User /></el-icon>
                  <el-icon v-else-if="node.node_type === 'CONDITION'"><Switch /></el-icon>
                  <el-icon v-else-if="node.node_type === 'CC'"><Message /></el-icon>
                </div>
                <div class="node-info">
                  <div class="node-name">{{ node.name }}</div>
                  <div class="node-type">{{ getNodeTypeLabel(node.node_type) }}</div>
                </div>
                <div class="node-actions" v-if="selectedNodeId === node.id">
                  <el-button
                    v-if="index > 0"
                    type="primary"
                    link
                    size="small"
                    @click.stop="handleMoveUp(index)"
                    title="上移"
                  >
                    <el-icon><ArrowUp /></el-icon>
                  </el-button>
                  <el-button
                    v-if="index < flowNodes.length - 1"
                    type="primary"
                    link
                    size="small"
                    @click.stop="handleMoveDown(index)"
                    title="下移"
                  >
                    <el-icon><ArrowDown /></el-icon>
                  </el-button>
                  <el-button
                    type="danger"
                    link
                    size="small"
                    @click.stop="handleDeleteNode(node.id)"
                    title="删除"
                  >
                    <el-icon><Delete /></el-icon>
                  </el-button>
                </div>
              </div>
            </div>

            <!-- 节点编辑面板 -->
            <div v-if="selectedNode" class="node-edit-panel">
              <div class="panel-header">
                <span>节点配置 - {{ selectedNode.name }}</span>
                <el-button link @click="selectedNodeId = null"><el-icon><Close /></el-icon></el-button>
              </div>
              <el-form :model="selectedNode" label-width="100px" size="small">
                <el-form-item label="节点名称">
                  <el-input v-model="selectedNode.name" placeholder="请输入节点名称" />
                </el-form-item>
                <el-form-item label="节点编码">
                  <el-input v-model="selectedNode.code" placeholder="请输入节点编码" />
                </el-form-item>
                <el-form-item label="节点类型" v-if="selectedNode.node_type !== 'START' && selectedNode.node_type !== 'END'">
                  <el-select v-model="selectedNode.node_type" placeholder="请选择">
                    <el-option label="审批节点" value="APPROVAL" />
                    <el-option label="条件节点" value="CONDITION" />
                    <el-option label="抄送节点" value="CC" />
                  </el-select>
                </el-form-item>

                <!-- 审批节点配置 -->
                <template v-if="selectedNode.node_type === 'APPROVAL'">
                  <el-form-item label="审批人类型">
                    <el-select v-model="selectedNode.approver_type" placeholder="请选择">
                      <el-option label="指定用户" value="USER" />
                      <el-option label="指定角色" value="ROLE" />
                      <el-option label="部门负责人" value="DEPARTMENT_LEADER" />
                      <el-option label="直接主管" value="DIRECT_MANAGER" />
                      <el-option label="多级审批" value="MULTI_LEVEL" />
                    </el-select>
                  </el-form-item>
                  <el-form-item label="审批人" v-if="selectedNode.approver_type === 'USER'">
                    <el-select v-model="selectedNode.approver_ids" multiple filterable placeholder="请选择审批人" style="width: 100%">
                      <el-option v-for="user in userList" :key="user.id" :label="user.name" :value="user.id" />
                    </el-select>
                  </el-form-item>
                  <el-form-item label="角色" v-if="selectedNode.approver_type === 'ROLE'">
                    <el-select v-model="selectedNode.role_ids" multiple filterable placeholder="请选择角色" style="width: 100%">
                      <el-option v-for="role in roleList" :key="role.id" :label="role.name" :value="role.id" />
                    </el-select>
                  </el-form-item>
                  <el-form-item label="超时时限">
                    <el-input-number v-model="selectedNode.timeout_hours" :min="0" :max="720" />
                    <span class="unit">小时 (0表示不超时)</span>
                  </el-form-item>
                  <el-form-item label="超时动作">
                    <el-select v-model="selectedNode.timeout_action" placeholder="请选择">
                      <el-option label="通知" value="NOTIFY" />
                      <el-option label="自动通过" value="AUTO_APPROVE" />
                      <el-option label="跳过" value="SKIP" />
                    </el-select>
                  </el-form-item>
                </template>

                <!-- 条件节点配置 -->
                <template v-if="selectedNode.node_type === 'CONDITION'">
                  <el-form-item label="条件表达式">
                    <el-input v-model="selectedNode.condition_expression" type="textarea" :rows="3" placeholder="请输入条件表达式，如: form.amount > 1000" />
                    <div class="form-tip">支持变量: form.xxx, workflow.initiator</div>
                  </el-form-item>
                </template>

                <!-- 抄送节点配置 -->
                <template v-if="selectedNode.node_type === 'CC'">
                  <el-form-item label="抄送人类型">
                    <el-select v-model="selectedNode.cc_type" placeholder="请选择">
                      <el-option label="指定用户" value="USER" />
                      <el-option label="发起人" value="INITIATOR" />
                    </el-select>
                  </el-form-item>
                  <el-form-item label="抄送人" v-if="selectedNode.cc_type === 'USER'">
                    <el-select v-model="selectedNode.cc_user_ids" multiple filterable placeholder="请选择抄送人" style="width: 100%">
                      <el-option v-for="user in userList" :key="user.id" :label="user.name" :value="user.id" />
                    </el-select>
                  </el-form-item>
                </template>
              </el-form>
            </div>

            <!-- 空白状态 -->
            <div v-if="flowNodes.length === 0" class="flow-empty">
              <el-empty description="暂无节点，请点击上方按钮添加节点">
                <template #image>
                  <svg width="120" height="120" viewBox="0 0 120 120">
                    <rect x="10" y="45" width="30" height="30" rx="4" fill="#409EFF" opacity="0.3" />
                    <rect x="45" y="45" width="30" height="30" rx="4" fill="#67C23A" opacity="0.3" />
                    <rect x="80" y="45" width="30" height="30" rx="4" fill="#E6A23C" opacity="0.3" />
                    <line x1="40" y1="60" x2="45" y2="60" stroke="#909399" stroke-width="2" stroke-dasharray="3" />
                    <line x1="75" y1="60" x2="80" y2="60" stroke="#909399" stroke-width="2" stroke-dasharray="3" />
                  </svg>
                </template>
              </el-empty>
            </div>
          </div>
        </div>

        <!-- 步骤3: 表单配置 -->
        <div v-show="activeStep === 2" class="step-panel">
          <div class="form-design-header">
            <el-button type="primary" @click="handleAddField" plain>
              <el-icon><Plus /></el-icon> 添加字段
            </el-button>
          </div>

          <el-table :data="formFields" border style="width: 100%">
            <el-table-column type="index" label="序号" width="60" />
            <el-table-column label="字段名称" prop="label" min-width="120">
              <template #default="{ row }">
                <el-input v-model="row.label" placeholder="字段显示名称" />
              </template>
            </el-table-column>
            <el-table-column label="字段编码" prop="name" min-width="120">
              <template #default="{ row }">
                <el-input v-model="row.name" placeholder="字段唯一标识" :disabled="row.isSystem" />
              </template>
            </el-table-column>
            <el-table-column label="字段类型" prop="type" width="140">
              <template #default="{ row }">
                <el-select v-model="row.type" placeholder="请选择" :disabled="row.isSystem">
                  <el-option label="单行文本" value="text" />
                  <el-option label="多行文本" value="textarea" />
                  <el-option label="数字" value="number" />
                  <el-option label="日期" value="date" />
                  <el-option label="日期时间" value="datetime" />
                  <el-option label="单选" value="radio" />
                  <el-option label="多选" value="checkbox" />
                  <el-option label="下拉选择" value="select" />
                  <el-option label="附件" value="file" />
                </el-select>
              </template>
            </el-table-column>
            <el-table-column label="占位提示" prop="placeholder" min-width="140">
              <template #default="{ row }">
                <el-input v-model="row.placeholder" placeholder="提示信息" />
              </template>
            </el-table-column>
            <el-table-column label="必填" prop="required" width="70" align="center">
              <template #default="{ row }">
                <el-checkbox v-model="row.required" :disabled="row.isSystem" />
              </template>
            </el-table-column>
            <el-table-column label="可编辑" prop="editable" width="70" align="center">
              <template #default="{ row }">
                <el-checkbox v-model="row.editable" />
              </template>
            </el-table-column>
            <el-table-column label="操作" width="80" align="center">
              <template #default="{ row, $index }">
                <el-button type="danger" link size="small" @click="handleDeleteField($index)" :disabled="row.isSystem">
                  删除
                </el-button>
              </template>
            </el-table-column>
          </el-table>

          <div class="form-tip" style="margin-top: 16px">
            <strong>提示：</strong>系统会默认添加"标题"和"说明"两个字段，审批过程中审批人可查看但不能修改。
          </div>
        </div>

        <!-- 步骤4: 权限设置 -->
        <div v-show="activeStep === 3" class="step-panel">
          <el-form :model="permissionForm" label-width="140px">
            <el-form-item label="是否启用">
              <el-switch v-model="permissionForm.is_active" />
              <span class="form-tip" style="margin-left: 12px">停用后无法发起新的审批</span>
            </el-form-item>

            <el-divider content-position="left">流程操作权限</el-divider>

            <el-form-item label="允许撤回">
              <el-switch v-model="permissionForm.allow_withdraw" />
              <span class="form-tip" style="margin-left: 12px">发起人可在审批完成前撤回申请</span>
            </el-form-item>

            <el-form-item label="允许转交">
              <el-switch v-model="permissionForm.allow_transfer" />
              <span class="form-tip" style="margin-left: 12px">审批人可将任务转交给其他人</span>
            </el-form-item>

            <el-form-item label="允许抄送">
              <el-switch v-model="permissionForm.allow_cc" />
              <span class="form-tip" style="margin-left: 12px">发起人可抄送相关人员知悉</span>
            </el-form-item>

            <el-form-item label="允许催办">
              <el-switch v-model="permissionForm.allow_urge" />
              <span class="form-tip" style="margin-left: 12px">发起人可催促审批人尽快处理</span>
            </el-form-item>

            <el-divider content-position="left">发起权限</el-divider>

            <el-form-item label="允许所有人发起">
              <el-switch v-model="permissionForm.allow_all_initiator" />
              <span class="form-tip" style="margin-left: 12px">关闭后需配置可发起的人员范围</span>
            </el-form-item>

            <el-form-item label="可发起角色" v-if="!permissionForm.allow_all_initiator">
              <el-select v-model="permissionForm.allowed_roles" multiple filterable placeholder="请选择可发起的角色" style="width: 100%">
                <el-option v-for="role in roleList" :key="role.id" :label="role.name" :value="role.id" />
              </el-select>
            </el-form-item>

            <el-form-item label="可发起部门" v-if="!permissionForm.allow_all_initiator">
              <el-cascader
                v-model="permissionForm.allowed_departments"
                :options="departmentTree"
                :props="{ value: 'id', label: 'name', children: 'children' }"
                placeholder="请选择可发起的部门"
                multiple
                collapse-tags
                clearable
                style="width: 100%"
              />
            </el-form-item>
          </el-form>
        </div>
      </div>

      <div class="step-actions">
        <el-button @click="handleBack">取消</el-button>
        <el-button v-if="activeStep > 0" @click="handlePrev">上一步</el-button>
        <el-button v-if="activeStep < 3" type="primary" @click="handleNext">下一步</el-button>
        <el-button v-if="activeStep === 3" type="primary" :loading="submitting" @click="handleSubmit">
          {{ isEdit ? '保存修改' : '创建工作流' }}
        </el-button>
        <el-button v-if="activeStep === 3 && isEdit && !permissionForm.is_active" type="success" @click="handlePublish">
          发布工作流
        </el-button>
      </div>
    </el-card>

    <!-- 添加字段对话框 -->
    <el-dialog v-model="fieldDialogVisible" title="添加表单字段" width="500px">
      <el-form :model="fieldForm" label-width="100px">
        <el-form-item label="字段类型">
          <el-select v-model="fieldForm.type" placeholder="请选择字段类型">
            <el-option label="单行文本" value="text" />
            <el-option label="多行文本" value="textarea" />
            <el-option label="数字" value="number" />
            <el-option label="日期" value="date" />
            <el-option label="日期时间" value="datetime" />
            <el-option label="单选" value="radio" />
            <el-option label="多选" value="checkbox" />
            <el-option label="下拉选择" value="select" />
            <el-option label="附件" value="file" />
          </el-select>
        </el-form-item>
        <el-form-item label="字段名称">
          <el-input v-model="fieldForm.label" placeholder="请输入字段显示名称" />
        </el-form-item>
        <el-form-item label="字段编码">
          <el-input v-model="fieldForm.name" placeholder="请输入字段唯一标识（英文）" />
        </el-form-item>
        <el-form-item label="占位提示">
          <el-input v-model="fieldForm.placeholder" placeholder="请输入提示信息" />
        </el-form-item>
        <el-form-item label="必填">
          <el-switch v-model="fieldForm.required" />
        </el-form-item>
        <el-form-item label="可编辑">
          <el-switch v-model="fieldForm.editable" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="fieldDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleConfirmAddField">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage, FormInstance, FormRules } from 'element-plus'
import {
  Plus, Delete, ArrowUp, ArrowDown, Close,
  VideoPlay, CircleCheck, User, Switch, Message
} from '@element-plus/icons-vue'
import { workflowApi } from '@/api/oa/workflows'
import { getUserOptions } from '@/api/system/user'
import { getRoleOptions, getDepartmentOptions } from '@/api/system/role'

const router = useRouter()
const route = useRoute()

// 状态
const activeStep = ref(0)
const submitting = ref(false)
const isEdit = computed(() => !!route.params.id)
const basicFormRef = ref<FormInstance>()
const flowCanvasRef = ref<HTMLElement>()
const selectedNodeId = ref<string | null>(null)
const fieldDialogVisible = ref(false)

// 用户列表
const userList = ref<any[]>([])
const roleList = ref<any[]>([])
const departmentTree = ref<any[]>([])

// 基本信息表单
const basicForm = reactive({
  name: '',
  code: '',
  category: 'general',
  business_type: '',
  description: '',
  version: 1
})

// 流程节点
const flowNodes = ref<any[]>([])

// 表单字段
const formFields = ref<any[]>([
  { name: 'title', label: '标题', type: 'text', required: true, editable: true, isSystem: true, placeholder: '请输入审批标题' },
  { name: 'reason', label: '说明', type: 'textarea', required: false, editable: true, isSystem: true, placeholder: '请输入审批说明' }
])

// 字段添加表单
const fieldForm = reactive({
  type: 'text',
  label: '',
  name: '',
  placeholder: '',
  required: false,
  editable: true
})

// 权限设置表单
const permissionForm = reactive({
  is_active: true,
  allow_withdraw: true,
  allow_transfer: true,
  allow_cc: true,
  allow_urge: true,
  allow_all_initiator: true,
  allowed_roles: [],
  allowed_departments: []
})

// 表单验证规则
const basicRules: FormRules = {
  name: [{ required: true, message: '请输入工作流名称', trigger: 'blur' }],
  code: [
    { required: true, message: '请输入工作流编码', trigger: 'blur' },
    { pattern: /^[a-z_][a-z0-9_]*$/, message: '编码只能包含小写字母、数字和下划线', trigger: 'blur' }
  ],
  category: [{ required: true, message: '请选择分类', trigger: 'change' }]
}

// 计算属性：当前选中的节点
const selectedNode = computed(() => {
  return flowNodes.value.find(n => n.id === selectedNodeId.value)
})

// 获取节点类型标签
const getNodeTypeLabel = (type: string) => {
  const map: Record<string, string> = {
    START: '开始',
    END: '结束',
    APPROVAL: '审批',
    CONDITION: '条件',
    CC: '抄送'
  }
  return map[type] || type
}

// 加载数据
const loadData = async () => {
  try {
    // 加载用户列表（用于审批人选择）
    try {
      const resUsers = await getUserOptions()
      userList.value = resUsers.data || []
    } catch (e) {
      console.warn('加载用户列表失败', e)
      userList.value = []
    }

    // 加载角色列表（用于审批角色选择）
    try {
      const resRoles = await getRoleOptions()
      roleList.value = resRoles.data || []
    } catch (e) {
      console.warn('加载角色列表失败', e)
      roleList.value = []
    }

    // 加载部门树（用于发起权限控制）
    try {
      const resDepts = await getDepartmentOptions()
      departmentTree.value = resDepts.data || []
    } catch (e) {
      console.warn('加载部门列表失败', e)
      departmentTree.value = []
    }

    if (isEdit.value) {
      const id = route.params.id as string
      const res = await workflowApi.getById(id)
      const data = res.data

      basicForm.name = data.name || ''
      basicForm.code = data.code || ''
      basicForm.category = data.category || 'general'
      basicForm.business_type = data.business_type || ''
      basicForm.description = data.description || ''
      basicForm.version = data.version || 1

      // 加载流程节点
      if (data.nodes && data.nodes.length > 0) {
        flowNodes.value = data.nodes.map((n: any, index: number) => ({
          id: n.id,
          name: n.name,
          code: n.code,
          node_type: n.node_type,
          x: 50 + (index % 4) * 200,
          y: 50 + Math.floor(index / 4) * 100,
          approver_type: n.approver_type,
          approver_ids: n.approver_ids || [],
          role_ids: n.role_ids || [],
          timeout_hours: n.timeout_hours,
          timeout_action: n.timeout_action,
          cc_type: n.cc_type,
          cc_user_ids: n.cc_user_ids || [],
          condition_expression: n.condition_expression
        }))
      }

      // 加载表单配置
      if (data.form_config && data.form_config.fields) {
        formFields.value = [
          { name: 'title', label: '标题', type: 'text', required: true, editable: true, isSystem: true, placeholder: '请输入审批标题' },
          { name: 'reason', label: '说明', type: 'textarea', required: false, editable: true, isSystem: true, placeholder: '请输入审批说明' },
          ...data.form_config.fields.filter((f: any) => !f.isSystem)
        ]
      }

      // 加载权限设置
      permissionForm.is_active = data.is_active ?? true
      permissionForm.allow_withdraw = data.allow_withdraw ?? true
      permissionForm.allow_transfer = data.allow_transfer ?? true
      permissionForm.allow_cc = data.allow_cc ?? true
      permissionForm.allow_urge = data.allow_urge ?? true
    } else {
      // 新建时添加默认的开始和结束节点
      flowNodes.value = [
        { id: 'start-' + Date.now(), name: '开始', node_type: 'START', x: 50, y: 150 },
        { id: 'end-' + Date.now(), name: '结束', node_type: 'END', x: 650, y: 150 }
      ]
    }
  } catch (error) {
    ElMessage.error('加载数据失败')
  }
}

// 添加节点
const handleAddNode = (type: string) => {
  const typeMap: Record<string, { name: string; node_type: string }> = {
    START: { name: '开始', node_type: 'START' },
    END: { name: '结束', node_type: 'END' },
    APPROVAL: { name: '审批节点', node_type: 'APPROVAL' },
    CONDITION: { name: '条件节点', node_type: 'CONDITION' },
    CC: { name: '抄送节点', node_type: 'CC' }
  }

  const config = typeMap[type]
  const nodeCount = flowNodes.value.filter(n => n.node_type === type).length + 1

  const newNode = {
    id: `${type.toLowerCase()}-${Date.now()}`,
    name: `${config.name}${nodeCount > 1 ? nodeCount : ''}`,
    code: `${type.toLowerCase()}_${nodeCount}`,
    node_type: config.node_type,
    x: 300,
    y: 50 + flowNodes.value.length * 100,
    approver_type: 'USER',
    approver_ids: [],
    role_ids: [],
    timeout_hours: 0,
    timeout_action: 'NOTIFY',
    cc_type: 'USER',
    cc_user_ids: [],
    condition_expression: ''
  }

  flowNodes.value.push(newNode)
  selectedNodeId.value = newNode.id
}

// 选择节点
const handleSelectNode = (node: any) => {
  selectedNodeId.value = node.id
}

// 删除节点
const handleDeleteNode = (nodeId: string) => {
  const node = flowNodes.value.find(n => n.id === nodeId)
  if (node && (node.node_type === 'START' || node.node_type === 'END')) {
    ElMessage.warning('不能删除开始和结束节点')
    return
  }

  const index = flowNodes.value.findIndex(n => n.id === nodeId)
  if (index > -1) {
    flowNodes.value.splice(index, 1)
    if (selectedNodeId.value === nodeId) {
      selectedNodeId.value = null
    }
    ElMessage.success('节点已删除')
  }
}

// 上移节点
const handleMoveUp = (index: number) => {
  if (index > 0) {
    const temp = flowNodes.value[index]
    flowNodes.value[index] = flowNodes.value[index - 1]
    flowNodes.value[index - 1] = temp
  }
}

// 下移节点
const handleMoveDown = (index: number) => {
  if (index < flowNodes.value.length - 1) {
    const temp = flowNodes.value[index]
    flowNodes.value[index] = flowNodes.value[index + 1]
    flowNodes.value[index + 1] = temp
  }
}

// 添加表单字段
const handleAddField = () => {
  fieldForm.type = 'text'
  fieldForm.label = ''
  fieldForm.name = ''
  fieldForm.placeholder = ''
  fieldForm.required = false
  fieldForm.editable = true
  fieldDialogVisible.value = true
}

// 确认添加字段
const handleConfirmAddField = () => {
  if (!fieldForm.label || !fieldForm.name) {
    ElMessage.warning('请填写字段名称和编码')
    return
  }

  if (formFields.value.some(f => f.name === fieldForm.name)) {
    ElMessage.warning('字段编码已存在')
    return
  }

  formFields.value.push({
    ...fieldForm,
    isSystem: false
  })

  fieldDialogVisible.value = false
  ElMessage.success('字段已添加')
}

// 删除表单字段
const handleDeleteField = (index: number) => {
  formFields.value.splice(index, 1)
}

// 返回
const handleBack = () => {
  router.push('/oa/workflows')
}

// 上一步
const handlePrev = () => {
  if (activeStep.value > 0) {
    activeStep.value--
  }
}

// 下一步
const handleNext = async () => {
  if (activeStep.value === 0) {
    // 验证基本信息
    if (!basicFormRef.value) return
    try {
      await basicFormRef.value.validate()
    } catch {
      ElMessage.warning('请完善基本信息')
      return
    }
  }

  if (activeStep.value === 1) {
    // 验证流程设计
    const hasStart = flowNodes.value.some(n => n.node_type === 'START')
    const hasEnd = flowNodes.value.some(n => n.node_type === 'END')
    if (!hasStart || !hasEnd) {
      ElMessage.warning('流程必须包含开始和结束节点')
      return
    }
  }

  if (activeStep.value < 3) {
    activeStep.value++
  }
}

// 提交表单
const handleSubmit = async () => {
  try {
    await basicFormRef.value?.validate()
  } catch {
    ElMessage.warning('请完善表单信息')
    return
  }

  submitting.value = true

  try {
    // 构建节点数据
    const nodes = flowNodes.value.map((n, index) => ({
      name: n.name,
      code: n.code,
      node_type: n.node_type,
      order_index: index,
      approver_rule: n.node_type === 'APPROVAL' ? {
        type: n.approver_type,
        user_ids: n.approver_ids,
        role_ids: n.role_ids
      } : null,
      config: {
        timeout_hours: n.timeout_hours,
        timeout_action: n.timeout_action,
        cc_type: n.cc_type,
        cc_user_ids: n.cc_user_ids,
        condition_expression: n.condition_expression
      }
    }))

    // 构建表单配置
    const formConfig = {
      fields: formFields.value.filter(f => !f.isSystem).map(f => ({
        name: f.name,
        label: f.label,
        type: f.type,
        required: f.required,
        editable: f.editable,
        placeholder: f.placeholder
      }))
    }

    const data = {
      ...basicForm,
      nodes,
      form_config: formConfig,
      is_active: permissionForm.is_active,
      allow_withdraw: permissionForm.allow_withdraw,
      allow_transfer: permissionForm.allow_transfer,
      allow_cc: permissionForm.allow_cc,
      allow_urge: permissionForm.allow_urge,
      allow_all_initiator: permissionForm.allow_all_initiator,
      allowed_roles: permissionForm.allowed_roles,
      allowed_departments: permissionForm.allowed_departments
    }

    if (isEdit.value) {
      await workflowApi.update(route.params.id as string, data)
      ElMessage.success('工作流已更新')
    } else {
      await workflowApi.create(data)
      ElMessage.success('工作流已创建')
    }

    router.push('/oa/workflows')
  } catch (error: any) {
    if (error?.response?.data?.message) {
      ElMessage.error(error.response.data.message)
    } else {
      ElMessage.error('保存失败')
    }
  } finally {
    submitting.value = false
  }
}

// 发布工作流
const handlePublish = async () => {
  try {
    await workflowApi.publish(route.params.id as string)
    ElMessage.success('工作流已发布')
    loadData()
  } catch {
    ElMessage.error('发布失败')
  }
}

// 组件挂载时加载数据
onMounted(() => {
  loadData()
})
</script>

<style scoped>
.workflow-create {
  padding: 16px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.page-title {
  font-size: 18px;
  font-weight: 600;
  margin-left: 16px;
}

.workflow-steps {
  margin: 24px 0;
}

.step-content {
  min-height: 500px;
  margin-top: 24px;
}

.step-panel {
  animation: fadeIn 0.3s ease;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.form-tip {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}

.unit {
  margin-left: 8px;
  color: #909399;
}

/* 流程设计样式 */
.flow-design-header {
  margin-bottom: 16px;
  display: flex;
  gap: 8px;
}

.flow-canvas {
  position: relative;
  min-height: 400px;
  background: #f5f7fa;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  overflow: auto;
}

.flow-nodes {
  position: relative;
  min-height: 400px;
  padding: 20px;
}

.flow-node {
  position: absolute;
  display: flex;
  align-items: center;
  padding: 12px 16px;
  background: #fff;
  border: 2px solid #dcdfe6;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s;
  min-width: 140px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.flow-node:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  transform: translateY(-2px);
}

.flow-node.node-selected {
  border-color: #409eff;
  box-shadow: 0 0 0 3px rgba(64, 158, 255, 0.2);
}

.flow-node.node-start {
  border-color: #67c23a;
  background: linear-gradient(135deg, #67c23a15, #67c23a08);
}

.flow-node.node-end {
  border-color: #e6a23c;
  background: linear-gradient(135deg, #e6a23c15, #e6a23c08);
}

.flow-node.node-approval {
  border-color: #409eff;
  background: linear-gradient(135deg, #409eff15, #409eff08);
}

.flow-node.node-condition {
  border-color: #f56c6c;
  background: linear-gradient(135deg, #f56c6c15, #f56c6c08);
}

.flow-node.node-cc {
  border-color: #909399;
  background: linear-gradient(135deg, #90939915, #90939908);
}

.node-icon {
  font-size: 20px;
  margin-right: 8px;
  color: #606266;
}

.node-start .node-icon {
  color: #67c23a;
}

.node-end .node-icon {
  color: #e6a23c;
}

.node-approval .node-icon {
  color: #409eff;
}

.node-condition .node-icon {
  color: #f56c6c;
}

.node-info {
  flex: 1;
}

.node-name {
  font-weight: 500;
  color: #303133;
}

.node-type {
  font-size: 12px;
  color: #909399;
  margin-top: 2px;
}

.node-actions {
  display: flex;
  gap: 4px;
  margin-left: 8px;
}

.node-edit-panel {
  position: absolute;
  right: 20px;
  top: 20px;
  width: 320px;
  background: #fff;
  border: 1px solid #dcdfe6;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  border-bottom: 1px solid #dcdfe6;
  font-weight: 500;
}

.panel-header .el-button {
  padding: 4px;
}

.node-edit-panel .el-form {
  padding: 16px;
}

.flow-empty {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
}

/* 表单设计样式 */
.form-design-header {
  margin-bottom: 16px;
}

/* 步骤操作按钮 */
.step-actions {
  display: flex;
  justify-content: center;
  gap: 12px;
  margin-top: 32px;
  padding-top: 24px;
  border-top: 1px solid #dcdfe6;
}
</style>
