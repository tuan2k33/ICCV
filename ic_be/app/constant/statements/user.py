class UserStatements:
    FIND_USER_BY_ID = """
                      SELECT id, \
                             username, \
                             email, \
                             fullname, \
                             phone_number, \
                             gender, \
                             address, \
                             is_active, \
                             roles, \
                             created_at, \
                             updated_at, \
                             deleted_at
                      FROM users
                      WHERE id = %s and deleted_at IS NULL; \
                      """

    CREATE_USER = """
                  INSERT INTO users (username, email, password, is_active, \
                                     roles)
                  VALUES (%s, %s, %s, %s, %s) RETURNING id; \
                  """

    FIND_USER_BY_USERNAME_OR_EMAIL = """
                                     SELECT id, \
                                            username, \
                                            email, \
                                            fullname, \
                                            phone_number, \
                                            password, \
                                            gender, \
                                            address, \
                                            is_active, \
                                            roles, \
                                            created_at, \
                                            updated_at, \
                                            deleted_at
                                     FROM users
                                     WHERE username = %s
                                        OR email = %s \
                                         AND deleted_at IS NULL; \
                                     """

    GET_USER_BY_ID = """
                     SELECT id, \
                            username, \
                            email, \
                            fullname, \
                            phone_number, \
                            gender, \
                            address, \
                            is_active, \
                            roles, \
                            created_at, \
                            updated_at, \
                            deleted_at
                     FROM users
                     WHERE id = %s \
                       AND deleted_at IS NULL; \
                     """

    UPDATE_USER = """
                  UPDATE users
                  SET username     = %s,
                      email        = %s,
                      fullname     = %s,
                      phone_number = %s,
                      gender       = %s,
                      address      = %s,
                      is_active    = %s,
                      roles        = %s,
                      updated_at   = NOW()
                  WHERE id = %s \
                    AND deleted_at IS NULL; \
                  """

    DELETE_USER = """
                  UPDATE users
                  SET deleted_at = NOW()
                  WHERE id = %s; \
                  """

    EXISTS_USER = """
                  SELECT EXISTS (SELECT 1
                                 FROM users
                                 WHERE username = %s OR phone_number = %s); \
                  """

    GET_ALL_USERS = """
                    SELECT id, \
                           username, \
                           email, \
                           fullname, \
                           phone_number, \
                           is_active, \
                           roles, \
                           created_at, \
                           updated_at, \
                           deleted_at
                    FROM users
                    WHERE deleted_at IS NULL \
                    OFFSET %s LIMIT %s; \
                    """
    COUNT_USERS = """
                  SELECT COUNT(*) AS count
                    FROM users
                    WHERE deleted_at IS NULL; \
                    """