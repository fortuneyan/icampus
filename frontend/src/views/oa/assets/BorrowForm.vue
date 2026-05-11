<template>
  <el-dialog
    :model-value="visible"
    @update:model-value="$emit('update:visible', $event)"
    title="借用申请"
    width="500px"
    @closed="resetForm"
  >
    <el-form ref="formRef" :model="formData" :rules="formRules" label-width="110px">
      <el-form-item label="资产名称">
        <el-input :model-value="assetName" disabled />
      </el-form-item>
      <el-form-item label="借用用途" prop="purpose">
        <el-input
          v-model="formData.purpose"
          type="textarea"
          :rows="3"
          placeholder="请输入借用用途"
        />
      </el-form-item>
      <el-form-item label="借用日期" prop="borrow_date">
        <el-date-picker
          v-model="formData.borrow_date"
          type="date"
          placeholder="选择借用日期"
          value-format="YYYY-MM-DD"
          style="width: 100%"
        />
      </el-form-item>
      <el-form-item label="预计归还日期" prop="expected_return_date">
        <el-date-picker
          v-model="formData.expected_return_date"
          type="date"
          placeholder="选择预计归还日期"
          value-format="YYYY-MM-DD"
          style="width: 100%"
        />
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="$emit('update:visible', false)">取消</el-button>
      <el-button type="primary" @click="handleSubmit" :loading="submitLoading">提交申请</el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, reactive, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { assetApi } from '@/api/oa/assets'

const props = defineProps<{
  visible: boolean
  assetId: string
  assetName: string
}>()

const emit = defineEmits<{
  (e: 'update:visible', value: boolean): void
  (e: 'success'): void
}>()

const formRef = ref()
const submitLoading = ref(false)

const formData = reactive({
  purpose: '',
  borrow_date: '',
  expected_return_date: ''
})

const validateReturnDate = (_rule: any, value: string, callback: any) => {
  if (value && formData.borrow_date && value <= formData.borrow_date) {
    callback(new Error('预计归还日期必须晚于借用日期'))
  } else {
    callback()
  }
}

const formRules = {
  purpose: [{ required: true, message: '请输入借用用途', trigger: 'blur' }],
  borrow_date: [{ required: true, message: '请选择借用日期', trigger: 'change' }],
  expected_return_date: [
    { required: true, message: '请选择预计归还日期', trigger: 'change' },
    { validator: validateReturnDate, trigger: 'change' }
  ]
}

const resetForm = () => {
  formRef.value?.resetFields()
  Object.assign(formData, {
    purpose: '',
    borrow_date: '',
    expected_return_date: ''
  })
}

const handleSubmit = async () => {
  try {
    await formRef.value?.validate()
    submitLoading.value = true
    await assetApi.claim(props.assetId, formData)
    ElMessage.success('借用申请已提交')
    emit('update:visible', false)
    emit('success')
  } catch (error: any) {
    if (error !== false) {
      ElMessage.error('提交失败')
    }
  } finally {
    submitLoading.value = false
  }
}
</script>
