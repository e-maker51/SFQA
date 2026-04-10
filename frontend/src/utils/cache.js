/**
 * Frontend Cache Manager
 * localStorage-based caching with TTL support
 */

const CACHE_PREFIX = 'sfqa_cache:'

/**
 * Get cached data by key. Returns null if expired or missing.
 * @param {string} key
 * @returns {any|null}
 */
export function getCache(key) {
  try {
    const raw = localStorage.getItem(CACHE_PREFIX + key)
    if (!raw) return null

    const entry = JSON.parse(raw)
    if (entry.expiresAt && Date.now() > entry.expiresAt) {
      localStorage.removeItem(CACHE_PREFIX + key)
      return null
    }
    return entry.data
  } catch {
    localStorage.removeItem(CACHE_PREFIX + key)
    return null
  }
}

/**
 * Set cache data with optional TTL.
 * @param {string} key
 * @param {any} data
 * @param {number} ttlMs - Time to live in milliseconds. 0 = no expiry.
 */
export function setCache(key, data, ttlMs = 0) {
  try {
    const entry = {
      data,
      createdAt: Date.now(),
      expiresAt: ttlMs > 0 ? Date.now() + ttlMs : null
    }
    localStorage.setItem(CACHE_PREFIX + key, JSON.stringify(entry))
  } catch (e) {
    // localStorage may be full, silently fail
    console.warn('Cache set failed:', e)
  }
}

/**
 * Invalidate (remove) a specific cache key.
 * @param {string} key
 */
export function invalidateCache(key) {
  localStorage.removeItem(CACHE_PREFIX + key)
}

/**
 * Invalidate all cache entries whose key starts with the given prefix.
 * @param {string} prefix
 */
export function invalidateCachePrefix(prefix) {
  const fullPrefix = CACHE_PREFIX + prefix
  const keysToRemove = []
  for (let i = 0; i < localStorage.length; i++) {
    const k = localStorage.key(i)
    if (k && k.startsWith(fullPrefix)) {
      keysToRemove.push(k)
    }
  }
  keysToRemove.forEach(k => localStorage.removeItem(k))
}

/**
 * Get cached data or fetch from async function if cache miss / expired.
 * @param {string} key
 * @param {Function} fetchFn - Async function that returns the data
 * @param {number} ttlMs - TTL in milliseconds
 * @returns {Promise<any>}
 */
export async function getOrFetch(key, fetchFn, ttlMs = 0) {
  const cached = getCache(key)
  if (cached !== null) {
    return cached
  }
  const data = await fetchFn()
  setCache(key, data, ttlMs)
  return data
}

/**
 * Clear all SFQA cache entries.
 */
export function clearAllCache() {
  const keysToRemove = []
  for (let i = 0; i < localStorage.length; i++) {
    const k = localStorage.key(i)
    if (k && k.startsWith(CACHE_PREFIX)) {
      keysToRemove.push(k)
    }
  }
  keysToRemove.forEach(k => localStorage.removeItem(k))
}

// Cache TTL constants (milliseconds)
export const CACHE_TTL = {
  MODELS: 10 * 60 * 1000,       // 10 minutes - models don't change often
  CONVERSATIONS: 60 * 1000,     // 1 minute - conversation list changes moderately
  MESSAGES: 10 * 60 * 1000      // 10 minutes - messages are immutable once sent
}
