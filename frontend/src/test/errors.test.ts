import { describe, it, expect } from 'vitest'
import { getErrorMessage } from '../utils/errors'

describe('getErrorMessage', () => {
  it('returns string detail from axios-like errors', () => {
    expect(
      getErrorMessage({ response: { data: { detail: 'Email ya registrado' } } }, 'fallback')
    ).toBe('Email ya registrado')
  })

  it('joins validation array details by msg', () => {
    expect(
      getErrorMessage(
        {
          response: {
            data: {
              detail: [{ msg: 'campo requerido' }, { msg: 'formato inválido' }],
            },
          },
        },
        'fallback'
      )
    ).toBe('campo requerido, formato inválido')
  })

  it('uses fallback when detail is missing', () => {
    expect(getErrorMessage({}, 'No se pudo cargar')).toBe('No se pudo cargar')
    expect(getErrorMessage(null, 'No se pudo cargar')).toBe('No se pudo cargar')
  })
})
