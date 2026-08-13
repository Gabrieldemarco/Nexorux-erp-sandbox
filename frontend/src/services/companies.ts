import { api } from './api'

export interface CompanyResponse {
  id: string
  tenant_id: string
  legal_name: string
  trade_name?: string
  rut: string
  fiscal_address?: string
  phone?: string
  email?: string
  website?: string
  country: string
  department?: string
  locality?: string
  currency: string
  tax_regime?: string
  created_at: string
  updated_at: string
}

export interface CompanyCreate {
  tenant_id: string
  legal_name: string
  trade_name?: string
  rut: string
  fiscal_address?: string
  phone?: string
  email?: string
  website?: string
  country?: string
  department?: string
  locality?: string
  currency?: string
  tax_regime?: string
}

export interface CompanyUpdate {
  legal_name?: string
  trade_name?: string
  rut?: string
  fiscal_address?: string
  phone?: string
  email?: string
  website?: string
  country?: string
  department?: string
  locality?: string
  currency?: string
  tax_regime?: string
}

export const companiesApi = {
  list: async (): Promise<CompanyResponse[]> => {
    const response = await api.get('/companies/')
    return response.data
  },

  get: async (id: string): Promise<CompanyResponse> => {
    const response = await api.get(`/companies/${id}`)
    return response.data
  },

  create: async (data: CompanyCreate): Promise<CompanyResponse> => {
    const response = await api.post('/companies/', data)
    return response.data
  },

  update: async (id: string, data: CompanyUpdate): Promise<CompanyResponse> => {
    const response = await api.put(`/companies/${id}`, data)
    return response.data
  },

  delete: async (id: string): Promise<void> => {
    await api.delete(`/companies/${id}`)
  },
}
