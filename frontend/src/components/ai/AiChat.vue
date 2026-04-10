<template>
  <div class="ai-chat-container">
    <!-- 头部区域 -->
    <div class="ai-chat-header">
      <div class="header-left">
        <slot name="header-left">
          <el-button
            v-if="showSidebarToggle"
            :icon="sidebarCollapsed ? Expand : Fold"
            circle
            size="small"
            @click="toggleSidebar"
          />
          <span class="header-title">{{ title }}</span>
        </slot>
      </div>
      
      <div class="header-center">
        <slot name="header-center">
          <!-- 模型选择器 -->
          <el-popover
            v-if="showModelSelector"
            v-model:visible="modelSelectorVisible"
            placement="bottom"
            :width="360"
            trigger="click"
            popper-class="model-selector-popover"
          >
            <template #reference>
              <el-button
                class="model-selector-btn"
                :disabled="isStreaming"
              >
                <span class="model-name">{{ currentModelName }}</span>
                <el-icon class="dropdown-icon"><ArrowDown /></el-icon>
              </el-button>
            </template>

            <div class="model-selector-dropdown">
              <div class="model-groups">
                <div
                  v-for="group in modelGroups"
                  :key="group.label"
                  class="model-group"
                >
                  <div class="group-label">{{ group.label }}</div>
                  <div class="model-list">
                    <div
                      v-for="model in group.models"
                      :key="model.id"
                      class="model-item"
                      :class="{ active: selectedModel === model.id }"
                      @click="selectModel(model.id)"
                    >
                      <div class="model-info">
                        <span class="model-name">{{ model.name }}</span>
                        <el-tag v-if="model.tag" size="small" effect="plain" class="model-tag">{{ model.tag }}</el-tag>
                      </div>
                      <el-checkbox
                        v-if="selectedModel === model.id"
                        v-model="isDefaultModel"
                        size="small"
                        @click.stop
                        @change="handleSetDefault(model.id)"
                      >
                        设为默认
                      </el-checkbox>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </el-popover>
        </slot>
      </div>
      
      <div class="header-right">
        <slot name="header-right" />
      </div>
    </div>
    
    <!-- 消息列表区域 -->
    <div class="ai-chat-messages" ref="messagesContainer">
      <!-- 欢迎区域 -->
      <div v-if="showWelcome && messages.length === 0 && !isStreaming" class="welcome-area">
        <slot name="welcome">
          <Welcome
            :title="welcomeTitle"
            :description="welcomeDescription"
            :icon="welcomeIcon"
          />
          <Prompts
            v-if="prompts.length > 0"
            :items="prompts"
            @click="handlePromptClick"
          />
        </slot>
      </div>
      
      <!-- 消息列表 -->
      <BubbleList
        v-else-if="bubbleList.length > 0"
        :list="bubbleList"
        :typing="false"
        :loading="false"
        :btn-loading="false"
        @action="handleMessageAction"
      >
        <template #avatar="{ item }">
          <slot name="message-avatar" :item="item">
            <el-avatar
              :size="36"
              :src="item.role === 'user' ? userAvatar : aiAvatar"
              :style="item.role === 'assistant' ? aiAvatarStyle : {}"
            >
              {{ item.role === 'user' ? userName?.[0] || 'U' : 'AI' }}
            </el-avatar>
          </slot>
        </template>
        
        <template #content="{ item }">
          <slot name="message-content" :item="item">
            <div class="message-content-wrapper">
              <AiMessage
                :content="item.content"
                :thinking="item.thinking"
                :thinking-duration="item.thinkingDuration"
                :sources="item.sources"
                :role="item.role"
                :loading="item.loading"
                :interrupted="item.interrupted"
                @source-click="handleSourceClick"
              />
              <div class="message-actions-inline">
                <el-tooltip content="复制" placement="bottom">
                  <el-button link size="small" @click="copyMessage(item.content)">
                    <el-icon><DocumentCopy /></el-icon>
                  </el-button>
                </el-tooltip>
                <el-tooltip v-if="item.role === 'assistant' && isLastMessage(item)" content="重新生成" placement="bottom">
                  <el-button link size="small" @click="regenerateMessage(item)">
                    <el-icon><RefreshRight /></el-icon>
                  </el-button>
                </el-tooltip>
                <el-tooltip v-if="item.role === 'user' && isLastUserMessage(item)" content="编辑" placement="bottom">
                  <el-button link size="small" @click="editMessage(item)">
                    <el-icon><Edit /></el-icon>
                  </el-button>
                </el-tooltip>
              </div>
            </div>
          </slot>
        </template>
      </BubbleList>
      
      <!-- 滚动到底部按钮 -->
      <transition name="fade">
        <div v-if="showScrollBtn" class="scroll-to-bottom" @click="scrollToBottom(true)">
          <el-icon :size="20"><ArrowDown /></el-icon>
        </div>
      </transition>
    </div>
    
    <!-- 输入区域 -->
    <div class="ai-chat-input">
      <slot name="input">
        <div class="custom-sender">
          <div class="sender-wrapper">
            <el-input
              v-model="inputMessage"
              type="textarea"
              :autosize="{ minRows: 1, maxRows: 6 }"
              :placeholder="inputPlaceholder"
              :disabled="inputDisabled"
              resize="none"
              @keydown.enter.exact.prevent="handleSend"
            />
          </div>
          <div class="sender-actions">
            <slot name="input-prefix" />
            <!-- 语音按钮 -->
            <el-tooltip
              v-if="allowSpeech"
              :content="speechLoading ? '正在录音...' : '语音输入'"
              placement="top"
            >
              <el-button
                :type="speechLoading ? 'danger' : 'default'"
                :icon="speechLoading ? VideoPause : Microphone"
                circle
                size="small"
                :loading="speechLoading"
                @click="$emit('speech')"
              />
            </el-tooltip>
            <!-- 发送/停止按钮 -->
            <el-button
              v-if="isStreaming"
              type="danger"
              :icon="VideoPause"
              circle
              size="small"
              @click="handleStop"
            />
            <el-button
              v-else
              type="primary"
              :icon="Promotion"
              circle
              size="small"
              :disabled="!inputMessage.trim() || inputDisabled"
              @click="handleSend"
            />
            <slot name="input-suffix" />
          </div>
        </div>
      </slot>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick, onMounted, onUnmounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Expand,
  Fold,
  DocumentCopy,
  RefreshRight,
  Edit,
  ArrowDown,
  Microphone,
  VideoPause,
  Promotion,
  Check
} from '@element-plus/icons-vue'
import { Welcome, Prompts, BubbleList } from 'vue-element-plus-x'
import AiMessage from './AiMessage.vue'

const props = defineProps({
  // 基础配置
  title: { type: String, default: 'AI 助手' },
  messages: { type: Array, default: () => [] },
  loading: { type: Boolean, default: false },
  isStreaming: { type: Boolean, default: false },
  
  // 欢迎区域
  showWelcome: { type: Boolean, default: true },
  welcomeTitle: { type: String, default: '你好，我是 AI 助手' },
  welcomeDescription: { type: String, default: '有什么我可以帮你的吗？' },
  welcomeIcon: { type: String, default: '' },
  prompts: { type: Array, default: () => [] },
  
  // 用户配置
  userName: { type: String, default: 'User' },
  userAvatar: { type: String, default: '' },
  aiAvatar: { type: String, default: '' },
  aiAvatarStyle: { type: Object, default: () => ({ background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' }) },
  
  // 模型配置
  showModelSelector: { type: Boolean, default: true },
  models: { type: Array, default: () => [] },
  defaultModel: { type: String, default: '' },
  
  // 输入配置
  inputPlaceholder: { type: String, default: '输入您的问题...' },
  inputDisabled: { type: Boolean, default: false },
  allowSpeech: { type: Boolean, default: true },
  speechLoading: { type: Boolean, default: false },
  
  // 布局配置
  showSidebarToggle: { type: Boolean, default: false },
  sidebarCollapsed: { type: Boolean, default: false }
})

const emit = defineEmits([
  'update:sidebarCollapsed',
  'send',
  'stop',
  'regenerate',
  'edit',
  'prompt-click',
  'source-click',
  'speech',
  'update:model'
])

// 状态
const inputMessage = ref('')
const selectedModel = ref(props.defaultModel)
const messagesContainer = ref(null)
const showScrollBtn = ref(false)
const modelSelectorVisible = ref(false)
const isDefaultModel = ref(false)
let userAtBottom = true

// 计算属性 - 当前模型名称
const currentModelName = computed(() => {
  const model = props.models.find(m => m.id === selectedModel.value)
  return model?.name || selectedModel.value || '选择模型'
})

// 计算属性 - 使用稳定的key避免不必要的重新渲染
const bubbleList = computed(() => {
  return props.messages.map((msg, index) => ({
    ...msg,
    key: msg.id || `msg-${index}`,
    placement: msg.role === 'user' ? 'end' : 'start',
    loading: msg.loading || false
  }))
})

const modelGroups = computed(() => {
  const groups = []
  const customModels = props.models.filter(m => m.type === 'custom')
  const ollamaModels = props.models.filter(m => m.type === 'ollama')
  
  if (customModels.length) {
    groups.push({
      label: '自定义模型',
      models: customModels.map(m => ({ ...m, tag: m.base_model }))
    })
  }
  
  if (ollamaModels.length) {
    groups.push({
      label: 'Ollama 基础模型',
      models: ollamaModels
    })
  }
  
  return groups
})

// 方法
function toggleSidebar() {
  emit('update:sidebarCollapsed', !props.sidebarCollapsed)
}

// 选择模型
function selectModel(modelId) {
  selectedModel.value = modelId
  emit('update:model', modelId)
  modelSelectorVisible.value = false

  // Check if this model is the default
  const savedDefault = localStorage.getItem('sfqa_default_model')
  isDefaultModel.value = savedDefault === modelId
}

// 设置默认模型
function handleSetDefault(modelId) {
  if (isDefaultModel.value) {
    localStorage.setItem('sfqa_default_model', modelId)
    ElMessage.success(`已将 ${currentModelName.value} 设为默认模型`)
  } else {
    // User unchecked the default option
    const savedDefault = localStorage.getItem('sfqa_default_model')
    if (savedDefault === modelId) {
      localStorage.removeItem('sfqa_default_model')
      ElMessage.info('已取消默认模型设置')
    }
  }
}

function handleSend() {
  if (!inputMessage.value.trim()) return

  if (props.isStreaming) {
    ElMessageBox.confirm('当前正在生成回答，发送新消息将暂停回答。确定继续吗？', '确认发送', {
      confirmButtonText: '发送',
      cancelButtonText: '取消',
      type: 'warning'
    }).then(() => {
      const messageToSend = inputMessage.value.trim()
      emit('stop')
      nextTick(() => {
        emit('send', {
          content: messageToSend,
          model: selectedModel.value
        })
        inputMessage.value = ''
      })
    }).catch(() => {})
  } else {
    emit('send', {
      content: inputMessage.value.trim(),
      model: selectedModel.value
    })
    inputMessage.value = ''
  }
}

function handleStop() {
  emit('stop')
}

function handlePromptClick(prompt) {
  emit('prompt-click', prompt)
  inputMessage.value = prompt.content || prompt.label
}

function handleMessageAction(action, item) {
  if (action === 'copy') {
    copyMessage(item.content)
  } else if (action === 'regenerate') {
    emit('regenerate', item)
  }
}

function handleSourceClick(source) {
  emit('source-click', source)
}

function handleSpeech() {
  emit('speech')
}

async function copyMessage(content) {
  try {
    await navigator.clipboard.writeText(content)
    ElMessage.success('已复制到剪贴板')
  } catch {
    const textarea = document.createElement('textarea')
    textarea.value = content
    document.body.appendChild(textarea)
    textarea.select()
    document.execCommand('copy')
    document.body.removeChild(textarea)
    ElMessage.success('已复制到剪贴板')
  }
}

function regenerateMessage(item) {
  emit('regenerate', item)
}

function editMessage(item) {
  emit('edit', item)
  inputMessage.value = item.content
}

function isLastMessage(item) {
  const lastMsg = props.messages[props.messages.length - 1]
  return lastMsg && lastMsg.id === item.id
}

function isLastUserMessage(item) {
  for (let i = props.messages.length - 1; i >= 0; i--) {
    if (props.messages[i].role === 'user') {
      return props.messages[i].id === item.id
    }
  }
  return false
}

// ==================== Scroll Handling with Safety Checks ====================

/**
 * Safely check if scroll position is near bottom
 * Includes null checks to prevent errors when DOM is not ready
 */
function isNearBottom() {
  const el = messagesContainer.value
  if (!el || typeof el.scrollHeight === 'undefined' || typeof el.scrollTop === 'undefined' || typeof el.clientHeight === 'undefined') {
    return true
  }
  return el.scrollHeight - el.scrollTop - el.clientHeight < 100
}

/**
 * Handle scroll events to track user position
 */
function onScroll() {
  userAtBottom = isNearBottom()
  showScrollBtn.value = !userAtBottom
}

/**
 * Safely scroll to bottom with comprehensive null checks
 * Uses requestAnimationFrame for better performance and safety
 */
function scrollToBottom(force = false) {
  // Skip if user has scrolled up (unless forced) or container not available
  if (!force && !userAtBottom) return

  // Use requestAnimationFrame to ensure DOM is ready
  requestAnimationFrame(() => {
    nextTick(() => {
      const el = messagesContainer.value

      // Comprehensive null and type checking
      if (!el || !(el instanceof Element)) {
        console.debug('scrollToBottom: Container not available')
        return
      }

      // Check if element is connected to DOM and visible
      if (!el.isConnected) {
        console.debug('scrollToBottom: Container not connected to DOM')
        return
      }

      // Safely access scroll properties with default values
      const scrollHeight = el.scrollHeight ?? 0
      const clientHeight = el.clientHeight ?? 0

      // Only scroll if there's actual content to scroll
      if (scrollHeight > clientHeight) {
        try {
          el.scrollTop = scrollHeight
          userAtBottom = true
          showScrollBtn.value = false
        } catch (e) {
          console.warn('scrollToBottom: Error during scroll', e)
        }
      }
    })
  })
}

/**
 * Safe scroll with retry mechanism for v-if conditions
 */
function scrollToBottomSafe(force = false, maxRetries = 3) {
  let attempts = 0

  const attemptScroll = () => {
    const el = messagesContainer.value

    if (el && el.isConnected) {
      scrollToBottom(force)
      return true
    }

    attempts++
    if (attempts < maxRetries) {
      // Retry after a short delay
      setTimeout(attemptScroll, 100)
    }
    return false
  }

  attemptScroll()
}

// ==================== Watchers with Safety ====================

// Watch messages and scroll to bottom on new messages
watch(() => props.messages, (newMessages, oldMessages) => {
  // Only scroll if messages actually changed and increased
  if (newMessages && oldMessages && newMessages.length > oldMessages.length) {
    scrollToBottomSafe()
  }
}, { deep: true, flush: 'post' })

// Watch streaming state
watch(() => props.isStreaming, (val, oldVal) => {
  if (val && !oldVal) {
    // Started streaming - force scroll
    scrollToBottomSafe(true)
  } else if (!val && oldVal) {
    // Finished streaming - scroll after content settles
    setTimeout(() => scrollToBottomSafe(true), 100)
  }
})

// Watch for container visibility changes (v-if conditions)
watch(messagesContainer, (el) => {
  if (el) {
    // Container became available - attach scroll listener and scroll
    el.addEventListener('scroll', onScroll)
    scrollToBottomSafe(true)
  }
})

watch(selectedModel, (val) => {
  emit('update:model', val)

  // Update isDefaultModel checkbox state when model changes
  const savedDefault = localStorage.getItem('sfqa_default_model')
  isDefaultModel.value = savedDefault === val
})

// Watch for external defaultModel changes
watch(() => props.defaultModel, (val) => {
  if (val && val !== selectedModel.value) {
    selectedModel.value = val
  }
})

// Initialize isDefaultModel on mount
onMounted(() => {
  const savedDefault = localStorage.getItem('sfqa_default_model')
  isDefaultModel.value = savedDefault === selectedModel.value
})

// ==================== Lifecycle ====================

onMounted(() => {
  // Delay scroll to ensure DOM is fully rendered
  setTimeout(() => {
    scrollToBottomSafe(true)
  }, 50)
})

onUnmounted(() => {
  // Clean up scroll listener
  const el = messagesContainer.value
  if (el) {
    el.removeEventListener('scroll', onScroll)
  }
})
</script>

<style scoped lang="scss">
.ai-chat-container {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: linear-gradient(180deg, #FAFBFE 0%, #F3F1FF 50%, #EEEDF9 100%);
}

.ai-chat-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 20px;
  background: rgba(255, 255, 255, 0.82);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border-bottom: 1px solid rgba(99, 102, 241, 0.08);
  height: 56px;
  flex-shrink: 0;
  
  .header-left {
    display: flex;
    align-items: center;
    gap: 12px;
    flex: 1;
    
    .header-title {
      font-size: 16px;
      font-weight: 700;
      background: linear-gradient(135deg, #4F46E5, #7C3AED);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      background-clip: text;
      letter-spacing: -0.3px;
    }
  }
  
  .header-center {
    display: flex;
    align-items: center;
    gap: 8px;

    .model-selector-btn {
      display: flex;
      align-items: center;
      gap: 12px;
      padding: 10px 20px;
      border-radius: 14px;
      background: rgba(99, 102, 241, 0.06);
      border: 1px solid rgba(99, 102, 241, 0.12);
      color: #1E1B4B;
      font-weight: 600;
      font-size: 15px;
      transition: all 0.25s ease;
      min-width: 160px;
      justify-content: space-between;

      &:hover {
        background: rgba(99, 102, 241, 0.1);
        border-color: rgba(99, 102, 241, 0.22);
        box-shadow: 0 4px 12px rgba(99, 102, 241, 0.15);
      }

      &:active {
        background: rgba(99, 102, 241, 0.14);
        transform: scale(0.98);
      }

      .model-name {
        max-width: 200px;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
      }

      .dropdown-icon {
        color: #6366F1;
        font-size: 16px;
        transition: transform 0.25s ease;
      }

      &[aria-expanded="true"] .dropdown-icon {
        transform: rotate(180deg);
      }
    }
  }
  
  .header-right {
    display: flex;
    align-items: center;
    gap: 8px;
    flex: 1;
    justify-content: flex-end;
  }
}

:deep(.model-selector-popover) {
  padding: 0 !important;
  border-radius: 16px;
  box-shadow: 0 12px 40px rgba(99, 102, 241, 0.2);
  border: 1px solid rgba(99, 102, 241, 0.12);
  overflow: hidden;
}

.model-selector-dropdown {
  max-height: 480px;
  overflow-y: auto;

  .model-groups {
    padding: 12px 0;
  }

  .model-group {
    &:not(:last-child) {
      margin-bottom: 8px;
      padding-bottom: 8px;
      border-bottom: 1px solid rgba(99, 102, 241, 0.06);
    }

    .group-label {
      padding: 12px 24px;
      font-size: 13px;
      font-weight: 600;
      color: #6B7280;
      text-transform: uppercase;
      letter-spacing: 0.8px;
    }

    .model-list {
      .model-item {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 16px 24px;
        margin: 4px 12px;
        cursor: pointer;
        transition: all 0.25s ease;
        border-radius: 12px;
        border: 2px solid transparent;

        &:hover {
          background: rgba(99, 102, 241, 0.06);
          border-color: rgba(99, 102, 241, 0.1);
        }

        &.active {
          background: linear-gradient(135deg, rgba(99, 102, 241, 0.12) 0%, rgba(124, 58, 210, 0.08) 100%);
          border-color: rgba(99, 102, 241, 0.25);

          .model-name {
            color: #4F46E5;
            font-weight: 700;
          }
        }

        .model-info {
          display: flex;
          align-items: center;
          gap: 16px;
          flex: 1;
          min-width: 0;

          .model-name {
            font-size: 15px;
            font-weight: 600;
            color: #1E1B4B;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
          }

          .model-tag {
            border-radius: 8px;
            font-weight: 500;
            font-size: 12px;
            background: rgba(99, 102, 241, 0.1);
            border-color: rgba(99, 102, 241, 0.25);
            color: #6366F1;
            padding: 4px 12px;
            flex-shrink: 0;
          }
        }

        :deep(.el-checkbox) {
          margin-right: 0;
          margin-left: 16px;
          flex-shrink: 0;

          .el-checkbox__label {
            font-size: 13px;
            color: #6366F1;
            padding-left: 6px;
            font-weight: 500;
          }

          .el-checkbox__input.is-checked .el-checkbox__inner {
            background-color: #6366F1;
            border-color: #6366F1;
          }

          .el-checkbox__inner {
            width: 18px;
            height: 18px;
          }
        }
      }
    }
  }
}

// Legacy styles for backward compatibility
.model-option {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;

  .model-option-info {
    display: flex;
    align-items: center;
    gap: 10px;
    width: 100%;
  }

  .model-name {
    font-size: 14px;
    font-weight: 600;
    color: #1E1B4B;
    flex: 1;
  }

  .model-tag {
    border-radius: 6px;
    font-weight: 500;
    font-size: 12px;
    background: rgba(99, 102, 241, 0.08);
    border-color: rgba(99, 102, 241, 0.2);
    color: #6366F1;
  }
}

.ai-chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 28px 32px;
  position: relative;
  scroll-behavior: smooth;
  
  .welcome-area {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    height: 100%;
    gap: 28px;
  }
}

.scroll-to-bottom {
  position: absolute;
  bottom: 24px;
  left: 50%;
  transform: translateX(-50%);
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: #fff;
  box-shadow: 0 4px 20px rgba(79, 70, 229, 0.18), 0 1px 3px rgba(0, 0, 0, 0.06);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  z-index: 10;
  color: #6366F1;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  border: 1px solid rgba(99, 102, 241, 0.12);
  
  &:hover {
    background: linear-gradient(135deg, #6366F1, #8B5CF6);
    color: #fff;
    box-shadow: 0 6px 24px rgba(99, 102, 241, 0.35);
    transform: translateX(-50%) translateY(-2px);
  }
}

.ai-chat-input {
  padding: 16px 28px 20px;
  background: rgba(255, 255, 255, 0.65);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  border-top: 1px solid rgba(99, 102, 241, 0.08);
  flex-shrink: 0;
}

.custom-sender {
  display: flex;
  align-items: flex-end;
  gap: 10px;
  background: #ffffff;
  border: 1px solid rgba(99, 102, 241, 0.14);
  border-radius: 18px;
  padding: 10px 14px;
  box-shadow: 0 2px 12px rgba(79, 70, 229, 0.06), 0 1px 3px rgba(0, 0, 0, 0.04);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);

  &:hover {
    border-color: rgba(99, 102, 241, 0.25);
    box-shadow: 0 4px 20px rgba(79, 70, 229, 0.1);
  }

  &:focus-within {
    border-color: #6366F1;
    box-shadow: 0 0 0 4px rgba(99, 102, 241, 0.12), 0 4px 20px rgba(79, 70, 229, 0.08);
  }

  .sender-wrapper {
    flex: 1;
    min-width: 0;

    :deep(.el-textarea__inner) {
      border: none;
      box-shadow: none;
      resize: none;
      padding: 6px 4px;
      font-size: 15px;
      line-height: 1.6;
      color: #1E1B4B;

      &::placeholder {
        color: #A5A3C9;
      }
      
      &:focus {
        box-shadow: none;
      }
    }
  }

  .sender-actions {
    display: flex;
    align-items: center;
    gap: 6px;
    flex-shrink: 0;
    padding-bottom: 2px;

    .el-button {
      width: 34px;
      height: 34px;
      border-color: transparent;

      &.el-button--primary {
        background: linear-gradient(135deg, #6366F1, #8B5CF6);
        border-color: transparent;

        &:hover:not(:disabled) {
          background: linear-gradient(135deg, #4F46E5, #7C3AED);
          transform: scale(1.06);
          box-shadow: 0 4px 14px rgba(99, 102, 241, 0.35);
        }
      }

      &:not(.el-button--primary):hover {
        background: rgba(99, 102, 241, 0.08);
        color: #6366F1;
        border-color: transparent;
      }
    }
  }
}

.message-actions-inline {
  display: flex;
  gap: 2px;
  padding: 6px 0 0;
  opacity: 1;

  .el-button {
    color: #8B87B5;
    padding: 4px 8px;
    border-radius: 6px;

    &:hover {
      color: #6366F1;
      background: rgba(99, 102, 241, 0.08);
    }
  }
}

.message-content-wrapper {
  display: flex;
  flex-direction: column;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease, transform 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
  transform: translateY(6px);
}

// EPX BubbleList 消息气泡深度覆盖
.ai-chat-messages {
  :deep(.el-bubble-list) {
    // 定义气泡宽度变量：85% of 列表宽度
    --bubble-max-width: 85%;

    // 气泡容器透明，宽度由内容决定
    .el-bubble {
      background: transparent !important;
      border: none !important;
      box-shadow: none !important;
      width: var(--bubble-max-width);
      max-width: var(--bubble-max-width);
    }

    // AI 消息气泡靠左
    .el-bubble-start {
      margin-right: auto;
    }

    // 用户消息气泡靠右
    .el-bubble-end {
      margin-left: auto;
    }

    // 第二层: .el-bubble-content-wrapper
    .el-bubble-content-wrapper {
      background: transparent !important;
      border: none !important;
      box-shadow: none !important;
      width: 100%;
      max-width: 100%;
    }

    // 第三层: .el-bubble-content 成为flex容器控制对齐
    .el-bubble-content {
      background: transparent !important;
      border: none !important;
      box-shadow: none !important;
      width: 100%;
      max-width: 100%;
      display: flex !important;
      flex-direction: column;
    }

    // AI消息靠左
    .el-bubble-start .el-bubble-content {
      align-items: flex-start;
    }

    // 用户消息靠右
    .el-bubble-end .el-bubble-content {
      align-items: flex-end;
    }
  }
}

// 滚动条样式
.ai-chat-messages {
  &::-webkit-scrollbar {
    width: 5px;
  }
  
  &::-webkit-scrollbar-track {
    background: transparent;
  }
  
  &::-webkit-scrollbar-thumb {
    background: rgba(99, 102, 241, 0.2);
    border-radius: 10px;
    
    &:hover {
      background: rgba(99, 102, 241, 0.35);
    }
  }
}
</style>
