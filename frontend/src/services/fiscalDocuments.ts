import { api } from './api'

export interface FiscalDocumentResponse {
  id: string
  tenant_id: string
  company_id: string
  invoice_id: string
  document_type: string
  series: string
  number: string
  state: string
  issued_at?: string
  signed_at?: string
  sent_at?: string
  response_at?: string
  is_contingency: boolean
  xml_reference?: string
  raw_payload?: Record<string, any>
  created_at: string
  updated_at: string
}

export interface FiscalDocumentCreate {
  tenant_id: string
  company_id: string
  invoice_id: string
  document_type: string
  series: string
  number: string
  state?: string
  is_contingency?: boolean
  xml_reference?: string
  raw_payload?: Record<string, any>
}

export interface FiscalDocumentUpdate {
  invoice_id?: string
  document_type?: string
  series?: string
  number?: string
  state?: string
  is_contingency?: boolean
  xml_reference?: string
}

export interface FiscalDocumentIssueRequest {
  certificate_id: string
}

export interface FiscalDocumentSendRequest {
  environment?: string
  certificate_id?: string
}

export interface FiscalDocumentRetryRequest {
  certificate_id?: string
}

export const fiscalDocumentsApi = {
  list: async (): Promise<FiscalDocumentResponse[]> => {
    const response = await api.get('/fiscal-documents/')
    return response.data
  },

  get: async (id: string): Promise<FiscalDocumentResponse> => {
    const response = await api.get(`/fiscal-documents/${id}`)
    return response.data
  },

  create: async (data: FiscalDocumentCreate): Promise<FiscalDocumentResponse> => {
    const response = await api.post('/fiscal-documents/', data)
    return response.data
  },

  update: async (id: string, data: FiscalDocumentUpdate): Promise<FiscalDocumentResponse> => {
    const response = await api.put(`/fiscal-documents/${id}`, data)
    return response.data
  },

  issue: async (id: string, data: FiscalDocumentIssueRequest): Promise<FiscalDocumentResponse> => {
    const response = await api.post(`/fiscal-documents/${id}/issue`, data)
    return response.data
  },

  send: async (id: string, data: FiscalDocumentSendRequest): Promise<Record<string, any>> => {
    const response = await api.post(`/fiscal-documents/${id}/send`, data)
    return response.data
  },

  queryStatus: async (id: string, environment?: string): Promise<Record<string, any>> => {
    const response = await api.get(`/fiscal-documents/${id}/query-status`, { params: { environment } })
    return response.data
  },

  retry: async (id: string, data: FiscalDocumentRetryRequest): Promise<FiscalDocumentResponse> => {
    const response = await api.post(`/fiscal-documents/${id}/retry`, data)
    return response.data
  },

  delete: async (id: string): Promise<void> => {
    await api.delete(`/fiscal-documents/${id}`)
  },
}
