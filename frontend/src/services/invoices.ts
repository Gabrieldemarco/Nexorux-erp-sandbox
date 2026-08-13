import { api } from './api'

export interface InvoiceResponse {
  id: string
  tenant_id: string
  company_id: string
  customer_id?: string
  branch_id?: string
  warehouse_id?: string
  document_type: string
  series: string
  number: string
  status: string
  issue_date: string
  due_date: string
  subtotal: number
  tax_total: number
  discount_total: number
  total: number
  currency: string
  exchange_rate: number
  notes?: string
  metadata?: Record<string, unknown> | null
  created_at: string
  updated_at: string
}

export interface InvoiceCreate {
  tenant_id: string
  company_id: string
  customer_id: string
  branch_id: string
  warehouse_id: string
  document_type: string
  series: string
  number: string
  status?: string
  issue_date: string
  due_date: string
  subtotal: number
  tax_total: number
  discount_total: number
  total: number
  currency: string
  exchange_rate?: number
  notes?: string
  metadata?: Record<string, unknown>
}

export interface InvoiceUpdate {
  document_type?: string
  series?: string
  number?: string
  status?: string
  issue_date?: string
  due_date?: string
  subtotal?: number
  tax_total?: number
  discount_total?: number
  total?: number
  currency?: string
  exchange_rate?: number
  notes?: string
  customer_id?: string
  branch_id?: string
  warehouse_id?: string
  metadata?: Record<string, unknown>
}

export const invoicesApi = {
  list: async (): Promise<InvoiceResponse[]> => {
    const response = await api.get('/invoices/')
    return response.data
  },

  get: async (id: string): Promise<InvoiceResponse> => {
    const response = await api.get(`/invoices/${id}`)
    return response.data
  },

  create: async (data: InvoiceCreate): Promise<InvoiceResponse> => {
    const response = await api.post('/invoices/', data)
    return response.data
  },

  update: async (id: string, data: InvoiceUpdate): Promise<InvoiceResponse> => {
    const response = await api.put(`/invoices/${id}`, data)
    return response.data
  },

  delete: async (id: string): Promise<void> => {
    await api.delete(`/invoices/${id}`)
  },
}
