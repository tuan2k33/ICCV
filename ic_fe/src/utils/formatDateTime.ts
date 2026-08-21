/**
 * Format a Date object using a format string.
 * Supported tokens:
 * YYYY = 4-digit year
 * M    = 1-digit month
 * MM   = 2-digit month
 * DD   = 2-digit day
 * HH   = 2-digit hours (00–23)
 * mm   = 2-digit minutes
 * ss   = 2-digit seconds
 * SSS  = milliseconds (000–999)
 */
export function formatDateTime(date: Date, format: string): string {
  const pad = (n: number, len = 2) => String(n).padStart(len, '0')

  const map: Record<string, string> = {
    YYYY: date.getFullYear().toString(),
    M: (date.getMonth() + 1).toString(),
    MM: pad(date.getMonth() + 1),
    DD: pad(date.getDate()),
    HH: pad(date.getHours()),
    mm: pad(date.getMinutes()),
    ss: pad(date.getSeconds()),
    SSS: pad(date.getMilliseconds(), 3),
  }

  return format.replace(/YYYY|MM|M|DD|HH|mm|ss|SSS/g, (match) => map[match])
}
