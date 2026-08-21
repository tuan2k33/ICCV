from datetime import datetime
from enum import Enum


class Role(str, Enum):
    ENTRY_1 = 'ENTRY_1'
    ENTRY_2 = 'ENTRY_2'
    CHECKER = 'CHECKER'


class DeliveryTask:
    def __init__(self, task: dict):
        self._id = task.get("id")  # bigint

        # user
        self._user_e1 = task.get("user_e1")
        self._user_e2 = task.get("user_e2")
        self._user_c = task.get("user_c")

        # result
        self._result_e1 = task.get("result_e1")
        self._result_e2 = task.get("result_e2")
        self._result_c = task.get("result_c")

        # time process
        self._time_process_e1 = task.get("time_process_e1")
        self._time_process_e2 = task.get("time_process_e2")
        self._time_process_c = task.get("time_process_c")

        # mark confirm
        self._flags_e1 = task.get("flags_e1")
        self._flags_e2 = task.get("flags_e2")
        self._flags_c = task.get("flags_c")

        # time submit
        self._time_submit_e1 = task.get("time_submit_e1")
        self._time_submit_e2 = task.get("time_submit_e2")
        self._time_submit_c = task.get("time_submit_c")

        self._release = False

        # mapping
        self._field_mapping = {
            'user_e1': {
                'result': 'result_e1',
                'time_submit': 'time_submit_e1',
                'time_process': 'time_process_e1',
                'flags': 'flags_e1'
            },
            'user_e2': {
                'result': 'result_e2',
                'time_submit': 'time_submit_e2',
                'time_process': 'time_process_e2',
                'flags': 'flags_e2'
            },
            'user_c': {
                'result': 'result_c',
                'time_submit': 'time_submit_c',
                'time_process': 'time_process_c',
                'flags': 'flags_c'
            },
        }
        self._role_to_field = {
            Role.ENTRY_1: 'user_e1',
            Role.ENTRY_2: 'user_e2',
            Role.CHECKER: 'user_c',
        }

    def to_dict(self):
        return {
            "id": self._id,
            "user_e1": self._user_e1,
            "user_e2": self._user_e2,
            "user_c": self._user_c,
            "result_e1": self._result_e1,
            "result_e2": self._result_e2,
            "result_c": self._result_c,
            "time_process_e1": self._time_process_e1,
            "time_process_e2": self._time_process_e2,
            "time_process_c": self._time_process_c,
            "time_submit_e1": self._time_submit_e1,
            "time_submit_e2": self._time_submit_e2,
            "time_submit_c": self._time_submit_c,
            "flags_e1": self._flags_e1,
            "flags_e2": self._flags_e2,
            "release": self._release,
        }

    def dict_et1(self):
        return {
            "id": self._id,
            "user_e1": self._user_e1,
            "result_e1": self._result_e1,
            "time_process_e1": self._time_process_e1,
            "time_submit_e1": self._time_submit_e1,
            "flags_e1": self._flags_e1,
            "release": self._release,
        }

    def dict_et2(self):
        return {
            "id": self._id,
            "user_e1": self._user_e2,
            "result_e1": self._result_e2,
            "time_process_e1": self._time_process_e2,
            "time_submit_e1": self._time_submit_e2,
            "flags_e1": self._flags_e2,
            "release": self._release,
        }

    def dict_c(self):
        return {
            "id": self._id,
            "user_e1": self._user_c,
            "result_e1": self._result_c,
            "time_process_e1": self._time_process_c,
            "time_submit_e1": self._time_submit_c,
            "release": self._release,
        }

    def _get_my_fields(self, user: dict):
        role = user.get("role", None)
        user_field = self._role_to_field.get(role)
        if not user_field:
            return None

        related = self._field_mapping[user_field]
        return {
            'user_field': user_field,
            'result_field': related['result'],
            'time_field': related['time_submit'],
            'time_process_field': related['time_process'],
            'flags_field': related['flags']
        }

    def assign_task(self, user: dict):
        my = self._get_my_fields(user)
        if my is None:
            raise ValueError("User role not allowed")

        cur = getattr(self, f"_{my['user_field']}")
        if cur and cur != user.get("id"):
            raise ValueError("This slot already assigned")

        setattr(self, f"_{my['user_field']}", user.get("id"))
        return self.to_dict()

    def _update_time_submit(self, user: dict):
        my = self._get_my_fields(user)
        if my is None:
            raise ValueError("User is not assigned to this task")
        setattr(self, f"_{my['time_field']}", datetime.now())

    def _release_task(self):
        self._result_c = self._result_e1
        self._release = True

    def compare_result(self, user: dict):
        if self._result_e1 is None or self._result_e2 is None:
            return
        if self._result_e1 == self._result_e2:
            self._release_task()

    def update_result(self, user: dict, result_data: dict):
        my = self._get_my_fields(user)
        if my is None:
            raise ValueError("User is not assigned to this task")

        setattr(self, f"_{my['result_field']}", result_data)

        if my['user_field'] == 'user_c':
            self._release = True

        self._update_time_submit(user)
        self.compare_result(user)

    def update_time_process(self, user: dict, process_data: dict):
        my = self._get_my_fields(user)
        if my is None:
            raise ValueError("User is not assigned to this task")
        cur = getattr(self, f"_{my['time_process_field']}") or {}
        cur.update(process_data)
        setattr(self, f"_{my['time_process_field']}", cur)

    def update_flags(self, user: dict, process_data: dict):
        my = self._get_my_fields(user)
        if my is None:
            raise ValueError("User is not assigned to this task")
        cur = getattr(self, f"_{my['flags_field']}") or {}
        if not isinstance(cur, dict):
            cur = {}
        cur.update(process_data)
        setattr(self, f"_{my['flags_field']}", cur)

    def update_result_mini(self, user: dict, keys: list, values: list):
        my = self._get_my_fields(user)
        if my is None:
            raise ValueError("User is not assigned to this task")
        cur = getattr(self, f"_{my['result_field']}") or {}
        if not isinstance(cur, dict):
            cur = {}
        for k, v in zip(keys, values):
            try:
                current_data = eval("cur" + k)
                current_data.update(v)
            except Exception:
                raise ValueError("Invalid result key")

        setattr(self, f"_{my['result_field']}", cur)
