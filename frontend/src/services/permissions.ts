import { api } from './api'

export interface PermissionResponse {
  id: string
  tenant_id: string
  name: string
  code: string
  description?: string | null
  created_at: string
  updated_at: string
}

export const permissionsApi = {
  list: async (): Promise<PermissionResponse[]> => {
    const response = await api.get('/permissions/')
    return response.data
  },
}
