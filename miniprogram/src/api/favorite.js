import { get, post } from './request'

/** 收藏 / 取消收藏（同一接口切换） */
export function toggleFavorite(sessionId, targetId) {
  return post('/favorite', { session_id: sessionId, target_id: targetId })
}

/** 当前会话的收藏列表 */
export function fetchFavorites(sessionId) {
  return get('/favorite', { session_id: sessionId })
}

/** 查询某个点位是否已收藏（爱心按钮初始状态） */
export function checkFavorite(sessionId, targetId) {
  return get('/favorite/check', { session_id: sessionId, target_id: targetId })
}
