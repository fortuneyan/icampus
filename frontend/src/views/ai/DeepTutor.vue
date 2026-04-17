<template>
  <div class="redirect-page">
    <el-empty description="正在跳转到 DeepTutor..." />
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'

onMounted(() => {
  window.location.href = 'http://localhost:5183/deeptutor'
})
</script>

<style scoped>
.redirect-page {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100%;
}
</style>