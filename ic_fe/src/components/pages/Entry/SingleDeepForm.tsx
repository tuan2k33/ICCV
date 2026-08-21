import { useEffect, useRef, type ChangeEvent, type ReactElement } from 'react'
import { useFormik, type FormikErrors } from 'formik'
import { useSelector } from 'react-redux'
import type { PalletStatus } from '~/types/task'
import type { RootState } from '~/redux'
import MinusCircle from '~/assets/icons/minus-circle.svg'
import PlusCircleIcon from '~/assets/icons/plus-circle.svg'
import CheckBox from '~/components/common/CheckBox'
import Input from '~/components/common/Input'
import { fakeFullData, type FormValues } from '.'

interface Props {
  form: ReturnType<typeof useFormik<FormValues>>
  submitButton: ReactElement
  onInputChange: (e: ChangeEvent<HTMLInputElement>) => void
  focusSubmitButton: (delay?: number) => void
}

export default function SingleDeepForm({
  form,
  submitButton,
  onInputChange,
  focusSubmitButton,
}: Readonly<Props>) {
  const missingOnLayerWrapperRef = useRef<HTMLDivElement>(null)
  const { user } = useSelector((state: RootState) => state.auth)

  useEffect(() => {
    let isCalculateAble = true

    if (Object.keys(form.errors).some((key) => key.startsWith('single_deep.missing_on_layer')))
      isCalculateAble = false

    if (isCalculateAble) {
      if (
        form.errors['single_deep.layer_count' as keyof FormikErrors<FormValues>] ||
        form.errors['single_deep.top_layer_product_count' as keyof FormikErrors<FormValues>]
      )
        isCalculateAble = false
    }

    if (
      isCalculateAble &&
      (!form.values.single_deep.layer_count || !form.values.single_deep.top_layer_product_count)
    )
      isCalculateAble = false

    if (isCalculateAble) {
      const layer_count = Number(form.values.single_deep.layer_count),
        top_layer_product_count = Number(form.values.single_deep.top_layer_product_count),
        missingOnLayerCount = form.values.single_deep.missing_on_layer.reduce(
          (prev, item) => prev + Number(item) || 0,
          0,
        )

      const total = layer_count * top_layer_product_count + missingOnLayerCount

      form.setFieldValue('single_deep.total', total + '')
    } else {
      const activeElement = document.activeElement
      if (
        (!(activeElement instanceof HTMLInputElement) ||
          activeElement.name !== 'single_deep.total') &&
        (form.errors['single_deep.layer_count' as keyof FormikErrors<FormValues>] ||
          form.errors['single_deep.top_layer_product_count' as keyof FormikErrors<FormValues>])
      ) {
        form.setFieldValue('single_deep.total', '')
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [form.values, form.errors])

  const handleInsertNewMissingField = () => {
    form.setFieldValue(
      'single_deep.missing_on_layer',
      [...form.values.single_deep.missing_on_layer, ''],
      false,
    )
    setTimeout(() => {
      missingOnLayerWrapperRef.current?.scrollTo({
        left: missingOnLayerWrapperRef.current.scrollWidth,
        behavior: 'smooth',
      })
    }, 100)
  }

  const handleChangeStatus = (status: PalletStatus, checked: boolean) => {
    let payload: Record<string, unknown>

    if (!checked)
      payload = {
        status: null,
        layer_count: '',
        top_layer_product_count: '',
        missing_on_layer: ['0'],
        total: '',
      }
    else if (status === 'full') {
      payload = {
        status: status,
        layer_count: fakeFullData.layer,
        top_layer_product_count: fakeFullData.layerProduct,
        missing_on_layer: ['0'],
        total: fakeFullData.total,
      }
    } else {
      payload = {
        status: status,
        layer_count: '0',
        top_layer_product_count: '0',
        missing_on_layer: ['0'],
        total: '0',
      }
    }

    form.setFieldValue('single_deep', payload)
    if (checked) focusSubmitButton(100)
  }

  const editable = user?.company !== 'Linfox'

  return (
    <div className="flex items-center gap-6">
      <div className="flex items-center gap-6">
        <CheckBox
          label="Trống"
          checked={form.values.single_deep.status === 'empty'}
          classNames={{
            wrapper: 'flex-col-reverse w-23 gap-0',
          }}
          disabled={!editable}
          onChange={(e) => handleChangeStatus('empty', e.target.checked)}
        />

        {!form.values.single_deep.status && (
          <>
            <Input
              label="SL lớp đầy"
              className="w-19 text-base"
              classnames={{
                label: 'text-sm',
              }}
              placeholder={editable ? 'Nhập' : ''}
              name="single_deep.layer_count"
              autoFocus
              value={form.values.single_deep.layer_count}
              touched={form.touched.single_deep?.layer_count}
              errorStatusWithOutMessage={
                !!form.errors['single_deep.layer_count' as keyof FormikErrors<FormValues>]
              }
              readOnly={!editable}
              onChange={onInputChange}
            />
            <Input
              label="SL thùng/lớp đầy"
              className="w-31 text-base"
              classnames={{
                label: 'text-sm',
              }}
              placeholder={editable ? 'Nhập' : ''}
              name="single_deep.top_layer_product_count"
              value={form.values.single_deep.top_layer_product_count}
              touched={form.touched.single_deep?.top_layer_product_count}
              errorStatusWithOutMessage={
                !!form.errors[
                  'single_deep.top_layer_product_count' as keyof FormikErrors<FormValues>
                ]
              }
              readOnly={!editable}
              onChange={onInputChange}
            />
            <div
              className="overflow-x-auto max-w-[304px] scrollbar-xs -mt-4 pt-3 pb-1 -mb-2"
              ref={missingOnLayerWrapperRef}
            >
              <div className="flex items-center gap-6 w-fit">
                {form.values.single_deep.missing_on_layer.map((val, index) => (
                  <Input
                    key={index + ''}
                    name={`single_deep.missing_on_layer[${index}]`}
                    label={`SL thùng/lớp lẻ ${form.values.single_deep.missing_on_layer.length > 1 ? index + 1 : ''}`}
                    className="text-base"
                    classnames={{
                      wrapper: 'w-35',
                      label: 'text-sm',
                    }}
                    placeholder={editable ? '0' : ''}
                    touched={form.touched.single_deep?.missing_on_layer}
                    errorStatusWithOutMessage={
                      !!form.errors[
                        `single_deep.missing_on_layer[${index}]` as keyof FormikErrors<FormValues>
                      ]
                    }
                    tabIndex={
                      index === 0 &&
                      form.values.single_deep.missing_on_layer.length === 1 &&
                      form.values.single_deep.missing_on_layer[index] + '' === '0'
                        ? -1
                        : undefined
                    }
                    value={val}
                    readOnly={!editable}
                    onChange={onInputChange}
                  />
                ))}
              </div>
            </div>

            {form.values.single_deep.missing_on_layer.length > 1 && editable && (
              <button
                className="text-xl -ml-2 cursor-pointer"
                type="button"
                onClick={() => {
                  const newValues = [...form.values.single_deep.missing_on_layer]
                  newValues.splice(-1)
                  form.setFieldValue('single_deep.missing_on_layer', newValues, false)
                }}
              >
                <MinusCircle />
              </button>
            )}

            {editable && (
              <button
                className="text-xl -ml-4 cursor-pointer disabled:cursor-not-allowed disabled:opacity-60"
                type="button"
                onClick={handleInsertNewMissingField}
              >
                <PlusCircleIcon />
              </button>
            )}
            <Input
              name="single_deep.total"
              label="Tổng"
              className="w-14 text-base"
              classnames={{
                label: 'text-sm',
              }}
              value={form.values.single_deep.total}
              touched={form.touched.single_deep?.total}
              errorStatusWithOutMessage={
                !!form.errors['single_deep.total' as keyof FormikErrors<FormValues>]
              }
              onChange={onInputChange}
            />
          </>
        )}
      </div>
      {submitButton}
    </div>
  )
}
