<template>
  <div class="page-container">
    <el-card shadow="never">
      <el-form :inline="true" :model="queryParams" class="search-form">
        <el-form-item label="关键词">
          <el-input
            v-model="queryParams.keyword"
            placeholder="规则名称"
            clearable
            style="width: 220px"
            @keyup.enter="handleSearch"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :icon="Search" @click="handleSearch">查询</el-button>
          <el-button :icon="Refresh" @click="handleReset">重置</el-button>
          <el-button type="success" :icon="Plus" @click="openCreate">新增规则</el-button>
        </el-form-item>
      </el-form>

      <el-table v-loading="loading" :data="tableData" border stripe>
        <el-table-column type="index" label="#" width="50" />
        <el-table-column prop="name" label="规则名称" min-width="150" />
        <el-table-column prop="triggerType" label="触发类型" width="120">
          <template #default="{ row }: { row: any }">
            <el-tag :type="triggerTagType(row.triggerType)">{{ triggerLabel(row.triggerType) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="triggerKeywords" label="触发关键词" min-width="150" />
        <el-table-column prop="deliveryContent" label="发货内容" min-width="150" show-overflow-tooltip />
        <el-table-column prop="priority" label="优先级" width="80" align="center" />
        <el-table-column prop="enabled" label="状态" width="100">
          <template #default="{ row }: { row: any }">
            <el-tag :type="row.enabled === 1 ? 'success' : 'warning'" size="small">
              {{ row.enabled === 1 ? '启用' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="createdAt" label="创建时间" width="160">
          <template #default="{ row }: { row: any }">
            {{ row.createdAt ? formatDateTime(row.createdAt) : '-' }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
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

    <el-dialog v-model="dialogVisible" :title="dialogType === 'create' ? '新增发货规则' : '编辑发货规则'" width="680px">
      <el-form ref="formRef" :model="form" :rules="formRules" label-width="110px">
        <el-form-item label="规则名称" prop="name">
          <el-input v-model="form.name" placeholder="如：下单自动发货" />
        </el-form-item>
        <el-form-item label="触发类型" prop="triggerType">
          <el-select v-model="form.triggerType" placeholder="选择触发类型" style="width: 100%">
            <el-option label="关键词触发" value="KEYWORD" />
            <el-option label="订单触发" value="ORDER" />
            <el-option label="全部消息" value="ALL" />
          </el-select>
        </el-form-item>
        <el-form-item label="触发关键词" v-if="form.triggerType === 'KEYWORD'" prop="triggerKeywords">
          <el-input v-model="form.triggerKeywords" placeholder="多个关键词用逗号分隔，如：发货,订单,购买" />
        </el-form-item>

        <el-form-item label="关联账号">
          <el-select
            v-model="form.accountId"
            placeholder="不限制"
            clearable
            filterable
            style="width: 100%"
            @change="onAccountChange"
          >
            <el-option
              v-for="a in accounts"
              :key="a.id"
              :label="accountLabel(a)"
              :value="a.id!"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="关联商品" v-if="form.triggerType === 'ORDER'">
          <div class="product-bind">
            <el-select
              v-model="form.productId"
              placeholder="不限制（任意商品）"
              clearable
              filterable
              style="width: 100%"
              :loading="optionsLoading"
            >
              <el-option
                v-for="p in products"
                :key="p.id"
                :label="productLabel(p)"
                :value="p.id!"
              />
            </el-select>
            <div class="product-bind-actions">
              <el-button
                type="warning"
                plain
                size="small"
                :loading="syncLoading"
                :disabled="!form.accountId"
                @click="syncProductsForAccount"
              >
                从闲鱼同步商品
              </el-button>
              <span class="form-hint" v-if="!form.accountId">请先选择关联账号再同步</span>
              <span class="form-hint" v-else-if="!products.length">暂无商品，请先同步或到「商品管理」新增</span>
              <span class="form-hint" v-else>已加载 {{ products.length }} 个商品</span>
            </div>
          </div>
        </el-form-item>

        <el-form-item label="发货内容" prop="deliveryContent">
          <el-input
            v-model="form.deliveryContent"
            type="textarea"
            :rows="4"
            placeholder="自动发送的内容&#10;可用变量：${inventory} 或 {{inventory}} 表示库存卡密"
          />
        </el-form-item>
        <el-form-item label="关联库存">
          <el-select v-model="form.inventoryId" placeholder="不关联" clearable filterable style="width: 100%">
            <el-option v-for="inv in inventories" :key="inv.id" :label="inventoryLabel(inv)" :value="inv.id!" />
          </el-select>
          <span class="form-hint">选中库存会自动扣减</span>
        </el-form-item>
        <el-form-item label="发货延时(秒)">
          <el-input-number v-model="form.delaySeconds" :min="0" :max="3600" />
        </el-form-item>
        <el-form-item label="自动确认发货">
          <el-switch v-model="form.autoConfirm" :active-value="1" :inactive-value="0" />
          <span class="form-hint">付款后调用闲鱼确认发货 API</span>
        </el-form-item>
        <el-form-item label="优先级" prop="priority">
          <el-input-number v-model="form.priority" :min="1" :max="999" />
          <span class="form-hint">数字越大优先级越高</span>
        </el-form-item>
        <el-form-item label="启用">
          <el-switch v-model="form.enabled" :active-value="1" :inactive-value="0" />
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
import { onMounted, reactive, ref, watch } from 'vue'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import { Plus, Refresh, Search } from '@element-plus/icons-vue'
import { createDeliveryRule, deleteDeliveryRule, pageDeliveryRule, type DeliveryRule, updateDeliveryRule } from '@/api/delivery'
import { listAllAccounts, type Account } from '@/api/account'
import { listProduct, syncProducts, type Product } from '@/api/product'
import { listInventory, type Inventory } from '@/api/inventory'
import { formatDateTime } from '@/utils/format'

const loading = ref(false)
const optionsLoading = ref(false)
const syncLoading = ref(false)
const tableData = ref<DeliveryRule[]>([])
const total = ref(0)
const queryParams = reactive({
  pageNo: 1,
  pageSize: 20,
  keyword: '',
  accountId: undefined as number | undefined
})

const dialogVisible = ref(false)
const dialogType = ref<'create' | 'edit'>('create')
const submitLoading = ref(false)
const formRef = ref<FormInstance>()
const form = reactive<Partial<DeliveryRule>>({
  name: '',
  triggerType: 'ORDER',
  triggerKeywords: '',
  productId: undefined,
  accountId: undefined,
  deliveryContent: '',
  inventoryId: undefined,
  autoConfirm: 1,
  delaySeconds: 0,
  priority: 100,
  enabled: 1
})

const formRules: FormRules = {
  name: [{ required: true, message: '请输入规则名称', trigger: 'blur' }],
  triggerType: [{ required: true, message: '请选择触发类型', trigger: 'change' }],
  deliveryContent: [{ required: true, message: '请输入发货内容', trigger: 'blur' }],
  priority: [{ required: true, message: '请输入优先级', trigger: 'blur' }]
}

const accounts = ref<Account[]>([])
const products = ref<Product[]>([])
const inventories = ref<Inventory[]>([])

watch(() => form.triggerType, (val) => {
  if (val !== 'KEYWORD') {
    form.triggerKeywords = ''
  }
})

function accountLabel(a: Account) {
  return a.nickname || a.userNick || a.userId || `账号#${a.id}`
}

function productLabel(p: Product) {
  const title = (p.title || p.name || '').trim() || `商品#${p.id}`
  const itemId = p.xianyuItemId ? ` · ${p.xianyuItemId}` : ''
  const shelf = p.shelfStatus === 'ON_SALE' ? '' : ' [下架]'
  return `${title}${itemId}${shelf}`
}

function inventoryLabel(inv: Inventory) {
  const code = (inv.code || '').slice(0, 40)
  return `${code}${(inv.code || '').length > 40 ? '…' : ''} (库存:${inv.stock ?? 0})`
}

async function loadData() {
  loading.value = true
  try {
    const res = await pageDeliveryRule(queryParams)
    tableData.value = res.list
    total.value = res.total
  } finally {
    loading.value = false
  }
}

async function loadAccountsAndInventory() {
  try {
    accounts.value = (await listAllAccounts()) || []
  } catch (e) {
    console.error(e)
    ElMessage.error('账号列表加载失败')
    accounts.value = []
  }
  try {
    inventories.value = (await listInventory()) || []
  } catch (e) {
    console.error(e)
    inventories.value = []
  }
}

async function loadProducts(accountId?: number) {
  optionsLoading.value = true
  try {
    products.value = (await listProduct(accountId ? { accountId } : undefined)) || []
  } catch (e) {
    console.error(e)
    ElMessage.error('商品列表加载失败')
    products.value = []
  } finally {
    optionsLoading.value = false
  }
}

async function onAccountChange() {
  // 切换账号后重载对应商品；若当前商品不属于该账号则清空
  await loadProducts(form.accountId)
  if (form.productId && !products.value.some((p) => p.id === form.productId)) {
    form.productId = undefined
  }
}

async function syncProductsForAccount() {
  if (!form.accountId) {
    ElMessage.warning('请先选择关联账号')
    return
  }
  syncLoading.value = true
  try {
    const res = await syncProducts(form.accountId)
    ElMessage.success(`同步完成：新增/更新 ${res?.upserted ?? 0}，失败 ${res?.errors ?? 0}`)
    await loadProducts(form.accountId)
    if (!products.value.length) {
      ElMessage.warning('同步后仍无商品，请确认闲鱼账号 Cookie 有效且店铺有在售商品')
    }
  } catch (e: any) {
    ElMessage.error(e?.message || '同步失败')
  } finally {
    syncLoading.value = false
  }
}

async function loadOptions() {
  await loadAccountsAndInventory()
  await loadProducts(form.accountId)
}

function handleSearch() {
  queryParams.pageNo = 1
  loadData()
}

function handleReset() {
  queryParams.keyword = ''
  queryParams.accountId = undefined
  queryParams.pageNo = 1
  loadData()
}

function openCreate() {
  dialogType.value = 'create'
  form.id = undefined
  form.name = ''
  form.triggerType = 'ORDER'
  form.triggerKeywords = ''
  form.productId = undefined
  form.accountId = accounts.value[0]?.id
  form.deliveryContent = ''
  form.inventoryId = undefined
  form.autoConfirm = 1
  form.delaySeconds = 0
  form.priority = 100
  form.enabled = 1
  loadOptions()
  dialogVisible.value = true
}

function openEdit(row: DeliveryRule) {
  dialogType.value = 'edit'
  form.id = row.id
  form.name = row.name
  form.triggerType = row.triggerType
  form.triggerKeywords = row.triggerKeywords
  form.productId = row.productId
  form.accountId = row.accountId
  form.deliveryContent = row.deliveryContent
  form.inventoryId = row.inventoryId
  form.autoConfirm = row.autoConfirm ?? 1
  form.delaySeconds = row.delaySeconds ?? 0
  form.priority = row.priority
  form.enabled = row.enabled
  loadOptions()
  dialogVisible.value = true
}

async function submitForm() {
  if (!formRef.value) return
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    submitLoading.value = true
    try {
      if (dialogType.value === 'create') {
        await createDeliveryRule(form as DeliveryRule)
        ElMessage.success('创建成功')
      } else {
        await updateDeliveryRule(form.id!, form)
        ElMessage.success('更新成功')
      }
      dialogVisible.value = false
      loadData()
    } finally {
      submitLoading.value = false
    }
  })
}

async function handleDelete(row: DeliveryRule) {
  await ElMessageBox.confirm(`确认删除规则 [${row.name}]？`, '提示', { type: 'warning' })
  await deleteDeliveryRule(row.id!)
  ElMessage.success('已删除')
  loadData()
}

function triggerLabel(type?: string) {
  const map: Record<string, string> = {
    KEYWORD: '关键词',
    ORDER: '订单',
    ALL: '全部消息'
  }
  return map[type || ''] || type
}

function triggerTagType(type?: string) {
  const map: Record<string, 'primary' | 'success' | 'warning' | 'info' | 'danger'> = {
    KEYWORD: 'primary',
    ORDER: 'success',
    ALL: 'info'
  }
  return map[type || ''] || 'info'
}

onMounted(async () => {
  await loadAccountsAndInventory()
  loadData()
})
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
.product-bind {
  width: 100%;
}
.product-bind-actions {
  margin-top: 8px;
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 4px;
}
</style>
