<template>
  <div class="page-container">
    <el-card shadow="never">
      <el-form :inline="true" :model="queryParams" class="search-form">
        <el-form-item label="关键词">
          <el-input
            v-model="queryParams.keyword"
            placeholder="关键词/回复内容"
            clearable
            style="width: 200px"
            @keyup.enter="handleSearch"
          />
        </el-form-item>
        <el-form-item label="账号">
          <el-select v-model="queryParams.accountId" clearable filterable placeholder="全部" style="width: 180px">
            <el-option v-for="a in accounts" :key="a.id" :label="accountLabel(a)" :value="a.id!" />
          </el-select>
        </el-form-item>
        <el-form-item label="匹配">
          <el-select v-model="queryParams.matchType" clearable placeholder="全部" style="width: 120px">
            <el-option label="精确" value="EXACT" />
            <el-option label="包含" value="CONTAINS" />
            <el-option label="正则" value="REGEX" />
            <el-option label="全部消息" value="ALL" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :icon="Search" @click="handleSearch">查询</el-button>
          <el-button :icon="Refresh" @click="handleReset">重置</el-button>
          <el-button type="success" :icon="Plus" @click="openCreate">新增规则</el-button>
        </el-form-item>
      </el-form>

      <el-alert
        type="info"
        :closable="false"
        show-icon
        class="mb-12"
        title="匹配优先级：精确 > 包含 > 正则 > 全部消息；同类型看「优先级」数字越大越先命中。发货规则已命中时不会再走自动回复。"
      />

      <el-table v-loading="loading" :data="tableData" border stripe>
        <el-table-column type="index" label="#" width="50" />
        <el-table-column label="账号" min-width="120">
          <template #default="{ row }: { row: any }">
            {{ accountName(row.accountId) }}
          </template>
        </el-table-column>
        <el-table-column prop="matchType" label="匹配类型" width="100">
          <template #default="{ row }: { row: any }">
            <el-tag size="small">{{ matchLabel(row.matchType) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="keyword" label="关键词" min-width="140" show-overflow-tooltip />
        <el-table-column prop="replyContent" label="回复内容" min-width="180" show-overflow-tooltip />
        <el-table-column prop="itemId" label="商品ID" width="120" show-overflow-tooltip>
          <template #default="{ row }: { row: any }">
            {{ row.itemId || '不限' }}
          </template>
        </el-table-column>
        <el-table-column prop="priority" label="优先级" width="80" align="center" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }: { row: any }">
            <el-switch
              :model-value="row.status === 'ENABLED'"
              @change="(v: string | number | boolean) => toggleStatus(row, !!v)"
            />
          </template>
        </el-table-column>
        <el-table-column prop="createdAt" label="创建时间" width="160">
          <template #default="{ row }: { row: any }">
            {{ row.createdAt ? formatDateTime(row.createdAt) : '-' }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="160" fixed="right">
          <template #default="{ row }: { row: any }">
            <el-button link type="primary" size="small" @click="openEdit(row)">编辑</el-button>
            <el-button link type="danger" size="small" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination
        v-model:current-page="queryParams.pageNo"
        v-model:page-size="queryParams.pageSize"
        :total="total"
        :page-sizes="[10, 20, 50]"
        layout="total, sizes, prev, pager, next, jumper"
        background
        class="mt-16"
        @size-change="loadData"
        @current-change="loadData"
      />
    </el-card>

    <el-dialog v-model="dialogVisible" :title="dialogType === 'create' ? '新增回复规则' : '编辑回复规则'" width="640px">
      <el-form ref="formRef" :model="form" :rules="formRules" label-width="100px">
        <el-form-item label="关联账号" prop="accountId">
          <el-select v-model="form.accountId" filterable placeholder="选择账号" style="width: 100%">
            <el-option v-for="a in accounts" :key="a.id" :label="accountLabel(a)" :value="a.id!" />
          </el-select>
        </el-form-item>
        <el-form-item label="匹配类型" prop="matchType">
          <el-select v-model="form.matchType" style="width: 100%">
            <el-option label="精确匹配" value="EXACT" />
            <el-option label="包含匹配（逗号分隔多词）" value="CONTAINS" />
            <el-option label="正则匹配" value="REGEX" />
            <el-option label="全部消息" value="ALL" />
          </el-select>
        </el-form-item>
        <el-form-item v-if="form.matchType !== 'ALL'" label="关键词" prop="keyword">
          <el-input
            v-model="form.keyword"
            :placeholder="form.matchType === 'REGEX' ? '正则表达式' : '如：包邮,多久发货'"
          />
        </el-form-item>
        <el-form-item label="回复内容" prop="replyContent">
          <el-input v-model="form.replyContent" type="textarea" :rows="4" placeholder="自动回复给买家的内容" />
        </el-form-item>
        <el-form-item label="商品ID">
          <el-input v-model="form.itemId" placeholder="可选，仅对指定闲鱼商品生效" clearable />
        </el-form-item>
        <el-form-item label="优先级" prop="priority">
          <el-input-number v-model="form.priority" :min="1" :max="999" />
          <span class="form-hint">数字越大越优先</span>
        </el-form-item>
        <el-form-item label="启用">
          <el-switch v-model="form.status" active-value="ENABLED" inactive-value="DISABLED" />
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
import { Plus, Refresh, Search } from '@element-plus/icons-vue'
import {
  createKeywordRule,
  deleteKeywordRule,
  pageKeywordRule,
  updateKeywordRule,
  updateKeywordRuleStatus,
  type KeywordRule
} from '@/api/reply'
import { listAllAccounts, type Account } from '@/api/account'
import { formatDateTime } from '@/utils/format'

const loading = ref(false)
const submitLoading = ref(false)
const tableData = ref<KeywordRule[]>([])
const total = ref(0)
const accounts = ref<Account[]>([])
const dialogVisible = ref(false)
const dialogType = ref<'create' | 'edit'>('create')
const formRef = ref<FormInstance>()
const editingId = ref<number>()

const queryParams = reactive({
  pageNo: 1,
  pageSize: 20,
  keyword: '',
  accountId: undefined as number | undefined,
  matchType: undefined as string | undefined
})

const form = reactive<KeywordRule>({
  accountId: 0,
  keyword: '',
  matchType: 'CONTAINS',
  replyContent: '',
  itemId: '',
  priority: 100,
  status: 'ENABLED'
})

const formRules: FormRules = {
  accountId: [{ required: true, message: '请选择账号', trigger: 'change' }],
  matchType: [{ required: true, message: '请选择匹配类型', trigger: 'change' }],
  keyword: [{
    validator: (_r, v, cb) => {
      if (form.matchType !== 'ALL' && !v) cb(new Error('请填写关键词'))
      else cb()
    },
    trigger: 'blur'
  }],
  replyContent: [{ required: true, message: '请填写回复内容', trigger: 'blur' }],
  priority: [{ required: true, message: '请设置优先级', trigger: 'change' }]
}

function accountLabel(a: Account) {
  return a.nickname || a.userNick || a.userId || `账号#${a.id}`
}

function accountName(id?: number) {
  if (!id) return '-'
  const a = accounts.value.find((x) => x.id === id)
  return a ? accountLabel(a) : `#${id}`
}

function matchLabel(t: string) {
  return ({ EXACT: '精确', CONTAINS: '包含', REGEX: '正则', ALL: '全部' } as Record<string, string>)[t] || t
}

async function loadAccounts() {
  accounts.value = (await listAllAccounts()) || []
}

async function loadData() {
  loading.value = true
  try {
    const res = await pageKeywordRule({ ...queryParams })
    tableData.value = res?.list || []
    total.value = res?.total || 0
  } finally {
    loading.value = false
  }
}

function handleSearch() {
  queryParams.pageNo = 1
  loadData()
}

function handleReset() {
  queryParams.keyword = ''
  queryParams.accountId = undefined
  queryParams.matchType = undefined
  handleSearch()
}

function openCreate() {
  dialogType.value = 'create'
  editingId.value = undefined
  Object.assign(form, {
    accountId: accounts.value[0]?.id || undefined,
    keyword: '',
    matchType: 'CONTAINS',
    replyContent: '',
    itemId: '',
    priority: 100,
    status: 'ENABLED'
  })
  dialogVisible.value = true
}

function openEdit(row: KeywordRule) {
  dialogType.value = 'edit'
  editingId.value = row.id
  Object.assign(form, {
    accountId: row.accountId,
    keyword: row.keyword,
    matchType: row.matchType,
    replyContent: row.replyContent,
    itemId: row.itemId || '',
    priority: row.priority,
    status: row.status
  })
  dialogVisible.value = true
}

async function submitForm() {
  await formRef.value?.validate()
  submitLoading.value = true
  try {
    const payload: KeywordRule = {
      accountId: form.accountId,
      keyword: form.matchType === 'ALL' ? (form.keyword || '*') : form.keyword,
      matchType: form.matchType,
      replyContent: form.replyContent,
      itemId: form.itemId || undefined,
      priority: form.priority,
      status: form.status
    }
    if (dialogType.value === 'create') {
      await createKeywordRule(payload)
      ElMessage.success('已创建')
    } else if (editingId.value) {
      await updateKeywordRule(editingId.value, payload)
      ElMessage.success('已更新')
    }
    dialogVisible.value = false
    loadData()
  } finally {
    submitLoading.value = false
  }
}

async function toggleStatus(row: KeywordRule, enabled: boolean) {
  if (!row.id) return
  await updateKeywordRuleStatus(row.id, enabled ? 'ENABLED' : 'DISABLED')
  row.status = enabled ? 'ENABLED' : 'DISABLED'
  ElMessage.success(enabled ? '已启用' : '已禁用')
}

async function handleDelete(row: KeywordRule) {
  if (!row.id) return
  await ElMessageBox.confirm('确认删除该规则？', '提示', { type: 'warning' })
  await deleteKeywordRule(row.id)
  ElMessage.success('已删除')
  loadData()
}

onMounted(async () => {
  await loadAccounts()
  await loadData()
})
</script>

<style scoped>
.mb-12 {
  margin-bottom: 12px;
}
.mt-16 {
  margin-top: 16px;
}
.form-hint {
  margin-left: 8px;
  color: #909399;
  font-size: 12px;
}
</style>
