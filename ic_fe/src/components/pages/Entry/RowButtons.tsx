import { useEffect, useImperativeHandle, useMemo, useRef, useState, type RefObject } from 'react'
import { twMerge } from 'tailwind-merge'
import { useSelector } from 'react-redux'
import type { PackData } from '~/types/task'
import type { RootState } from '~/redux'
import ArrowRightIcon from '~/assets/icons/arrow-right.svg'
import CheckIcon from '~/assets/icons/check.svg'
import FlipBackwardIcon from '~/assets/icons/flip-backward.svg'
import FlagIcon from '~/assets/icons/flag.svg'
import Button from '~/components/common/Button'
import Modal from '~/components/common/Modal'

export interface RowButtonsRef {
  openConfirmModal: () => void
}

interface Props {
  list: string[]
  currentPosition: number
  allowFinish: boolean
  dataPack: PackData[] | null
  taskName: string
  ref?: RefObject<RowButtonsRef | null>
  onChange?: (index: number) => void
  onFinish: () => void
}

export default function RowButtons({
  list,
  currentPosition,
  dataPack,
  taskName,
  ref,
  onChange,
  onFinish,
}: Readonly<Props>) {
  const { user } = useSelector((state: RootState) => state.auth)
  const [openConfirm, setOpenConfirm] = useState(false)
  const wrapperRef = useRef<HTMLDivElement>(null)
  const finishedColumn = useMemo(() => {
    const result = {
      finished: new Set(),
      needConfirm: new Set(),
    }

    dataPack?.forEach((column) => {
      let existNeedConfirm = false
      if (
        column.pallets.every((pallet) => {
          if (pallet.data._need_confirm) existNeedConfirm = true
          return pallet.data._is_finished || pallet.data._need_confirm
        })
      ) {
        if (existNeedConfirm) result.needConfirm.add(column.name)
        else result.finished.add(column.name)
      }
    })

    return result
  }, [dataPack])

  useEffect(() => {
    wrapperRef.current
      ?.querySelector(`#row-button-${currentPosition}`)
      ?.scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'center' })
  }, [currentPosition])

  useImperativeHandle(
    ref,
    () => ({
      openConfirmModal() {
        setOpenConfirm(true)
      },
    }),
    [],
  )

  return (
    <div ref={wrapperRef} className="flex items-top gap-3.5">
      <div
        className="flex items-center gap-2.5 overflow-x-auto relative scrollbar-xs pb-1 -mb-1"
        onWheel={(e) => {
          e.currentTarget.scrollLeft += e.deltaY
        }}
      >
        {list.map((item, index) => (
          <Button
            key={item}
            id={`row-button-${index}`}
            className={twMerge(
              'w-fit shrink-0 h-[30px] text-sm px-3',
              finishedColumn.finished.has(item) && 'text-success',
              finishedColumn.needConfirm.has(item) && 'text-error',
              currentPosition === index && 'text-white',
            )}
            outline={currentPosition !== index}
            type="button"
            onClick={() => {
              if (index !== currentPosition) onChange?.(index)
            }}
          >
            {item.split('-').pop()}{' '}
            {finishedColumn.finished.has(item) && (
              <CheckIcon className="inline-block shrink-0 ml-1 text-xl" />
            )}
            {finishedColumn.needConfirm.has(item) && (
              <FlagIcon className="inline-block shrink-0 ml-1 text-xl" />
            )}
          </Button>
        ))}
      </div>

      {finishedColumn.finished.size + finishedColumn.needConfirm.size === dataPack?.length &&
        user?.company === 'Unilever' && (
          <Button
            className="bg-error shrink-0 w-fit h-[30px] text-sm px-3"
            onClick={() => setOpenConfirm(true)}
          >
            Kết thúc
          </Button>
        )}
      <Modal
        open={openConfirm}
        classNames={{
          body: 'w-[720px]',
        }}
        onRequestClose={() => setOpenConfirm(false)}
      >
        <div>
          <h3 className="font-semibold uppercase">NỘP DÃY {taskName}</h3>
          <p className="mt-[26px] py-0.5 text-sm">
            Bạn đã hoàn thành đếm dãy {taskName}. Bạn có chắc chắn muốn nộp?
          </p>
          <div className="mt-[38px] flex items-center justify-end gap-3">
            <Button
              className="w-fit h-9 text-sm font-semibold text-[#FF5630] border-current"
              outline
              onClick={() => setOpenConfirm(false)}
            >
              <FlipBackwardIcon className="mr-2 text-base" />
              Không, xem lại
            </Button>
            <Button
              className="w-fit h-9 text-sm font-semibold bg-blue-secondary"
              onClick={() => {
                onFinish()
                setOpenConfirm(false)
              }}
            >
              Có, nộp
              <ArrowRightIcon className="text-base ml-2" />
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  )
}
