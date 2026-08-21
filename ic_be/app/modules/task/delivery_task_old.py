from datetime import datetime, timedelta
from enum import Enum


class Role(str, Enum):
    ENTRY = 'ENTRY'
    CHECKER = 'CHECKER'


class DeliveryTask:
    def __init__(self, task):
        self.id = task.id  # bigint
        self.user_e1 = task.user_e1  # bigint
        self.user_e2 = task.user_e2  # bigint
        self.user_c = task.user_c  # bigint
        self.end_time_e1 = task.end_time_e1  # datetime
        self.end_time_e2 = task.end_time_e2  # datetime
        self.end_time_c = task.end_time_c  # datetime
        self.result_e1 = task.result_e1  # json
        self.result_e2 = task.result_e2  # json
        self.result_c = task.result_c  # json
        self.time_submit = task.time_submit
        self.release = False  # boolean

        # Mapping user fields with end_time and result
        self.field_mapping = {
            'user_e1': {'end_time': 'end_time_e1', 'result': 'result_e1', 'duration': 3},
            'user_e2': {'end_time': 'end_time_e2', 'result': 'result_e2', 'duration': 3},
            'user_c': {'end_time': 'end_time_c', 'result': 'result_c', 'duration': 5}
        }

    def get_task_info(self):
        return self

    def dict(self):
        return {
            "task_id": self.id,
            "user_e1": self.user_e1,
            "user_e2": self.user_e2,
            "user_c": self.user_c,
            "end_time_e1": self.end_time_e1,
            "end_time_e2": self.end_time_e2,
            "end_time_c": self.end_time_c,
            "result_e1": self.result_e1,
            "result_e2": self.result_e2,
            "result_c": self.result_c,
            "time_submit": getattr(self, 'time_submit', {}),
            "release": self.release,
        }

    def _get_my_fields(self, user):
        """Return field names corresponding to the current user"""
        for user_field, related_fields in self.field_mapping.items():
            if getattr(self, user_field) == user.id:
                return {
                    'user_field': user_field,
                    'end_time_field': related_fields['end_time'],
                    'result_field': related_fields['result'],
                    'duration': related_fields['duration']
                }
        return None

    def _assign_as_entry(self, user):
        if self.user_e1 is None or self.user_e1:
            self.user_e1 = user.id
        elif self.user_e2 is None or self.user_e2:
            self.user_e2 = user.id
        else:
            raise ValueError("Task already has someone assigned")

    def _assign_as_checker(self, user):
        self.user_c = user.id

    def _update_time_submit(self, user):
        """
        Update time_submit with current time for specific user
        :return:
        """
        my_fields = self._get_my_fields(user)
        if my_fields is None:
            raise ValueError("User is not assigned to this task")

        current_time = datetime.now()

        # Update time_submit in format user_field: datetime
        if not hasattr(self, 'time_submit') or self.time_submit is None:
            self.time_submit = {}
        if not isinstance(self.time_submit, dict):
            self.time_submit = {}

        self.time_submit[my_fields['user_field']] = current_time

    def _release_task(self):
        """
        Get comparison result of result_e1 vs result_e2 and assign to result_c
        """

        self.result_c = self.result_e1
        self.result_c = self.result_e1
        self.release = True
        print("Release")

    def _check_time_expired(self, user):
        my_fields = self._get_my_fields(user)
        if my_fields is None:
            raise ValueError("User is not assigned to this task")

        # Get actual end_time value for user
        end_time_value = getattr(self, my_fields['end_time_field'])
        current_time = datetime.now() + timedelta(minutes=2, seconds=59)
        return current_time > end_time_value

    def _reassign_task(self, user):
        """
        Check which task the user is currently working on, user_e1 or user_e2, then set value to None
        """
        my_fields = self._get_my_fields(user)
        if my_fields is None:
            raise ValueError("User is not assigned to this task")

        # Reset all related fields in task object
        setattr(self, my_fields['user_field'], None)
        setattr(self, my_fields['end_time_field'], None)
        setattr(self, my_fields['result_field'], None)

    def assign_task(self, user):
        """
        Role: ENTRY
            Check if task.user_e1 or task.user_e2 is available, then assign user to task.user_e1 or task.user_e2
            If task.user_e1 or task.user_e2 equals user, raise error - cannot do the same task twice
            If both task.user_e1 and task.user_e2 are occupied, raise error - task already has someone assigned
        Role: CHECKER
            If no one is assigned yet, assign to that person, otherwise raise error - already exists
        """

        if user.role == Role.ENTRY:
            self._assign_as_entry(user)
        elif user.role == Role.CHECKER:
            self._assign_as_checker(user)
        else:
            raise ValueError("Invalid role")
        self.update_time_for_task(user)

    def update_time_for_task(self, user):
        """
        If user_e1, update end_time_e1 = current time + 3 minutes
        If user_e2, update end_time_e2 = current time + 3 minutes
        If user_c, update end_time_c = current time + 5 minutes
        """
        my_fields = self._get_my_fields(user)
        if my_fields is None:
            raise ValueError("User is not assigned to this task")

        current_time = datetime.now()
        new_time = current_time + timedelta(minutes=my_fields['duration'])
        setattr(self, my_fields['end_time_field'], new_time)

    def compare_result(self, user):
        """
        If current user is user_e1, compare with user_e2 (result_e1 vs result_e2)
        If current user is user_e2, compare with user_e1 (result_e2 vs result_e1)
        If they match, call release_task and return True, else False
        :return:
        """
        my_fields = self._get_my_fields(user)
        if my_fields is None:
            raise ValueError("User is not assigned to this task")

        # Check if both results are available
        if self.result_e1 is None or self.result_e2 is None:
            print("Not enough results to compare")
            return

        # Compare results
        if self.result_e1 == self.result_e2:
            self._release_task()
            print("Match")

    def update_result(self, user, result_data):
        """
        If user_e1, update result for result_e1
        If user_e2, update result for result_e2
        If user_c, update result for result_c
        :return:
        """
        my_fields = self._get_my_fields(user)
        if my_fields is None:
            raise ValueError("User is not assigned to this task")

        # Check time expire for task
        if self._check_time_expired(user):
            self._reassign_task(user)
            raise ValueError("Submitted past the deadline")

            # Update result for user
        setattr(self, my_fields['result_field'], result_data)

        # If checker, set release = True
        if my_fields['user_field'] == 'user_c':
            self.release = True

        self._update_time_submit(user)

