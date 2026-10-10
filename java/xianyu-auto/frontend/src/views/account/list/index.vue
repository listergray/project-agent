<template>
  <div class="page-container">
    <el-card shadow="never">
      <!-- 查询栏 -->
      <el-form :inline="true" :model="queryParams" class="search-form">
        <el-form-item label="关键词">
          <el-input
            v-model="queryParams.keyword"
            placeholder="昵称 / 用户ID"
            clearable
            style="width: 220px"
            @keyup.enter="handleSearch"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :icon="Search" @click="handleSearch">查询</el-button>
          <el-button :icon="Refresh" @click="handleReset">重置</el-button>
          <el-button type="success" :icon="Plus" @click="openCreate">新增账号</el-button>
          <el-button :icon="Connection" @click="refreshStatus">刷新状态</el-button>
        </el-form-item>
      </el-form>

      <!-- 表格 -->
      <el-table v-loading="loading" :data="tableData" border stripe>
        <el-table-column type="index" label="#" width="50" />
        <el-table-column prop="nickname" label="昵称" min-width="120" />
        <el-table-column prop="userId" label="闲鱼用户ID" min-width="120">
          <template #default="{ row }: { row: any }">
            {{ row.userId || '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="userNick" label="闲鱼昵称" min-width="120">
          <template #default="{ row }: { row: any }">
            {{ row.userNick || '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }: { row: any }">
            <el-tag :type="statusTagType(row.status)">
              {{ statusLabel(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="lastLoginAt" label="最后登录" width="160">
          <template #default="{ row }: { row: any }">
            {{ row.lastLoginAt ? formatDateTime(row.lastLoginAt) : '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="lastKeepaliveAt" label="最后保活" width="160">
          <template #default="{ row }: { row: any }">
            {{ row.lastKeepaliveAt ? formatDateTime(row.lastKeepaliveAt) : '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="autoStart" label="自动启动" width="100" align="center">
          <template #default="{ row }: { row: any }">
            <el-tag :type="row.autoStart === 1 ? 'success' : 'info'" size="small">
              {{ row.autoStart === 1 ? '是' : '否' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="320" fixed="right">
          <template #default="{ row }: { row: any }">
            <el-button link type="primary" size="small" @click="openCookieDialog(row)">更新Cookie</el-button>
            <el-button
              v-if="!isOnline(row.status)"
              link
              type="success"
              size="small"
              @click="handleConnect(row)"
            >启动连接</el-button>
            <el-button
              v-else
              link
              type="warning"
              size="small"
              @click="handleDisconnect(row)"
            >断开</el-button>
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

    <!-- 新增/编辑账号 -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogType === 'create' ? '新增账号' : '编辑账号'"
      width="500px"
    >
      <el-form ref="formRef" :model="form" :rules="formRules" label-width="100px">
        <el-form-item label="账号昵称" prop="nickname">
          <el-input v-model="form.nickname" placeholder="用于后台识别，如：主账号" />
        </el-form-item>
        <el-form-item label="自动启动" prop="autoStart">
          <el-switch v-model="form.autoStart" :active-value="1" :inactive-value="0" />
          <span class="form-hint">应用启动时自动连接</span>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitLoading" @click="submitForm">确定</el-button>
      </template>
    </el-dialog>

    <!-- 更新 Cookie -->
    <el-dialog v-model="cookieDialogVisible" title="更新 Cookie" width="640px">
      <el-alert
        title="如何获取 Cookie"
        type="info"
        :closable="false"
        show-icon
        style="margin-bottom: 12px"
      >
        <template #default>
          <div style="line-height: 1.6">
            1. 浏览器登录 <a href="https://www.goofish.com/" target="_blank">闲鱼网页版</a><br />
            2. 按 F12 → Application → Cookies → 复制全部 Cookie<br />
            3. 必须包含字段：<code>_m_h5_tk</code>、<code>_m_h5_tk_enc</code>、<code>unb</code>
          </div>
        </template>
      </el-alert>
      <el-form ref="cookieFormRef" :model="cookieForm" :rules="cookieRules" label-width="80px">
        <el-form-item label="账号">
          <span>{{ currentAccount?.nickname }}</span>
        </el-form-item>
        <el-form-item label="Cookie" prop="cookie">
          <el-input
            v-model="cookieForm.cookie"
            type="textarea"
            :rows="10"
            placeholder="粘贴 Cookie 字符串"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="cookieDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="cookieLoading" @click="submitCookie">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import { Connection, Plus, Refresh, Search } from '@element-plus/icons-vue'
import {
  connectAccount,
  createAccount,
  deleteAccount,
  disconnectAccount,
  pageAccounts,
  updateAccount,
  updateAccountCookie,
  type Account
} from '@/api/account'
import { formatDateTime } from '@/utils/format'

const loading = ref(false)
const tableData = ref<Account[]>([])
const total = ref(0)
const queryParams = reactive({
  pageNo: 1,
  pageSize: 10,
  keyword: ''
})

const dialogVisible = ref(false)
const dialogType = ref<'create' | 'edit'>('create')
const submitLoading = ref(false)
const formRef = ref<FormInstance>()
const form = reactive<Partial<Account>>({
  nickname: '',
  autoStart: 0
})

const formRules: FormRules = {
  nickname: [{ required: true, message: '请输入账号昵称', trigger: 'blur' }]
}

const cookieDialogVisible = ref(false)
const cookieLoading = ref(false)
const cookieFormRef = ref<FormInstance>()
const cookieForm = reactive({ cookie: '' })
const cookieRules: FormRules = {
  cookie: [{ required: true, message: '请粘贴 Cookie', trigger: 'blur' }]
}

const currentAccount = ref<Account | null>(null)

async function loadData() {
  loading.value = true
  try {
    const res = await pageAccounts(queryParams)
    tableData.value = res.list
    total.value = res.total
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
  queryParams.pageNo = 1
  loadData()
}

function refreshStatus() {
  loadData()
  ElMessage.success('已刷新')
}

function openCreate() {
  dialogType.value = 'create'
  form.id = undefined
  form.nickname = ''
  form.autoStart = 0
  dialogVisible.value = true
}

function openEdit(row: Account) {
  dialogType.value = 'edit'
  form.id = row.id
  form.nickname = row.nickname
  form.autoStart = row.autoStart
  dialogVisible.value = true
}

async function submitForm() {
  if (!formRef.value) return
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    submitLoading.value = true
    try {
      if (dialogType.value === 'create') {
        await createAccount(form)
        ElMessage.success('创建成功')
      } else {
        await updateAccount(form.id!, form)
        ElMessage.success('更新成功')
      }
      dialogVisible.value = false
      loadData()
    } finally {
      submitLoading.value = false
    }
  })
}

function openCookieDialog(row: Account) {
  currentAccount.value = row
  cookieForm.cookie = ''
  cookieDialogVisible.value = true
}

async function submitCookie() {
  if (!cookieFormRef.value) return
  await cookieFormRef.value.validate(async (valid) => {
    if (!valid) return
    cookieLoading.value = true
    try {
      await updateAccountCookie(currentAccount.value!.id!, cookieForm.cookie)
      ElMessage.success('Cookie 保存成功')
      cookieDialogVisible.value = false
      loadData()
    } finally {
      cookieLoading.value = false
    }
  })
}

async function handleConnect(row: Account) {
  try {
    await connectAccount(row.id!)
    ElMessage.success('连接启动中')
    setTimeout(loadData, 1000)
  } catch (e) {
    ElMessage.error('启动失败')
  }
}

async function handleDisconnect(row: Account) {
  await ElMessageBox.confirm(`确认断开账号 [${row.nickname}] 的连接？`, '提示', { type: 'warning' })
  await disconnectAccount(row.id!)
  ElMessage.success('已断开')
  loadData()
}

async function handleDelete(row: Account) {
  await ElMessageBox.confirm(`确认删除账号 [${row.nickname}]？删除后不可恢复`, '提示', { type: 'warning' })
  await deleteAccount(row.id!)
  ElMessage.success('已删除')
  loadData()
}

function statusLabel(status?: string) {
  const map: Record<string, string> = {
    OFFLINE: '离线',
    CONNECTING: '连接中',
    ONLINE: '在线',
    ERROR: '错误',
    NEED_VERIFY: '需验证',
    EXPIRED: 'Cookie失效',
    DISABLED: '已禁用'
  }
  return map[status || ''] || status
}

function statusTagType(status?: string): 'primary' | 'success' | 'warning' | 'info' | 'danger' {
  const map: Record<string, 'primary' | 'success' | 'warning' | 'info' | 'danger'> = {
    OFFLINE: 'info',
    CONNECTING: 'warning',
    ONLINE: 'success',
    ERROR: 'danger',
    NEED_VERIFY: 'danger',
    EXPIRED: 'danger',
    DISABLED: 'info'
  }
  return map[status || ''] || 'info'
}

function isOnline(status?: string) {
  return status === 'ONLINE' || status === 'CONNECTING'
}

onMounted(loadData)
</script>

<style scoped lang="scss">
.page-container { padding: 0; }
.search-form { margin-bottom: 12px; }
.mt-16 { margin-top: 16px; }
.form-hint {
  margin-left: 8px;
  color: var(--el-text-color-secondary);
  font-size: 12px;
}
</style>
