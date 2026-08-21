import { useEffect } from 'react'

type Shortcut = {
  key: string
  ctrl?: boolean
  shift?: boolean
  alt?: boolean
  meta?: boolean
  listener: () => void
}

export function useKeyboardShortcuts(shortcuts: Shortcut[]) {
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      for (const shortcut of shortcuts) {
        if (
          e.key.toLowerCase() === shortcut.key.toLowerCase() &&
          !!shortcut.ctrl === e.ctrlKey &&
          !!shortcut.shift === e.shiftKey &&
          !!shortcut.alt === e.altKey &&
          !!shortcut.meta === e.metaKey
        ) {
          e.preventDefault()
          shortcut.listener()
          break
        }
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [shortcuts])
}
