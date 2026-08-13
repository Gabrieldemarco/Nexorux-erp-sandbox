import { api } from './api'

export interface BranchResponse {
  id: string
  tenant_id: string
  company_id: string
  name: string
  code: string
  address?: string
  phone?: string
  email?: string
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface BranchCreate {
  tenant_id: string
  company_id: string
  name: string
  code: string
  address?: string
  phone?: string
  email?: string
  is_active?: boolean
}

export interface BranchUpdate {
  name?: string
  code?: string
  address?: string
  phone?: string
  email?: string
  is_active?: boolean
}

export const branchesApi = {
  list: async (): Promise<BranchResponse[]> => {
    const response = await api.get('/branches/')
    return response.data
  },

  get: async (id: string): Promise<BranchResponse> => {
    const response = await api.get(`/branches/${id}`)
    return response.data
  },

  create: async (data: BranchCreate): Promise<BranchResponse> => {
    const response = await api.post('/branches/', data)
    return response.data
  },

  update: async (id: string, data: BranchUpdate): Promise<BranchResponse> => {
    const response = await api.put(`/branches/${id}`, data)
    return response.data
  },

  delete: async (id: string): Promise<void> => {
    await api.delete(`/branches/${id}`)
  },
}
