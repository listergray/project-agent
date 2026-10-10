<template>
  <div class="page-container">
    <el-result icon="info" title="功能开发中" :sub-title="`「${route.meta.title}」将在后续阶段开放`">
      <template #extra>
        <el-button type="primary" @click="router.push('/dashboard')">返回看板</el-button>
      </template>
    </el-result>
  </div>
</template>

<script setup lang="ts">
import { useRoute, useRouter } from 'vue-router'
const route = useRoute()
const router = useRouter()
</script>
