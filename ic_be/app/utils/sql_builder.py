import copy
import json


class SQLBuilder:
    _BINARY_OPERATORS = {
        "eq": "=",
        "ne": "!=",
        "gt": ">",
        "gte": ">=",
        "lt": "<",
        "lte": "<=",
        "in": "IN",
        "nin": "NOT IN",
        "like": "LIKE",
        "ilike": "ILIKE"
    }

    _UNARY_OPERATORS = {
        "isnull": "IS NULL",
        "isnotnull": "IS NOT NULL",
    }

    def __init__(self, table: str, json_fields: set = None):
        self.json_fields = json_fields if json_fields else set()
        self._table = table
        self._select_fields = []
        self._insert_fields = {}
        self._update_fields = {}
        self._update_raw_clauses = []
        self._where_clauses = []  # (sql, params, operator)
        self._order_by = []
        self._returning = ["id"]
        self._count_field = None
        self._limit = None
        self._offset = None
        self._bulk_insert_rows = []
        self._bulk_update_rows = []
        self._delete = False
        self._bulk_update_keys = None

    # Deep copy
    def copy(self):
        return copy.deepcopy(self)

    # SELECT
    def select(self, *fields):
        self._select_fields.extend(fields)
        return self

    # COUNT
    def count(self, field: str = "*"):
        self._count_field = field
        return self

    # INSERT
    def insert(self, **fields):
        for key, value in fields.items():
            if isinstance(value, dict):
                self._insert_fields[key] = json.dumps(value)
            else:
                self._insert_fields[key] = value
        return self

    def _convert_value(self, key, value):
        if key in self.json_fields:
            return json.dumps(value)
        if isinstance(value, dict):
            return json.dumps(value)
        return value

    # BULK INSERT
    def bulk_insert(self, rows: list[dict]):
        for row in rows:
            converted = {k: self._convert_value(k, v) for k, v in row.items()}
            self._bulk_insert_rows.append(converted)
        return self

    # UPDATE
    def update(self, **fields):
        for key, value in fields.items():
            self._update_fields[key] = self._convert_value(key, value)
        return self

    def update_raw(self, clause: str, params: tuple | list = ()):
        """
        Add raw SQL for UPDATE SET clause.
        Example: update_raw("racks = array_remove(racks, %s)", ('AA-even',))
        """
        if not isinstance(params, (tuple, list)):
            params = (params,)
        self._update_raw_clauses.append((clause, params))
        return self

    # BULK UPDATE (CASE WHEN)
    def bulk_update(self, rows: list[dict], key_fields: str | list[str] = "id"):
        """
        rows: list of dicts, each dict must include key_fields + fields to update
        Example:
          [{"id":1,"name":"A"},{"id":2,"name":"B"}]
          [{"batch_id":1,"rack":"A","val":123}]

        key_fields = ["id","name"]
        """
        if not rows:
            raise ValueError("rows must not be empty")

        if isinstance(key_fields, str):
            key_fields = [key_fields]

        self._bulk_update_rows = [
            {k: json.dumps(v) if isinstance(v, dict) else v for k, v in row.items()}
            for row in rows
        ]
        self._bulk_update_keys = key_fields
        return self

    # DELETE
    def delete(self):
        self._delete = True
        return self

    # parse conditions: field__op=value
    def _parse_conditions(self, conditions: dict):
        clauses, params = [], []
        for k, v in conditions.items():
            if "__" in k:
                field, op = k.split("__", 1)

                # Unary operators (không cần value)
                if op in self._UNARY_OPERATORS:
                    clauses.append(f"{field} {self._UNARY_OPERATORS[op]}")
                    continue

                # Binary operators
                sql_op = self._BINARY_OPERATORS.get(op)
                if not sql_op:
                    raise ValueError(f"Unsupported operator: {op}")

                if op in ["in", "nin"]:
                    placeholders = ", ".join(["%s"] * len(v))
                    clauses.append(f"{field} {sql_op} ({placeholders})")
                    params.extend(v)
                else:
                    clauses.append(f"{field} {sql_op} %s")
                    params.append(v)
            else:
                clauses.append(f"{k} = %s")
                params.append(v)
        return clauses, tuple(params)

    # WHERE (AND group)
    def where(self, **conditions):
        clauses, params = self._parse_conditions(conditions)
        sql = " AND ".join(clauses)
        self._where_clauses.append((sql, params, "AND"))
        return self

    # OR WHERE (OR with previous group)
    def or_where(self, **conditions):
        clauses, params = self._parse_conditions(conditions)
        sql = " AND ".join(clauses)  # trong group vẫn là AND
        self._where_clauses.append((sql, params, "OR"))
        return self

    # WHERE GROUP OR (OR inside a group)
    def where_or(self, **conditions):
        clauses, params = self._parse_conditions(conditions)
        sql = " OR ".join(clauses)
        self._where_clauses.append((sql, params, "AND"))
        return self

    # WHERE RAW (custom SQL)
    def where_raw(self, clause: str, params: tuple | list = ()):
        if not isinstance(params, (tuple, list)):
            params = (params,)
        self._where_clauses.append((clause, params, "AND"))
        return self

    # OR WHERE RAW
    def or_where_raw(self, clause: str, params: tuple = ()):
        self._where_clauses.append((clause, params, "OR"))
        return self

    # ORDER BY
    def order_by(self, field: str, direction: str = "ASC"):
        self._order_by.append(f"{field} {direction}")
        return self

    # RETURNING
    def returning(self, *fields):
        self._returning.extend(fields)
        return self

    # LIMIT
    def limit(self, n: int):
        self._limit = n
        return self

    # OFFSET
    def offset(self, n: int):
        self._offset = n
        return self

    # Build
    def build(self):
        if hasattr(self, "_delete") and self._delete:
            return self._build_delete()
        elif self._bulk_insert_rows:
            return self._build_bulk_insert()
        elif self._insert_fields:
            return self._build_insert()
        elif self._bulk_update_rows:
            return self._build_bulk_update()
        elif self._update_fields or self._update_raw_clauses:
            return self._build_update()
        else:
            return self._build_select()

    def _build_where(self):
        if not self._where_clauses:
            return "", ()
        sql_parts, params = [], []

        for idx, (clause, clause_params, operator) in enumerate(self._where_clauses):
            prefix = "WHERE" if idx == 0 else operator
            sql_parts.append(f"{prefix} ({clause})")
            params.extend(clause_params)

        return " " + " ".join(sql_parts), tuple(params)

    def _build_select(self):
        if self._count_field:  # nếu có count
            fields = f"COUNT({self._count_field})"
        else:
            fields = ", ".join(self._select_fields) if self._select_fields else "*"

        query = f"SELECT {fields} FROM {self._table}"
        where_clause, params = self._build_where()
        query += where_clause
        if self._order_by and not self._count_field:
            query += " ORDER BY " + ", ".join(self._order_by)

        if self._limit is not None:
            query += f" LIMIT {self._limit}"
        if self._offset is not None:
            query += f" OFFSET {self._offset}"
        return query, params

    def _build_insert(self):
        cols = ", ".join(self._insert_fields.keys())
        placeholders = ", ".join(["%s"] * len(self._insert_fields))
        query = f"INSERT INTO {self._table} ({cols}) VALUES ({placeholders})"
        if self._returning:
            query += " RETURNING " + ", ".join(self._returning)
        return query, tuple(self._insert_fields.values())

    def _build_update(self):
        # MODIFIED: Handle both regular updates and raw updates
        set_parts = []
        params = []

        # Add regular field updates
        for k, v in self._update_fields.items():
            set_parts.append(f"{k} = %s")
            params.append(v)

        # Add raw updates
        for clause, clause_params in self._update_raw_clauses:
            set_parts.append(clause)
            params.extend(clause_params)

        if not set_parts:
            raise ValueError("No fields to update")

        set_clause = ", ".join(set_parts)
        query = f"UPDATE {self._table} SET {set_clause}"

        where_clause, where_params = self._build_where()
        query += where_clause
        params.extend(where_params)

        if self._returning:
            query += " RETURNING " + ", ".join(self._returning)

        return query, tuple(params)

    def _build_delete(self):
        query = f"DELETE FROM {self._table}"
        where_clause, params = self._build_where()
        query += where_clause
        if self._returning:
            query += " RETURNING " + ", ".join(self._returning)
        return query, params

    def _build_bulk_insert(self):
        if not self._bulk_insert_rows:
            return "", ()
        cols = list(self._bulk_insert_rows[0].keys())
        col_str = ", ".join(cols)
        placeholders = "(" + ", ".join(["%s"] * len(cols)) + ")"
        all_placeholders = ", ".join([placeholders] * len(self._bulk_insert_rows))

        params = []
        for row in self._bulk_insert_rows:
            params.extend(row.get(c, None) for c in cols)

        query = f"INSERT INTO {self._table} ({col_str}) VALUES {all_placeholders}"
        if self._returning:
            query += " RETURNING " + ", ".join(self._returning)
        return query, tuple(params)

    def _build_bulk_update(self):
        if not self._bulk_update_rows:
            return "", ()

        rows = self._bulk_update_rows
        keys = self._bulk_update_keys

        all_fields = list(rows[0].keys())
        update_fields = [f for f in all_fields if f not in keys]

        if not update_fields:
            raise ValueError("No fields to update. Each row must contain at least one non-key field.")

        query = f'UPDATE "{self._table}" AS t SET '
        set_clauses = [f'"{field}" = v."{field}"' for field in update_fields]
        query += ", ".join(set_clauses)

        query += ' FROM (VALUES '
        placeholders = ", ".join(['%s'] * len(all_fields))
        query += ", ".join([f'({placeholders})'] * len(rows))
        query += f') AS v(' + ", ".join(f'"{f}"' for f in all_fields) + ')'

        where_clauses = [f't."{k}" = v."{k}"' for k in keys]
        query += ' WHERE ' + " AND ".join(where_clauses)

        params = []
        for row in rows:
            params.extend([row[f] for f in all_fields])

        if self._returning:
            query += " RETURNING " + ", ".join(f't."{r}"' for r in self._returning)

        return query, tuple(params)


if __name__ == "__main__":
    # Example usage
    builder = SQLBuilder("users")

    # normal where
    q1, p1 = builder.select().where(username="john", age__gte=18).build()
    print(q1, p1)
    # SELECT * FROM users WHERE (username = %s AND age >= %s) ('john', 18)

    # with IS NOT NULL
    builder = SQLBuilder("users")
    q2, p2 = builder.select().where(last_login__isnotnull=True).build()
    print(q2, p2)
