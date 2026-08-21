import type { ReactNode } from 'react'
import { twMerge } from 'tailwind-merge'
import XCircleFilledIcon from '~/assets/icons/x-circle-filled.svg'
import SaveIcon from '~/assets/icons/save.svg'
import Button, { type ButtonProps } from '../Button'
import Modal, { type ModalProps } from '../Modal'

interface Props extends ModalProps {
  title: ReactNode
  children: ReactNode
  cancelButton?: Partial<ButtonProps> & {
    label?: ReactNode
    icon?: ReactNode
  }
  confirmButton?: Partial<ButtonProps> & {
    label?: ReactNode
    icon?: ReactNode
  }
  footer?: ReactNode
}

export default function BaseModal({
  title,
  children,
  cancelButton,
  confirmButton,
  footer,
  ...props
}: Readonly<Props>) {
  return (
    <Modal destroyOnHide {...props}>
      <div>
        <h2 className="font-semibold pt-0.5">{title}</h2>
        <div className="mt-5">{children}</div>
        {footer ?? (
          <div className="flex items-center justify-end gap-3 mt-8">
            <Button
              outline
              className="text-[#FF5630] border-current w-fit text-sm gap-2 px-2.5 h-9"
              onClick={props.onRequestClose}
              {...cancelButton}
            >
              {cancelButton?.icon ?? <XCircleFilledIcon className="text-base" />}
              {cancelButton?.label ?? 'Hủy'}
            </Button>
            <Button
              {...confirmButton}
              className={twMerge(
                'w-fit text-sm gap-2 px-2.5 h-9 bg-blue-secondary disabled:bg-[#F1F3F9] disabled:opacity-100 disabled:text-[#8498B2]',
                confirmButton?.className,
              )}
            >
              {confirmButton?.icon ?? <SaveIcon className="text-base" />}
              {confirmButton?.label ?? 'Thêm'}
            </Button>
          </div>
        )}
      </div>
    </Modal>
  )
}
