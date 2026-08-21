export const formatTime = (s: number) => {
  const mins = Math.floor(s / 60).toString()
  const secs = (s % 60).toString().padStart(2, '0')
  return `${mins}:${secs}`
}
