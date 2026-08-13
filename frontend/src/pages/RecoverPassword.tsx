import { useEffect, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { authApi } from '../services/auth'
import BrandLogo from '../components/BrandLogo'

const RecoverPassword = () => {
  const [searchParams] = useSearchParams()
  const [email, setEmail] = useState('')
  const [resetToken, setResetToken] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')
  const [loadingRequest, setLoadingRequest] = useState(false)
  const [loadingReset, setLoadingReset] = useState(false)
  const [step, setStep] = useState<'request' | 'reset'>('request')

  useEffect(() => {
    const fromLink = searchParams.get('token')
    if (fromLink) {
      setResetToken(fromLink)
      setStep('reset')
      setMessage('Abriste el enlace del correo. Definí tu nueva contraseña.')
    }
  }, [searchParams])

  const handleRequestReset = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setMessage('')
    setLoadingRequest(true)
    try {
      const response = await authApi.requestPasswordReset({ email: email.trim() })
      setMessage(response.message)
      setStep('reset')
    } catch (err: any) {
      const detail = err.response?.data?.detail
      let msg = 'No se pudo enviar el correo de recuperación'
      if (typeof detail === 'string') {
        msg = detail
      } else if (Array.isArray(detail) && detail[0]?.msg) {
        msg = detail.map((d: { msg?: string }) => d.msg).filter(Boolean).join(' · ')
      } else if (!err.response) {
        msg = 'No se pudo conectar con el servidor. ¿Está el backend en marcha?'
      }
      setError(msg)
    } finally {
      setLoadingRequest(false)
    }
  }

  const handleResetPassword = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setMessage('')
    if (newPassword.length < 8) {
      setError('La contraseña debe tener al menos 8 caracteres')
      return
    }
    if (newPassword !== confirmPassword) {
      setError('Las contraseñas no coinciden')
      return
    }
    if (!resetToken.trim()) {
      setError('Pegá el token que llegó a tu correo')
      return
    }
    setLoadingReset(true)
    try {
      const response = await authApi.resetPassword({
        token: resetToken.trim(),
        new_password: newPassword,
      })
      setMessage(response.message)
      setResetToken('')
      setNewPassword('')
      setConfirmPassword('')
      setStep('request')
    } catch (err: any) {
      const detail = err.response?.data?.detail
      setError(
        typeof detail === 'string'
          ? detail
          : 'No se pudo restablecer la contraseña'
      )
    } finally {
      setLoadingReset(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-50 px-4">
      <div className="w-full max-w-lg space-y-6">
        <div className="text-center">
          <BrandLogo size="lg" className="mx-auto" />
          <h2 className="mt-6 text-2xl font-bold tracking-tight text-slate-900">Recuperar contraseña</h2>
          <p className="mt-2 text-sm text-slate-600">
            Usá el correo con el que estás registrado. Te enviamos un token; con ese token
            definís la nueva contraseña.
          </p>
        </div>

        {message && <div className="rounded-md bg-green-50 p-4 text-green-700">{message}</div>}
        {error && <div className="rounded-md bg-red-50 p-4 text-red-700">{error}</div>}

        {step === 'request' && (
          <form onSubmit={handleRequestReset} className="rounded-lg bg-white p-6 shadow space-y-4">
            <h3 className="text-lg font-semibold text-gray-900">1. Enviar token al correo</h3>
            <label className="block text-sm text-gray-700">
              Correo registrado
              <input
                type="email"
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                placeholder="tu@correo.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                autoComplete="email"
              />
            </label>
            <button
              type="submit"
              disabled={loadingRequest}
              className="rounded-md bg-blue-600 px-4 py-2 text-white hover:bg-blue-700 disabled:opacity-50"
            >
              {loadingRequest ? 'Enviando...' : 'Enviar token al correo'}
            </button>
          </form>
        )}

        {step === 'reset' && (
          <form onSubmit={handleResetPassword} className="rounded-lg bg-white p-6 shadow space-y-4">
            <h3 className="text-lg font-semibold text-gray-900">2. Nueva contraseña</h3>
            <p className="text-sm text-gray-600">
              Copiá el token del correo (o usá el enlace). Si no llegó, revisá spam o
              volvé a solicitarlo.
            </p>
            <label className="block text-sm text-gray-700">
              Token del correo
              <input
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                placeholder="Pegá el token aquí"
                value={resetToken}
                onChange={(e) => setResetToken(e.target.value)}
                required
              />
            </label>
            <label className="block text-sm text-gray-700">
              Nueva contraseña
              <input
                type="password"
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                placeholder="Mínimo 8 caracteres"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                minLength={8}
                required
                autoComplete="new-password"
              />
            </label>
            <label className="block text-sm text-gray-700">
              Confirmar contraseña
              <input
                type="password"
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                placeholder="Repetí la contraseña"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                minLength={8}
                required
                autoComplete="new-password"
              />
            </label>
            <div className="flex flex-wrap gap-3">
              <button
                type="submit"
                disabled={loadingReset}
                className="rounded-md bg-gray-900 px-4 py-2 text-white hover:bg-gray-800 disabled:opacity-50"
              >
                {loadingReset ? 'Guardando...' : 'Cambiar contraseña'}
              </button>
              <button
                type="button"
                className="rounded-md border border-gray-300 px-4 py-2 text-gray-700 hover:bg-gray-50"
                onClick={() => {
                  setStep('request')
                  setError('')
                  setMessage('')
                }}
              >
                Reenviar token
              </button>
            </div>
          </form>
        )}

        <p className="text-sm text-center text-gray-600">
          <Link to="/login" className="text-blue-600 hover:text-blue-500">
            Volver al ingreso
          </Link>
        </p>
      </div>
    </div>
  )
}

export default RecoverPassword
