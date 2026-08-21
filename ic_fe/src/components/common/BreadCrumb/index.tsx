import React, { Fragment, type ReactNode } from 'react'
import { twMerge } from 'tailwind-merge'

interface BreadCrumbItem {
  label: ReactNode
  onClick?: () => void
}

interface Props {
  items: BreadCrumbItem[]
}

export default function BreadCrumb({ items }: Readonly<Props>) {
  return (
    <div className="flex items-center gap-1">
      {items.map((item, index) => {
        const Comp = 'div'
        return (
          <Fragment key={index}>
            <Comp
              className={twMerge(
                'text-sm text-quaternary cursor-pointer font-semibold',
                index === items.length - 1 && 'text-blue-secondary',
              )}
              onClick={item.onClick}
            >
              {item.label}
            </Comp>
            {items[index + 1] && (
              <span className="text-[#D0D5DD] inline-block px-1 text-lg">/</span>
            )}
          </Fragment>
        )
      })}
    </div>
  )
}
