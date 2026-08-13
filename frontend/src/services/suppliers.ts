import { api } from './api'

export interface SupplierResponse {
  id: string
  tenant_id: string
  company_id: string
  legal_name: string
  trade_name?: string
  rut: string
  document_type?: string
  address?: string
  email?: string
  phone?: string
  currency: string
  payment_terms?: string
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface SupplierCreate {
  tenant_id: string
  company_id: string
  legal_name: string
  trade_name?: string
  rut: string
  document_type?: string
  address?: string
  email?: string
  phone?: string
  currency?: string
  payment_terms?: string
  is_active?: boolean
}

export interface SupplierUpdate {
  legal_name?: string
  trade_name?: string
  rut?: string
  document_type?: string
  address?: string
  email?: string
  phone?: string
  currency?: string
  payment_terms?: string
  is_active?: boolean
}

export const suppliersApi = {
  list: async (): Promise<SupplierResponse[]> => {
    const response = await api.get('/suppliers/')
    return response.data
  },

  get: async (id: string): Promise<SupplierResponse> => {
    const response = await api.get(`/suppliers/${id}`)
    return response.data
  },

  create: async (data: SupplierCreate): Promise<SupplierResponse> => {
    const response = await api.post('/suppliers/', data)
    return response.data
  },

  update: async (id: string, data: SupplierUpdate): Promise<SupplierResponse> => {
    const response = await api.put(`/suppliers/${id}`, data)
    return response.data
  },

  delete: async (id: string): Promise<void> => {
    await api.delete(`/suppliers/${id}`)
  },
}
