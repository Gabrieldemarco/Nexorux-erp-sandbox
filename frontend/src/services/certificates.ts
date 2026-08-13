import { api } from './api'

export interface CertificateResponse {
  id: string
  tenant_id: string
  company_id: string
  name: string
  thumbprint: string
  issued_at?: string
  expires_at?: string
  usage?: string
  is_active: boolean
  metadata?: { cert_path?: string; key_path?: string; [key: string]: unknown }
  created_at: string
  updated_at: string
}

export interface CertificateCreate {
  tenant_id: string
  company_id: string
  name: string
  thumbprint: string
  issued_at?: string
  expires_at?: string
  usage?: string
  is_active?: boolean
  metadata?: { cert_path?: string; key_path?: string; [key: string]: unknown }
}

export interface CertificateUpdate {
  name?: string
  thumbprint?: string
  issued_at?: string
  expires_at?: string
  usage?: string
  is_active?: boolean
  metadata?: { cert_path?: string; key_path?: string; [key: string]: unknown }
}

export const certificatesApi = {
  list: async (): Promise<CertificateResponse[]> => {
    const response = await api.get('/certificates/')
    return response.data
  },

  get: async (id: string): Promise<CertificateResponse> => {
    const response = await api.get(`/certificates/${id}`)
    return response.data
  },

  create: async (data: CertificateCreate): Promise<CertificateResponse> => {
    const response = await api.post('/certificates/', data)
    return response.data
  },

  update: async (id: string, data: CertificateUpdate): Promise<CertificateResponse> => {
    const response = await api.put(`/certificates/${id}`, data)
    return response.data
  },

  delete: async (id: string): Promise<void> => {
    await api.delete(`/certificates/${id}`)
  },
}
