import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import Roles from '../pages/Roles'
import AuditLogs from '../pages/AuditLogs'
import { AuthProvider } from '../hooks/useAuth'
import { authApi } from '../services/auth'
import { rolesApi } from '../services/roles'
import { permissionsApi } from '../services/permissions'
import { auditLogsApi } from '../services/auditLogs'

vi.mock('../services/auth')
vi.mock('../services/roles')
vi.mock('../services/permissions')
vi.mock('../services/auditLogs')

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

describe('Roles page', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    localStorage.setItem('access_token', 'test-token')
    vi.mocked(authApi.me).mockResolvedValue(mockUser)
    vi.mocked(rolesApi.list).mockResolvedValue([])
    vi.mocked(permissionsApi.list).mockResolvedValue([])
  })

  it('renders Roles title', async () => {
    render(
      <MemoryRouter>
        <AuthProvider>
          <Roles />
        </AuthProvider>
      </MemoryRouter>
    )
    expect(await screen.findByRole('heading', { name: 'Roles' })).toBeInTheDocument()
  })
})

describe('AuditLogs page', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    localStorage.setItem('access_token', 'test-token')
    vi.mocked(authApi.me).mockResolvedValue(mockUser)
    vi.mocked(auditLogsApi.list).mockResolvedValue([])
  })

  it('renders Auditoría title', async () => {
    render(
      <MemoryRouter>
        <AuthProvider>
          <AuditLogs />
        </AuthProvider>
      </MemoryRouter>
    )
    expect(await screen.findByRole('heading', { name: 'Auditoría' })).toBeInTheDocument()
  })
})
