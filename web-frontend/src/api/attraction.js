import request from './request'

export function fetchAttractions(params) {
  return request.get('/attractions', { params })
}

// 后台管理：返回全部状态（需登录）
export function fetchAdminAttractions(params) {
  return request.get('/attractions/admin', { params })
}

export function fetchAttraction(id) {
  return request.get(`/attractions/${id}`)
}

export function fetchMapMarkers() {
  return request.get('/attractions/map')
}

export function fetchMeta() {
  return request.get('/attractions/meta')
}

export function createAttraction(data) {
  return request.post('/attractions', data)
}

export function updateAttraction(id, data) {
  return request.put(`/attractions/${id}`, data)
}

export function deleteAttraction(id) {
  return request.delete(`/attractions/${id}`)
}

export function toggleAttractionStatus(id, status) {
  return request.patch(`/attractions/${id}/status`, { status })
}
