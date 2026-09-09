<script setup lang="ts">
import { RouterLink } from 'vue-router'
import NavBar from '../components/NavBar.vue'
</script>

<template>
  <NavBar>
    <template #right>
      <RouterLink class="ghost-btn" to="/">← 首页</RouterLink>
      <RouterLink class="ghost-btn" to="/chat">对话</RouterLink>
    </template>
  </NavBar>
  <section class="home-hero">
    <h2>知识库导入</h2>
    <h1>上传流水线入口</h1>
    <p>完整导入 UI 可继续扩展；当前请用 API / CLI <code>rag-import</code> 或对话验证检索。</p>
    <p style="margin-top: 16px">
      <RouterLink class="btn btn-primary" to="/chat">去对话</RouterLink>
    </p>
  </section>
</template>
