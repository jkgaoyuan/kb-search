import request from '@/utils/request'

export const searchDocuments = (params) => {
  return request.get('/search', { params })
}

export const getSearchSuggestions = (q) => {
  return request.get('/search/suggest', { params: { q } })
}

export const getHotSearches = (params) => {
  return request.get('/search/hot', { params })
}
