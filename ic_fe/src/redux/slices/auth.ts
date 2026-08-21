import { createAsyncThunk, createSlice, type PayloadAction } from '@reduxjs/toolkit'
import type { User } from '~/types/auth'
import { endpoints } from '~/configs/endpoints'
import { axiosInstance } from '~/utils/axiosInstance'
import { UsernameStore } from '~/classStore/UsernameStore'
import { actionThunkGetActiveBatch } from './app'

interface AuthState {
  loading: boolean
  user: User | null
  selectedRole: string | null
}

const initialState: AuthState = {
  loading: true,
  user: null,
  selectedRole: null,
}

export const actionThunkGetMe = createAsyncThunk('auth/getMe', async (_, { dispatch }) => {
  const response = await axiosInstance.get(endpoints.AUTH_ME)
  dispatch(actionThunkGetActiveBatch((response.data as User).tenant_id))
  return response.data as User
})

const authSlice = createSlice({
  name: 'auth',
  initialState,
  reducers: {
    actionLogin: (state, action: PayloadAction<User>) => {
      state.user = action.payload
    },
    actionLogout: (state) => {
      state.user = null
      state.selectedRole = null
      UsernameStore.clear()
    },
    actionSetSelectedRole: (state, action: PayloadAction<string | null>) => {
      state.selectedRole = action.payload
    },
  },
  extraReducers: (builder) => {
    builder.addCase(actionThunkGetMe.pending, (state) => {
      state.loading = true
    })
    builder.addCase(actionThunkGetMe.fulfilled, (state, action) => {
      state.user = action.payload
      state.loading = false
    })
    builder.addCase(actionThunkGetMe.rejected, (state) => {
      state.loading = false
    })
  },
})

export const { actionLogin, actionLogout, actionSetSelectedRole } = authSlice.actions
export default authSlice.reducer
