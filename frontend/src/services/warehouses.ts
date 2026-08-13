import { api } from './api'

export interface WarehouseResponse {
  id: string
  tenant_id: string
  company_id: string
  branch_id?: string
  name: string
  code: string
  description?: string
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface WarehouseCreate {
  tenant_id: string
  company_id: string
  branch_id?: string
  name: string
  code: string
  description?: string
  is_active?: boolean
}

export interface WarehouseUpdate {
  branch_id?: string
  name?: string
  code?: string
  description?: string
  is_active?: boolean
}

export const warehousesApi = {
  list: async (): Promise<WarehouseResponse[]> => {
    const response = await api.get('/warehouses/')
    return response.data
  },

  get: async (id: string): Promise<WarehouseResponse> => {
    const response = await api.get(`/warehouses/${id}`)
    return response.data
  },

  create: async (data: WarehouseCreate): Promise<WarehouseResponse> => {
    const response = await api.post('/warehouses/', data)
    return response.data
  },

  update: async (id: string, data: WarehouseUpdate): Promise<WarehouseResponse> => {
    const response = await api.put(`/warehouses/${id}`, data)
    return response.data
  },

  delete: async (id: string): Promise<void> => {
    await api.delete(`/warehouses/${id}`)
  },
}
