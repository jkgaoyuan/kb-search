import request from '@/utils/request'

export const uploadDocument = (data) => {
  const formData = new FormData()
  formData.append('title', data.title)
  formData.append('category_id', data.category_id)
  formData.append('tags', data.tags)
  formData.append('file', data.file)

  return request.post('/documents', formData, {
    headers: { 'Content-Type': undefined }
  })
}

export const getDocuments = (params) => {
  return request.get('/documents', { params })
}

export const getDocument = (id) => {
  return request.get(`/documents/${id}`)
}

export const getDocumentStatus = (id) => {
  return request.get(`/documents/${id}/status`)
}

export const updateDocument = (id, data) => {
  return request.put(`/documents/${id}`, null, { params: data })
}

export const deleteDocument = (id) => {
  return request.delete(`/documents/${id}`)
}
