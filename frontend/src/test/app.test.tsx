import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { BrowserRouter } from 'react-router-dom'
import { AuthProvider } from '../hooks/useAuth'
import Login from '../pages/Login'
import Dashboard from '../pages/Dashboard'
import { authApi } from '../services/auth'

vi.mock('../services/auth')

const renderWithProviders = (ui: React.ReactElement) => {
  return render(
    <BrowserRouter>
      <AuthProvider>{ui}</AuthProvider>
    </BrowserRouter>
  )
}

describe('Login', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    localStorage.clear()
  })

  it('renders login form', () => {
    renderWithProviders(<Login />)
    expect(screen.getByRole('heading', { name: 'Ingresar' })).toBeInTheDocument()
    expect(screen.getByAltText('Nexorux ERP')).toBeInTheDocument()
    expect(screen.getByPlaceholderText('Correo electrónico')).toBeInTheDocument()
    expect(screen.getByPlaceholderText('Contraseña')).toBeInTheDocument()
  })

  it('calls login API on submit', async () => {
    const user = userEvent.setup()
    const mockLogin = vi.mocked(authApi.login).mockResolvedValue({
      access_token: 'test-token',
      refresh_token: 'test-refresh',
      token_type: 'bearer',
    })
    vi.mocked(authApi.me).mockResolvedValue({
      id: '1',
      email: 'test@example.com',
      username: 'test',
      full_name: 'Test User',
      tenant_id: 'tenant-1',
      company_id: 'company-1',
      is_active: true,
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
    })

    renderWithProviders(<Login />)
    await user.type(screen.getByPlaceholderText('Correo electrónico'), 'test@example.com')
    await user.type(screen.getByPlaceholderText('Contraseña'), 'password')
    await user.click(screen.getByRole('button', { name: /ingresar/i }))

    await waitFor(() => {
      expect(mockLogin).toHaveBeenCalledWith({
        email: 'test@example.com',
        password: 'password',
      })
    })
  })
})

describe('Dashboard', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    localStorage.setItem('access_token', 'test-token')
  })

  it('shows loading state initially', () => {
    renderWithProviders(<Dashboard />)
    expect(screen.getByText('Cargando panel...')).toBeInTheDocument()
  })

  it('displays stats after loading including fiscal documents', async () => {
    vi.mocked(authApi.me).mockResolvedValue({
      id: '1',
      email: 'test@example.com',
      username: 'test',
      full_name: 'Test User',
      tenant_id: 'tenant-1',
      company_id: 'company-1',
      is_active: true,
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
    })

    const mockTenantsApi = await import('../services/tenants')
    vi.spyOn(mockTenantsApi.tenantsApi, 'list').mockResolvedValue([{ id: '1', name: 'Test', status: 'active', settings: {}, created_at: '2024-01-01T00:00:00Z', updated_at: '2024-01-01T00:00:00Z' }])

    const mockCompaniesApi = await import('../services/companies')
    vi.spyOn(mockCompaniesApi.companiesApi, 'list').mockResolvedValue([{ id: '1', legal_name: 'Test', tenant_id: 'tenant-1', rut: '123', country: 'UY', currency: 'UYU', created_at: '2024-01-01T00:00:00Z', updated_at: '2024-01-01T00:00:00Z' }])

    const mockProductsApi = await import('../services/products')
    vi.spyOn(mockProductsApi.productsApi, 'list').mockResolvedValue([{ id: '1', name: 'Test', tenant_id: 'tenant-1', company_id: 'company-1', sku: 'SKU', product_type: 'good', unit_of_measure: 'unit', sales_price: 100, cost_price: 50, tax_rate: 22, is_service: false, is_active: true, created_at: '2024-01-01T00:00:00Z', updated_at: '2024-01-01T00:00:00Z' }])

    const mockCustomersApi = await import('../services/customers')
    vi.spyOn(mockCustomersApi.customersApi, 'list').mockResolvedValue([{ id: '1', legal_name: 'Test', tenant_id: 'tenant-1', company_id: 'company-1', customer_type: 'company', rut: '123', currency: 'UYU', credit_limit: 1000, is_active: true, created_at: '2024-01-01T00:00:00Z', updated_at: '2024-01-01T00:00:00Z' }])

    const mockInvoicesApi = await import('../services/invoices')
    vi.spyOn(mockInvoicesApi.invoicesApi, 'list').mockResolvedValue([{ id: '1', number: '1', tenant_id: 'tenant-1', company_id: 'company-1', document_type: '111', series: 'A', status: 'draft', issue_date: '2024-01-01', due_date: '2024-01-31', subtotal: 100, tax_total: 22, discount_total: 0, total: 122, currency: 'UYU', exchange_rate: 1, created_at: '2024-01-01T00:00:00Z', updated_at: '2024-01-01T00:00:00Z' }])

    const mockFiscalApi = await import('../services/fiscalDocuments')
    vi.spyOn(mockFiscalApi.fiscalDocumentsApi, 'list').mockResolvedValue([
      {
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
      },
      {
        id: 'doc-2',
        tenant_id: 'tenant-1',
        company_id: 'company-1',
        invoice_id: 'inv-2',
        document_type: '101',
        series: 'B',
        number: '0002',
        state: 'accepted',
        is_contingency: false,
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z',
      },
    ])

    const mockPaymentsApi = await import('../services/payments')
    vi.spyOn(mockPaymentsApi.paymentsApi, 'list').mockResolvedValue([])

    renderWithProviders(<Dashboard />)

    await waitFor(() => {
      expect(screen.getByText('Total empresas')).toBeInTheDocument()
    })
    expect(screen.getAllByText('Documentos fiscales').length).toBeGreaterThan(0)
    expect(screen.getByText('2')).toBeInTheDocument()
    const ones = screen.getAllByText('1')
    expect(ones.length).toBeGreaterThan(0)
  })

  it('survives partial API failures and shows warning', async () => {
    vi.mocked(authApi.me).mockResolvedValue({
      id: '1',
      email: 'test@example.com',
      username: 'test',
      full_name: 'Test User',
      tenant_id: 'tenant-1',
      company_id: 'company-1',
      is_active: true,
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
    })

    const mockTenantsApi = await import('../services/tenants')
    vi.spyOn(mockTenantsApi.tenantsApi, 'list').mockResolvedValue([])

    const mockCompaniesApi = await import('../services/companies')
    vi.spyOn(mockCompaniesApi.companiesApi, 'list').mockResolvedValue([
      {
        id: '1',
        legal_name: 'Test',
        tenant_id: 'tenant-1',
        rut: '123',
        country: 'UY',
        currency: 'UYU',
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z',
      },
    ])

    const mockProductsApi = await import('../services/products')
    vi.spyOn(mockProductsApi.productsApi, 'list').mockRejectedValue(new Error('products down'))

    const mockCustomersApi = await import('../services/customers')
    vi.spyOn(mockCustomersApi.customersApi, 'list').mockResolvedValue([])

    const mockInvoicesApi = await import('../services/invoices')
    vi.spyOn(mockInvoicesApi.invoicesApi, 'list').mockResolvedValue([])

    const mockFiscalApi = await import('../services/fiscalDocuments')
    vi.spyOn(mockFiscalApi.fiscalDocumentsApi, 'list').mockResolvedValue([])

    const mockPaymentsApi = await import('../services/payments')
    vi.spyOn(mockPaymentsApi.paymentsApi, 'list').mockResolvedValue([])

    renderWithProviders(<Dashboard />)

    expect(
      await screen.findByText('Algunos datos del panel no se pudieron cargar')
    ).toBeInTheDocument()
    expect(screen.getByText('Razones sociales')).toBeInTheDocument()
    expect(screen.getByText('1')).toBeInTheDocument()
    expect(screen.getByText('—')).toBeInTheDocument()
  })
})
