const getEndPoint = <T extends Record<string, string>>(baseURL: string, subEndpoint: T) => {
  for (const key in subEndpoint) {
    subEndpoint[key] = `/${baseURL}/${subEndpoint[key]}` as T[Extract<keyof T, string>]
  }

  return subEndpoint
}

export const endpoints = getEndPoint('api', {
  AUTH_LOGIN: 'auth/login',
  AUTH_LOGOUT: 'auth/logout',
  AUTH_ME: 'auth/me',
  AUTH_REGISTER: 'auth/register',
  AUTH_IMPORT_USERS: 'auth/import_users',
  AUTH_CHECK_EXIST_USERNAME: 'auth/check_exist_username',
  AUTH_CHECK_EXIST_PHONE_NUMBER: 'auth/check_exist_phone_number',

  ASSIGN_TASK: 'task/assign_task',
  SUBMIT_TASK: 'task/{task_id}/submit_task',
  MY_TASKS: 'task/my_tasks',
  GET_TASK_BY_ID: 'task/{id}',
  TASK_FLAG: 'task/{id}/flag',
  TASK_TIME_PROCESS_TASK: 'task/{id}/time_process_task',
  TASK_START_WORKING: 'task/{task_id}/start_working',
  TASK_EXPORT_DATA: 'task/export_data',

  UPLOADER: 'uploader',

  BATCH: 'batch',
  BATCH_PREVIEW: 'batch/preview',
  BATCH_ACTIVE: 'batch/active',

  TENANT_INFORMATION_RACKS: 'tenant/{tenant_id}/information/racks',

  COUNTING_GROUP: 'counting_group',
  COUNTING_GROUP_RANDOM: 'counting_group/random',
  COUNTING_GROUP_EXPORT: 'counting_group/export',
  COUNTING_GROUP_SUBMIT: 'counting_group/submit',
  COUNTING_GROUP_MOVE_RACK: 'counting_group/move_rack',
  COUNTING_GROUP_CHANGE_USER_IN_GROUP: 'counting_group/change_user_in_group',

  USER: 'user',
  USER_DELETE_USERS: 'user/delete_users',
  USER_UPDATE: 'user/{user_id}',
  USER_FETCH_ALL: 'user/fetch_all_users',
})
