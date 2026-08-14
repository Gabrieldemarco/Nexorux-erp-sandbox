import { api } from './api'

export interface LoginRequest {
  email: string
  password: string
}

export interface LoginResponse {
  access_token: string
  refresh_token: string
  token_type: string
}

export interface RegisterRequest {
  email: string
  username: string
  full_name: string
  password: string
  tenant_id?: string
  company_id?: string
}

export interface UserResponse {
  id: string
  email: string
  username: string
  full_name: string
  tenant_id: string
  company_id: string
  is_active: boolean
  settings?: Record<string, any> | null
  permission_codes?: string[]
  role_keys?: string[]
  created_at: string
  updated_at: string
}

export interface UserProfileUpdateRequest {
  email?: string
  username?: string
  full_name?: string
  settings?: Record<string, any> | null
}

export interface ChangePasswordRequest {
  current_password: string
  new_password: string
}

export interface PasswordRecoveryRequest {
  email: string
}

export interface PasswordRecoveryResponse {
  message: string
  reset_token?: string
}

export interface PasswordResetRequest {
  token: string
  new_password: string
}

export const authApi = {
  login: async (data: LoginRequest): Promise<LoginResponse> => {
    const formData = new URLSearchParams()
    formData.append('username', data.email)
    formData.append('password', data.password)
    const response = await api.post('/auth/token', formData, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
    })
    return response.data
  },

  register: async (data: RegisterRequest): Promise<UserResponse> => {
    const response = await api.post('/auth/register', data)
    return response.data
  },

  refresh: async (refresh_token: string): Promise<LoginResponse> => {
    const response = await api.post('/auth/refresh', { refresh_token })
    return response.data
  },

  me: async (): Promise<UserResponse> => {
    const response = await api.get('/auth/me')
    return response.data
  },

  updateMe: async (data: UserProfileUpdateRequest): Promise<UserResponse> => {
    const response = await api.put('/auth/me', data)
    return response.data
  },

  changePassword: async (data: ChangePasswordRequest): Promise<{ message: string }> => {
    const response = await api.post('/auth/me/password', data)
    return response.data
  },

  requestPasswordReset: async (data: PasswordRecoveryRequest): Promise<PasswordRecoveryResponse> => {
    const response = await api.post('/auth/password/forgot', {
      email: data.email.trim(),
    })
    return response.data
  },

  resetPassword: async (data: PasswordResetRequest): Promise<{ message: string }> => {
    const response = await api.post('/auth/password/reset', data)
    return response.data
  },
}
