import { createAsyncThunk, createSlice } from '@reduxjs/toolkit'
import { API_URL } from '~/configs/constants'
import { endpoints } from '~/configs/endpoints'
import { axiosInstance } from '~/utils/axiosInstance'

export const actionThunkGetActiveBatch = createAsyncThunk(
  'app/getActiveBatch',
  async (tenantId: number) => {
    const response = await axiosInstance.get<{ data: number }>(endpoints.BATCH_ACTIVE, {
      params: {
        tenant_id: tenantId,
      },
    })
    return response.data.data
  },
)

const appSlice = createSlice({
  name: 'app',
  initialState: {
    webSocket: null as WebSocket | null,
    loadingBatch: false,
    batch: null as number | null,
  },
  reducers: {
    actionRegisterWebSocket: (state) => {
      const { host, protocol } = new URL(API_URL)

      const wsProtocol = protocol.replace('http', 'ws')
      const socket = new WebSocket(`${wsProtocol}//${host}/ws`)

      state.webSocket = socket
    },
    actionUnregisterWebSocket: (state) => {
      state.webSocket?.close()
      state.webSocket = null
    },
  },
  extraReducers(builder) {
    builder.addCase(actionThunkGetActiveBatch.pending, (state) => {
      state.loadingBatch = true
    })
    builder.addCase(actionThunkGetActiveBatch.fulfilled, (state, action) => {
      state.batch = action.payload
      state.loadingBatch = false
    })
    builder.addCase(actionThunkGetActiveBatch.rejected, (state) => {
      state.loadingBatch = false
    })
  },
})

export const { actionRegisterWebSocket, actionUnregisterWebSocket } = appSlice.actions

export default appSlice.reducer
