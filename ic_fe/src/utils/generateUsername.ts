import { normalizeVietnamese } from './normalizeVietnameseName'

export const generateUsername = (fullname: string, subfix: string) => {
  if (!fullname) return ''
  const splitName = normalizeVietnamese(fullname).split(' ')
  const username =
    splitName
      .map((part, index) => {
        if (index === splitName.length - 1)
          return `${part.charAt(0).toUpperCase()}${part.slice(1).toLowerCase()}`
        return part.charAt(0).toUpperCase()
      })
      .join('') + subfix

  return username
}
