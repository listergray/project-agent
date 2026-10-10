<template>
  <div class="page-container">
    <el-card shadow="never">
      <el-form :inline="true" class="search-form">
        <el-form-item>
          <el-button :icon="Refresh" @click="loadData">刷新</el-button>
          <el-button type="primary" :icon="Connection" @click="reconnectAll">一键全部重连</el-button>
        </el-form-item>
        <el-form-item>
          <el-switch
            v-model="autoRefresh"
            active-text="自动刷新"
            @change="(v: any) => toggleAutoRefresh(Boolean(v))"
          />
          <span class="form-hint">每 5 秒刷新一次状态</span>
        </el-form-item>
      </el-form>

      <el-table v-loading="loading" :data="tableData" border stripe>
        <el-table-column type="index" label="#" width="50" />
        <el-table-column prop="nickname" label="账号" min-width="120" />
        <el-table-column prop="userId" label="用户ID" min-width="100">
          <template #default="{ row }: { row: any }">
            {{ row.userId || '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }: { row: any }">
            <el-tag :type="statusTagType(row.status)">
              {{ statusLabel(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="connected" label="WS连接" width="100" align="center">
          <template #default="{ row }: { row: any }">
            <el-tag :type="row.wsConnected ? 'success' : 'info'" size="small">
              {{ row.wsConnected ? '已建立' : '未建立' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="registered" label="已注册" width="100" align="center">
          <template #default="{ row }: { row: any }">
            <el-tag :type="row.wsRegistered ? 'success' : 'info'" size="small">
              {{ row.wsRegistered ? '是' : '否' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="lastHeartbeatAt" label="最后心跳" width="160">
          <template #default="{ row }: { row: any }">
            {{ row.lastHeartbeatAt ? formatDateTime(row.lastHeartbeatAt) : '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="reconnectAttempts" label="重连次数" width="100" align="center">
          <template #default="{ row }: { row: any }">
            <el-tag :type="row.reconnectAttempts > 0 ? 'warning' : 'info'" size="small">
              {{ row.reconnectAttempts || 0 }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="lastError" label="错误信息" min-width="200">
          <template #default="{ row }: { row: any }">
            <!-- 已在线且 WS 正常时，忽略历史残留错误 -->
            <template v-if="row.wsConnected && row.status === 'ONLINE'">
              <span>-</span>
            </template>
            <el-tooltip v-else-if="row.lastError" :content="row.lastError" placement="top">
              <span class="error-text">{{ row.lastError }}</span>
            </el-tooltip>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }: { row: any }">
            <el-button link type="primary" size="small" @click="handleReconnect(row)">重连</el-button>
            <el-button link type="warning" size="small" @click="handleDisconnect(row)">断开</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { onMounted, onUnmounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Connection, Refresh } from '@element-plus/icons-vue'
import {
  disconnectAccount,
  getAllWsStatus,
  listAllAccounts,
  reconnectAccount
} from '@/api/account'
import { formatDateTime } from '@/utils/format'

interface StatusRow {
  id: number
  nickname?: string
  userId?: string
  status?: string
  wsConnected: boolean
  wsRegistered: boolean
  lastHeartbeatAt?: number
  reconnectAttempts?: number
  lastError?: string | null
}

const loading = ref(false)
const tableData = ref<StatusRow[]>([])
const autoRefresh = ref(false)
let timer: ReturnType<typeof setInterval> | null = null

async function loadData() {
  loading.value = true
  try {
    const [accountsRes, wsRes] = await Promise.all([listAllAccounts(), getAllWsStatus()])
    const accounts = accountsRes || []
    const wsStatus = wsRes || {}
    tableData.value = accounts.map((acc: any) => {
      const ws = wsStatus[acc.id] || ({} as any)
      return {
        id: acc.id,
        nickname: acc.nickname,
        userId: acc.userId,
        status: acc.status,
        wsConnected: ws.connected || false,
        wsRegistered: ws.registered || false,
        lastHeartbeatAt: ws.lastHeartbeatAt,
        reconnectAttempts: ws.reconnectAttempts,
        lastError: acc.lastError
      }
    })
  } finally {
    loading.value = false
  }
}

async function handleReconnect(row: StatusRow) {
  try {
    await reconnectAccount(row.id)
    ElMessage.success('重连中')
    setTimeout(loadData, 1000)
  } catch {
    ElMessage.error('重连失败')
  }
}

async function handleDisconnect(row: StatusRow) {
  await ElMessageBox.confirm(`确认断开账号 [${row.nickname}]？`, '提示', { type: 'warning' })
  await disconnectAccount(row.id)
  ElMessage.success('已断开')
  loadData()
}

async function reconnectAll() {
  await ElMessageBox.confirm('确认重连所有账号？', '提示', { type: 'warning' })
  const tasks = tableData.value.map((row) => reconnectAccount(row.id).catch(() => null))
  await Promise.all(tasks)
  ElMessage.success('已触发全部重连')
  setTimeout(loadData, 1500)
}

function toggleAutoRefresh(v: boolean) {
  if (v) {
    timer = setInterval(loadData, 5000)
  } else if (timer) {
    clearInterval(timer)
    timer = null
  }
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

onMounted(loadData)
onUnmounted(() => {
  if (timer) clearInterval(timer)
})
</script>

<style scoped lang="scss">
.page-container { padding: 0; }
.search-form { margin-bottom: 12px; }
.form-hint {
  margin-left: 8px;
  color: var(--el-text-color-secondary);
  font-size: 12px;
}
.error-text {
  color: var(--el-color-danger);
  display: inline-block;
  max-width: 200px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>
