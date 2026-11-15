const SESSION_KEY = 'jrt_session_id'

/**
 * 设备级会话标识（UV 统计依据）。
 * 首次进入生成，之后持久化在本地存储。
 */
export function getSessionId() {
  let sessionId = uni.getStorageSync(SESSION_KEY)
  if (!sessionId) {
    sessionId = `mp-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 10)}`
    uni.setStorageSync(SESSION_KEY, sessionId)
  }
  return sessionId
}

export function resetSessionId() {
  uni.removeStorageSync(SESSION_KEY)
  return getSessionId()
}
