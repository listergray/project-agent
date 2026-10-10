<template>
  <div class="page-container">
    <el-card shadow="never">
      <el-form :inline="true" :model="queryParams" class="search-form">
        <el-form-item label="关键词">
          <el-input
            v-model="queryParams.keyword"
            placeholder="卡密/内容"
            clearable
            style="width: 220px"
            @keyup.enter="handleSearch"
          />
        </el-form-item>
        <el-form-item label="类型">
          <el-select v-model="queryParams.type" placeholder="全部" clearable style="width: 120px">
            <el-option label="卡密" value="CARD" />
            <el-option label="链接" value="LINK" />
            <el-option label="文本" value="TEXT" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :icon="Search" @click="handleSearch">查询</el-button>
          <el-button :icon="Refresh" @click="handleReset">重置</el-button>
          <el-button type="success" :icon="Plus" @click="openCreate">新增</el-button>
          <el-button type="primary" :icon="Upload" @click="openBatchCreate">批量导入</el-button>
        </el-form-item>
      </el-form>

      <el-table v-loading="loading" :data="tableData" border stripe>
        <el-table-column type="selection" width="55" />
        <el-table-column type="index" label="#" width="50" />
        <el-table-column prop="code" label="卡密/编号" min-width="150" />
        <el-table-column prop="content" label="内容" min-width="200" show-overflow-tooltip />
        <el-table-column prop="type" label="类型" width="80">
          <template #default="{ row }: { row: any }">
            <el-tag :type="typeTagType(row.type)">{{ typeLabel(row.type) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="productName" label="关联商品" min-width="120">
          <template #default="{ row }: { row: any }">{{ row.productName || '-' }}</template>
        </el-table-column>
        <el-table-column prop="stock" label="库存" width="80" align="center">
          <template #default="{ row }: { row: any }">
            <el-tag :type="row.stock > 0 ? 'success' : 'info'" size="small">{{ row.stock }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="usedCount" label="已使用" width="80" align="center" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }: { row: any }">
            <el-tag :type="statusTagType(row.status)">{{ statusLabel(row.status) }}</el-tag>
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

      <div class="mt-16" style="display: flex; justify-content: space-between; align-items: center">
        <el-button type="danger" :icon="Delete" @click="handleBatchDelete">批量删除</el-button>
        <el-pagination
          v-model:current-page="queryParams.pageNo"
          v-model:page-size="queryParams.pageSize"
          :total="total"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          background
          @size-change="loadData"
          @current-change="loadData"
        />
      </div>
    </el-card>

    <el-dialog v-model="dialogVisible" :title="dialogType === 'create' ? '新增库存' : '编辑库存'" width="560px">
      <el-form ref="formRef" :model="form" :rules="formRules" label-width="100px">
        <el-form-item label="卡密/编号" prop="code">
          <el-input v-model="form.code" placeholder="如：ABC123" />
        </el-form-item>
        <el-form-item label="内容" prop="content">
          <el-input v-model="form.content" type="textarea" :rows="3" placeholder="网盘链接或其他内容" />
        </el-form-item>
        <el-form-item label="类型" prop="type">
          <el-select v-model="form.type" placeholder="选择类型">
            <el-option label="卡密" value="CARD" />
            <el-option label="链接" value="LINK" />
            <el-option label="文本" value="TEXT" />
          </el-select>
        </el-form-item>
        <el-form-item label="关联商品">
          <el-select v-model="form.productId" placeholder="不关联" clearable>
            <el-option v-for="p in products" :key="p.id" :label="p.name" :value="p.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="库存" prop="stock">
          <el-input-number v-model="form.stock" :min="0" :max="9999" />
        </el-form-item>
        <el-form-item label="状态" prop="status">
          <el-select v-model="form.status">
            <el-option label="可用" value="AVAILABLE" />
            <el-option label="已使用" value="USED" />
            <el-option label="已禁用" value="DISABLED" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitLoading" @click="submitForm">确定</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="batchDialogVisible" title="批量导入卡密" width="560px">
      <el-form ref="batchFormRef" :model="batchForm" :rules="batchRules" label-width="100px">
        <el-form-item label="卡密列表" prop="codes">
          <el-input
            v-model="batchForm.codesText"
            type="textarea"
            :rows="8"
            placeholder="每行一个卡密&#10;如：&#10;ABC123&#10;DEF456&#10;GHI789"
          />
        </el-form-item>
        <el-form-item label="公共内容" prop="content">
          <el-input v-model="batchForm.content" type="textarea" :rows="2" placeholder="网盘链接等公共内容" />
        </el-form-item>
        <el-form-item label="类型" prop="type">
          <el-select v-model="batchForm.type" placeholder="选择类型">
            <el-option label="卡密" value="CARD" />
            <el-option label="链接" value="LINK" />
            <el-option label="文本" value="TEXT" />
          </el-select>
        </el-form-item>
        <el-form-item label="关联商品">
          <el-select v-model="batchForm.productId" placeholder="不关联" clearable>
            <el-option v-for="p in products" :key="p.id" :label="p.name" :value="p.id" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="batchDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="batchLoading" @click="submitBatch">确定（{{ batchForm.codesText.split('\n').filter(v => v.trim()).length }}条）</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import { Delete, Plus, Refresh, Search, Upload } from '@element-plus/icons-vue'
import {
  batchCreateInventory,
  batchDeleteInventory,
  createInventory,
  deleteInventory,
  pageInventory,
  type Inventory,
  updateInventory
} from '@/api/inventory'
import { listProduct } from '@/api/product'
import { formatDateTime } from '@/utils/format'

const loading = ref(false)
const tableData = ref<Inventory[]>([])
const total = ref(0)
const queryParams = reactive({
  pageNo: 1,
  pageSize: 20,
  keyword: '',
  type: '',
  productId: undefined as number | undefined
})

const dialogVisible = ref(false)
const dialogType = ref<'create' | 'edit'>('create')
const submitLoading = ref(false)
const formRef = ref<FormInstance>()
const form = reactive<Partial<Inventory>>({
  code: '',
  content: '',
  type: 'CARD',
  productId: undefined,
  stock: 1,
  status: 'AVAILABLE'
})

const formRules: FormRules = {
  code: [{ required: true, message: '请输入卡密/编号', trigger: 'blur' }],
  type: [{ required: true, message: '请选择类型', trigger: 'blur' }],
  stock: [{ required: true, message: '请输入库存', trigger: 'blur' }]
}

const batchDialogVisible = ref(false)
const batchLoading = ref(false)
const batchFormRef = ref<FormInstance>()
const batchForm = reactive({
  codesText: '',
  content: '',
  type: 'CARD',
  productId: undefined as number | undefined
})

const batchRules: FormRules = {
  codesText: [{ required: true, message: '请粘贴卡密列表', trigger: 'blur' }],
  type: [{ required: true, message: '请选择类型', trigger: 'blur' }]
}

const products = ref<{ id: number; name: string }[]>([])
const selectedIds = ref<number[]>([])

async function loadData() {
  loading.value = true
  try {
    const res = await pageInventory(queryParams)
    tableData.value = res.list
    total.value = res.total
  } finally {
    loading.value = false
  }
}

async function loadProducts() {
  try {
    const res = await listProduct()
    products.value = (res || []).map((p: any) => ({ id: p.id as number, name: p.name }))
  } catch {}
}

function handleSearch() {
  queryParams.pageNo = 1
  loadData()
}

function handleReset() {
  queryParams.keyword = ''
  queryParams.type = ''
  queryParams.productId = undefined
  queryParams.pageNo = 1
  loadData()
}

function openCreate() {
  dialogType.value = 'create'
  form.id = undefined
  form.code = ''
  form.content = ''
  form.type = 'CARD'
  form.productId = undefined
  form.stock = 1
  form.status = 'AVAILABLE'
  dialogVisible.value = true
}

function openEdit(row: Inventory) {
  dialogType.value = 'edit'
  form.id = row.id
  form.code = row.code
  form.content = row.content
  form.type = row.type
  form.productId = row.productId
  form.stock = row.stock
  form.status = row.status
  dialogVisible.value = true
}

async function submitForm() {
  if (!formRef.value) return
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    submitLoading.value = true
    try {
      if (dialogType.value === 'create') {
        await createInventory(form as Inventory)
        ElMessage.success('创建成功')
      } else {
        await updateInventory(form.id!, form)
        ElMessage.success('更新成功')
      }
      dialogVisible.value = false
      loadData()
    } finally {
      submitLoading.value = false
    }
  })
}

function openBatchCreate() {
  batchForm.codesText = ''
  batchForm.content = ''
  batchForm.type = 'CARD'
  batchForm.productId = undefined
  batchDialogVisible.value = true
}

async function submitBatch() {
  if (!batchFormRef.value) return
  await batchFormRef.value.validate(async (valid) => {
    if (!valid) return
    batchLoading.value = true
    try {
      const codes = batchForm.codesText.split('\n').filter(v => v.trim())
      await batchCreateInventory({
        codes,
        content: batchForm.content,
        type: batchForm.type,
        productId: batchForm.productId
      })
      ElMessage.success(`成功导入 ${codes.length} 条`)
      batchDialogVisible.value = false
      loadData()
    } finally {
      batchLoading.value = false
    }
  })
}

async function handleDelete(row: Inventory) {
  await ElMessageBox.confirm(`确认删除库存 [${row.code}]？`, '提示', { type: 'warning' })
  await deleteInventory(row.id!)
  ElMessage.success('已删除')
  loadData()
}

async function handleBatchDelete() {
  if (selectedIds.value.length === 0) {
    ElMessage.warning('请选择要删除的记录')
    return
  }
  await ElMessageBox.confirm(`确认删除选中的 ${selectedIds.value.length} 条记录？`, '提示', { type: 'warning' })
  await batchDeleteInventory(selectedIds.value)
  ElMessage.success('已批量删除')
  selectedIds.value = []
  loadData()
}

function typeLabel(type?: string) {
  const map: Record<string, string> = { CARD: '卡密', LINK: '链接', TEXT: '文本' }
  return map[type || ''] || type
}

function typeTagType(type?: string) {
  const map: Record<string, 'primary' | 'success' | 'warning' | 'info' | 'danger'> = {
    CARD: 'primary',
    LINK: 'success',
    TEXT: 'info'
  }
  return map[type || ''] || 'info'
}

function statusLabel(status?: string) {
  const map: Record<string, string> = { AVAILABLE: '可用', USED: '已使用', DISABLED: '已禁用' }
  return map[status || ''] || status
}

function statusTagType(status?: string) {
  const map: Record<string, 'primary' | 'success' | 'warning' | 'info' | 'danger'> = {
    AVAILABLE: 'success',
    USED: 'info',
    DISABLED: 'warning'
  }
  return map[status || ''] || 'info'
}

onMounted(() => {
  loadData()
  loadProducts()
})
</script>

<style scoped lang="scss">
.page-container { padding: 0; }
.search-form { margin-bottom: 12px; }
.mt-16 { margin-top: 16px; }
</style>
