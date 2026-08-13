import { api } from './api'

export interface RolePermission {
  id: string
  code: string
  name: string
}

export interface RoleResponse {
  id: string
  tenant_id: string
  name: string
  key: string
  description?: string | null
  is_default: boolean
  permissions?: RolePermission[]
  created_at: string
  updated_at: string
}

export interface RoleCreate {
  tenant_id: string
  name: string
  key: string
  description?: string
  is_default?: boolean
  permission_ids?: string[]
}

export interface RoleUpdate {
  name?: string
  key?: string
  description?: string
  is_default?: boolean
  permission_ids?: string[]
}

export const rolesApi = {
  list: async (): Promise<RoleResponse[]> => {
    const response = await api.get('/roles/')
    return response.data
  },

  get: async (id: string): Promise<RoleResponse> => {
    const response = await api.get(`/roles/${id}`)
    return response.data
  },

  create: async (data: RoleCreate): Promise<RoleResponse> => {
    const response = await api.post('/roles/', data)
    return response.data
  },

  update: async (id: string, data: RoleUpdate): Promise<RoleResponse> => {
    const response = await api.put(`/roles/${id}`, data)
    return response.data
  },

  setPermissions: async (id: string, permission_ids: string[]): Promise<RoleResponse> => {
    const response = await api.put(`/roles/${id}/permissions`, { permission_ids })
    return response.data
  },

  delete: async (id: string): Promise<void> => {
    await api.delete(`/roles/${id}`)
  },
}
