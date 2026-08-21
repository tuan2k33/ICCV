import { useState } from 'react'
import FolderPlusIcon from '~/assets/icons/folder-plus.svg'
import PlusIcon from '~/assets/icons/plus.svg'
import Button from '~/components/common/Button'
import AddSingleUser, { type CreateUserForm } from './AddSingleUserForm'
import AddBatch from './AddBatch'

interface Props {
  submitting: boolean
  hasCompany?: boolean
  onSubmitSingle: (values: CreateUserForm) => void
  onCreateBatchUserSuccess: () => void
}

export default function NoData({
  submitting,
  hasCompany,
  onSubmitSingle,
  onCreateBatchUserSuccess,
}: Readonly<Props>) {
  const [openModal, setOpenModal] = useState<null | 'add_single' | 'add_multi'>(null)
  return (
    <>
      <div className="h-full pb-3 flex flex-col items-center justify-center">
        <p className="text-text-primary text-lg font-semibold">Danh sách trống</p>
        <p className="text-center mt-2 text-sm leading-4 text-tertiary-600">
          Danh sách của bạn hiện chưa có người dùng nào. <br />
          <br /> Chọn cách thêm người dùng:
        </p>
        <div className="flex items-center gap-3 mt-8">
          <Button
            className="w-fit text-sm gap-1 px-4 ml-auto h-11"
            outline
            onClick={() => setOpenModal('add_single')}
          >
            <PlusIcon className="text-xl" />
            Thêm lẻ
          </Button>
          <Button
            className="w-fit text-sm gap-1 px-4 h-11 bg-blue-secondary"
            onClick={() => setOpenModal('add_multi')}
          >
            <FolderPlusIcon className="text-xl" />
            Thêm hàng loạt
          </Button>
        </div>
      </div>
      <AddSingleUser
        open={openModal === 'add_single'}
        hasCompany={hasCompany}
        onRequestClose={() => setOpenModal(null)}
        submitting={submitting}
        onSubmit={onSubmitSingle}
      />
      <AddBatch
        open={openModal === 'add_multi'}
        hasCompany={hasCompany}
        onRequestClose={() => setOpenModal(null)}
        onCreateSuccess={onCreateBatchUserSuccess}
      />
    </>
  )
}
