<template>
  <div class="page-container">
    <el-row :gutter="16">
      <el-col :span="6" v-for="card in statCards" :key="card.title">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-card-body">
            <el-icon :size="36" :color="card.color">
              <component :is="card.icon" />
            </el-icon>
            <div class="stat-info">
              <div class="stat-value">{{ card.value }}</div>
              <div class="stat-title">{{ card.title }}</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-card class="mt-16" shadow="never">
      <template #header>
        <span>系统信息</span>
      </template>
      <el-descriptions :column="2" border>
        <el-descriptions-item label="项目名称">闲鱼自动发货系统</el-descriptions-item>
        <el-descriptions-item label="版本号">v1.0.0</el-descriptions-item>
        <el-descriptions-item label="技术栈">Spring Boot 3.5 + Vue 3 + Element Plus</el-descriptions-item>
        <el-descriptions-item label="数据库">SQLite（嵌入式）</el-descriptions-item>
        <el-descriptions-item label="当前用户">{{ userStore.userInfo?.nickname || userStore.userInfo?.username }}</el-descriptions-item>
        <el-descriptions-item label="角色权限">{{ userStore.isAdmin() ? '超级管理员' : '普通用户' }}</el-descriptions-item>
      </el-descriptions>
    </el-card>

    <el-card class="mt-16" shadow="never">
      <template #header>
        <span>开发进度（Phase 1 已完成）</span>
      </template>
      <el-timeline>
        <el-timeline-item
          v-for="(phase, idx) in phases"
          :key="idx"
          :timestamp="phase.timestamp"
          :type="phase.type"
          :hollow="phase.hollow"
        >
          <h4>{{ phase.title }}</h4>
          <p>{{ phase.desc }}</p>
        </el-timeline-item>
      </el-timeline>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useUserStore } from '@/stores/modules/user'

const userStore = useUserStore()

const statCards = ref([
  { title: '闲鱼账号', value: 0, icon: 'Iphone', color: '#409eff' },
  { title: '在售商品', value: 0, icon: 'Goods', color: '#67c23a' },
  { title: '今日发货', value: 0, icon: 'Promotion', color: '#e6a23c' },
  { title: '今日消息', value: 0, icon: 'ChatDotRound', color: '#f56c6c' }
])

const phases = ref([
  {
    title: 'Phase 1 - 项目骨架 + 登录 + 基础 CRUD',
    desc: 'Maven 项目、SQLite 数据库、Sa-Token 鉴权、Vue3 + Element Plus 前端框架',
    timestamp: '当前',
    type: 'primary' as const,
    hollow: false
  },
  {
    title: 'Phase 2 - 闲鱼集成层',
    desc: 'WebSocket 连接、Cookie 鉴权、消息收发',
    timestamp: '待开始',
    type: 'info' as const,
    hollow: true
  },
  {
    title: 'Phase 3 - 自动发货核心',
    desc: '订单识别、规则匹配、库存扣减、确认发货',
    timestamp: '待开始',
    type: 'info' as const,
    hollow: true
  },
  {
    title: 'Phase 4 - 自动回复 + AI',
    desc: '关键词匹配、通义千问/OpenAI/DeepSeek 接入',
    timestamp: '已完成',
    type: 'success' as const,
    hollow: false
  },
  {
    title: 'Phase 5 - 通知服务',
    desc: '邮件 + 站内消息 + 企业微信 Webhook',
    timestamp: '待开始',
    type: 'info' as const,
    hollow: true
  },
  {
    title: 'Phase 6 - 前端完善',
    desc: '数据看板图表、在线聊天、批量导入',
    timestamp: '待开始',
    type: 'info' as const,
    hollow: true
  },
  {
    title: 'Phase 7 - Docker 部署',
    desc: 'Dockerfile、docker-compose、README 文档',
    timestamp: '待开始',
    type: 'info' as const,
    hollow: true
  }
])
</script>

<style scoped lang="scss">
.stat-card {
  .stat-card-body {
    display: flex;
    align-items: center;
    gap: 16px;
  }

  .stat-info {
    .stat-value {
      font-size: 24px;
      font-weight: 600;
      color: #303133;
      line-height: 1.2;
    }

    .stat-title {
      font-size: 13px;
      color: #909399;
      margin-top: 4px;
    }
  }
}
</style>
