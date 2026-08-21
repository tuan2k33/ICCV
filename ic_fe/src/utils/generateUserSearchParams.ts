export const generateUserSearchParams = (search: string) => {
  if (!search) return {}
  if (search.length === 10 && search.startsWith('0') && /^[0-9]+$/.test(search))
    return {
      phone_number: search,
    }
  return { fullname__ilike: `%${search}%` }
}
