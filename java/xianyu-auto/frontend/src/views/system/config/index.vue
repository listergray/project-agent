﻿﻿<template>
  <div class="page-container">
    <el-card shadow="never">
      <div class="flex-between mb-16">
        <div>
          <el-select v-model="currentGroup" style="width: 200px" @change="loadData">
            <el-option v-for="g in groups" :key="g.value" :label="g.label" :value="g.value" />
          </el-select>
          <el-button class="ml-8" :icon="Refresh" @click="loadData">刷新</el-button>
        </div>
        <el-button type="primary" :icon="Plus" @click="openCreate">新增配置</el-button>
      </div>

      <el-table v-loading="loading" :data="tableData" border stripe>
        <el-table-column prop="configKey" label="配置 Key" min-width="200" />
        <el-table-column prop="configValue" label="配置 Value" min-width="240" show-overflow-tooltip>
          <template #default="{ row }: { row: any }">
            <span v-if="isSecret(row.configKey)">***</span>
            <span v-else>{{ row.configValue || '-' }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="configGroup" label="分组" width="120" />
        <el-table-column prop="description" label="说明" min-width="200" show-overflow-tooltip />
        <el-table-column label="更新时间" width="160">
          <template #default="{ row }: { row: any }">{{ formatDateTime(row.updatedAt) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="160" fixed="right">
          <template #default="{ row }: { row: any }">
            <el-button link type="primary" size="small" @click="openEdit(row)">编辑</el-button>
            <el-button link type="danger" size="small" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 新增/编辑 -->
    <el-dialog v-model="dialogVisible" :title="dialogType === 'create' ? '新增配置' : '编辑配置'" width="560px">
      <el-form ref="formRef" :model="form" :rules="formRules" label-width="100px">
        <el-form-item label="配置 Key" prop="configKey">
          <el-input v-model="form.configKey" :disabled="dialogType === 'edit'" placeholder="如 ai.openai.api-key" />
        </el-form-item>
        <el-form-item label="配置 Value" prop="configValue">
          <el-input v-model="form.configValue" type="textarea" :rows="3" placeholder="配置值" />
        </el-form-item>
        <el-form-item label="分组" prop="configGroup">
          <el-input v-model="form.configGroup" placeholder="如 ai / notify / system" />
        </el-form-item>
        <el-form-item label="说明" prop="description">
          <el-input v-model="form.description" placeholder="配置说明" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitLoading" @click="submitForm">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import { Refresh, Plus } from '@element-plus/icons-vue'
import { listConfigs, saveConfig, deleteConfig, type SysConfig } from '@/api/system/config'
import { formatDateTime } from '@/utils/format'

const groups = [
  { label: '全部', value: '' },
  { label: 'system', value: 'system' },
  { label: 'ai', value: 'ai' },
  { label: 'notify', value: 'notify' },
  { label: 'xianyu', value: 'xianyu' },
  { label: 'reply', value: 'reply' }
]
const currentGroup = ref('')
const loading = ref(false)
const tableData = ref<SysConfig[]>([])

async function loadData() {
  loading.value = true
  try {
    const res = await listConfigs(currentGroup.value || undefined)
    tableData.value = res
  } finally {
    loading.value = false
  }
}

const dialogVisible = ref(false)
const dialogType = ref<'create' | 'edit'>('create')
const submitLoading = ref(false)
const formRef = ref<FormInstance>()
const form = reactive<SysConfig>({
  configKey: '',
  configValue: '',
  configGroup: 'system',
  description: ''
})

const formRules: FormRules = {
  configKey: [
    { required: true, message: '请输入配置 Key', trigger: 'blur' },
    { pattern: /^[a-z0-9.\-_]+$/i, message: '仅支持字母数字 . - _', trigger: 'blur' }
  ],
  configValue: [{ required: true, message: '请输入配置 Value', trigger: 'blur' }]
}

function isSecret(key: string): boolean {
  if (!key) return false
  const k = key.toLowerCase()
  return k.includes('password') || k.includes('secret') || k.includes('api-key') || k.includes('token')
}

function openCreate() {
  dialogType.value = 'create'
  Object.assign(form, {
    id: undefined,
    configKey: '',
    configValue: '',
    configGroup: currentGroup.value || 'system',
    description: ''
  })
  dialogVisible.value = true
}

function openEdit(row: SysConfig) {
  dialogType.value = 'edit'
  Object.assign(form, { ...row })
  dialogVisible.value = true
}

async function submitForm() {
  if (!formRef.value) return
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    submitLoading.value = true
    try {
      await saveConfig({ ...form })
      ElMessage.success('保存成功')
      dialogVisible.value = false
      loadData()
    } finally {
      submitLoading.value = false
    }
  })
}

async function handleDelete(row: SysConfig) {
  await ElMessageBox.confirm(`确认删除配置「${row.configKey}」？`, '提示', { type: 'warning' })
  await deleteConfig(row.configKey!)
  ElMessage.success('删除成功')
  loadData()
}

onMounted(loadData)
</script>
