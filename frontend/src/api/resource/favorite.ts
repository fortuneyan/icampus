import request from '@/utils/request'

export function getFavorites(params?: any) {
  return request.get('/resource/favorites', { params })
}

export function addFavorite(data: any) {
  return request.post('/resource/favorites', data)
}

export function removeFavorite(resourceId: string) {
  return request.delete(`/resource/favorites/${resourceId}`)
}

export function checkFavorite(resourceId: string) {
  return request.get(`/resource/favorites/check/${resourceId}`)
}