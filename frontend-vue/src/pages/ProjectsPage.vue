<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { RouterLink } from 'vue-router'
import { api } from '../api/client'
import NavBar from '../components/NavBar.vue'
import { emptyProjectFields, type ProjectFields, type ProjectRecord, type ProjectStats } from '../types'
import './ProjectsPage.css'

const tab = ref<'list' | 'form'>('list')
const filter = ref('')
const items = ref<ProjectRecord[]>([])
const stats = ref<ProjectStats>({ total: 0, draft: 0, pending: 0, approved: 0, rejected: 0 })
const form = reactive<ProjectFields>(emptyProjectFields())
const editingId = ref<string | null>(null)
const toast = ref('')
const busy = ref(false)
let toastTimer: ReturnType<typeof setTimeout> | null = null

const filtered = computed(() =>
  filter.value ? items.value.filter((i) => i.status === filter.value) : items.value,
)

function tip(msg: string) {
  toast.value = msg
  if (toastTimer) clearTimeout(toastTimer)
  toastTimer = setTimeout(() => (toast.value = ''), 2500)
}

async function refresh() {
  const [s, list] = await Promise.all([api.projectStats(), api.listProjects(filter.value || undefined)])
  stats.value = s
  items.value = list.items
}

onMounted(() => {
  refresh().catch((e) => tip(String(e.message || e)))
})

function openNew() {
  editingId.value = null
  Object.assign(form, emptyProjectFields())
  tab.value = 'form'
}

function openEdit(p: ProjectRecord) {
  editingId.value = p.id
  Object.assign(form, emptyProjectFields(), {
    project_code: p.project_code,
    project_name: p.project_name,
    project_type: p.project_type,
    owner: p.owner,
    department: p.department,
    sponsor: p.sponsor,
    start_date: p.start_date,
    end_date: p.end_date,
    budget: p.budget,
    priority: p.priority,
    risk_level: p.risk_level,
    members: p.members,
    description: p.description,
    goals: p.goals,
    source_file: p.source_file,
    remark: p.remark,
  })
  tab.value = 'form'
}

async function saveDraft() {
  busy.value = true
  try {
    if (editingId.value) await api.updateProject(editingId.value, { ...form })
    else {
      const rec = await api.createProject({ ...form })
      editingId.value = rec.id
    }
    tip('已保存草稿')
    await refresh()
    tab.value = 'list'
  } catch (e) {
    tip((e as Error).message)
  } finally {
    busy.value = false
  }
}

async function submit() {
  if (!editingId.value) await saveDraft()
  if (!editingId.value) return
  busy.value = true
  try {
    await api.submitProject(editingId.value)
    tip('已提交审批')
    await refresh()
    tab.value = 'list'
  } catch (e) {
    tip((e as Error).message)
  } finally {
    busy.value = false
  }
}

async function review(id: string, action: 'approve' | 'reject') {
  busy.value = true
  try {
    const rec = await api.reviewProject(id, { action, reviewer: '审批人', comment: '' })
    if (action === 'approve' && rec.rag_synced) tip('已通过并同步知识库')
    else tip(action === 'approve' ? '已通过' : '已驳回')
    await refresh()
  } catch (e) {
    tip((e as Error).message)
  } finally {
    busy.value = false
  }
}

async function onParse(ev: Event) {
  const input = ev.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return
  busy.value = true
  try {
    const r = await api.parseProject(file)
    Object.assign(form, r.fields)
    tip(`解析完成（${r.method} · 置信度 ${Math.round((r.confidence || 0) * 100)}%）`)
    tab.value = 'form'
  } catch (e) {
    tip((e as Error).message)
  } finally {
    busy.value = false
    input.value = ''
  }
}
</script>

<template>
  <NavBar>
    <template #right>
      <RouterLink class="ghost-btn" to="/">← 首页</RouterLink>
      <RouterLink class="ghost-btn" to="/chat">对话</RouterLink>
    </template>
  </NavBar>

  <section class="proj-hero">
    <h2>项目管理</h2>
    <h1>立项录入与审批 HITL</h1>
    <p>业务人工确认；通过后同步 RAG。与对话图级 interrupt 分工不同。</p>
  </section>

  <div class="proj-stats">
    <div class="s"><b>{{ stats.total }}</b><span>全部</span></div>
    <div class="s"><b>{{ stats.draft }}</b><span>草稿</span></div>
    <div class="s"><b>{{ stats.pending }}</b><span>待审</span></div>
    <div class="s"><b>{{ stats.approved }}</b><span>已通过</span></div>
  </div>

  <div class="proj-toolbar">
    <button class="btn btn-primary" type="button" @click="openNew">新建立项</button>
    <label class="btn btn-ghost">
      上传解析
      <input type="file" accept=".md,.txt,.pdf" hidden @change="onParse" />
    </label>
    <select v-model="filter" @change="refresh()">
      <option value="">全部状态</option>
      <option value="draft">草稿</option>
      <option value="pending">待审</option>
      <option value="approved">已通过</option>
      <option value="rejected">驳回</option>
    </select>
    <button class="btn btn-ghost" type="button" :class="{ active: tab === 'list' }" @click="tab = 'list'">列表</button>
  </div>

  <div v-if="tab === 'list'" class="proj-list">
    <div v-for="p in filtered" :key="p.id" class="proj-card">
      <div class="row">
        <strong>{{ p.project_name }}</strong>
        <span class="badge">{{ p.status }}</span>
      </div>
      <div class="sub">{{ p.project_code || '无编号' }} · {{ p.owner || '未填负责人' }}</div>
      <div class="actions">
        <button class="btn btn-ghost" type="button" @click="openEdit(p)">查看/编辑</button>
        <button
          v-if="p.status === 'pending'"
          class="btn btn-ok"
          type="button"
          :disabled="busy"
          @click="review(p.id, 'approve')"
        >
          通过
        </button>
        <button
          v-if="p.status === 'pending'"
          class="btn btn-danger"
          type="button"
          :disabled="busy"
          @click="review(p.id, 'reject')"
        >
          驳回
        </button>
      </div>
    </div>
    <p v-if="!filtered.length" class="empty">暂无项目</p>
  </div>

  <div v-else class="proj-form">
    <div class="grid">
      <label>项目名称<input v-model="form.project_name" /></label>
      <label>项目编号<input v-model="form.project_code" /></label>
      <label>负责人<input v-model="form.owner" /></label>
      <label>部门<input v-model="form.department" /></label>
      <label>类型<input v-model="form.project_type" /></label>
      <label>优先级<input v-model="form.priority" /></label>
    </div>
    <label>概述<textarea v-model="form.description" rows="3" /></label>
    <label>目标<textarea v-model="form.goals" rows="3" /></label>
    <div class="actions">
      <button class="btn btn-primary" type="button" :disabled="busy" @click="saveDraft">保存草稿</button>
      <button class="btn btn-ok" type="button" :disabled="busy" @click="submit">提交审批</button>
      <button class="btn btn-ghost" type="button" @click="tab = 'list'">返回列表</button>
    </div>
  </div>

  <div class="toast" :class="{ show: !!toast }">{{ toast }}</div>
</template>
