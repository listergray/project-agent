# -*- coding: utf-8 -*-
"""Generate reply/ai/index.vue with UTF-8 Chinese (ASCII-only source)."""
from pathlib import Path

u = lambda *codes: "".join(chr(c) for c in codes)

# Chinese snippets
AUTO_REPLY_AI = u(0x81EA, 0x52A8, 0x56DE, 0x590D) + " / AI " + u(0x914D, 0x7F6E)
SAVE = u(0x4FDD, 0x5B58)
MASTER = u(0x603B, 0x5F00, 0x5173)
ENABLE_REPLY = u(0x542F, 0x7528, 0x81EA, 0x52A8, 0x56DE, 0x590D)
HINT_OFF = u(0x5173, 0x95ED, 0x540E, 0x5173, 0x952E, 0x8BCD, 0x4E0E) + " AI " + u(0x5747, 0x4E0D, 0x56DE, 0x590D)
DEFAULT_REPLY = u(0x9ED8, 0x8BA4, 0x56DE, 0x590D)
PH_DEFAULT = (
    u(0x65E0, 0x5173, 0x952E, 0x8BCD, 0x547D, 0x4E2D, 0x4E14)
    + " AI "
    + u(0x5173, 0x95ED, 0x2F, 0x5931, 0x8D25, 0x65F6, 0x53D1, 0x9001)
    + u(0xFF08, 0x53EF, 0x7559, 0x7A7A, 0x8868, 0x793A, 0x4E0D, 0x56DE, 0x590D, 0xFF09)
)
DELAY = u(0x56DE, 0x590D, 0x5EF6, 0x65F6)
CURRENT = u(0x5F53, 0x524D)
SEC_HINT = u(0x79D2) + u(0xFF08, 0x7531) + " .env " + u(0x7684) + " REPLY_DELAY_* " + u(0x63A7, 0x5236, 0xFF09)
AI_FALLBACK = "AI " + u(0x515C, 0x5E95)
ENABLE_AI = u(0x542F, 0x7528) + " AI"
HINT_AI = u(0x5173, 0x952E, 0x8BCD, 0x672A, 0x547D, 0x4E2D, 0x65F6, 0x8C03, 0x7528, 0x5927, 0x6A21, 0x578B)
PROVIDER = u(0x63D0, 0x4F9B, 0x5546)
QWEN = u(0x901A, 0x4E49, 0x5343, 0x95EE) + " DashScope"
KEY_STATUS = "Key " + u(0x72B6, 0x6001)
CONFIGURED = u(0x5DF2, 0x914D, 0x7F6E)
NOT_CFG = u(0x672A, 0x914D, 0x7F6E)
KEY_HINT = (
    "API Key "
    + u(0x8BF7, 0x5199, 0x5728, 0x9879, 0x76EE, 0x6839, 0x76EE, 0x5F55)
    + " .env"
    + u(0xFF08)
    + "DASHSCOPE_API_KEY / OPENAI_API_KEY / DEEPSEEK_API_KEY"
    + u(0xFF09, 0xFF0C, 0x4FDD, 0x5B58, 0x540E, 0x91CD, 0x542F, 0x751F, 0x6548, 0x3002)
)
SYS_PROMPT = u(0x7CFB, 0x7EDF, 0x63D0, 0x793A, 0x8BCD)
TEST_CONN = u(0x8FDE, 0x901A, 0x6027, 0x6D4B, 0x8BD5)
TEST_Q = u(0x6D4B, 0x8BD5, 0x63D0, 0x95EE)
TEST_AI = u(0x6D4B, 0x8BD5) + " AI"
TEST_RESULT = u(0x6D4B, 0x8BD5, 0x7ED3, 0x679C)
HELLO = u(0x4F60, 0x597D, 0xFF0C, 0x8BF7, 0x95EE, 0x8FD8, 0x5728, 0x5417, 0xFF1F)
SAVED = u(0x5DF2, 0x4FDD, 0x5B58)
COLON = u(0xFF1A)

content = f"""<template>
  <div class="page-container">
    <el-card shadow="never" v-loading="loading">
      <template #header>
        <div class="card-header">
          <span>{AUTO_REPLY_AI}</span>
          <el-button type="primary" :loading="saving" @click="handleSave">{SAVE}</el-button>
        </div>
      </template>

      <el-form :model="form" label-width="140px" style="max-width: 720px">
        <el-divider content-position="left">{MASTER}</el-divider>
        <el-form-item label="{ENABLE_REPLY}">
          <el-switch v-model="form.enabled" />
          <span class="form-hint">{HINT_OFF}</span>
        </el-form-item>
        <el-form-item label="{DEFAULT_REPLY}">
          <el-input
            v-model="form.defaultContent"
            type="textarea"
            :rows="3"
            placeholder="{PH_DEFAULT}"
          />
        </el-form-item>
        <el-form-item label="{DELAY}">
          <span class="form-hint">
            {CURRENT} {{{{ form.delayMinSec ?? 3 }}}}-{{{{ form.delayMaxSec ?? 7 }}}} {SEC_HINT}
          </span>
        </el-form-item>

        <el-divider content-position="left">{AI_FALLBACK}</el-divider>
        <el-form-item label="{ENABLE_AI}">
          <el-switch v-model="form.aiEnabled" />
          <span class="form-hint">{HINT_AI}</span>
        </el-form-item>
        <el-form-item label="{PROVIDER}">
          <el-select v-model="form.aiProvider" style="width: 240px">
            <el-option label="{QWEN}" value="dashscope" />
            <el-option label="OpenAI" value="openai" />
            <el-option label="DeepSeek" value="deepseek" />
          </el-select>
        </el-form-item>
        <el-form-item label="{KEY_STATUS}">
          <div class="provider-status">
            <el-tag
              v-for="(p, name) in form.providers || {{}}"
              :key="name"
              :type="p.configured ? 'success' : 'info'"
              class="mr-8"
            >
              {{{{ name }}}}{COLON}{{{{ p.configured ? `{CONFIGURED} (${{p.model}})` : '{NOT_CFG}' }}}}
            </el-tag>
          </div>
          <div class="form-hint block">
            {KEY_HINT}
          </div>
        </el-form-item>
        <el-form-item label="{SYS_PROMPT}">
          <el-input v-model="form.aiSystemPrompt" type="textarea" :rows="5" />
        </el-form-item>
        <el-form-item label="{TEST_CONN}">
          <el-input v-model="testPrompt" placeholder="{TEST_Q}" style="width: 320px; margin-right: 8px" />
          <el-button :loading="testing" @click="handleTest">{TEST_AI}</el-button>
        </el-form-item>
        <el-form-item v-if="testAnswer" label="{TEST_RESULT}">
          <el-alert type="success" :closable="false" :title="testAnswer" />
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import {{ onMounted, reactive, ref }} from 'vue'
import {{ ElMessage }} from 'element-plus'
import {{ getReplySettings, saveReplySettings, testAi, type ReplySettings }} from '@/api/reply'

const loading = ref(false)
const saving = ref(false)
const testing = ref(false)
const testPrompt = ref('{HELLO}')
const testAnswer = ref('')

const form = reactive<ReplySettings>({{
  enabled: true,
  defaultContent: '',
  aiEnabled: false,
  aiProvider: 'dashscope',
  aiSystemPrompt: '',
  providers: {{}}
}})

async function load() {{
  loading.value = true
  try {{
    const data = await getReplySettings()
    Object.assign(form, data)
  }} finally {{
    loading.value = false
  }}
}}

async function handleSave() {{
  saving.value = true
  try {{
    await saveReplySettings({{
      enabled: form.enabled,
      defaultContent: form.defaultContent,
      aiEnabled: form.aiEnabled,
      aiProvider: form.aiProvider,
      aiSystemPrompt: form.aiSystemPrompt
    }})
    ElMessage.success('{SAVED}')
    await load()
  }} finally {{
    saving.value = false
  }}
}}

async function handleTest() {{
  testing.value = true
  testAnswer.value = ''
  try {{
    const res = await testAi(testPrompt.value)
    testAnswer.value = res?.answer || '(empty)'
    ElMessage.success('AI OK')
  }} catch {{
  }} finally {{
    testing.value = false
  }}
}}

onMounted(load)
</script>

<style scoped>
.card-header {{
  display: flex;
  align-items: center;
  justify-content: space-between;
}}
.form-hint {{
  margin-left: 8px;
  color: #909399;
  font-size: 12px;
}}
.form-hint.block {{
  display: block;
  margin-left: 0;
  margin-top: 6px;
}}
.provider-status {{
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}}
.mr-8 {{
  margin-right: 8px;
}}
</style>
"""

root = Path(__file__).resolve().parents[1]
out = root / "frontend" / "src" / "views" / "reply" / "ai" / "index.vue"
out.write_text(content, encoding="utf-8")
print("OK", out)
print("check", AUTO_REPLY_AI in out.read_text(encoding="utf-8"))
