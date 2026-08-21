export function formatString(str: string, values: Record<string, string | number>) {
  return str.replace(/{(\w+)}/g, (_, key) => (values[key] ? values[key] + '' : `{${key}}`))
}
