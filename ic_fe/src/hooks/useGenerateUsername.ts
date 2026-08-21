import { useEffect } from 'react'
import { generateUsername } from '~/utils/generateUsername'
import { axiosInstance } from '~/utils/axiosInstance'
import { endpoints } from '~/configs/endpoints'
import { UsernameStore } from '~/classStore/UsernameStore'
import { useDebounce } from './useDebounce'

/**
 * Generate username from fullname, phone number and company
 */
export const useGenerateUsername = (
  fullname: string,
  phoneNumber: string,
  company?: 'linfox' | 'unilever',
  options?: {
    disabled?: boolean
    userId?: number
    onGenerate?: (username: string) => void
  },
) => {
  const [debouncedFullname] = useDebounce(fullname, 400)
  const [debouncedPhoneNumber] = useDebounce(phoneNumber, 400)
  const [debouncedCompany] = useDebounce(company, 400)

  useEffect(() => {
    const generatedBaseUsername = generateUsername(
      debouncedFullname,
      getUsernameSubfix(debouncedCompany),
    )

    if (!generatedBaseUsername || options?.disabled) return

    const checkerUsernameExist = async () => {
      try {
        const { data: existed } = await isUsernameExist(generatedBaseUsername, options?.userId)
        if (existed) {
          UsernameStore.set(generatedBaseUsername, '_')

          const phoneNumberLength = debouncedPhoneNumber.length
          const usernameWith1Number = `${generatedBaseUsername}${debouncedPhoneNumber.charAt(phoneNumberLength - 1)}`
          const { data: exist1Number } = await isUsernameExist(usernameWith1Number, options?.userId)
          if (exist1Number) {
            UsernameStore.set(usernameWith1Number, '_')
            return `${generatedBaseUsername}${debouncedPhoneNumber.slice(phoneNumberLength - 2)}`
          } else return usernameWith1Number
        } else return generatedBaseUsername
      } catch {
        return
      }
    }

    checkerUsernameExist().then((newUsername) => {
      if (newUsername) {
        options?.onGenerate?.(newUsername)
      }
    })

    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [
    debouncedFullname,
    debouncedPhoneNumber,
    debouncedCompany,
    options?.disabled,
    options?.userId,
  ])
}

const getUsernameSubfix = (company?: string) => {
  if (company) return company === 'linfox' ? '_lf' : '_ul'

  return ''
}

const isUsernameExist = (username: string, userId?: number) => {
  if (UsernameStore.has(username)) {
    let existed = true
    // skip check if the username is belong to the userId
    if (userId && UsernameStore.get(username) === userId) existed = false

    return {
      data: existed,
    }
  }

  return axiosInstance.get<boolean>(endpoints.AUTH_CHECK_EXIST_USERNAME, {
    params: {
      username: username,
    },
  })
}
