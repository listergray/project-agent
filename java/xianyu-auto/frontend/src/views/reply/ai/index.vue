<template>
  <div class="page-container">
    <el-card shadow="never" v-loading="loading">
      <template #header>
        <div class="card-header">
          <span>自动回复 / AI 配置</span>
          <el-button type="primary" :loading="saving" @click="handleSave">保存</el-button>
        </div>
      </template>

      <el-form :model="form" label-width="140px" style="max-width: 720px">
        <el-divider content-position="left">总开关</el-divider>
        <el-form-item label="启用自动回复">
          <el-switch v-model="form.enabled" />
          <span class="form-hint">关闭后关键词与 AI 均不回复</span>
        </el-form-item>
        <el-form-item label="默认回复">
          <el-input
            v-model="form.defaultContent"
            type="textarea"
            :rows="3"
            placeholder="无关键词命中且 AI 关闭/失败时发送（可留空表示不回复）"
          />
        </el-form-item>
        <el-form-item label="回复延时">
          <span class="form-hint">
            当前 {{ form.delayMinSec ?? 3 }}-{{ form.delayMaxSec ?? 7 }} 秒（由 .env 的 REPLY_DELAY_* 控制）
          </span>
        </el-form-item>

        <el-divider content-position="left">AI 兜底</el-divider>
        <el-form-item label="启用 AI">
          <el-switch v-model="form.aiEnabled" />
          <span class="form-hint">关键词未命中时调用大模型</span>
        </el-form-item>
        <el-form-item label="提供商">
          <el-select v-model="form.aiProvider" style="width: 240px">
            <el-option label="通义千问 DashScope" value="dashscope" />
            <el-option label="OpenAI" value="openai" />
            <el-option label="DeepSeek" value="deepseek" />
          </el-select>
        </el-form-item>
        <el-form-item label="Key 状态">
          <div class="provider-status">
            <el-tag
              v-for="(p, name) in form.providers || {}"
              :key="name"
              :type="p.configured ? 'success' : 'info'"
              class="mr-8"
            >
              {{ name }}：{{ p.configured ? `已配置 (${p.model})` : '未配置' }}
            </el-tag>
          </div>
          <div class="form-hint block">
            API Key 请写在项目根目录 .env（DASHSCOPE_API_KEY / OPENAI_API_KEY / DEEPSEEK_API_KEY），保存后重启生效。
          </div>
        </el-form-item>
        <el-form-item label="系统提示词">
          <el-input v-model="form.aiSystemPrompt" type="textarea" :rows="5" />
        </el-form-item>
        <el-form-item label="连通性测试">
          <el-input v-model="testPrompt" placeholder="测试提问" style="width: 320px; margin-right: 8px" />
          <el-button :loading="testing" @click="handleTest">测试 AI</el-button>
        </el-form-item>
        <el-form-item v-if="testAnswer" label="测试结果">
          <el-alert type="success" :closable="false" :title="testAnswer" />
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { getReplySettings, saveReplySettings, testAi, type ReplySettings } from '@/api/reply'

const loading = ref(false)
const saving = ref(false)
const testing = ref(false)
const testPrompt = ref('你好，请问还在吗？')
const testAnswer = ref('')

const form = reactive<ReplySettings>({
  enabled: true,
  defaultContent: '',
  aiEnabled: false,
  aiProvider: 'dashscope',
  aiSystemPrompt: '',
  providers: {}
})

async function load() {
  loading.value = true
  try {
    const data = await getReplySettings()
    Object.assign(form, data)
  } finally {
    loading.value = false
  }
}

async function handleSave() {
  saving.value = true
  try {
    await saveReplySettings({
      enabled: form.enabled,
      defaultContent: form.defaultContent,
      aiEnabled: form.aiEnabled,
      aiProvider: form.aiProvider,
      aiSystemPrompt: form.aiSystemPrompt
    })
    ElMessage.success('已保存')
    await load()
  } finally {
    saving.value = false
  }
}

async function handleTest() {
  testing.value = true
  testAnswer.value = ''
  try {
    const res = await testAi(testPrompt.value)
    testAnswer.value = res?.answer || '(empty)'
    ElMessage.success('AI OK')
  } catch {
  } finally {
    testing.value = false
  }
}

onMounted(load)
</script>

<style scoped>
.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.form-hint {
  margin-left: 8px;
  color: #909399;
  font-size: 12px;
}
.form-hint.block {
  display: block;
  margin-left: 0;
  margin-top: 6px;
}
.provider-status {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
.mr-8 {
  margin-right: 8px;
}
</style>
