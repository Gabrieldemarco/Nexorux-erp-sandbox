import { api } from './api'

export interface TenantResponse {
  id: string
  name: string
  status: string
  settings: Record<string, unknown>
  created_at: string
  updated_at: string
}

export interface TenantCreate {
  name: string
  status?: string
  settings?: Record<string, unknown>
}

export interface TenantUpdate {
  name?: string
  status?: string
  settings?: Record<string, unknown>
}

export const tenantsApi = {
  list: async (): Promise<TenantResponse[]> => {
    const response = await api.get('/tenants/')
    return response.data
  },

  get: async (id: string): Promise<TenantResponse> => {
    const response = await api.get(`/tenants/${id}`)
    return response.data
  },

  create: async (data: TenantCreate): Promise<TenantResponse> => {
    const response = await api.post('/tenants/', data)
    return response.data
  },

  update: async (id: string, data: TenantUpdate): Promise<TenantResponse> => {
    const response = await api.put(`/tenants/${id}`, data)
    return response.data
  },

  delete: async (id: string): Promise<void> => {
    await api.delete(`/tenants/${id}`)
  },
}
