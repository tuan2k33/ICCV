import { array, object, string } from 'yup'
import { axiosInstance } from '~/utils/axiosInstance'
import { formatString } from '~/utils/formatString'
import { PhoneNumberStore } from '~/classStore/PhoneNumberStore'
import { endpoints } from './endpoints'

export const errorMessage = {
  onlyNumber: 'Chỉ được nhập số',
  maxLengthNumber: 'Tối đa {max} số',
  notInputYet: 'Chưa nhập giá trị',
  mustEnoughNumberLength: 'Phải nhập đủ {length} số',
}

export const LoginSchema = object({
  username: string().trim().required('Username is required'),
  password: string()
    .min(6, 'Password must be at least 6 characters')
    .required('Password is required'),
})

const LayerCountSchema = string()
  .test({
    name: 'only-number-rule',
    message: errorMessage.onlyNumber,
    test: (value) => !value || /^\d+$/.test(value),
  })
  .max(
    2,
    formatString(errorMessage.maxLengthNumber, {
      max: 2,
    }),
  )
  .test({
    name: 'option',
    message: errorMessage.notInputYet,
    test(value, context) {
      if (context.path.startsWith('double_deep')) {
        const prefix = context.path.split('.')[1].split('_')[0] + '_'
        if (!context.parent[`${prefix}total`]) return !!value
        return !context.parent[`${prefix}top_layer_product_count`] || !!value
      }

      if (!context.parent.total) return !!value
      return !context.parent.top_layer_product_count || !!value
    },
  })

const TopLayerProductCountSchema = string()
  .test({
    name: 'only-number-rule',
    message: errorMessage.onlyNumber,
    test: (value) => !value || /^\d+$/.test(value),
  })
  .max(
    2,
    formatString(errorMessage.maxLengthNumber, {
      max: 2,
    }),
  )
  .test({
    name: 'option',
    message: errorMessage.notInputYet,
    test(value, context) {
      if (context.path.startsWith('double_deep')) {
        const prefix = context.path.split('.')[1].split('_')[0] + '_'
        if (!context.parent[`${prefix}total`]) return !!value
        return !context.parent[`${prefix}layer_count`] || !!value
      }
      if (!context.parent.total) return !!value
      return !context.parent.layer_count || !!value
    },
  })

const MissingOnLayerSchema = array().of(
  string().test({
    name: 'only-number-rule',
    message: errorMessage.onlyNumber,
    test: (value) => !value || /^\d+$/.test(value),
  }),
)

const TotalSchema = string()
  .required(errorMessage.notInputYet)
  .test({
    name: 'only-number-rule',
    message: errorMessage.onlyNumber,
    test: (value) => /^\d+$/.test(value),
  })
  .max(
    4,
    formatString(errorMessage.maxLengthNumber, {
      max: 4,
    }),
  )

export const SingleDeepEntrySchema = object({
  layer_count: LayerCountSchema,
  top_layer_product_count: TopLayerProductCountSchema,
  missing_on_layer: MissingOnLayerSchema,
  total: TotalSchema,
})

export const DoubleDeepEntrySchema = object({
  outer_layer_count: LayerCountSchema,
  outer_top_layer_product_count: TopLayerProductCountSchema,
  outer_missing_on_layer: MissingOnLayerSchema,
  outer_total: TotalSchema,

  inner_layer_count: LayerCountSchema,
  inner_top_layer_product_count: TopLayerProductCountSchema,
  inner_missing_on_layer: MissingOnLayerSchema,
  inner_total: TotalSchema,
})

export const EntrySchema = object({
  location: string()
    .required(errorMessage.notInputYet)
    .test({
      name: 'only-number-rule',
      message: errorMessage.onlyNumber,
      test: (value) => {
        return /^\d+$/.test(value.replaceAll('-', ''))
      },
    })
    .test({
      name: 'length-rule',
      message: formatString(errorMessage.mustEnoughNumberLength, {
        length: 4,
      }),
      test: (value) => {
        return value.replaceAll('-', '').length === 4
      },
    }),

  product_id: string()
    .test({
      name: 'require-rule',
      message: formatString(errorMessage.mustEnoughNumberLength, {
        length: 8,
      }),
      test: (value, context) => {
        const isEmpty =
          context.parent.single_deep.status === 'empty' ||
          (context.parent.double_deep.inner_status === 'empty' &&
            context.parent.double_deep.outer_status === 'empty')

        if (context.parent.confirm_reason || !context.parent._origin_product_id || isEmpty)
          return true
        return !!value?.length
      },
    })
    .test({
      name: 'only-number-rule',
      message: errorMessage.onlyNumber,
      test: (value) => !value || /^\d+$/.test(value),
    })
    .test({
      name: 'length-rule',
      message: formatString(errorMessage.mustEnoughNumberLength, {
        length: 8,
      }),
      test: (value, context) => {
        const isEmpty =
          context.parent.single_deep.status === 'empty' ||
          (context.parent.double_deep.inner_status === 'empty' &&
            context.parent.double_deep.outer_status === 'empty')

        if (context.parent.confirm_reason || !context.parent._origin_product_id || isEmpty)
          return true
        return value?.length === 8
      },
    }),
  single_deep: SingleDeepEntrySchema,
  double_deep: DoubleDeepEntrySchema,
})

export const OtherReasonConfirmEntrySchema = object({
  other_reason: string().required(errorMessage.notInputYet),
})

const createUserErrorMessage = {
  nameLength: 'Vui lòng nhập tối thiểu 2 ký tự để tạo username.',
  invalidFormat: 'Không đúng định dạng',
  invalidPhone: 'Số điện thoại phải gồm 10 chữ số, bắt đầu bằng 0.',
  existedPhoneNumber: 'Số điện thoại trùng với user khác',
}

// support Vietnamese
const fullnameRegex = /^[a-zA-Z\u00C0-\u024F\u1E00-\u1EFF]+( [a-zA-Z\u00C0-\u024F\u1E00-\u1EFF]+)*$/

const FullnameSchema = string()
  .required(createUserErrorMessage.nameLength)
  .min(2, createUserErrorMessage.nameLength)
  .matches(fullnameRegex, {
    message: createUserErrorMessage.invalidFormat,
  })

export const CreateUserSchema = object({
  fullname: FullnameSchema,
  phoneNumber: string()
    .required(createUserErrorMessage.invalidPhone)
    .length(10, createUserErrorMessage.invalidPhone)
    .test({
      name: 'phone-number',
      message: createUserErrorMessage.invalidPhone,
      test: (value) => value.startsWith('0') && /^[0-9]+$/.test(value),
    })
    .test({
      name: 'check-existed-phone-number',
      message: createUserErrorMessage.existedPhoneNumber,
      test: async (value) => {
        if (value.length !== 10 || !(value.startsWith('0') && /^[0-9]+$/.test(value))) return false
        return isPhoneNumberExist(value)
      },
    }),
})

export const UpdateUserSchema = object({
  fullname: FullnameSchema,
  phoneNumber: string()
    .required(createUserErrorMessage.invalidPhone)
    .length(10, createUserErrorMessage.invalidPhone)
    .test({
      name: 'phone-number',
      message: createUserErrorMessage.invalidPhone,
      test: (value) => value.startsWith('0') && /^[0-9]+$/.test(value),
    })
    .test({
      name: 'check-existed-phone-number',
      message: createUserErrorMessage.existedPhoneNumber,
      test: async (value, context) => {
        if (value.length !== 10 || !(value.startsWith('0') && /^[0-9]+$/.test(value))) return false
        return await isPhoneNumberExist(value, context.parent.id)
      },
    }),
})

const isPhoneNumberExist = async (phoneNumber: string, userId?: number) => {
  if (PhoneNumberStore.has(phoneNumber)) {
    if (userId) return PhoneNumberStore.get(phoneNumber) === userId
    return false
  }
  try {
    const response = await axiosInstance.get<string[]>(endpoints.AUTH_CHECK_EXIST_PHONE_NUMBER, {
      params: {
        phone_numbers: phoneNumber,
      },
    })
    if (response.data.includes(phoneNumber)) {
      PhoneNumberStore.set(phoneNumber, '_')
      return false
    }
  } catch {
    //
  }
  return true
}
