<template>
  <div class="chat-page">
    <div class="chat-layout">
      <!-- 聊天窗口 -->
      <div class="chat-panel">
        <el-card class="chat-card" shadow="never">
          <!-- 聊天头部 -->
          <template #header>
            <div class="chat-header">
              <div class="header-left">
                <el-button class="back-btn" text circle @click="goBack" title="返回上一页">
                  <el-icon><ArrowLeft /></el-icon>
                </el-button>
                <div class="chat-title">
                  <span>🤖 智能新闻对话</span>
                  
                </div>
              </div>
              <el-button size="small" text @click="clearChat">
                <el-icon><Delete /></el-icon>
                清空对话
              </el-button>
            </div>
          </template>

          <!-- 消息列表 -->
          <div class="chat-messages" ref="messagesContainer">
            <div
              v-for="(msg, idx) in messages"
              :key="idx"
              :class="['message-wrapper', msg.role]"
            >
              <div class="avatar">
                <span v-if="msg.role === 'assistant'">🤖</span>
                <span v-else>👤</span>
              </div>
              <div :class="['message-bubble', msg.role]">
                <div class="message-text" v-html="formatMessage(msg.content)"></div>
                <div class="message-time">{{ msg.time }}</div>
              </div>
            </div>

            <!-- 正在输入指示器 -->
            <div v-if="isTyping" class="message-wrapper assistant">
              <div class="avatar"><span>🤖</span></div>
              <div class="message-bubble assistant typing-indicator">
                <span class="dot"></span>
                <span class="dot"></span>
                <span class="dot"></span>
              </div>
            </div>
          </div>

          <!-- 快捷问题 -->
          <div class="quick-questions" v-if="messages.length <= 1">
            <p class="quick-label">💡 试试问我：</p>
            <div class="quick-btns">
              <el-button
                v-for="q in quickQuestions"
                :key="q"
                size="small"
                round
                @click="sendQuickQuestion(q)"
              >
                {{ q }}
              </el-button>
            </div>
          </div>

          <!-- 附加的新闻上下文区域 -->
          <div class="context-attachment" v-if="attachedNewsContext">
            <div class="context-info">
              <el-icon><Document /></el-icon>
              <span>已关联新闻：<strong>{{ attachedNewsContext.title }}</strong></span>
            </div>
            <el-button class="remove-context-btn" type="danger" text circle size="small" @click="removeContext" title="移除关联">
              <el-icon><Close /></el-icon>
            </el-button>
          </div>

          <!-- 输入区域 -->
          <div class="chat-input-area">
            <el-input
              v-model="inputMessage"
              :autosize="{ minRows: 1, maxRows: 4 }"
              type="textarea"
              :placeholder="attachedNewsContext ? `提问关于《${attachedNewsContext.title}》的问题...` : '输入你关于新闻的问题，AI 将结合新闻库为你解答...'"
              resize="none"
              @keydown.enter.exact.prevent="sendMessage"
              :disabled="isTyping"
            />
            <el-button
              type="primary"
              :icon="Promotion"
              circle
              size="large"
              :loading="isTyping"
              :disabled="!inputMessage.trim() || isTyping"
              @click="sendMessage"
              class="send-btn"
            />
          </div>
        </el-card>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Delete, Promotion, Document, Close, ArrowLeft } from '@element-plus/icons-vue'
import { chatApi } from '../api/index.js'

const route = useRoute()
const router = useRouter()
const messagesContainer = ref(null)
const inputMessage = ref('')
const isTyping = ref(false)

// 附加的新闻上下文
const attachedNewsContext = ref(null)

const quickQuestions = [
  '今天有什么关于AI的大新闻？',
  '最近科技领域有什么突破？',
  '帮我总结今日热点新闻',
  '有什么和教育相关的新闻？'
]

const getCurrentTime = () => {
  const now = new Date()
  return `${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}`
}

const defaultWelcomeMessage = {
  role: 'assistant',
  content: '你好！👋 我是智能新闻助手，我能结合本地新闻库为你提供准确的新闻资讯和分析。\n\n你可以问我任何关于新闻的问题，例如：\n- 今天有什么重要新闻？\n- 最近 AI 领域有哪些进展？\n- 帮我分析某条新闻的影响',
  time: getCurrentTime()
}

const messages = ref([])
// 仅用于后端 /api/chat 的上下文：不包含 time 字段
const sessionMessages = ref([])

// 持久化聊天记录
const loadChatHistory = () => {
  try {
    const savedMessages = localStorage.getItem('ina_chat_messages')
    const savedSession = localStorage.getItem('ina_session_messages')
    
    if (savedMessages && savedSession) {
      messages.value = JSON.parse(savedMessages)
      sessionMessages.value = JSON.parse(savedSession)
    } else {
      // 没有历史记录时，加载默认欢迎语
      messages.value = [defaultWelcomeMessage]
      sessionMessages.value = []
    }
  } catch (e) {
    console.error('加载聊天记录失败', e)
    messages.value = [defaultWelcomeMessage]
    sessionMessages.value = []
  }
}

const saveChatHistory = () => {
  try {
    localStorage.setItem('ina_chat_messages', JSON.stringify(messages.value))
    localStorage.setItem('ina_session_messages', JSON.stringify(sessionMessages.value))
  } catch (e) {
    console.error('保存聊天记录失败', e)
  }
}

const formatMessage = (text) => {
  return text
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\n/g, '<br />')
    .replace(/- (.*?)(?=<br|$)/g, '• $1')
}

const scrollToBottom = async () => {
  await nextTick()
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}

const sendQuickQuestion = (question) => {
  inputMessage.value = question
  sendMessage()
}

const removeContext = () => {
  attachedNewsContext.value = null
  // 移除 URL 中的 query 参数
  router.replace({ query: {} })
  ElMessage.success('已取消关联新闻')
}

const sendMessage = async () => {
  const content = inputMessage.value.trim()
  if (!content || isTyping.value) return

  // 如果有关联新闻，将其作为隐藏上下文拼接到实际发送给后端的请求中，但前端UI只展示用户原本的话
  let actualContentToSend = content
  if (attachedNewsContext.value) {
    actualContentToSend = `[基于新闻ID:${attachedNewsContext.value.id}，标题:"${attachedNewsContext.value.title}"]\n${content}`
  }

  // 添加用户消息到前端 UI 显示
  messages.value.push({
    role: 'user',
    content, // 前端仅显示用户的实际输入
    time: getCurrentTime()
  })
  
  // 发送给后端的会话消息，包含隐藏的上下文
  sessionMessages.value.push({ role: 'user', content: actualContentToSend })
  inputMessage.value = ''
  isTyping.value = true
  await scrollToBottom()

  try {
    const res = await chatApi.sendMessages(sessionMessages.value)
    if (res?.code !== 0) {
      throw new Error(res?.message || '对话失败')
    }
    const answer = res?.data?.answer
    if (!answer) {
      throw new Error('对话失败：未获取到 answer')
    }

    messages.value.push({
      role: 'assistant',
      content: answer,
      time: getCurrentTime()
    })
    sessionMessages.value.push({ role: 'assistant', content: answer })
    saveChatHistory() // 保存记录
  } catch (error) {
    const backendMsg =
      error?.response?.data?.message ||
      error?.response?.data?.detail ||
      error?.message ||
      '对话失败'
    ElMessage.error(backendMsg)
    // 回滚本次用户消息
    messages.value.pop()
    sessionMessages.value.pop()
  } finally {
    isTyping.value = false
    await scrollToBottom()
  }
}

const clearChat = () => {
  messages.value = [defaultWelcomeMessage]
  sessionMessages.value = []
  localStorage.removeItem('ina_chat_messages')
  localStorage.removeItem('ina_session_messages')
  ElMessage.success('对话已清空')
}

const goBack = () => {
  // 返回到跳转过来的上一页
  router.back()
}

onMounted(() => {
  loadChatHistory()
  scrollToBottom()
  
  // 检查是否是从新闻详情页带了新闻上下文过来
  if (route.query.context_id && route.query.context_title) {
    attachedNewsContext.value = {
      id: route.query.context_id,
      title: decodeURIComponent(route.query.context_title)
    }
  }
})
</script>

<style scoped>
.chat-page {
  height: calc(100vh - 120px);
  max-width: 1000px;
  margin: 0 auto;
  padding-bottom: 24px;
}
.chat-layout {
  display: flex;
  height: 100%;
}

/* ===== 聊天面板 ===== */
.chat-panel {
  flex: 1;
  min-width: 0;
  height: 100%;
}
.chat-card {
  height: 100%;
  border-radius: var(--ina-radius-md);
  display: flex;
  flex-direction: column;
  background: var(--ina-surface-solid);
  border: 1px solid var(--ina-border);
  box-shadow: var(--ina-shadow-sm);
}
:deep(.chat-card > .el-card__body) {
  flex: 1;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  padding: 0;
}
.chat-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid var(--ina-border);
}
.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}
.back-btn {
  font-size: 18px;
  padding: 8px;
}
.chat-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 18px;
  font-weight: 700;
  color: var(--ina-text);
  letter-spacing: -0.3px;
}

/* ===== 消息区域 ===== */
.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 24px;
  background: var(--ina-bg);
}
.message-wrapper {
  display: flex;
  gap: 16px;
  max-width: 85%;
}
.message-wrapper.user {
  flex-direction: row-reverse;
  align-self: flex-end;
}
.message-wrapper.assistant {
  align-self: flex-start;
}
.avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  flex-shrink: 0;
  background: var(--ina-surface-solid);
  border: 1px solid var(--ina-border);
}
.message-wrapper.user .avatar {
  background: var(--ina-primary);
  color: white;
  border-color: transparent;
}
.message-wrapper.assistant .avatar {
  background: var(--ina-accent);
  color: white;
  border-color: transparent;
}
.message-bubble {
  padding: 16px 20px;
  border-radius: var(--ina-radius-md);
  font-size: 15px;
  line-height: 1.6;
  position: relative;
  box-shadow: var(--ina-shadow-sm);
}
.message-bubble.assistant {
  background: var(--ina-surface-solid);
  color: var(--ina-text);
  border: 1px solid var(--ina-border);
  border-top-left-radius: 4px;
}
.message-bubble.user {
  background: var(--ina-primary);
  color: #ffffff;
  border: none;
  border-top-right-radius: 4px;
}
.message-text {
  word-break: break-word;
}
.message-text :deep(strong) {
  font-weight: 700;
}
.message-time {
  font-size: 11px;
  opacity: 0.6;
  margin-top: 6px;
  text-align: right;
}

/* ===== 打字指示器 ===== */
.typing-indicator {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 16px 20px;
}
.typing-indicator .dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #909399;
  animation: typingBounce 1.4s infinite ease-in-out;
}
.typing-indicator .dot:nth-child(1) { animation-delay: 0s; }
.typing-indicator .dot:nth-child(2) { animation-delay: 0.2s; }
.typing-indicator .dot:nth-child(3) { animation-delay: 0.4s; }
@keyframes typingBounce {
  0%, 80%, 100% { transform: scale(0.6); opacity: 0.4; }
  40% { transform: scale(1); opacity: 1; }
}

/* ===== 快捷问题 ===== */
.quick-questions {
  padding: 0 20px 12px;
  border-top: 1px solid rgba(31, 45, 61, 0.10);
}
.quick-label {
  font-size: 13px;
  color: var(--ina-text-3);
  margin: 12px 0 8px;
}
.quick-btns {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

/* ===== 附加新闻上下文 ===== */
.context-attachment {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  margin: 0 24px 16px;
  background-color: var(--ina-bg-2);
  border: 1px solid var(--ina-border);
  border-radius: var(--ina-radius-sm);
  color: var(--ina-accent);
  font-size: 14px;
}
.context-info {
  display: flex;
  align-items: center;
  gap: 8px;
  overflow: hidden;
  font-weight: 500;
}
.context-info span {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.remove-context-btn {
  margin-left: 10px;
}

/* ===== 输入区域 ===== */
.chat-input-area {
  display: flex;
  align-items: flex-end;
  gap: 16px;
  padding: 20px 24px;
  border-top: 1px solid var(--ina-border);
  background: var(--ina-surface-solid);
}
.chat-input-area :deep(.el-textarea__inner) {
  border-radius: var(--ina-radius-sm);
  padding: 12px 16px;
  font-size: 15px;
  background: var(--ina-bg);
  border: 1px solid var(--ina-border);
  box-shadow: none !important;
  transition: all 0.2s ease;
}
.chat-input-area :deep(.el-textarea__inner:focus) {
  background: var(--ina-surface-solid);
  border-color: var(--ina-accent);
  box-shadow: 0 0 0 1px var(--ina-accent) !important;
}
.send-btn {
  flex-shrink: 0;
  width: 48px;
  height: 48px;
  background-color: var(--ina-accent) !important;
  border-color: var(--ina-accent) !important;
  border-radius: var(--ina-radius-sm);
}
.send-btn:hover {
  background-color: #1d4ed8 !important;
  border-color: #1d4ed8 !important;
}

@media (max-width: 768px) {
  .chat-page {
    height: auto;
  }
}
</style>
