<script setup lang="ts">
import { onMounted, onUnmounted, ref } from 'vue'
import { RouterLink } from 'vue-router'
import { api } from '../api/client'
import NavBar from '../components/NavBar.vue'
import './HomePage.css'

const chunks = ref('—')
const items = ref('—')
const tip = ref('')
let tipTimer: ReturnType<typeof setTimeout> | null = null

onMounted(() => {
  api
    .health()
    .then((j) => {
      if (j.milvus) {
        chunks.value = String(j.milvus.kb_chunks ?? '—')
        items.value = String(j.milvus.kb_item_names ?? '—')
      }
    })
    .catch(() => {})
})

onUnmounted(() => {
  if (tipTimer) clearTimeout(tipTimer)
})

function showComingSoon() {
  tip.value = '功能开发中...'
  if (tipTimer) clearTimeout(tipTimer)
  tipTimer = setTimeout(() => {
    tip.value = ''
  }, 2200)
}
</script>

<template>
  <NavBar />
  <section class="home-hero">
    <h2>AI赋能</h2>
    <h1>智化工程</h1>
    <div class="home-tip" :class="{ show: !!tip }" aria-live="polite">{{ tip || '\u00A0' }}</div>
    <div class="card-grid">
      <RouterLink class="glass chat" to="/chat">
        <div class="ic">💬</div>
        <h3>开始对话</h3>
        <p>RAG · Self-RAG · 多查询 Fusion · Function Calling · HITL · SSE</p>
      </RouterLink>
      <RouterLink class="glass project" to="/projects">
        <div class="ic">📁</div>
        <h3>项目管理</h3>
        <p>人工录入 / 文件解析 · 表单确认 · 提交审批 · 立项 HITL</p>
      </RouterLink>
      <button type="button" class="glass asset" @click="showComingSoon">
        <div class="ic">📦</div>
        <h3>资源管理</h3>
        <p>资产台账 · 库存盘点 · 编码与库位 · 出入库流转</p>
      </button>
      <button type="button" class="glass people" @click="showComingSoon">
        <div class="ic">👥</div>
        <h3>人员管理</h3>
        <p>组织架构 · 工号岗位 · 权限角色 · 人员档案</p>
      </button>
    </div>
  </section>
  <section class="home-stats">
    <div class="stat">
      <div class="v">{{ chunks }}</div>
      <div class="l">向量库 chunk 数</div>
    </div>
    <div class="stat">
      <div class="v">{{ items }}</div>
      <div class="l">已导入知识手册</div>
    </div>
    <div class="stat">
      <div class="v">Vue3</div>
      <div class="l">前端门户</div>
    </div>
  </section>
</template>
