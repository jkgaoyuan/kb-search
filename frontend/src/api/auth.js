import request from '@/utils/request'

export const register = (data) => {
  const formData = new URLSearchParams()
  formData.append('username', data.username)
  formData.append('password', data.password)

  return request.post('/auth/register', formData, {
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
  })
}

export const login = (data) => {
  const formData = new URLSearchParams()
  formData.append('username', data.username)
  formData.append('password', data.password)

  return request.post('/auth/login', formData, {
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
  })
}

export const refreshToken = () => {
  return request.post('/auth/refresh')
}
