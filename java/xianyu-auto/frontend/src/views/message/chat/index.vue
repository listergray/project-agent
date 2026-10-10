<template>
  <div class="chat-page">
    <el-card shadow="never" class="chat-card">
      <!-- 顶部账号选择 -->
      <div class="chat-header">
        <el-form :inline="true">
          <el-form-item label="账号">
            <el-select
              v-model="selectedAccountId"
              placeholder="选择账号"
              style="width: 200px"
              @change="handleAccountChange"
            >
              <el-option
                v-for="acc in accounts"
                :key="acc.id"
                :label="acc.nickname || `账号${acc.id}`"
                :value="acc.id!"
              />
            </el-select>
          </el-form-item>
          <el-form-item>
            <el-button :icon="Refresh" :loading="loadingConv" @click="loadConversations">刷新会话</el-button>
            <el-button :icon="ChatLineRound" @click="togglePolling">
              {{ polling ? '暂停轮询' : '自动刷新' }}
            </el-button>
          </el-form-item>
        </el-form>
      </div>

      <div class="chat-body">
        <!-- 左侧会话列表 -->
        <div class="conv-list">
          <el-scrollbar height="500px">
            <div
              v-for="conv in conversations"
              :key="conv.conversationId"
              :class="['conv-item', { active: selectedConv === conv.conversationId }]"
              @click="selectConversation(conv)"
            >
              <div class="conv-head">
                <span class="conv-nick">{{ conv.senderNick || conv.senderId || conv.conversationId }}</span>
                <el-badge v-if="conv.unreadCount > 0" :value="conv.unreadCount" />
              </div>
              <div class="conv-last">{{ conv.lastContent || '(空消息)' }}</div>
              <div class="conv-time">{{ formatDateTime(conv.lastMsgAt) }}</div>
            </div>
            <el-empty v-if="conversations.length === 0" description="暂无会话" />
          </el-scrollbar>
        </div>

        <!-- 右侧消息区 -->
        <div class="msg-area">
          <div v-if="!selectedConv" class="empty-tip">
            <el-empty description="请选择左侧会话" />
          </div>
          <template v-else>
            <div class="msg-list" ref="msgListRef">
              <el-scrollbar height="420px" ref="scrollbarRef">
                <div
                  v-for="msg in messages"
                  :key="msg.id"
                  :class="['msg-bubble', msgClass(msg.sender)]"
                >
                  <div class="msg-sender">
                    {{ msg.senderNick || msg.senderId || (msg.sender === 'SELLER' ? '我' : '买家') }}
                    <span class="msg-time">{{ formatDateTime(msg.createdAt) }}</span>
                  </div>
                  <div class="msg-content">
                    <template v-if="msg.msgType === 'TEXT'">{{ msg.content }}</template>
                    <el-tag v-else size="small" type="info">{{ msg.msgType }}</el-tag>
                  </div>
                </div>
                <el-empty v-if="messages.length === 0" description="暂无消息" />
              </el-scrollbar>
            </div>
            <div class="msg-input">
              <el-input
                v-model="inputText"
                type="textarea"
                :rows="2"
                placeholder="输入消息内容，按 Ctrl+Enter 发送"
                resize="none"
                @keydown.enter.ctrl.prevent="handleSend"
              />
              <el-button type="primary" :loading="sending" :disabled="!inputText.trim()" @click="handleSend">
                发送
              </el-button>
            </div>
          </template>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { nextTick, onMounted, onUnmounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { ChatLineRound, Refresh } from '@element-plus/icons-vue'
import { listAllAccounts, type Account } from '@/api/account'
import {
  listConversations,
  markConversationRead,
  pageMessages,
  sendMessage,
  type ChatMessage,
  type Conversation
} from '@/api/message'
import { formatDateTime } from '@/utils/format'

const accounts = ref<Account[]>([])
const selectedAccountId = ref<number>()
const conversations = ref<Conversation[]>([])
const selectedConv = ref<string>('')

const messages = ref<ChatMessage[]>([])
const inputText = ref('')
const sending = ref(false)
const loadingConv = ref(false)

const polling = ref(false)
let timer: ReturnType<typeof setInterval> | null = null

async function loadAccounts() {
  const res = await listAllAccounts()
  accounts.value = res || []
  if (accounts.value.length > 0 && !selectedAccountId.value) {
    selectedAccountId.value = accounts.value[0].id
    await loadConversations()
  }
}

async function loadConversations() {
  if (!selectedAccountId.value) return
  loadingConv.value = true
  try {
    const res = await listConversations(selectedAccountId.value)
    conversations.value = res || []
  } finally {
    loadingConv.value = false
  }
}

async function handleAccountChange() {
  selectedConv.value = ''
  messages.value = []
  await loadConversations()
}

async function selectConversation(conv: Conversation) {
  selectedConv.value = conv.conversationId
  await loadMessages()
  await markConversationRead(selectedAccountId.value!, conv.conversationId)
  conv.unreadCount = 0
  scrollToBottom()
}

async function loadMessages() {
  if (!selectedAccountId.value || !selectedConv.value) return
  const res = await pageMessages({
    accountId: selectedAccountId.value,
    conversationId: selectedConv.value,
    pageSize: 100
  })
  messages.value = res.list
  scrollToBottom()
}

async function handleSend() {
  if (!inputText.value.trim() || !selectedAccountId.value || !selectedConv.value) return
  sending.value = true
  try {
    await sendMessage({
      accountId: selectedAccountId.value,
      conversationId: selectedConv.value,
      content: inputText.value.trim()
    })
    inputText.value = ''
    ElMessage.success('发送成功')
    await loadMessages()
  } finally {
    sending.value = false
  }
}

function togglePolling() {
  polling.value = !polling.value
  if (polling.value) {
    timer = setInterval(async () => {
      await loadConversations()
      if (selectedConv.value) {
        await loadMessages()
      }
    }, 3000)
  } else if (timer) {
    clearInterval(timer)
    timer = null
  }
}

function msgClass(sender?: string) {
  return sender === 'SELLER' ? 'msg-mine' : sender === 'SYSTEM' ? 'msg-system' : 'msg-buyer'
}

function scrollToBottom() {
  nextTick(() => {
    const el = document.querySelector('.msg-list .el-scrollbar__view')
    if (el) el.scrollTop = el.scrollHeight
  })
}

onMounted(loadAccounts)
onUnmounted(() => {
  if (timer) clearInterval(timer)
})
</script>

<style scoped lang="scss">
.chat-page { padding: 0; }
.chat-card { height: calc(100vh - 140px); }
.chat-header { border-bottom: 1px solid var(--el-border-color-light); padding-bottom: 8px; }
.chat-body { display: flex; gap: 12px; margin-top: 12px; height: calc(100% - 80px); }
.conv-list { width: 260px; border-right: 1px solid var(--el-border-color-light); padding-right: 8px; }
.msg-area { flex: 1; display: flex; flex-direction: column; }

.conv-item {
  padding: 8px 12px;
  border-radius: 4px;
  cursor: pointer;
  &:hover { background: var(--el-fill-color-light); }
  &.active { background: var(--el-color-primary-light-9); }
  .conv-head {
    display: flex;
    justify-content: space-between;
    align-items: center;
    .conv-nick { font-weight: 500; }
  }
  .conv-last {
    font-size: 12px;
    color: var(--el-text-color-secondary);
    margin: 4px 0;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
  .conv-time { font-size: 11px; color: var(--el-text-color-placeholder); }
}

.empty-tip { display: flex; align-items: center; justify-content: center; height: 100%; }

.msg-list { flex: 1; padding: 8px; }
.msg-bubble {
  max-width: 70%;
  margin: 8px 0;
  padding: 8px 12px;
  border-radius: 6px;
  word-wrap: break-word;
  &.msg-mine {
    margin-left: auto;
    background: var(--el-color-primary-light-8);
    border: 1px solid var(--el-color-primary-light-5);
  }
  &.msg-buyer {
    background: var(--el-fill-color-light);
  }
  &.msg-system {
    margin: 0 auto;
    background: var(--el-fill-color);
    text-align: center;
    color: var(--el-text-color-secondary);
  }
  .msg-sender {
    font-size: 12px;
    color: var(--el-text-color-secondary);
    margin-bottom: 4px;
    .msg-time { margin-left: 8px; }
  }
}

.msg-input {
  display: flex;
  gap: 8px;
  margin-top: 8px;
  .el-button { align-self: flex-end; }
}
</style>
