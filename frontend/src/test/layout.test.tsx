import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import Layout from '../components/Layout'
import { AuthProvider } from '../hooks/useAuth'
import { authApi } from '../services/auth'
import { tenantsApi } from '../services/tenants'
import { resetAccessCache } from '../utils/access'

vi.mock('../services/auth')
vi.mock('../services/tenants')

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

const renderLayout = () =>
  render(
    <MemoryRouter>
      <AuthProvider>
        <Layout>
          <div>Contenido</div>
        </Layout>
      </AuthProvider>
    </MemoryRouter>
  )

describe('Layout sidebar nav', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    localStorage.setItem('access_token', 'test-token')
    resetAccessCache()
    vi.mocked(authApi.me).mockResolvedValue(mockUser)
  })

  it('shows Tenants link when probe succeeds', async () => {
    vi.mocked(tenantsApi.list).mockResolvedValue([])
    renderLayout()
    expect(await screen.findByRole('link', { name: 'Tenants' })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Facturas' })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Panel' })).toBeInTheDocument()
  })

  it('hides Tenants link on HTTP 403', async () => {
    vi.mocked(tenantsApi.list).mockRejectedValue({ response: { status: 403 } })
    renderLayout()
    await screen.findByText('Contenido')
    await waitFor(() => {
      expect(screen.queryByRole('link', { name: 'Tenants' })).not.toBeInTheDocument()
    })
    expect(screen.getByRole('link', { name: 'Facturas' })).toBeInTheDocument()
  })
})
