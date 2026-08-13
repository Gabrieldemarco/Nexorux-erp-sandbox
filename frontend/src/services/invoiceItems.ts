import { api } from './api'

export interface InvoiceItemResponse {
  id: string
  tenant_id: string
  company_id: string
  invoice_id: string
  product_id?: string
  quantity: number
  unit_price: number
  discount: number
  tax_amount: number
  total: number
  description?: string
  created_at: string
  updated_at: string
}

export interface InvoiceItemCreate {
  tenant_id: string
  company_id: string
  invoice_id: string
  product_id?: string
  quantity: number
  unit_price: number
  discount?: number
  tax_amount: number
  total: number
  description?: string
}

export interface InvoiceItemUpdate {
  product_id?: string
  quantity?: number
  unit_price?: number
  discount?: number
  tax_amount?: number
  total?: number
  description?: string
}

export const invoiceItemsApi = {
  list: async (invoiceId?: string): Promise<InvoiceItemResponse[]> => {
    const response = await api.get('/invoice-items/', {
      params: invoiceId ? { invoice_id: invoiceId } : undefined,
    })
    return response.data
  },

  create: async (data: InvoiceItemCreate): Promise<InvoiceItemResponse> => {
    const response = await api.post('/invoice-items/', data)
    return response.data
  },

  update: async (id: string, data: InvoiceItemUpdate): Promise<InvoiceItemResponse> => {
    const response = await api.put(`/invoice-items/${id}`, data)
    return response.data
  },

  delete: async (id: string): Promise<void> => {
    await api.delete(`/invoice-items/${id}`)
  },
}
