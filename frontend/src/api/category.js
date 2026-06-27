import request from '@/utils/request'

export const getCategories = (params) => {
  return request.get('/categories', { params })
}

export const getBreadcrumb = (id) => {
  return request.get(`/categories/${id}/breadcrumb`)
}

export const createCategory = (data) => {
  return request.post('/categories', null, { params: data })
}
