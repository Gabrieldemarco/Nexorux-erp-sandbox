import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import ProtectedRoute from '../components/ProtectedRoute'
import GuestRoute from '../components/GuestRoute'
import { AuthProvider } from '../hooks/useAuth'
import { authApi } from '../services/auth'

vi.mock('../services/auth')

const renderWithAuth = (ui: React.ReactElement, initialPath = '/') => {
  return render(
    <MemoryRouter initialEntries={[initialPath]}>
      <AuthProvider>{ui}</AuthProvider>
    </MemoryRouter>
  )
}

describe('ProtectedRoute', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    localStorage.clear()
  })

  it('redirects to login when no token', async () => {
    renderWithAuth(
      <ProtectedRoute>
        <div>Private content</div>
      </ProtectedRoute>
    )

    expect(screen.queryByText('Private content')).not.toBeInTheDocument()
  })

  it('renders children when token exists', async () => {
    localStorage.setItem('access_token', 'test-token')
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

    renderWithAuth(
      <ProtectedRoute>
        <div>Private content</div>
      </ProtectedRoute>
    )

    expect(await screen.findByText('Private content')).toBeInTheDocument()
  })
})

describe('GuestRoute', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    localStorage.clear()
  })

  it('renders children when not authenticated', () => {
    renderWithAuth(
      <GuestRoute>
        <div>Login page</div>
      </GuestRoute>,
      '/login'
    )

    expect(screen.getByText('Login page')).toBeInTheDocument()
  })

  it('redirects away when already authenticated', async () => {
    localStorage.setItem('access_token', 'test-token')
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

    renderWithAuth(
      <GuestRoute>
        <div>Login page</div>
      </GuestRoute>,
      '/login'
    )

    expect(screen.queryByText('Login page')).not.toBeInTheDocument()
  })
})
