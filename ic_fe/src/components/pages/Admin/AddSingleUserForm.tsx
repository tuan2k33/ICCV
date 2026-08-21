import { useEffect, type ChangeEvent } from 'react'
import { useFormik } from 'formik'
import { CreateUserSchema } from '~/configs/schemas'
import { useGenerateUsername } from '~/hooks/useGenerateUsername'

import SaveIcon from '~/assets/icons/save.svg'
import XCircleFilledIcon from '~/assets/icons/x-circle-filled.svg'
import Button from '~/components/common/Button'
import Input from '~/components/common/Input'
import Modal from '~/components/common/Modal'
import Radio from '~/components/common/Radio'

export interface CreateUserForm {
  company: 'linfox' | 'unilever'
  fullname: string
  phoneNumber: string
  username: string
  password: string
}

interface Props {
  open: boolean
  hasCompany?: boolean
  submitting: boolean
  onRequestClose: () => void
  onSubmit: (values: CreateUserForm) => void
}

export default function AddSingleUser({
  open,
  hasCompany,
  submitting,
  onRequestClose,
  onSubmit,
}: Readonly<Props>) {
  const form = useFormik<CreateUserForm>({
    initialValues: {
      company: 'linfox',
      fullname: '',
      phoneNumber: '',
      username: '',
      password: '',
    },
    validateOnBlur: true,
    validationSchema: CreateUserSchema,
    onSubmit: (values) => {
      const clonedValued = { ...values }
      clonedValued.fullname = clonedValued.fullname
        .split(' ')
        .map((word) => `${word.charAt(0).toUpperCase()}${word.slice(1).toLowerCase()}`)
        .join(' ')

      onSubmit(clonedValued)
    },
  })

  useGenerateUsername(
    form.values.fullname,
    form.values.phoneNumber,
    hasCompany ? form.values.company : undefined,
    {
      disabled: !!form.errors.fullname,
      onGenerate: (username) => {
        form.setFieldValue('username', username)
      },
    },
  )

  useEffect(() => {
    if (open) form.validateForm()

    return () => {
      if (open) form.resetForm()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open])

  const handleChangeCompany = (e: ChangeEvent<HTMLInputElement>) => {
    if (e.target.checked) {
      form.setValues({
        ...form.values,
        company: e.target.value as CreateUserForm['company'],
      })
    }
  }

  const handleInputChange = (e: ChangeEvent<HTMLInputElement>) => {
    if (e.target.name === 'phoneNumber') {
      let password = form.values.password
      if (!e.target.value || (e.target.value.startsWith('0') && /^[0-9]+$/.test(e.target.value)))
        password = e.target.value

      form.setValues({ ...form.values, password, phoneNumber: e.target.value })
    } else if (e.target.name === 'fullname') {
      const fullname = e.target.value
      form.setValues({ ...form.values, fullname: fullname })
    }
  }

  return (
    <Modal open={open} destroyOnHide onRequestClose={onRequestClose}>
      <div className="w-[400px]">
        <h2 className="font-semibold pt-0.5">THÊM LẺ</h2>
        <form className="mt-5 flex flex-col gap-4" onSubmit={form.handleSubmit}>
          {hasCompany && (
            <div className="flex items-center gap-3">
              <p className="text-[13px] font-semibold text-text-default-secondary">Công ty*</p>
              <Radio
                name="company"
                value="linfox"
                label="Linfox"
                checked={form.values.company === 'linfox'}
                classNames={{
                  label: form.values.company === 'linfox' ? 'font-semibold' : '',
                  dot: 'hidden',
                }}
                onChange={handleChangeCompany}
              />
              <Radio
                name="company"
                value="unilever"
                label="Unilever"
                checked={form.values.company === 'unilever'}
                classNames={{
                  label: form.values.company === 'unilever' ? 'font-semibold' : '',
                  dot: 'hidden',
                }}
                onChange={handleChangeCompany}
              />
            </div>
          )}
          <Input
            label="Họ và tên*"
            classnames={{
              wrapper: 'h-13',
              label: 'text-[13px] text-text-default-secondary',
            }}
            stackLabel={false}
            bubbleLabel
            placeholder=" "
            name="fullname"
            maxLength={100}
            error={form.errors.fullname}
            touched={form.touched.fullname}
            onChange={handleInputChange}
          />
          <Input
            name="phoneNumber"
            label="Số điện thoại*"
            classnames={{
              wrapper: 'h-13',
              label: 'text-[13px] text-text-default-secondary',
            }}
            stackLabel={false}
            bubbleLabel
            placeholder=" "
            error={form.errors.phoneNumber}
            touched={form.touched.phoneNumber}
            maxLength={10}
            onChange={handleInputChange}
          />
          <Input
            label="Tên người dùng"
            classnames={{
              wrapper: 'h-13',
              label: 'text-[13px] text-text-default-secondary',
              labelWrapper: 'bg-transparent',
            }}
            stackLabel={false}
            bubbleLabel
            placeholder=" "
            disabled
            value={form.values.username}
          />
          <Input
            label="Mật khẩu"
            classnames={{
              wrapper: 'h-13',
              label: 'text-[13px] text-text-default-secondary',
              labelWrapper: 'bg-transparent',
            }}
            stackLabel={false}
            bubbleLabel
            placeholder=" "
            disabled
            value={form.values.password}
          />
        </form>
        <div className="flex items-center justify-end gap-3 mt-8">
          <Button
            outline
            className="text-[#FF5630] border-current w-fit text-sm gap-2 px-2.5 h-9"
            disabled={submitting}
            onClick={onRequestClose}
          >
            <XCircleFilledIcon className="text-base" /> Hủy
          </Button>
          <Button
            className="w-fit text-sm gap-2 px-2.5 h-9 bg-blue-secondary disabled:bg-[#F1F3F9] disabled:opacity-100 disabled:text-[#8498B2]"
            loading={submitting}
            onClick={form.submitForm}
          >
            <SaveIcon className="text-base" />
            Thêm
          </Button>
        </div>
      </div>
    </Modal>
  )
}
