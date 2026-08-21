class TenantStatements:
    INSERT_TENANT = """
                    INSERT INTO tenants (name, description, banner, settings, information)
                    VALUES (%s, %s, %s, %s, %s) RETURNING name, description, banner;
                    """

    UPDATE_TENANT = """
                    UPDATE tenants
                    SET name        = %s,
                        description = %s,
                        banner      = %s
                    WHERE id = %s RETURNING name, description, banner;
                    """

    UPDATE_INFORMATION = """
                    UPDATE tenants
                    SET information = %s,
                        updated_at = NOW()
                    WHERE id = %s RETURNING id;
                    """

    UPDATE_SETTINGS = """
                      UPDATE tenants
                      SET settings   = %s,
                          updated_at = NOW()
                      WHERE id = %s RETURNING settings;
                      """

    FIND_TENANT_BY_ID = """
                        SELECT name, description, banner
                        FROM tenants
                        WHERE id = %s;
                        """

    FIND_SETTINGS_TENANT_BY_ID = """
                                 SELECT settings
                                 FROM tenants
                                 WHERE id = %s;
                                 """

    FIND_INFORMATION_TENANT_BY_ID = """
                                    SELECT information
                                    FROM tenants
                                    WHERE id = %s;
                                    """