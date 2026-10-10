<template>
  <div class="page-container">
    <el-card shadow="never">
      <el-form :inline="true" :model="query" class="search-form">
        <el-form-item label="账号">
          <el-select v-model="query.accountId" clearable placeholder="全部" style="width: 160px">
            <el-option v-for="a in accounts" :key="a.id" :label="a.nickname || a.userId" :value="a.id!" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="query.status" clearable style="width: 140px">
            <el-option label="待付款" value="WAIT_PAY" />
            <el-option label="待发货" value="WAIT_SHIP" />
            <el-option label="已发货" value="SHIPPED" />
            <el-option label="完成" value="SUCCESS" />
            <el-option label="关闭" value="CLOSED" />
          </el-select>
        </el-form-item>
        <el-form-item label="关键词">
          <el-input v-model="query.keyword" placeholder="订单号/买家/商品" clearable style="width: 200px" @keyup.enter="search" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="search">查询</el-button>
          <el-button @click="reset">重置</el-button>
          <el-button type="warning" :loading="syncLoading" @click="openSync">同步订单</el-button>
        </el-form-item>
      </el-form>

      <el-table v-loading="loading" :data="list" border stripe>
        <el-table-column prop="orderId" label="订单号" min-width="160" show-overflow-tooltip />
        <el-table-column prop="itemId" label="商品ID" min-width="120" show-overflow-tooltip />
        <el-table-column prop="itemTitle" label="商品" min-width="140" show-overflow-tooltip />
        <el-table-column prop="buyerNick" label="买家" width="120" show-overflow-tooltip />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }: { row: any }">
            <el-tag size="small">{{ statusLabel(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="consignStatus" label="确认发货" width="100" />
        <el-table-column prop="paidAt" label="付款时间" width="160">
          <template #default="{ row }: { row: any }">
            {{ row.paidAt ? formatDateTime(row.paidAt) : '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="updatedAt" label="更新" width="160">
          <template #default="{ row }: { row: any }">
            {{ row.updatedAt ? formatDateTime(row.updatedAt) : '-' }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="120" fixed="right">
          <template #default="{ row }: { row: any }">
            <el-button
              v-if="row.status === 'WAIT_SHIP'"
              link type="primary" size="small"
              :loading="consignLoadingId === row.id"
              @click="doConsign(row)"
            >确认发货</el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination
        v-model:current-page="query.pageNo"
        v-model:page-size="query.pageSize"
        :total="total"
        :page-sizes="[10, 20, 50]"
        layout="total, sizes, prev, pager, next"
        background
        class="mt-16"
        @size-change="load"
        @current-change="load"
      />
    </el-card>

    <el-dialog v-model="syncVisible" title="从闲鱼同步订单" width="420px">
      <el-form label-width="90px">
        <el-form-item label="账号" required>
          <el-select v-model="syncAccountId" placeholder="选择账号" style="width: 100%">
            <el-option v-for="a in accounts" :key="a.id" :label="a.nickname || a.userId" :value="a.id!" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="syncVisible = false">取消</el-button>
        <el-button type="primary" :loading="syncLoading" @click="doSync">开始同步</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { consignOrder, pageOrder, syncOrders, type TradeOrder } from '@/api/order'
import { pageAccounts, type Account } from '@/api/account'
import { formatDateTime } from '@/utils/format'

const loading = ref(false)
const list = ref<TradeOrder[]>([])
const total = ref(0)
const accounts = ref<Account[]>([])
const consignLoadingId = ref<number>()
const syncVisible = ref(false)
const syncLoading = ref(false)
const syncAccountId = ref<number>()
const query = reactive({
  pageNo: 1,
  pageSize: 20,
  accountId: undefined as number | undefined,
  status: undefined as string | undefined,
  keyword: ''
})

async function load() {
  loading.value = true
  try {
    const res = await pageOrder(query)
    list.value = res.list
    total.value = res.total
  } finally {
    loading.value = false
  }
}
function search() { query.pageNo = 1; load() }
function reset() {
  query.accountId = undefined
  query.status = undefined
  query.keyword = ''
  search()
}
function statusLabel(s: string) {
  const m: Record<string, string> = {
    WAIT_PAY: '待付款', WAIT_SHIP: '待发货', SHIPPED: '已发货', SUCCESS: '完成', CLOSED: '关闭'
  }
  return m[s] || s
}
async function doConsign(row: TradeOrder) {
  consignLoadingId.value = row.id
  try {
    const res = await consignOrder(row.id!)
    ElMessage.success(res.success ? '确认发货成功' : '确认发货失败')
    load()
  } finally {
    consignLoadingId.value = undefined
  }
}

function openSync() {
  syncAccountId.value = query.accountId
  syncVisible.value = true
}
async function doSync() {
  if (!syncAccountId.value) {
    ElMessage.warning('请选择账号')
    return
  }
  syncLoading.value = true
  try {
    const res = await syncOrders(syncAccountId.value)
    ElMessage.success(`同步完成：更新 ${res.upserted}，失败 ${res.errors}`)
    syncVisible.value = false
    load()
  } finally {
    syncLoading.value = false
  }
}

onMounted(async () => {
  const res = await pageAccounts({ pageNo: 1, pageSize: 100 })
  accounts.value = res.list || []
  await load()
})
</script>

<style scoped>
.page-container { padding: 0; }
.search-form { margin-bottom: 12px; }
.mt-16 { margin-top: 16px; }
</style>
