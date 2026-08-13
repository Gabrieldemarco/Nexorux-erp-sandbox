import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import FiscalDocuments from '../pages/FiscalDocuments'
import { AuthProvider } from '../hooks/useAuth'
import { authApi } from '../services/auth'
import { fiscalDocumentsApi } from '../services/fiscalDocuments'
import { invoicesApi } from '../services/invoices'
import { certificatesApi } from '../services/certificates'

vi.mock('../services/auth')
vi.mock('../services/fiscalDocuments')
vi.mock('../services/invoices')
vi.mock('../services/certificates')

const mockUser = {
  id: '1',
  email: 'test@example.com',
  username: 'test',
  full_name: 'Test User',
  tenant_id: 'tenant-1',
  company_id: 'company-1',
  is_active: true,
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:00:00Z',
}

const mockDoc = {
  id: 'doc-1',
  tenant_id: 'tenant-1',
  company_id: 'company-1',
  invoice_id: 'inv-1',
  document_type: '111',
  series: 'A',
  number: '0001',
  state: 'draft',
  is_contingency: false,
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:00:00Z',
}

const renderPage = () =>
  render(
    <MemoryRouter>
      <AuthProvider>
        <FiscalDocuments />
      </AuthProvider>
    </MemoryRouter>
  )

describe('FiscalDocuments CRUD', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    localStorage.setItem('access_token', 'test-token')
    vi.mocked(authApi.me).mockResolvedValue(mockUser)
    vi.mocked(fiscalDocumentsApi.list).mockResolvedValue([mockDoc])
    vi.mocked(fiscalDocumentsApi.create).mockResolvedValue(mockDoc)
    vi.mocked(fiscalDocumentsApi.delete).mockResolvedValue()
    vi.mocked(fiscalDocumentsApi.issue).mockResolvedValue({ ...mockDoc, state: 'pending_sign' })
    vi.mocked(invoicesApi.list).mockResolvedValue([
      {
        id: 'inv-1',
        tenant_id: 'tenant-1',
        company_id: 'company-1',
        customer_id: 'cust-1',
        branch_id: 'branch-1',
        warehouse_id: 'wh-1',
        document_type: '111',
        series: 'A',
        number: '0001',
        status: 'draft',
        issue_date: '2024-01-01T00:00:00',
        due_date: '2024-01-31T00:00:00',
        subtotal: 100,
        tax_total: 22,
        discount_total: 0,
        total: 122,
        currency: 'UYU',
        exchange_rate: 1,
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z',
      },
    ])
    vi.mocked(certificatesApi.list).mockResolvedValue([
      {
        id: 'cert-1',
        tenant_id: 'tenant-1',
        company_id: 'company-1',
        name: 'Cert Demo',
        thumbprint: 'ABC123',
        is_active: true,
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z',
      },
    ])
  })

  it('renders fiscal document list', async () => {
    renderPage()
    expect(await screen.findByText('e-Factura (111) A-0001')).toBeInTheDocument()
  })

  it('creates a fiscal document', async () => {
    const user = userEvent.setup()
    renderPage()
    await screen.findByText('e-Factura (111) A-0001')

    await user.click(screen.getByRole('button', { name: /agregar documento fiscal/i }))
    await user.click(screen.getByRole('button', { name: /guardar/i }))

    await waitFor(() => {
      expect(fiscalDocumentsApi.create).toHaveBeenCalledWith(
        expect.objectContaining({
          invoice_id: 'inv-1',
          document_type: '111',
          series: 'A',
          number: '0001',
          state: 'draft',
        })
      )
    })
  })

  it('deletes a fiscal document', async () => {
    const user = userEvent.setup()
    vi.spyOn(window, 'confirm').mockReturnValue(true)
    renderPage()
    await screen.findByText('e-Factura (111) A-0001')

    await user.click(screen.getByRole('button', { name: /^eliminar$/i }))

    await waitFor(() => {
      expect(fiscalDocumentsApi.delete).toHaveBeenCalledWith('doc-1')
    })
  })

  it('opens issue modal with certificates', async () => {
    const user = userEvent.setup()
    renderPage()
    await screen.findByText('e-Factura (111) A-0001')

    await user.click(screen.getByRole('button', { name: /^emitir$/i }))

    expect(await screen.findByRole('heading', { name: /emitir documento fiscal/i })).toBeInTheDocument()
    expect(screen.getByText('Cert Demo (ABC123)')).toBeInTheDocument()
  })
})
