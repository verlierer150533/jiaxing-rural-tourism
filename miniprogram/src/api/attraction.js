import { get } from './request'

export function fetchAttractions(params) {
  return get('/attractions', params)
}

export function fetchAttraction(id) {
  return get(`/attractions/${id}`)
}

export function fetchMapMarkers() {
  return get('/attractions/map')
}

export function fetchMeta() {
  return get('/attractions/meta')
}
