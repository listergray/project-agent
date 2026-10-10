<template>
  <div class="page-container">
    <el-card shadow="never">
      <el-form :inline="true" :model="queryParams" class="search-form">
        <el-form-item label="账号">
          <el-select v-model="queryParams.accountId" clearable placeholder="全部账号" style="width: 160px">
            <el-option v-for="a in accounts" :key="a.id" :label="a.nickname || a.userId" :value="a.id!" />
          </el-select>
        </el-form-item>
        <el-form-item label="上下架">
          <el-select v-model="queryParams.shelfStatus" clearable placeholder="全部" style="width: 120px">
            <el-option label="在售" value="ON_SALE" />
            <el-option label="下架" value="OFF_SHELF" />
          </el-select>
        </el-form-item>
        <el-form-item label="关键词">
          <el-input v-model="queryParams.keyword" placeholder="名称/闲鱼ID" clearable style="width: 200px" @keyup.enter="handleSearch" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :icon="Search" @click="handleSearch">查询</el-button>
          <el-button :icon="Refresh" @click="handleReset">重置</el-button>
          <el-button type="success" :icon="Plus" @click="openCreate">新增</el-button>
          <el-button type="warning" :loading="syncLoading" @click="openSync">从闲鱼同步</el-button>
          <el-button type="primary" plain :disabled="!selectedIds.length" @click="openMigrate">一键搬家</el-button>
        </el-form-item>
      </el-form>

      <el-table v-loading="loading" :data="tableData" border stripe @selection-change="onSelect">
        <el-table-column type="selection" width="45" />
        <el-table-column type="index" label="#" width="50" />
        <el-table-column prop="name" label="商品名称" min-width="160" show-overflow-tooltip />
        <el-table-column prop="xianyuItemId" label="闲鱼ID" min-width="120" show-overflow-tooltip />
        <el-table-column prop="price" label="价格" width="90" />
        <el-table-column prop="shelfStatus" label="上架" width="90">
          <template #default="{ row }: { row: any }">
            <el-tag :type="row.shelfStatus === 'ON_SALE' ? 'success' : 'info'" size="small">
              {{ row.shelfStatus === 'ON_SALE' ? '在售' : '下架' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="totalStock" label="库存" width="70" align="center" />
        <el-table-column prop="autoDelivery" label="自动发货" width="90" align="center">
          <template #default="{ row }: { row: any }">
            <el-tag :type="row.autoDelivery === 1 ? 'success' : 'info'" size="small">
              {{ row.autoDelivery === 1 ? '开' : '关' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="syncStatus" label="同步" width="80" />
        <el-table-column label="操作" width="360" fixed="right">
          <template #default="{ row }: { row: any }">
            <el-button link type="primary" size="small" @click="openEdit(row)">编辑</el-button>
            <el-button link type="primary" size="small" @click="openDeliveryContent(row)">发货内容</el-button>
            <el-button link type="success" size="small" @click="toggleShelf(row, true)">上架</el-button>
            <el-button link type="warning" size="small" @click="toggleShelf(row, false)">下架</el-button>
            <el-button link type="primary" size="small" @click="handleCopy(row)">复制</el-button>
            <el-button link type="danger" size="small" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination
        v-model:current-page="queryParams.pageNo"
        v-model:page-size="queryParams.pageSize"
        :total="total"
        :page-sizes="[10, 20, 50]"
        layout="total, sizes, prev, pager, next"
        background
        class="mt-16"
        @size-change="loadData"
        @current-change="loadData"
      />
    </el-card>

    <el-dialog v-model="dialogVisible" :title="dialogType === 'create' ? '新增商品' : '编辑商品'" width="640px">
      <el-form ref="formRef" :model="form" :rules="formRules" label-width="100px">
        <el-form-item label="归属账号">
          <el-select v-model="form.accountId" clearable placeholder="可选">
            <el-option v-for="a in accounts" :key="a.id" :label="a.nickname || a.userId" :value="a.id!" />
          </el-select>
        </el-form-item>
        <el-form-item label="商品名称" prop="name">
          <el-input v-model="form.name" />
        </el-form-item>
        <el-form-item label="标题">
          <el-input v-model="form.title" />
        </el-form-item>
        <el-form-item label="闲鱼商品ID">
          <el-input v-model="form.xianyuItemId" placeholder="可空，同步后自动填充" />
        </el-form-item>
        <el-form-item label="价格">
          <el-input-number v-model="form.price" :min="0" :precision="2" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="form.description" type="textarea" :rows="3" />
        </el-form-item>
        <el-form-item label="自动发货">
          <el-switch v-model="form.autoDelivery" :active-value="1" :inactive-value="0" />
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="form.status">
            <el-option label="启用" value="ENABLED" />
            <el-option label="禁用" value="DISABLED" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitLoading" @click="submitForm">确定</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="deliveryDialogVisible" title="设置发货内容" width="560px">
      <el-form ref="deliveryFormRef" :model="deliveryForm" :rules="deliveryRules" label-width="100px">
        <el-form-item label="商品"><span>{{ currentProduct?.name }}</span></el-form-item>
        <el-form-item label="发货内容" prop="deliveryContent">
          <el-input v-model="deliveryForm.deliveryContent" type="textarea" :rows="6" placeholder="可用 {{inventory}}" />
        </el-form-item>
        <el-form-item label="关联库存">
          <el-select v-model="deliveryForm.defaultInventoryId" clearable>
            <el-option v-for="inv in inventories" :key="inv.id" :label="`${inv.code} (${inv.stock})`" :value="inv.id!" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="deliveryDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="deliveryLoading" @click="submitDelivery">确定</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="syncVisible" title="从闲鱼同步商品" width="420px">
      <el-form label-width="90px">
        <el-form-item label="账号" required>
          <el-select v-model="syncAccountId" placeholder="选择在线账号" style="width: 100%">
            <el-option v-for="a in accounts" :key="a.id" :label="a.nickname || a.userId" :value="a.id!" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="syncVisible = false">取消</el-button>
        <el-button type="primary" :loading="syncLoading" @click="doSync">开始同步</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="migrateVisible" title="一键搬家" width="480px">
      <el-form label-width="100px">
        <el-form-item label="源账号" required>
          <el-select v-model="migrateFrom" style="width: 100%">
            <el-option v-for="a in accounts" :key="a.id" :label="a.nickname || a.userId" :value="a.id!" />
          </el-select>
        </el-form-item>
        <el-form-item label="目标账号" required>
          <el-select v-model="migrateTo" style="width: 100%">
            <el-option v-for="a in accounts" :key="'t'+a.id" :label="a.nickname || a.userId" :value="a.id!" />
          </el-select>
        </el-form-item>
        <el-form-item label="已选商品">
          <span>{{ selectedIds.length }} 个</span>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="migrateVisible = false">取消</el-button>
        <el-button type="primary" :loading="migrateLoading" @click="doMigrate">开始搬家</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import { Plus, Refresh, Search } from '@element-plus/icons-vue'
import {
  copyProduct, createProduct, deleteProduct, migrateProducts, pageProduct,
  setProductShelf, syncProducts, type Product, updateProduct
} from '@/api/product'
import { listInventory, type Inventory } from '@/api/inventory'
import { pageAccounts, type Account } from '@/api/account'

const loading = ref(false)
const tableData = ref<Product[]>([])
const total = ref(0)
const accounts = ref<Account[]>([])
const selectedIds = ref<number[]>([])
const queryParams = reactive({
  pageNo: 1,
  pageSize: 20,
  keyword: '',
  accountId: undefined as number | undefined,
  shelfStatus: undefined as string | undefined
})

const dialogVisible = ref(false)
const dialogType = ref<'create' | 'edit'>('create')
const submitLoading = ref(false)
const formRef = ref<FormInstance>()
const form = reactive<Partial<Product>>({
  name: '', xianyuItemId: '', description: '', autoDelivery: 0, status: 'ENABLED', price: undefined, title: '', accountId: undefined
})
const formRules: FormRules = {
  name: [{ required: true, message: '请输入商品名称', trigger: 'blur' }]
}

const deliveryDialogVisible = ref(false)
const deliveryLoading = ref(false)
const deliveryFormRef = ref<FormInstance>()
const deliveryForm = reactive({ deliveryContent: '', defaultInventoryId: undefined as number | undefined })
const deliveryRules: FormRules = { deliveryContent: [{ required: true, message: '请输入发货内容', trigger: 'blur' }] }
const currentProduct = ref<Product | null>(null)
const inventories = ref<Inventory[]>([])

const syncVisible = ref(false)
const syncLoading = ref(false)
const syncAccountId = ref<number>()
const migrateVisible = ref(false)
const migrateLoading = ref(false)
const migrateFrom = ref<number>()
const migrateTo = ref<number>()

async function loadAccounts() {
  const res = await pageAccounts({ pageNo: 1, pageSize: 100 })
  accounts.value = res.list || []
}

async function loadData() {
  loading.value = true
  try {
    const res = await pageProduct(queryParams)
    tableData.value = res.list
    total.value = res.total
  } finally {
    loading.value = false
  }
}

function onSelect(rows: Product[]) {
  selectedIds.value = rows.map(r => r.id!).filter(Boolean)
}
function handleSearch() { queryParams.pageNo = 1; loadData() }
function handleReset() {
  queryParams.keyword = ''
  queryParams.accountId = undefined
  queryParams.shelfStatus = undefined
  queryParams.pageNo = 1
  loadData()
}

function openCreate() {
  dialogType.value = 'create'
  Object.assign(form, { id: undefined, name: '', title: '', xianyuItemId: '', description: '', autoDelivery: 0, status: 'ENABLED', price: undefined, accountId: queryParams.accountId })
  dialogVisible.value = true
}
function openEdit(row: Product) {
  dialogType.value = 'edit'
  Object.assign(form, row)
  dialogVisible.value = true
}

async function submitForm() {
  if (!formRef.value) return
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    submitLoading.value = true
    try {
      if (dialogType.value === 'create') {
        await createProduct(form as Product)
        ElMessage.success('创建成功')
      } else {
        await updateProduct(form.id!, form)
        ElMessage.success('更新成功')
      }
      dialogVisible.value = false
      loadData()
    } finally {
      submitLoading.value = false
    }
  })
}

function openDeliveryContent(row: Product) {
  currentProduct.value = row
  deliveryForm.deliveryContent = row.deliveryContent || ''
  deliveryForm.defaultInventoryId = row.defaultInventoryId
  listInventory().then(r => { inventories.value = r }).catch(() => {})
  deliveryDialogVisible.value = true
}

async function submitDelivery() {
  if (!deliveryFormRef.value) return
  await deliveryFormRef.value.validate(async (valid) => {
    if (!valid) return
    deliveryLoading.value = true
    try {
      await updateProduct(currentProduct.value!.id!, {
        deliveryContent: deliveryForm.deliveryContent,
        defaultInventoryId: deliveryForm.defaultInventoryId
      })
      ElMessage.success('更新成功')
      deliveryDialogVisible.value = false
      loadData()
    } finally {
      deliveryLoading.value = false
    }
  })
}

async function toggleShelf(row: Product, onSale: boolean) {
  await setProductShelf(row.id!, onSale, row.accountId)
  ElMessage.success(onSale ? '已上架' : '已下架')
  loadData()
}

async function handleCopy(row: Product) {
  await copyProduct(row.id!)
  ElMessage.success('已复制到本地')
  loadData()
}

async function handleDelete(row: Product) {
  await ElMessageBox.confirm(`确认删除 [${row.name}]？`, '提示', { type: 'warning' })
  await deleteProduct(row.id!)
  ElMessage.success('已删除')
  loadData()
}

function openSync() { syncAccountId.value = queryParams.accountId; syncVisible.value = true }
async function doSync() {
  if (!syncAccountId.value) { ElMessage.warning('请选择账号'); return }
  syncLoading.value = true
  try {
    const res = await syncProducts(syncAccountId.value)
    ElMessage.success(`同步完成：更新 ${res.upserted}，失败 ${res.errors}`)
    syncVisible.value = false
    loadData()
  } finally {
    syncLoading.value = false
  }
}

function openMigrate() {
  if (!selectedIds.value.length) return
  migrateFrom.value = queryParams.accountId
  migrateVisible.value = true
}
async function doMigrate() {
  if (!migrateFrom.value || !migrateTo.value) { ElMessage.warning('请选择源/目标账号'); return }
  migrateLoading.value = true
  try {
    const res = await migrateProducts({
      fromAccountId: migrateFrom.value,
      toAccountId: migrateTo.value,
      productIds: selectedIds.value
    })
    ElMessage.success(`搬家完成：成功 ${res.success}，失败 ${res.failed}`)
    migrateVisible.value = false
    loadData()
  } finally {
    migrateLoading.value = false
  }
}

onMounted(async () => {
  await loadAccounts()
  await loadData()
})
</script>

<style scoped lang="scss">
.page-container { padding: 0; }
.search-form { margin-bottom: 12px; }
.mt-16 { margin-top: 16px; }
</style>
