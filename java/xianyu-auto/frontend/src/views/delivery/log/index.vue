<template>
  <div class="page-container">
    <el-card shadow="never">
      <el-form :inline="true" :model="queryParams" class="search-form">
        <el-form-item label="关键词">
          <el-input
            v-model="queryParams.keyword"
            placeholder="买家昵称/商品/订单号"
            clearable
            style="width: 220px"
            @keyup.enter="handleSearch"
          />
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="queryParams.status" placeholder="全部" clearable style="width: 120px">
            <el-option label="成功" value="SUCCESS" />
            <el-option label="失败" value="FAILED" />
            <el-option label="待处理" value="PENDING" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :icon="Search" @click="handleSearch">查询</el-button>
          <el-button :icon="Refresh" @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>

      <el-table v-loading="loading" :data="tableData" border stripe>
        <el-table-column type="index" label="#" width="50" />
        <el-table-column prop="accountNickname" label="账号" min-width="100" />
        <el-table-column prop="ruleName" label="规则" min-width="120" />
        <el-table-column prop="buyerNick" label="买家" min-width="100" />
        <el-table-column prop="orderId" label="订单号" min-width="140" show-overflow-tooltip>
          <template #default="{ row }: { row: any }">
            {{ row.orderId || '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="itemId" label="商品ID" min-width="120" />
        <el-table-column prop="itemName" label="商品名称" min-width="120" />
        <el-table-column prop="deliveryContent" label="发货内容" min-width="200" show-overflow-tooltip />
        <el-table-column prop="inventoryCode" label="库存卡密" min-width="120" />
        <el-table-column prop="status" label="状态" width="90">
          <template #default="{ row }: { row: any }">
            <el-tag :type="statusTagType(row.status)">{{ statusLabel(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="consignStatus" label="确认发货" width="100">
          <template #default="{ row }: { row: any }">
            {{ consignLabel(row.consignStatus) }}
          </template>
        </el-table-column>
        <el-table-column prop="errorMsg" label="错误信息" min-width="150" show-overflow-tooltip>
          <template #default="{ row }: { row: any }">
            <span v-if="row.errorMsg" class="error-text">{{ row.errorMsg }}</span>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column prop="createdAt" label="发货时间" width="160">
          <template #default="{ row }: { row: any }">
            {{ row.createdAt ? formatDateTime(row.createdAt) : '-' }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="100" fixed="right">
          <template #default="{ row }: { row: any }">
            <el-button link type="primary" size="small" :loading="resendingId === row.id" @click="handleResend(row)">
              重发
            </el-button>
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
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Refresh, Search } from '@element-plus/icons-vue'
import { pageDeliveryLog, resendDeliveryLog, type DeliveryLog } from '@/api/delivery'
import { formatDateTime } from '@/utils/format'

const loading = ref(false)
const resendingId = ref<number | undefined>()
const tableData = ref<DeliveryLog[]>([])
const total = ref(0)
const queryParams = reactive({
  pageNo: 1,
  pageSize: 20,
  keyword: '',
  status: ''
})

async function loadData() {
  loading.value = true
  try {
    const res = await pageDeliveryLog(queryParams)
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
  queryParams.status = ''
  queryParams.pageNo = 1
  loadData()
}

async function handleResend(row: DeliveryLog) {
  await ElMessageBox.confirm('确认向买家重新发送该发货内容？（不重复扣库存）', '手动重发', {
    type: 'warning'
  })
  resendingId.value = row.id
  try {
    await resendDeliveryLog(row.id!)
    ElMessage.success('重发成功')
    loadData()
  } finally {
    resendingId.value = undefined
  }
}

function statusLabel(status?: string) {
  const map: Record<string, string> = { SUCCESS: '成功', FAILED: '失败', PENDING: '待处理' }
  return map[status || ''] || status
}

function statusTagType(status?: string) {
  const map: Record<string, 'primary' | 'success' | 'warning' | 'info' | 'danger'> = {
    SUCCESS: 'success',
    FAILED: 'danger',
    PENDING: 'warning'
  }
  return map[status || ''] || 'info'
}

function consignLabel(status?: string) {
  const map: Record<string, string> = {
    SUCCESS: '已确认',
    FAILED: '失败',
    SKIPPED: '跳过'
  }
  return map[status || ''] || '-'
}

onMounted(loadData)
</script>

<style scoped lang="scss">
.page-container { padding: 0; }
.search-form { margin-bottom: 12px; }
.mt-16 { margin-top: 16px; }
.error-text { color: var(--el-color-danger); }
</style>
