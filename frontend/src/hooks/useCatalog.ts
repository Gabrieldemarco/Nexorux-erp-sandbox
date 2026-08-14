import { useEffect, useState } from 'react'
import { companiesApi, CompanyResponse } from '../services/companies'
import { fetchCatalog, type AppCatalog } from '../services/catalog'
import { useAuth } from './useAuth'

export function useCatalog() {
  const { user } = useAuth()
  const [catalog, setCatalog] = useState<AppCatalog | null>(null)
  const [company, setCompany] = useState<CompanyResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!user) {
      setCatalog(null)
      setCompany(null)
      setLoading(false)
      return
    }
    let cancelled = false
    setLoading(true)
    Promise.all([fetchCatalog(), companiesApi.list()])
      .then(([cat, companies]) => {
        if (cancelled) return
        setCatalog(cat)
        setCompany(companies.find((c) => c.id === user.company_id) || companies[0] || null)
      })
      .catch((err) => {
        if (!cancelled) setError(String(err))
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [user])

  const currency = company?.currency || catalog?.currency || 'UYU'
  const country = company?.country || catalog?.country || 'Uruguay'

  return { catalog, company, currency, country, loading, error }
}
