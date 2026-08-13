import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import { getErrorMessage } from '../utils/errors'
import BrandLogo from '../components/BrandLogo'

type OrgMode = 'bootstrap' | 'join'

const Register = () => {
  const [formData, setFormData] = useState({
    email: '',
    username: '',
    full_name: '',
    password: '',
    tenant_id: '',
    company_id: '',
  })
  const [orgMode, setOrgMode] = useState<OrgMode>('bootstrap')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const { register } = useAuth()
  const navigate = useNavigate()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')

    if (orgMode === 'join') {
      if (!formData.tenant_id.trim() || !formData.company_id.trim()) {
        setError('Para unirte a una organización existente, indicá tenant y razón social (UUID).')
        return
      }
    }

    setLoading(true)
    try {
      const payload: Record<string, string> = {
        email: formData.email,
        username: formData.username,
        full_name: formData.full_name,
        password: formData.password,
      }
      if (orgMode === 'join') {
        payload.tenant_id = formData.tenant_id.trim()
        payload.company_id = formData.company_id.trim()
      }
      await register(payload)
      navigate('/')
    } catch (err: unknown) {
      const axiosErr = err as { response?: unknown }
      if (!axiosErr.response) {
        setError('No se pudo conectar con el servidor. Verificá que el backend esté disponible.')
      } else {
        setError(getErrorMessage(err, 'No se pudo registrar'))
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-100 px-4 py-10">
      <div className="max-w-md w-full space-y-8 rounded-2xl border border-slate-200 bg-white p-8 shadow-sm">
        <div className="text-center">
          <BrandLogo size="lg" className="mx-auto" />
          <h2 className="mt-6 text-2xl font-bold tracking-tight text-slate-900">Crear cuenta</h2>
          <p className="mt-2 text-sm text-slate-600">
            Por defecto se crea una organización nueva. También podés unirte a una existente con sus UUIDs.
          </p>
        </div>
        <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
          {error && <div className="rounded-md bg-red-50 p-3 text-red-700 text-sm">{error}</div>}
          <div className="rounded-md shadow-sm -space-y-px">
            <input
              type="text"
              required
              className="appearance-none rounded-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-t-md focus:outline-none focus:ring-teal-700 focus:border-teal-700 focus:z-10 sm:text-sm"
              placeholder="Nombre completo"
              value={formData.full_name}
              onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
            />
            <input
              type="email"
              required
              className="appearance-none rounded-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 focus:outline-none focus:ring-teal-700 focus:border-teal-700 focus:z-10 sm:text-sm"
              placeholder="Correo electrónico"
              value={formData.email}
              onChange={(e) => setFormData({ ...formData, email: e.target.value })}
            />
            <input
              type="text"
              required
              className="appearance-none rounded-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 focus:outline-none focus:ring-teal-700 focus:border-teal-700 focus:z-10 sm:text-sm"
              placeholder="Usuario"
              value={formData.username}
              onChange={(e) => setFormData({ ...formData, username: e.target.value })}
            />
            <input
              type="password"
              required
              minLength={8}
              className="appearance-none rounded-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-b-md focus:outline-none focus:ring-teal-700 focus:border-teal-700 focus:z-10 sm:text-sm"
              placeholder="Contraseña (mín. 8)"
              value={formData.password}
              onChange={(e) => setFormData({ ...formData, password: e.target.value })}
            />
          </div>

          <fieldset className="space-y-3">
            <legend className="text-sm font-medium text-gray-700">Organización</legend>
            <label className="flex items-start gap-2 text-sm text-gray-700">
              <input
                type="radio"
                name="orgMode"
                className="mt-1"
                checked={orgMode === 'bootstrap'}
                onChange={() => setOrgMode('bootstrap')}
              />
              <span>
                Crear organización nueva
                <span className="block text-xs text-gray-500">
                  El backend genera tenant + razón social automáticamente.
                </span>
              </span>
            </label>
            <label className="flex items-start gap-2 text-sm text-gray-700">
              <input
                type="radio"
                name="orgMode"
                className="mt-1"
                checked={orgMode === 'join'}
                onChange={() => setOrgMode('join')}
              />
              <span>
                Unirme a organización existente
                <span className="block text-xs text-gray-500">
                  Requiere los UUID de tenant y company (pedilos a un admin).
                </span>
              </span>
            </label>

            {orgMode === 'join' && (
              <div className="space-y-3 rounded-md border border-gray-200 bg-white p-3">
                <div>
                  <label className="mb-1 block text-xs font-medium text-gray-600">Tenant ID</label>
                  <input
                    type="text"
                    className="block w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-teal-700 focus:outline-none focus:ring-teal-700"
                    placeholder="uuid del tenant"
                    value={formData.tenant_id}
                    onChange={(e) => setFormData({ ...formData, tenant_id: e.target.value })}
                  />
                </div>
                <div>
                  <label className="mb-1 block text-xs font-medium text-gray-600">Company ID</label>
                  <input
                    type="text"
                    className="block w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-teal-700 focus:outline-none focus:ring-teal-700"
                    placeholder="uuid de la razón social"
                    value={formData.company_id}
                    onChange={(e) => setFormData({ ...formData, company_id: e.target.value })}
                  />
                </div>
              </div>
            )}
          </fieldset>

          <button
            type="submit"
            disabled={loading}
            className="group relative w-full flex justify-center py-2.5 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-teal-800 hover:bg-teal-900 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-teal-700 disabled:opacity-50"
          >
            {loading ? 'Creando cuenta...' : 'Registrarse'}
          </button>
          <p className="text-center text-sm text-gray-600">
            ¿Ya tenés cuenta?{' '}
            <Link to="/login" className="font-medium text-teal-800 hover:text-teal-900">
              Ingresar
            </Link>
          </p>
        </form>
      </div>
    </div>
  )
}

export default Register
