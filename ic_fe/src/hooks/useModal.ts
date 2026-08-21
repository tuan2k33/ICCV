import { useState } from 'react'

export const useModal = (init = false) => {
  const [open, setOpen] = useState(init)

  return {
    open,
    openModal: () => setOpen(true),
    closeModal: () => setOpen(false),
    toggleModal: () => setOpen((prev) => !prev),
  }
}
