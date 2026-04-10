import { ref, reactive, computed } from 'vue'

/**
 * Global streaming state manager
 * Maintains streaming state across conversation switches
 * Allows background streaming while viewing other conversations
 */

// Global state (singleton)
const globalState = reactive({
  // Map of conversationId -> streaming state
  activeStreams: new Map(),
  // Currently visible conversation
  visibleConversationId: null,
  // Global streaming lock to prevent multiple simultaneous streams per conversation
  streamingLocks: new Set()
})

/**
 * Composable for managing global streaming state
 * This allows streaming to continue in the background when switching conversations
 */
export function useGlobalStreaming() {
  /**
   * Check if a conversation has an active stream
   */
  function hasActiveStream(conversationId) {
    if (!conversationId) return false
    const state = globalState.activeStreams.get(conversationId)
    return state?.isStreaming ?? false
  }

  /**
   * Get streaming state for a conversation
   */
  function getStreamState(conversationId) {
    if (!conversationId) return null
    return globalState.activeStreams.get(conversationId) || null
  }

  /**
   * Start a new stream for a conversation
   */
  function startStream(conversationId, initialData = {}) {
    if (!conversationId) return false

    // Prevent duplicate streams for the same conversation
    if (globalState.streamingLocks.has(conversationId)) {
      console.warn(`Stream already active for conversation ${conversationId}`)
      return false
    }

    globalState.streamingLocks.add(conversationId)

    const streamState = {
      conversationId,
      isStreaming: true,
      isAborted: false,
      content: '',
      thinking: '',
      thinkingDuration: 0,
      sources: [],
      status: 'Starting...',
      error: null,
      messageId: null,
      userMessageId: null,
      startedAt: Date.now(),
      lastUpdateAt: Date.now(),
      // Callbacks for the active component
      onContent: null,
      onThinking: null,
      onThinkingStart: null,
      onThinkingEnd: null,
      onSources: null,
      onStatus: null,
      onDone: null,
      onError: null,
      // Abort controller
      abortController: null,
      ...initialData
    }

    globalState.activeStreams.set(conversationId, streamState)
    return true
  }

  /**
   * Update stream content
   */
  function updateStreamContent(conversationId, content) {
    const state = globalState.activeStreams.get(conversationId)
    if (state && state.isStreaming) {
      state.content = content
      state.lastUpdateAt = Date.now()

      // Call registered callback if exists
      if (typeof state.onContent === 'function') {
        try {
          state.onContent(content)
        } catch (e) {
          console.error('Error in onContent callback:', e)
        }
      }
    }
  }

  /**
   * Update stream thinking content
   */
  function updateStreamThinking(conversationId, thinking) {
    const state = globalState.activeStreams.get(conversationId)
    if (state && state.isStreaming) {
      state.thinking = thinking
      state.lastUpdateAt = Date.now()

      if (typeof state.onThinking === 'function') {
        try {
          state.onThinking(thinking)
        } catch (e) {
          console.error('Error in onThinking callback:', e)
        }
      }
    }
  }

  /**
   * Update stream status
   */
  function updateStreamStatus(conversationId, status) {
    const state = globalState.activeStreams.get(conversationId)
    if (state && state.isStreaming) {
      state.status = status
      state.lastUpdateAt = Date.now()

      if (typeof state.onStatus === 'function') {
        try {
          state.onStatus(status)
        } catch (e) {
          console.error('Error in onStatus callback:', e)
        }
      }
    }
  }

  /**
   * Update stream sources
   */
  function updateStreamSources(conversationId, sources) {
    const state = globalState.activeStreams.get(conversationId)
    if (state && state.isStreaming) {
      state.sources = sources
      state.lastUpdateAt = Date.now()

      if (typeof state.onSources === 'function') {
        try {
          state.onSources(sources)
        } catch (e) {
          console.error('Error in onSources callback:', e)
        }
      }
    }
  }

  /**
   * Mark stream as thinking started
   */
  function markThinkingStarted(conversationId) {
    const state = globalState.activeStreams.get(conversationId)
    if (state && state.isStreaming) {
      state.isThinking = true
      state.thinkingStartedAt = Date.now()

      if (typeof state.onThinkingStart === 'function') {
        try {
          state.onThinkingStart()
        } catch (e) {
          console.error('Error in onThinkingStart callback:', e)
        }
      }
    }
  }

  /**
   * Mark stream as thinking ended
   */
  function markThinkingEnded(conversationId, duration) {
    const state = globalState.activeStreams.get(conversationId)
    if (state && state.isStreaming) {
      state.isThinking = false
      state.thinkingDuration = duration

      if (typeof state.onThinkingEnd === 'function') {
        try {
          state.onThinkingEnd(duration)
        } catch (e) {
          console.error('Error in onThinkingEnd callback:', e)
        }
      }
    }
  }

  /**
   * Complete a stream
   */
  function completeStream(conversationId, result = {}) {
    const state = globalState.activeStreams.get(conversationId)
    if (state) {
      state.isStreaming = false
      state.messageId = result.messageId || state.messageId
      state.userMessageId = result.userMessageId || state.userMessageId
      state.completedAt = Date.now()

      // Call onDone callback
      if (typeof state.onDone === 'function') {
        try {
          state.onDone({
            content: state.content,
            thinking: state.thinking,
            thinkingDuration: state.thinkingDuration,
            sources: state.sources,
            messageId: state.messageId,
            userMessageId: state.userMessageId,
            ...result
          })
        } catch (e) {
          console.error('Error in onDone callback:', e)
        }
      }

      // Clean up after a delay to allow component to read final state
      setTimeout(() => {
        globalState.activeStreams.delete(conversationId)
        globalState.streamingLocks.delete(conversationId)
      }, 5000)
    }
  }

  /**
   * Mark stream as errored
   */
  function errorStream(conversationId, error) {
    const state = globalState.activeStreams.get(conversationId)
    if (state) {
      state.isStreaming = false
      state.error = error

      if (typeof state.onError === 'function') {
        try {
          state.onError(error)
        } catch (e) {
          console.error('Error in onError callback:', e)
        }
      }

      // Clean up
      setTimeout(() => {
        globalState.activeStreams.delete(conversationId)
        globalState.streamingLocks.delete(conversationId)
      }, 5000)
    }
  }

  /**
   * Abort a stream
   */
  function abortStream(conversationId) {
    const state = globalState.activeStreams.get(conversationId)
    if (state && state.abortController) {
      try {
        state.abortController.abort()
        state.isAborted = true
      } catch (e) {
        console.error('Error aborting stream:', e)
      }
    }
    globalState.streamingLocks.delete(conversationId)
  }

  /**
   * Register callbacks for a stream
   * Used when a component becomes visible and wants to receive updates
   */
  function registerCallbacks(conversationId, callbacks) {
    const state = globalState.activeStreams.get(conversationId)
    if (state) {
      Object.assign(state, callbacks)

      // Immediately call with current state if streaming
      if (state.isStreaming) {
        if (callbacks.onContent && state.content) {
          callbacks.onContent(state.content)
        }
        if (callbacks.onThinking && state.thinking) {
          callbacks.onThinking(state.thinking)
        }
        if (callbacks.onSources && state.sources.length) {
          callbacks.onSources(state.sources)
        }
      }
    }
  }

  /**
   * Unregister callbacks for a stream
   * Used when a component is hidden (switching conversations)
   */
  function unregisterCallbacks(conversationId) {
    const state = globalState.activeStreams.get(conversationId)
    if (state) {
      state.onContent = null
      state.onThinking = null
      state.onThinkingStart = null
      state.onThinkingEnd = null
      state.onSources = null
      state.onStatus = null
      state.onDone = null
      state.onError = null
    }
  }

  /**
   * Set the currently visible conversation
   */
  function setVisibleConversation(conversationId) {
    const previousId = globalState.visibleConversationId

    // Unregister callbacks from previous conversation
    if (previousId && previousId !== conversationId) {
      unregisterCallbacks(previousId)
    }

    globalState.visibleConversationId = conversationId

    // Register callbacks for new conversation if it has an active stream
    if (conversationId && hasActiveStream(conversationId)) {
      return getStreamState(conversationId)
    }

    return null
  }

  /**
   * Get the currently visible conversation
   */
  function getVisibleConversation() {
    return globalState.visibleConversationId
  }

  /**
   * Set abort controller for a stream
   */
  function setAbortController(conversationId, controller) {
    const state = globalState.activeStreams.get(conversationId)
    if (state) {
      state.abortController = controller
    }
  }

  /**
   * Get all active streams (for debugging)
   */
  function getActiveStreams() {
    return Array.from(globalState.activeStreams.entries()).map(([id, state]) => ({
      conversationId: id,
      isStreaming: state.isStreaming,
      duration: state.startedAt ? Date.now() - state.startedAt : 0
    }))
  }

  return {
    // State checks
    hasActiveStream,
    getStreamState,
    getVisibleConversation,
    getActiveStreams,

    // Stream lifecycle
    startStream,
    completeStream,
    errorStream,
    abortStream,

    // Stream updates
    updateStreamContent,
    updateStreamThinking,
    updateStreamStatus,
    updateStreamSources,
    markThinkingStarted,
    markThinkingEnded,

    // Callback management
    registerCallbacks,
    unregisterCallbacks,
    setVisibleConversation,
    setAbortController
  }
}
