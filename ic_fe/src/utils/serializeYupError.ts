import type { ValidationError } from 'yup'

export type SerializedYupError = Record<string, string[]>

export const serializeYupError = (error: ValidationError): SerializedYupError => {
  const serialized: Record<string, string[]> = {}

  error.inner.forEach((item) => {
    if (!item.path) return
    if (!(item.path in serialized)) {
      serialized[item.path] = []
    }
    serialized[item.path].push(...item.errors)
  })

  return serialized
}
