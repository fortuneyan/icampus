import request from '@/utils/request'

export function getRecommendations(params?: any) {
  return request.get('/resource/recommendations', { params })
}

export function getPopularResources(params?: any) {
  return request.get('/resource/recommendations/popular', { params })
}

export function markRecommendationClicked(id: string) {
  return request.put(`/resource/recommendations/${id}/click`)
}