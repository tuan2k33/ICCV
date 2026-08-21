export const generateDisplayFullname = (fullname: string, search: string) => {
  if (!search) return fullname

  const index = fullname.toLowerCase().indexOf(search.toLowerCase())
  if (index < 0) return fullname

  return `${fullname.slice(0, index)}<span class="bg-[#F2B32C]">${fullname.slice(
    index,
    index + search.length,
  )}</span>${fullname.slice(index + search.length)}`
}
