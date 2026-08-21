import { type ReactElement, type RefObject } from 'react'
import { useSelector } from 'react-redux'
import type { useFormik } from 'formik'
import type { RootState } from '~/redux'
import Radio from '~/components/common/Radio'
import Input from '~/components/common/Input'
import { confirmOptions, type FormValues } from '.'

interface Props {
  form: ReturnType<typeof useFormik<FormValues>>
  formRef: RefObject<HTMLElement | null>
  submitButton: ReactElement
}

export default function ConfirmForm({ form, formRef, submitButton }: Readonly<Props>) {
  const { user } = useSelector((state: RootState) => state.auth)
  const editable = user?.company !== 'Linfox'

  return (
    <div className="flex items-center gap-5 min-h-10">
      <div className="flex flex-wrap gap-x-3">
        {confirmOptions.map((item) => (
          <Radio
            key={item.value}
            name="confirm_reason"
            value={item.value}
            label={item.label}
            checked={item.value === form.values.confirm_reason}
            disabled={!editable}
            onChange={() => {
              form.setFieldValue('confirm_reason', item.value)
              setTimeout(() => {
                ;(
                  (formRef.current?.querySelector(
                    'input[name="other_reason"]',
                  ) as HTMLInputElement) || null
                )?.focus()
              }, 100)
            }}
          />
        ))}

        {form.values.confirm_reason === 'other' && (
          <Input
            name="other_reason"
            placeholder={editable ? 'Nhập lý do khác' : ''}
            value={form.values.other_reason}
            touched={form.touched.other_reason}
            errorStatusWithOutMessage={!!form.errors.other_reason}
            readOnly={!editable}
            onChange={form.handleChange}
          />
        )}
      </div>
      {submitButton}
    </div>
  )
}
