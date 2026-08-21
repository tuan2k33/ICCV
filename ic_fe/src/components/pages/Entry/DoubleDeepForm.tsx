import { useEffect, useMemo, type ChangeEvent, type ReactElement } from 'react'
import type { useFormik } from 'formik'
import DoubleDeepBaseForm from './DoubleDeepBaseForm'
import type { FormValues } from '.'

interface Props {
  form: ReturnType<typeof useFormik<FormValues>>
  submitButton: ReactElement
  showErrorToast: (message: string) => void
  onInputChange: (e: ChangeEvent<HTMLInputElement>) => void
  focusSubmitButton: (delay?: number) => void
}

export default function DoubleDeepForm({ submitButton, ...props }: Readonly<Props>) {
  const allowFullCheckInnerDeep = useMemo(() => {
    for (const errorKey in props.form.errors) {
      if (!Object.hasOwn(props.form.errors, errorKey)) continue
      if (errorKey.includes('outer_')) return 'disable'
    }

    if (
      props.form.values.double_deep.outer_status !== 'empty' &&
      props.form.values.double_deep.outer_missing_on_layer.every((value) => !Number(value))
    )
      return true

    return 'disable'
  }, [props.form])

  useEffect(() => {
    if (
      (!allowFullCheckInnerDeep || allowFullCheckInnerDeep === 'disable') &&
      props.form.values.double_deep.inner_status === 'full'
    )
      props.form.setFieldValue('double_deep.inner_status', null)
  }, [allowFullCheckInnerDeep, props.form])

  return (
    <div className="flex items-center gap-[50px]">
      <div className="flex flex-col gap-5 shrink-0">
        <DoubleDeepBaseForm prefix="outer_" label="Pallet ngoài" autoFocus {...props} />
        <DoubleDeepBaseForm
          prefix="inner_"
          label="Pallet Trong"
          allowFullCheck={allowFullCheckInnerDeep}
          {...props}
        />
      </div>
      {submitButton}
    </div>
  )
}
