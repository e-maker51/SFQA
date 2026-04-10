import { ref, watch } from 'vue'
import { getItem, setItem, removeItem } from '@/utils/storage'

const STORAGE_PREFIX = 'sfqa_conv:'
const STORAGE_MESSAGES_PREFIX = 'sfqa_conv_messages:'
const STORAGE_LIST_KEY = 'sfqa_conversations_list'
const MAX_CONVERSATIONS = 100
const MAX_MESSAGES_PER_CONV = 500

/**
 * Composable for managing conversation local storage
 * Provides persistent storage for conversations and messages
 */
export function useConversationStorage() {
  const isReady = ref(false)

  /**
   * Save conversation list to localStorage
   */
  function saveConversationsList(conversations) {
    try {
      const data = {
        conversations: conversations.slice(0, MAX_CONVERSATIONS),
        updatedAt: Date.now()
      }
      setItem(STORAGE_LIST_KEY, data)
    } catch (e) {
      console.warn('Failed to save conversations list:', e)
      // If storage is full, clear old message caches
      cleanupOldCaches()
    }
  }

  /**
   * Load conversation list from localStorage
   */
  function loadConversationsList() {
    try {
      const data = getItem(STORAGE_LIST_KEY)
      if (data && data.conversations) {
        return data.conversations
      }
    } catch (e) {
      console.warn('Failed to load conversations list:', e)
    }
    return null
  }

  /**
   * Save messages for a specific conversation
   */
  function saveConversationMessages(conversationId, messages) {
    if (!conversationId) return

    try {
      const key = STORAGE_MESSAGES_PREFIX + conversationId
      const data = {
        messages: messages.slice(-MAX_MESSAGES_PER_CONV), // Keep only last 500 messages
        updatedAt: Date.now()
      }
      setItem(key, data)
    } catch (e) {
      console.warn('Failed to save conversation messages:', e)
      cleanupOldCaches()
    }
  }

  /**
   * Load messages for a specific conversation
   */
  function loadConversationMessages(conversationId) {
    if (!conversationId) return null

    try {
      const key = STORAGE_MESSAGES_PREFIX + conversationId
      const data = getItem(key)
      if (data && data.messages) {
        return data.messages
      }
    } catch (e) {
      console.warn('Failed to load conversation messages:', e)
    }
    return null
  }

  /**
   * Save a single conversation metadata
   */
  function saveConversation(conversation) {
    if (!conversation || !conversation.id) return

    try {
      const key = STORAGE_PREFIX + conversation.id
      const data = {
        ...conversation,
        updatedAt: Date.now()
      }
      setItem(key, data)
    } catch (e) {
      console.warn('Failed to save conversation:', e)
    }
  }

  /**
   * Load a single conversation metadata
   */
  function loadConversation(conversationId) {
    if (!conversationId) return null

    try {
      const key = STORAGE_PREFIX + conversationId
      return getItem(key)
    } catch (e) {
      console.warn('Failed to load conversation:', e)
    }
    return null
  }

  /**
   * Delete conversation data from localStorage
   */
  function deleteConversation(conversationId) {
    if (!conversationId) return

    try {
      removeItem(STORAGE_PREFIX + conversationId)
      removeItem(STORAGE_MESSAGES_PREFIX + conversationId)
    } catch (e) {
      console.warn('Failed to delete conversation:', e)
    }
  }

  /**
   * Clear all conversation-related caches
   */
  function clearAllConversationCaches() {
    try {
      const keysToRemove = []
      for (let i = 0; i < localStorage.length; i++) {
        const key = localStorage.key(i)
        if (key && (key.startsWith(STORAGE_PREFIX) ||
                    key.startsWith(STORAGE_MESSAGES_PREFIX) ||
                    key === STORAGE_LIST_KEY)) {
          keysToRemove.push(key)
        }
      }
      keysToRemove.forEach(key => localStorage.removeItem(key))
    } catch (e) {
      console.warn('Failed to clear conversation caches:', e)
    }
  }

  /**
   * Clean up old caches when storage is full
   */
  function cleanupOldCaches() {
    try {
      const caches = []

      // Collect all message caches with their timestamps
      for (let i = 0; i < localStorage.length; i++) {
        const key = localStorage.key(i)
        if (key && key.startsWith(STORAGE_MESSAGES_PREFIX)) {
          try {
            const data = getItem(key)
            if (data && data.updatedAt) {
              caches.push({ key, updatedAt: data.updatedAt })
            }
          } catch (e) {
            // Ignore invalid entries
          }
        }
      }

      // Sort by oldest first and remove oldest 20%
      caches.sort((a, b) => a.updatedAt - b.updatedAt)
      const toRemove = Math.ceil(caches.length * 0.2)

      for (let i = 0; i < toRemove; i++) {
        localStorage.removeItem(caches[i].key)
      }
    } catch (e) {
      console.warn('Failed to cleanup old caches:', e)
    }
  }

  /**
   * Sync conversation list from server and update localStorage
   */
  function syncConversationsFromServer(serverConversations) {
    if (!Array.isArray(serverConversations)) return

    // Save to localStorage
    saveConversationsList(serverConversations)

    // Also save individual conversation metadata
    serverConversations.forEach(conv => {
      saveConversation(conv)
    })
  }

  /**
   * Sync messages from server and update localStorage
   */
  function syncMessagesFromServer(conversationId, serverMessages) {
    if (!conversationId || !Array.isArray(serverMessages)) return

    const existingMessages = loadConversationMessages(conversationId) || []

    // Merge server messages with local (server takes precedence)
    const messageMap = new Map()

    // Add existing local messages
    existingMessages.forEach(msg => {
      if (msg.id) {
        messageMap.set(msg.id, msg)
      }
    })

    // Override with server messages
    serverMessages.forEach(msg => {
      if (msg.id) {
        messageMap.set(msg.id, msg)
      }
    })

    // Convert back to array and sort by created_at
    const mergedMessages = Array.from(messageMap.values())
    mergedMessages.sort((a, b) => {
      const timeA = a.created_at ? new Date(a.created_at).getTime() : 0
      const timeB = b.created_at ? new Date(b.created_at).getTime() : 0
      return timeA - timeB
    })

    saveConversationMessages(conversationId, mergedMessages)
    return mergedMessages
  }

  /**
   * Append a message to a conversation's local storage
   */
  function appendMessage(conversationId, message) {
    if (!conversationId || !message) return

    const messages = loadConversationMessages(conversationId) || []
    messages.push(message)
    saveConversationMessages(conversationId, messages)
  }

  /**
   * Update a message in local storage
   */
  function updateMessage(conversationId, messageId, updates) {
    if (!conversationId || !messageId) return

    const messages = loadConversationMessages(conversationId) || []
    const index = messages.findIndex(m => m.id === messageId)

    if (index !== -1) {
      messages[index] = { ...messages[index], ...updates }
      saveConversationMessages(conversationId, messages)
    }
  }

  /**
   * Get storage statistics
   */
  function getStorageStats() {
    try {
      let totalConversations = 0
      let totalMessages = 0
      let oldestCache = Date.now()

      for (let i = 0; i < localStorage.length; i++) {
        const key = localStorage.key(i)
        if (key && key.startsWith(STORAGE_MESSAGES_PREFIX)) {
          const data = getItem(key)
          if (data) {
            totalConversations++
            if (data.messages) {
              totalMessages += data.messages.length
            }
            if (data.updatedAt && data.updatedAt < oldestCache) {
              oldestCache = data.updatedAt
            }
          }
        }
      }

      return {
        totalConversations,
        totalMessages,
        oldestCache: oldestCache === Date.now() ? null : new Date(oldestCache).toISOString()
      }
    } catch (e) {
      return { totalConversations: 0, totalMessages: 0, oldestCache: null }
    }
  }

  // Mark as ready
  isReady.value = true

  return {
    isReady,
    saveConversationsList,
    loadConversationsList,
    saveConversationMessages,
    loadConversationMessages,
    saveConversation,
    loadConversation,
    deleteConversation,
    clearAllConversationCaches,
    syncConversationsFromServer,
    syncMessagesFromServer,
    appendMessage,
    updateMessage,
    getStorageStats,
    cleanupOldCaches
  }
}
