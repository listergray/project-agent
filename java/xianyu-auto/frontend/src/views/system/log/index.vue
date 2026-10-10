﻿﻿<template>
  <div class="page-container">
    <el-card shadow="never">
      <el-form :inline="true" :model="queryParams" class="search-form">
        <el-form-item label="关键词">
          <el-input
            v-model="queryParams.keyword"
            placeholder="操作人/方法/参数"
            clearable
            style="width: 220px"
            @keyup.enter="handleSearch"
          />
        </el-form-item>
        <el-form-item label="操作类型">
          <el-input v-model="queryParams.action" placeholder="如 LOGIN" clearable style="width: 160px" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :icon="Search" @click="handleSearch">查询</el-button>
          <el-button :icon="Refresh" @click="handleReset">重置</el-button>
          <el-button type="danger" :icon="Delete" @click="handleClear">清空</el-button>
        </el-form-item>
      </el-form>

      <el-table v-loading="loading" :data="tableData" border stripe>
        <el-table-column prop="operator" label="操作人" width="120" />
        <el-table-column prop="action" label="操作类型" width="120">
          <template #default="{ row }: { row: any }">
            <el-tag>{{ row.action }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="method" label="方法" min-width="200" show-overflow-tooltip />
        <el-table-column prop="params" label="参数" min-width="200" show-overflow-tooltip />
        <el-table-column prop="result" label="结果" width="80">
          <template #default="{ row }: { row: any }">
            <el-tag :type="row.result === 'success' ? 'success' : 'danger'">
              {{ row.result === 'success' ? '成功' : '失败' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="ip" label="IP" width="120" />
        <el-table-column label="耗时" width="80">
          <template #default="{ row }: { row: any }">{{ formatDuration(row.durationMs) }}</template>
        </el-table-column>
        <el-table-column prop="errorMsg" label="错误信息" min-width="200" show-overflow-tooltip />
        <el-table-column label="时间" width="160">
          <template #default="{ row }: { row: any }">{{ formatDateTime(row.createdAt) }}</template>
        </el-table-column>
      </el-table>

      <el-pagination
        v-model:current-page="queryParams.pageNo"
        v-model:page-size="queryParams.pageSize"
        :total="total"
        :page-sizes="[20, 50, 100]"
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
import { Search, Refresh, Delete } from '@element-plus/icons-vue'
import { pageLogs, clearAllLogs, type SysLog } from '@/api/system/log'
import { formatDateTime, formatDuration } from '@/utils/format'

const loading = ref(false)
const tableData = ref<SysLog[]>([])
const total = ref(0)

const queryParams = reactive({
  pageNo: 1,
  pageSize: 20,
  keyword: '',
  action: ''
})

async function loadData() {
  loading.value = true
  try {
    const res = await pageLogs(queryParams)
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
  queryParams.action = ''
  queryParams.pageNo = 1
  loadData()
}

async function handleClear() {
  await ElMessageBox.confirm('确认清空全部日志？此操作不可逆！', '警告', { type: 'warning' })
  await clearAllLogs()
  ElMessage.success('已清空')
  loadData()
}

onMounted(loadData)
</script>

<style scoped>
.search-form {
  margin-bottom: 12px;
}
</style>
