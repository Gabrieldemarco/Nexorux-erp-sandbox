import { api } from './api'

export interface CustomerResponse {
  id: string
  tenant_id: string
  company_id: string
  customer_type: string
  legal_name: string
  trade_name?: string
  rut: string
  document_type?: string
  address?: string
  email?: string
  phone?: string
  currency: string
  credit_limit: number
  payment_terms?: string
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface CustomerCreate {
  tenant_id: string
  company_id: string
  customer_type: string
  legal_name: string
  trade_name?: string
  rut: string
  document_type?: string
  address?: string
  email?: string
  phone?: string
  currency?: string
  credit_limit?: number
  payment_terms?: string
  is_active?: boolean
}

export interface CustomerUpdate {
  customer_type?: string
  legal_name?: string
  trade_name?: string
  rut?: string
  document_type?: string
  address?: string
  email?: string
  phone?: string
  currency?: string
  credit_limit?: number
  payment_terms?: string
  is_active?: boolean
}

export const customersApi = {
  list: async (): Promise<CustomerResponse[]> => {
    const response = await api.get('/customers/')
    return response.data
  },

  get: async (id: string): Promise<CustomerResponse> => {
    const response = await api.get(`/customers/${id}`)
    return response.data
  },

  create: async (data: CustomerCreate): Promise<CustomerResponse> => {
    const response = await api.post('/customers/', data)
    return response.data
  },

  update: async (id: string, data: CustomerUpdate): Promise<CustomerResponse> => {
    const response = await api.put(`/customers/${id}`, data)
    return response.data
  },

  delete: async (id: string): Promise<void> => {
    await api.delete(`/customers/${id}`)
  },
}
