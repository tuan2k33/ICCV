class TaskStatements:
    CREATE_INDEX = """
                   CREATE INDEX idx_tasks_un_result ON tasks (result) WHERE result IS NULL;
                   """

    INSERT_TASK = """
                  INSERT INTO tasks (name, images, video)
                  VALUES (%s, %s, %s) RETURNING id;
                  """

    UPDATE_RESULT = """
                    UPDATE tasks
                    SET result      = %s,
                        time_submit = NOW()
                    WHERE id = %s
                      AND user_assign = %s;
                    """

    UPDATE_USER_ASSIGN = """
                         UPDATE tasks
                         SET user_assign  = %s,
                             time_assign  = %s,
                             version = version + 1
                         WHERE id = %s
                           AND version = %s;
                         """

    FIND_TASK_BY_ID = """
                      SELECT id,
                             name,
                             images,
                             video,
                             result,
                             user_assign,
                             time_assign,
                             time_submit,
                             version
                      FROM tasks
                      WHERE id = %s;
                      """

    FIND_TASK_BY_USER = """
                        SELECT id,
                               name,
                               images,
                               video,
                               result,
                               user_assign,
                               time_assign,
                               time_submit,
                               version
                        FROM tasks
                        WHERE time_assign >= CURRENT_TIMESTAMP
                          AND result IS NULL
                          AND user_assign = %s;
                        """

    FIND_TASK_NOT_ASSIGNED = """
                             SELECT id,
                                    name,
                                    images,
                                    video,
                                    result,
                                    user_assign,
                                    time_assign,
                                    time_submit,
                                    version
                             FROM tasks
                             WHERE time_assign < CURRENT_TIMESTAMP
                               AND result IS NULL LIMIT 1;
                             """
