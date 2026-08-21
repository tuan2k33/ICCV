from datetime import datetime
import json
from time import sleep
from pprint import pprint

from app.modules.task.delivery_task import DeliveryTask


# Mock classes để test
class MockUser:
    def __init__(self, id, role):
        self.id = id
        self.role = role


task = {
    "id": 1,
    "user_e1": None,
    "user_e2": None,
    "user_c": None,
    "result_e1": None,
    "result_e2": None,
    "result_c": None,
    "time_submit": None
}



def print_task_info(delivery_task, title):
    """Helper function để in thông tin task đẹp"""
    print(f"\n=== {title} ===")
    info = delivery_task.dict()
    print(json.dumps(info, indent=2, default=str))


# Test basic functionality
if __name__ == "__main__":
    # Tạo mock objects
    task = task

    # Tạo users
    entry_user1 = dict(id=101, role="ENTRY_2")
    entry_user2 = dict(id=102, role="ENTRY_2")
    checker_user1 = dict(id=201, role="CHECKER")
    checker_user2 = dict(id=202, role="CHECKER")

    print("=== Testing DeliveryTask (Final Version) ===")

    # Test 1: Assign entry users
    print("\n1. Testing assign entry users:")
    delivery_task = DeliveryTask(task)


    delivery_task.assign_task(entry_user2)
    # delivery_task.update_result(entry_user2, {"answer": "A", "score": 94})
    # delivery_task.update_time_process(entry_user2, {"BE-00-1": 20})
    # delivery_task.update_flags(entry_user2, {"BE-00-1": "2e32qe4234234"})
    # delivery_task.compare_result(entry_user2)

    # Assign Task
    delivery_task.assign_task(entry_user1)
    # delivery_task.update_result(entry_user1, {"answer": "A", "score": 95})
    # delivery_task.update_time_process(entry_user1, {"BE-00-1": 10})
    # delivery_task.update_flags(entry_user1, {"BE-00-1": "loi"})
    # delivery_task.compare_result(entry_user1)



    # delivery_task.assign_task(checker_user1)
    # delivery_task.update_result(checker_user1, {"answer": "A", "score": 94})
    # delivery_task.update_time_process(checker_user1, {"BE-00-1": 20})
    # delivery_task.compare_result(checker_user1)
    # update task CK
    # delivery_task.assign_task(checker_user1)
    # delivery_task.update_result(checker_user1, {"answer": "A", "score": 91})
    # #
    pprint(delivery_task.dict())
    # delivery_task.assign_task(entry_user2)

    # print_task_info(delivery_task, "After assigning user 101")
    # print(f"Task object - user_e1: {task.user_e1}, user_e2: {task.user_e2}")

    # delivery_task.assign_task(entry_user2)
    # delivery_task.update_time_for_task(entry_user2)

    # print_task_info(delivery_task, "After assigning user 102")
    # print(f"Task object - user_e1: {task.user_e1}, user_e2: {task.user_e2}")

    # Test 2: Assign checker
    # print("\n2. Testing assign checker:")
    # delivery_task.assign_task(checker_user)
    # print_task_info(delivery_task, "After assigning checker")
    # print(f"Task object - user_e1: {task.user_e1}, user_e2: {task.user_e2}, user_c: {task.user_c}")
    #
    # # Test 3: Test with results
    # print("\n3. Testing results functionality:")
    # delivery_task.update_result(entry_user1, {"answer": "A", "score": 95})
    # delivery_task.update_result(entry_user2, {"answer": "A", "score": 95})
    #
    # print(f"Task results - result_e1: {task.result_e1}, result_e2: {task.result_e2}")
    #
    # # Test compare
    # match_result = delivery_task.compare_result(entry_user1)
    # print(f"Results match: {match_result}")
    # print(f"Task after compare - result_c: {task.result_c}, time_submit: {task.time_submit}")
    #
    # # Test 4: Test error cases
    # print("\n4. Testing error cases:")
    # try:
    #     # Try to assign same user again
    #     delivery_task.assign_task(entry_user1)
    # except ValueError as e:
    #     print(f"Expected error when assigning same user twice: {e}")
    #
    # try:
    #     # Try to assign third entry user
    #     entry_user3 = MockUser(103, "ENTRY")
    #     delivery_task.assign_task(entry_user3)
    # except ValueError as e:
    #     print(f"Expected error when task is full: {e}")
    #
    # # Test 5: Test time functionality
    # print("\n5. Testing time functionality:")
    # delivery_task.update_time_for_task(entry_user1)
    # print(f"End time for user 101: {task.end_time_e1}")
    #
    # delivery_task.update_time_for_task(checker_user)
    # print(f"End time for checker: {task.end_time_c}")
    #
    # print("\n=== Test completed successfully! ===")
