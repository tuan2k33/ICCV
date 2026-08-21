export function getValueByPath<T extends object, R = unknown>(obj: T, path: string): R | undefined {
  // Convert array-style path (e.g. "items[0].name") to dot-style ("items.0.name")
  const keys = path.replace(/\[(\d+)\]/g, '.$1').split('.')

  return keys.reduce<any>((acc, key) => (acc != null ? acc[key] : undefined), obj)
}
