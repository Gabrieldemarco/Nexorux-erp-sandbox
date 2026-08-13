import { api } from './api'

export interface PaymentResponse {
  id: string
  tenant_id: string
  company_id: string
  invoice_id?: string | null
  customer_id?: string | null
  payment_date: string
  amount: number
  currency: string
  payment_method: string
  reference?: string
  status?: string
  created_at: string
  updated_at: string
}

export interface PaymentCreate {
  tenant_id: string
  company_id: string
  invoice_id?: string
  customer_id?: string
  payment_date: string
  amount: number
  currency: string
  payment_method: string
  reference?: string
  status?: string
}

export interface PaymentUpdate {
  payment_date?: string
  amount?: number
  currency?: string
  payment_method?: string
  reference?: string
  status?: string
  invoice_id?: string
  customer_id?: string
}

export const paymentsApi = {
  list: async (): Promise<PaymentResponse[]> => {
    const response = await api.get('/payments/')
    return response.data
  },

  get: async (id: string): Promise<PaymentResponse> => {
    const response = await api.get(`/payments/${id}`)
    return response.data
  },

  create: async (data: PaymentCreate): Promise<PaymentResponse> => {
    const response = await api.post('/payments/', data)
    return response.data
  },

  update: async (id: string, data: PaymentUpdate): Promise<PaymentResponse> => {
    const response = await api.put(`/payments/${id}`, data)
    return response.data
  },

  delete: async (id: string): Promise<void> => {
    await api.delete(`/payments/${id}`)
  },
}
