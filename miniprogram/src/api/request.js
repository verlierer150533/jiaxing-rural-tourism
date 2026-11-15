import { BASE_URL } from '../config'

function buildQuery(params) {
  if (!params) return ''
  const pairs = []
  Object.keys(params).forEach((key) => {
    const value = params[key]
    if (value === undefined || value === null || value === '') return
    pairs.push(`${encodeURIComponent(key)}=${encodeURIComponent(value)}`)
  })
  return pairs.length ? `?${pairs.join('&')}` : ''
}

/**
 * 统一请求封装：拆解后端 {code, message, data} 响应体。
 */
export function request(options) {
  const { url, method = 'GET', data, params, header = {} } = options
  const fullUrl = BASE_URL + url + buildQuery(params)

  return new Promise((resolve, reject) => {
    uni.request({
      url: fullUrl,
      method,
      data,
      timeout: 15000,
      header: { 'Content-Type': 'application/json', ...header },
      success(res) {
        const body = res.data
        if (res.statusCode >= 200 && res.statusCode < 300 && body && body.code === 0) {
          resolve(body.data)
          return
        }
        reject(new Error((body && body.message) || `请求失败（${res.statusCode}）`))
      },
      fail(err) {
        reject(new Error(err.errMsg || '网络异常'))
      }
    })
  })
}

export function get(url, params) {
  return request({ url, params })
}

export function post(url, data) {
  return request({ url, method: 'POST', data })
}
