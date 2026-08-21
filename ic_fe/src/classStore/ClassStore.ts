export class ClassStore {
  protected static readonly store = new Map<unknown, unknown>()

  static has(value: unknown) {
    return this.store.has(value)
  }

  /**
   * @param value set to `'_'` if the value is not complete yet
   */
  static set(key: unknown, value: unknown) {
    this.store.set(key, value)
  }

  /**
   * @returns `'_'` for temp value, it exist but not complete yet
   */
  static get<T = unknown>(key: unknown) {
    return this.store.get(key) as T | '_' | undefined
  }

  static delete(key: unknown) {
    return this.store.delete(key)
  }

  static clear() {
    this.store.clear()
  }
}
