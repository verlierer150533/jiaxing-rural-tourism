import { post } from '../api/request'
import { getSessionId } from './session'

const HISTORY_KEY = 'jrt_view_history'
const HISTORY_MAX = 10

/**
 * 上报浏览足迹。
 * 失败静默处理——埋点绝不能打断正常浏览。
 */
export function track(action, targetType, targetId, detail) {
  const payload = {
    action,
    target_type: targetType,
    target_id: targetId,
    source: 'miniprogram',
    session_id: getSessionId(),
    detail: detail || ''
  }
  post('/log', payload).catch(() => {})
}

/** 本地浏览历史（仅用于“我的”页展示，不参与统计） */
export function saveLocalHistory(item) {
  try {
    const list = uni.getStorageSync(HISTORY_KEY) || []
    const next = [
      { id: item.id, name: item.name, category: item.category, town: item.town, at: Date.now() },
      ...list.filter((row) => row.id !== item.id)
    ].slice(0, HISTORY_MAX)
    uni.setStorageSync(HISTORY_KEY, next)
  } catch (error) {
    /* 忽略本地存储异常 */
  }
}

export function getLocalHistory() {
  try {
    return uni.getStorageSync(HISTORY_KEY) || []
  } catch (error) {
    return []
  }
}

export function clearLocalHistory() {
  uni.removeStorageSync(HISTORY_KEY)
}
