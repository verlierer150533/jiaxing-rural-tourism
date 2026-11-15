import request from './request'

export function fetchOverview() {
  return request.get('/stats/overview')
}

export function fetchLogs(params) {
  return request.get('/logs', { params })
}
