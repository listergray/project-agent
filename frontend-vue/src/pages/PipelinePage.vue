<script setup lang="ts">
import { ref } from 'vue'
import { RouterLink } from 'vue-router'
import { api } from '../api/client'
import NavBar from '../components/NavBar.vue'

const log = ref('')
const busy = ref(false)

async function run() {
  busy.value = true
  log.value = '启动中…'
  try {
    const j = await api.copilotRun()
    log.value = `完成 → ${j.output_dir}\n步骤: ${(j.steps_done || []).join(' → ')}`
  } catch (e) {
    log.value = (e as Error).message
  } finally {
    busy.value = false
  }
}
</script>

<template>
  <NavBar>
    <template #right>
      <RouterLink class="ghost-btn" to="/">← 首页</RouterLink>
    </template>
  </NavBar>
  <section class="home-hero">
    <h2>代码助手</h2>
    <h1>5+1 流水线预研</h1>
    <button class="btn btn-primary" type="button" :disabled="busy" @click="run">运行一次</button>
    <pre style="margin-top: 16px; white-space: pre-wrap">{{ log }}</pre>
  </section>
</template>
