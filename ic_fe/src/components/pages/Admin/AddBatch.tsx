import { Fragment, useRef, useState } from 'react'
import { AxiosError } from 'axios'
import { useSelector } from 'react-redux'

import { toastError } from '~/utils/showErrorToast'
import { formatBytes } from '~/utils/formatBytes'
import { toastSuccess } from '~/utils/toastSuccess'
import { useMutation } from '~/hooks/useMutation'
import { endpoints } from '~/configs/endpoints'
import { ErrorCode, ImportExcelRowErrorCode } from '~/configs/errorCode'
import { Role } from '~/types/auth'
import type { RootState } from '~/redux'

import DownloadSVG from '~/assets/icons/download.svg'
import UploadIcon from '~/assets/icons/upload.svg'
import TrashIcon from '~/assets/icons/trash.svg'
import XLSXIcon from '~/assets/xlsx.png'
import Radio from '~/components/common/Radio'
import Table from '~/components/common/Table'
import BaseModal from '~/components/common/BaseModal'

export interface CreateBatchUserForm {
  company: string
  file: File
}

interface RowErrorInfo {
  fullname: string
  phone_number: string
}

interface RowError {
  row_index: number
  errors: ImportExcelRowErrorCode[]
  info: RowErrorInfo
  isFullnameError?: boolean
  isPhoneNumberError?: boolean
}

interface Props {
  open: boolean
  hasCompany?: boolean
  onRequestClose: () => void
  onCreateSuccess: () => void
}

const fullnameErrors: ImportExcelRowErrorCode[] = [
  ImportExcelRowErrorCode.EMPTY_FULLNAME,
  ImportExcelRowErrorCode.LESS_THAN_2_CHARACTERS,
  ImportExcelRowErrorCode.INVALID_CHARACTERS_IN_NAME,
]

const phoneNumberErrors: ImportExcelRowErrorCode[] = [
  ImportExcelRowErrorCode.EMPTY_PHONE_NUMBER,
  ImportExcelRowErrorCode.INVALID_PHONE_NUMBER,
  ImportExcelRowErrorCode.PHONE_NUMBER_ALREADY_EXIST,
]

const COMPANIES = [
  {
    id: 'linfox',
    name: 'Linfox',
  },
  {
    id: 'unilever',
    name: 'Unilever',
  },
]

const errorMappingMessage: Record<ImportExcelRowErrorCode, string> = {
  EMPTY_FULLNAME: 'Họ & Tên rỗng',
  LESS_THAN_2_CHARACTERS: 'Họ & Tên không đúng định dạng',
  EMPTY_PHONE_NUMBER: 'Số điện thoại rỗng',
  INVALID_PHONE_NUMBER: 'Số điện thoại không đúng định dạng',
  INVALID_CHARACTERS_IN_NAME: 'Họ & Tên không đúng định dạng',
  PHONE_NUMBER_ALREADY_EXIST: 'Số điện thoại trùng với user khác',
  PHONE_NUMBER_DUPLICATED_IN_SHEET: 'Số điện thoại trùng với dòng khác',
}

export default function AddBatch({
  open,
  hasCompany,
  onRequestClose: onRequestCloseProp,
  onCreateSuccess,
}: Readonly<Props>) {
  const { user } = useSelector((state: RootState) => state.auth)
  const [selectedCompany, setSelectedCompany] = useState<string>('linfox')
  const [file, setFile] = useState<File | null>(null)
  const [errorRowsDisplay, setErrorRowsDisplay] = useState<{
    errors: RowError[]
    total: number
  } | null>(null)

  const createBatchUserMutation = useMutation<{
    data: {
      total: number
    }
  }>({
    url: endpoints.AUTH_IMPORT_USERS,
    method: 'post',
    config: {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      timeout: 0,
    },
  })

  const onRequestClose = () => {
    if (createBatchUserMutation.pending) return
    onRequestCloseProp()
    setFile(null)
    setErrorRowsDisplay(null)
    setSelectedCompany('linfox')
  }

  const maxWidth = errorRowsDisplay?.errors.length && file ? 'max-w-[650px]' : 'max-w-[430px]'

  const handleRowsError = ({ errors, total }: { errors: RowError[]; total: number }) => {
    setErrorRowsDisplay({
      errors: errors.map((rowError) => {
        const isFullnameError = rowError.errors.some((error) => fullnameErrors.includes(error))
        const isPhoneNumberError = rowError.errors.some((error) =>
          phoneNumberErrors.includes(error),
        )
        return {
          ...rowError,
          isFullnameError,
          isPhoneNumberError,
        }
      }),
      total,
    })
  }

  const handleSubmit = () => {
    const formData = new FormData()
    formData.append('file_excel', file!)
    formData.append('roles', hasCompany ? Role.ENTRY : Role.CHECKER)
    const params: Record<string, unknown> = {
      tenant_id: user?.tenant_id,
    }

    if (hasCompany) {
      params.company = selectedCompany.replace(
        selectedCompany.charAt(0),
        selectedCompany.charAt(0).toUpperCase(),
      )
    }

    createBatchUserMutation.mutate(
      {
        body: formData,
        config: {
          params,
        },
      },
      {
        onError(error) {
          if (
            error instanceof AxiosError &&
            (error.response?.data?.detail?.error_code === ErrorCode.ERROR_USER_DATA_IMPORT ||
              error.response?.data?.detail?.error_code ===
                ErrorCode.ERROR_USER_PHONE_ALREADY_EXISTS)
          ) {
            handleRowsError(error.response?.data?.detail?.data)
          } else toastError('Thêm người dùng thất bại')
        },
        onSuccess(response) {
          toastSuccess(`Thêm ${response.data.total} người dùng thành công`)
          onCreateSuccess()
          onRequestClose()
        },
      },
    )
  }

  return (
    <BaseModal
      open={open}
      destroyOnHide
      onRequestClose={onRequestClose}
      classNames={{
        body: `${maxWidth} w-full`,
      }}
      title="THÊM HÀNG LOẠT"
      footer={file ? undefined : ''}
      confirmButton={{
        onClick() {
          handleSubmit()
        },
        loading: createBatchUserMutation.pending,
      }}
    >
      <div className={` w-full flex flex-col`}>
        {hasCompany && (
          <div className="flex items-center gap-3 pb-2.5">
            <span className="text-[13px] font-semibold leading-6 text-text-default-secondary">
              Công ty*
            </span>

            <CompanySelector
              companies={COMPANIES}
              selectedCompanyId={selectedCompany ?? ''}
              onSelect={setSelectedCompany}
            />
          </div>
        )}

        {!file ? (
          <div className="my-4">
            <Intruction />
          </div>
        ) : null}

        {!!errorRowsDisplay?.errors.length && !!file && (
          <>
            <div className="flex gap-1 items-center mt-3">
              <span className="text-[14px] leading-5 text-tertiary-600">Thêm</span>
              <span className="text-[14px] text-success leading-5 font-bold">
                {errorRowsDisplay.total - errorRowsDisplay.errors.length}/{errorRowsDisplay.total}
              </span>
              <span className="text-[14px] leading-5 text-tertiary-600">
                người dùng hợp lệ. Vui lòng kiểm tra và chỉnh sửa các thông tin lỗi dưới đây.
              </span>
            </div>
            <div className="mt-4 relative max-h-[300px] overflow-y-auto">
              <Table
                dataKey="row_index"
                classNames={{
                  row: 'last:border-b-1',
                  thead: 'sticky top-0 left-0',
                }}
                columns={[
                  {
                    key: 'full_name',
                    label: 'Họ và tên',
                    align: 'left',
                    className: 'font-medium',
                    render(record) {
                      return (
                        <span className={record.isFullnameError ? 'text-error-secondary' : ''}>
                          {record.info.fullname}
                        </span>
                      )
                    },
                  },
                  {
                    key: 'phone_number',
                    label: 'Số điện thoại',
                    align: 'left',
                    className: 'font-medium',
                    render(record) {
                      return (
                        <span className={record.isPhoneNumberError ? 'text-error-secondary' : ''}>
                          {record.info.phone_number}
                        </span>
                      )
                    },
                  },
                  {
                    key: 'reason',
                    label: 'Lý do lỗi',
                    align: 'left',
                    className: 'font-medium',
                    cellClassName: 'text-tertiary-600',
                    render(record) {
                      return (
                        <p>
                          {record.errors.map((error, index) => (
                            <Fragment key={index}>
                              {errorMappingMessage[error]}
                              <br />
                            </Fragment>
                          ))}
                        </p>
                      )
                    },
                  },
                ]}
                // avoid unexpected TS error
                dataSource={
                  errorRowsDisplay.errors as unknown as {
                    row_index: number
                    errors: ImportExcelRowErrorCode[]
                    info: RowErrorInfo
                    isFullnameError: boolean
                    isPhoneNumberError: boolean
                  }[]
                }
              />
            </div>
          </>
        )}
        {!file && (
          <Upload
            validations={[
              (file: File) => {
                if (!file.name.toLowerCase().endsWith('.xlsx')) return 'Chỉ hỗ trợ định dạng .XLSX'
                return null
              },
              (file: File) => {
                if (file.size > 1024 * 1024) return 'File phải nhỏ hơn 1MB'
                return null
              },
            ]}
            onChange={(file) => {
              setErrorRowsDisplay(null)
              setFile(file)
            }}
          />
        )}

        {file ? (
          <div className="mt-4">
            <ViewFile
              file={{
                name: file.name,
                size: file.size,
              }}
              onDelete={() => {
                if (createBatchUserMutation.pending) return
                setFile(null)
                setErrorRowsDisplay(null)
              }}
            />
          </div>
        ) : null}
      </div>
    </BaseModal>
  )
}

interface ViewFileProps {
  file: {
    name: string
    size: number
  }
  onDelete: () => void
}

const ViewFile = ({ file, onDelete }: ViewFileProps) => {
  return (
    <div className="h-[96px] rounded-[12px] border border-border-secondary p-4">
      <div className="h-full overflow-y-auto w-full">
        <div className="flex gap-3">
          <img
            src={XLSXIcon}
            alt="XLSXIcon"
            width={40}
            height={40}
            className="shrink-0 w-[40px] h-[40px]"
          />

          <div className="flex flex-col flex-1">
            <span className="text-[14px] leading-5 font-medium text-text-secondary line-clamp-1">
              {file.name}
            </span>
            <span className="text-[14px] leading-5 text-[#475467]">{formatBytes(file.size)}</span>
          </div>

          <button
            className="h-full"
            onClick={(e) => {
              e.stopPropagation()
              onDelete()
            }}
          >
            <TrashIcon className="text-[#757575]" />
          </button>
        </div>
      </div>
    </div>
  )
}

const Intruction = () => {
  const handleDownloadTemplate = () => {
    window.open('/AI_IC_import_template.xlsx', '_blank')
  }

  const DATA_INTRUCTION: { title: string | React.ReactNode; desc?: string }[] = [
    {
      title: (
        <div className="flex items-center gap-1.5 text-sm leading-[20px]">
          <span className="font-bold">{`Bước 1:`}</span> <span>Tải tệp mẫu</span>
          <button
            className="border border-text-default-secondary rounded-[6px] h-7 px-2 py-1.5 flex items-center gap-2 ml-1.5 text-primary-black"
            onClick={(e) => {
              e.stopPropagation()
              handleDownloadTemplate()
            }}
          >
            <DownloadSVG className="text-base" />
            <span className="text-xs leading-[16px] tracking-[2%] font-semibold">
              Tệp mẫu Excel (*.xlsx)
            </span>
          </button>
        </div>
      ),
      desc: '',
    },
    {
      title: 'Điền thông tin',
      desc: 'Vui lòng không thay đổi tiêu đề các cột để hệ thống đọc tệp chính xác.',
    },
    {
      title: 'Tải lại tệp vừa điền lên hệ thống',
    },
  ]

  return (
    <div className="flex flex-col gap-4 ">
      {DATA_INTRUCTION.map((intruction, index) => (
        <div className="flex flex-col gap-4 text-tertiary-600 text-sm" key={index}>
          {typeof intruction.title === 'string' ? (
            <div className="flex items-center gap-1.5 leading-[20px]">
              <span className="font-bold">{`Bước ${index + 1}:`}</span>{' '}
              <span>{intruction.title}</span>
            </div>
          ) : (
            intruction.title
          )}

          {intruction.desc ? <p>{intruction.desc}</p> : null}
        </div>
      ))}
    </div>
  )
}

interface UploadProps {
  validations?: ((file: File) => string | null)[]
  onChange: (file: File) => void
}

const Upload = ({ validations, onChange }: Readonly<UploadProps>) => {
  const inputRef = useRef<HTMLInputElement>(null)

  const runValidations = (file: File): string[] => {
    const errors: string[] = []

    validations?.forEach((validateFn) => {
      const result = validateFn(file)
      if (result) errors.push(result)
    })

    return errors
  }

  const handleFile = (file: File) => {
    const errors = runValidations(file)

    if (errors.length > 0) {
      toastError(errors.join('\n'))
      return
    }

    onChange(file)
  }

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]

    if (!file) return

    handleFile(file)
    inputRef.current!.value = ''
  }

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault()

    const file = e.dataTransfer.files?.[0]

    if (!file) return

    handleFile(file)
  }

  return (
    <div
      className="h-[126px] rounded-[12px] border border-border-secondary p-4 cursor-pointer mb-3"
      onClick={() => inputRef.current?.click()}
      onDragOver={(e) => e.preventDefault()}
      onDrop={handleDrop}
    >
      <input
        ref={inputRef}
        type="file"
        accept=".xlsx"
        className="hidden"
        onChange={handleFileChange}
      />

      <div className="flex flex-col items-center justify-center h-full">
        <div className="mx-auto h-[40px] w-[40px] shadow-[0px_1px_2px_0px_#1018280D] border border-border-secondary grid place-items-center rounded-[8px]">
          <UploadIcon />
        </div>

        <div className="mt-3 mb-1 flex items-center gap-1">
          <span className="text-[14px] leading-5 font-semibold text-error-secondary">
            Nhấn để tải lên
          </span>
          <span className="text-[14px] leading-5 text-[#475467]">hoặc kéo thả file</span>
        </div>

        <p className="text-[12px] leading-[18px] text-[#475467]">
          Chỉ hỗ trợ định dạng .XLSX, mỗi lần chỉ tải lên 1 tệp dưới 1MB
        </p>
      </div>
    </div>
  )
}

interface Company {
  id: string
  name: string
}

interface CompanySelectorProps {
  companies: Company[]
  selectedCompanyId: string
  onSelect: (id: string) => void
}

const CompanySelector: React.FC<CompanySelectorProps> = ({
  companies,
  selectedCompanyId,
  onSelect,
}) => {
  return (
    <div className="flex items-center gap-3">
      {companies.map((company) => {
        const isChecked = company.id === selectedCompanyId
        return (
          <label
            key={company.id}
            htmlFor={company.id}
            className="flex gap-2 items-center cursor-pointer"
          >
            <Radio
              id={company.id}
              checked={isChecked}
              onChange={() => onSelect(company.id)}
              classNames={{
                dot: 'hidden',
              }}
            />

            <span
              className={`text-sm leading-6 transition-all ${isChecked ? 'font-semibold' : ''}`}
            >
              {company.name}
            </span>
          </label>
        )
      })}
    </div>
  )
}
