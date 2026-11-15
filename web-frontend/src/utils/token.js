const TOKEN_KEY = 'jrt_token'
const ADMIN_KEY = 'jrt_admin'

export function getToken() {
  return localStorage.getItem(TOKEN_KEY) || ''
}

export function setToken(token) {
  localStorage.setItem(TOKEN_KEY, token)
}

export function getAdmin() {
  try {
    return JSON.parse(localStorage.getItem(ADMIN_KEY) || 'null')
  } catch (error) {
    return null
  }
}

export function setAdmin(admin) {
  localStorage.setItem(ADMIN_KEY, JSON.stringify(admin || null))
}

export function clearToken() {
  localStorage.removeItem(TOKEN_KEY)
  localStorage.removeItem(ADMIN_KEY)
}
