import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import BrandLogo from '../components/BrandLogo'

const Login = () => {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const { login } = useAuth()
  const navigate = useNavigate()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      await login(email, password)
      navigate('/')
    } catch (err: any) {
      setError(err.response?.data?.detail || 'No se pudo iniciar sesión')
    } finally {
      setLoading(false)
    }
  }

  const fieldClass =
    'appearance-none relative block w-full px-3 py-2.5 border border-slate-300 placeholder-slate-400 text-[#1E293B] focus:outline-none focus:ring-2 focus:ring-[#3E92CC]/40 focus:border-[#247BA0] focus:z-10 sm:text-sm'

  return (
    <div className="min-h-screen flex items-center justify-center bg-[#F8FAFC] px-4 py-10">
      <div className="max-w-md w-full space-y-8 rounded-2xl border border-slate-200 bg-white p-8 shadow-sm">
        <div className="text-center">
          <BrandLogo size="lg" className="mx-auto" />
          <h2 className="mt-6 text-2xl font-bold tracking-tight text-[#1E293B]">Ingresar</h2>
          <p className="mt-2 text-sm text-slate-600">Accedé con tu correo y contraseña.</p>
        </div>
        <form className="space-y-6" onSubmit={handleSubmit}>
          {error && <div className="rounded-md bg-red-50 p-3 text-red-700 text-sm">{error}</div>}
          <div className="rounded-md shadow-sm -space-y-px">
            <input
              type="email"
              required
              className={`${fieldClass} rounded-t-md`}
              placeholder="Correo electrónico"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
            <input
              type="password"
              required
              className={`${fieldClass} rounded-b-md`}
              placeholder="Contraseña"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
          </div>
          <button type="submit" disabled={loading} className="btn-primary w-full py-2.5 px-4 text-sm">
            {loading ? 'Ingresando...' : 'Ingresar'}
          </button>
          <div className="space-y-2 text-center text-sm text-slate-600">
            <p>
              ¿No tenés cuenta?{' '}
              <Link to="/register" className="link-brand">
                Registrate
              </Link>
            </p>
            <p>
              <Link to="/recover-password" className="link-brand">
                Olvidaste tu contraseña?
              </Link>
            </p>
          </div>
        </form>
      </div>
    </div>
  )
}

export default Login
