import unicodedata
from time import sleep

import pandas as pd
import re
import json

from app.utils.hasher import hash_04_password
from app.utils.timestamp import get_now

pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)
pd.set_option('display.width', 1000)
pd.set_option('display.max_colwidth', None)


class DataFrameValidator:
    """
    A class to validate a DataFrame based on rules for name and phone number columns,
    and to return detailed error codes for each row.
    """
    # --- Predefined error codes ---
    EMPTY_FULLNAME = "EMPTY_FULLNAME"
    EMPTY_PHONE_NUMBER = "EMPTY_PHONE_NUMBER"
    LESS_THAN_2_CHARACTERS = "LESS_THAN_2_CHARACTERS"
    INVALID_CHARACTERS_IN_NAME = "INVALID_CHARACTERS_IN_NAME"
    INVALID_PHONE_NUMBER = "INVALID_PHONE_NUMBER"
    PHONE_NUMBER_ALREADY_EXIST = "PHONE_NUMBER_ALREADY_EXIST"
    PHONE_NUMBER_DUPLICATED_IN_SHEET = "PHONE_NUMBER_DUPLICATED_IN_SHEET"

    def __init__(self, dataframe, company: str, tenant_id: int, roles: list):
        """
        Initializes the Validator.
        """
        self.df = dataframe.copy()
        self.df = self.df.fillna("")
        self.name_column = "fullname"
        self.phone_column = "phone_number"
        self.username_column = "username"
        self.password_column = "password"
        self.company_column = "company"
        self.role_column = "roles"
        self.tenant_column = "tenant_id"
        self.username_tmp_column = "username_tmp"
        self.role = roles
        self.company = company
        self.tenant_id = tenant_id
        self.count_rows = len(self.df)

        # Rename input columns to the expected internal names
        column_map = {
            "Họ & Tên\n(Ví dụ: Nguyễn Văn A)": self.name_column,
            "Số điện thoại\n(Ví dụ: 086867563)": self.phone_column
        }
        self.df = self.df.rename(columns=column_map)

        # New attribute to store detailed errors
        self.structured_errors = []
        self.invalid_rows_df = pd.DataFrame()

    def _is_valid_name(self, name):
        """
        [Internal] Checks the validity of a name and returns an error code if invalid.
        """
        if pd.isna(name) or str(name).strip() == "":
            return self.EMPTY_FULLNAME

        name_str = str(name)

        if len(name_str) < 2:
            return self.LESS_THAN_2_CHARACTERS

        if not re.match(r"^[a-zA-ZÀ-ỹà-ỹ\s]+$", name):
            return self.INVALID_CHARACTERS_IN_NAME

        return None

    def _is_valid_phone(self, phone):
        """
        [Internal] Checks the validity of a phone number and returns an error code if invalid.
        """
        if pd.isna(phone) or str(phone).strip() == "":
            return self.EMPTY_PHONE_NUMBER

        phone_str = str(phone)

        if not phone_str.isdigit() or len(phone_str) != 10:
            return self.INVALID_PHONE_NUMBER

        return None

    def _initial_username(self, name):
        """
        [Internal] Creates a username based on the name and company.
        Example: "Nguyen Van Anh" -> "NVAnh_company"
        """
        if self.company:
            name_company = '_lf' if self.company == "Linfox" else '_ul'
        else:
            name_company = ''
        words = str(name).strip().split()
        if len(words) == 1:
            username_base = words[0]
        else:
            middle_words = words[:-1]
            last_word = self.remove_accents(words[-1].capitalize())
            initials = "".join(self.remove_accents(p[0].upper()) for p in middle_words)
            username_base = initials + last_word

        return f"{username_base}{name_company}"

    @staticmethod
    def remove_accents(input_str: str) -> str:
        nfkd_form = unicodedata.normalize('NFKD', input_str)
        return "".join([c for c in nfkd_form if not unicodedata.combining(c)])

    @staticmethod
    def _initial_password(password):
        return hash_04_password(str(password))

    @staticmethod
    def normalize_name(name_str: str) -> str:
        """Change full name: Trần Minh Hiếu"""
        name_str = name_str.strip()
        name_str = name_str.lower()
        words = [w.capitalize() for w in name_str.split()]
        return " ".join(words)

    def validate(self):
        """
        Executes the validation process and builds a detailed list of errors.
        """
        name_error_col = "name_error"
        phone_error_col = "phone_error"

        self.df[name_error_col] = self.df[self.name_column].apply(self._is_valid_name)
        self.df[self.name_column] = self.df[self.name_column].apply(self.normalize_name)
        self.df[phone_error_col] = self.df[self.phone_column].apply(self._is_valid_phone)
        self.check_duplicate_phones_in_sheet(phone_error_col)

        # A row is invalid if there is an error in any validation column
        invalid_mask = self.df[name_error_col].notna() | self.df[phone_error_col].notna()
        self.invalid_rows_df = self.df[invalid_mask]

        self._handle_struct_err_sheet(name_error_col, phone_error_col)
        if not self.structured_errors:
            self.add_username_password()

        return self

    def _handle_struct_err_sheet(self, name_error_col, phone_error_col):
        for index, row in self.invalid_rows_df.iterrows():
            errors = []
            if pd.notna(row[name_error_col]):
                errors.append(row[name_error_col])
            if pd.notna(row[phone_error_col]):
                errors.append(row[phone_error_col])

            self.structured_errors.append({
                "row_index": index,
                "info": row.to_dict(),
                "errors": errors
            })
        return self

    def add_username_password(self):
        """
        Adds 'username', 'password', and 'company' columns to the DataFrame.
        """
        self.df[self.username_column] = self.df[self.name_column].apply(self._initial_username)
        self.df[self.password_column] = self.df[self.phone_column].apply(self._initial_password)
        self.df[self.company_column] = self.company
        self.df[self.tenant_column] = self.tenant_id
        self.df[self.username_tmp_column] = self.df[self.username_column]
        self.df[self.role_column] = [[self.role[0]]] * len(self.df)
        return self

    def get_invalid_rows_dataframe(self):
        """
        Returns a DataFrame containing only the invalid rows.
        """
        return self.invalid_rows_df

    def get_structured_errors(self):
        """
        Returns the detailed list of errors in a structured format.
        """
        return self.structured_errors

    def update_username(self, list_username: list):
        """
        Finds rows with names in list_fullname and updates their username
        by appending the last two digits of the phone number.
        """
        mask = self.df[self.username_column].isin(list_username)

        if mask.any():
            current_usernames = self.df.loc[mask, self.username_column]
            last_two_digits = self.df.loc[mask, self.phone_column].str[-2:]
            new_usernames = current_usernames + last_two_digits
            self.df.loc[mask, self.username_column] = new_usernames
        return self

    def check_duplicate_phones_in_sheet(self, phone_error_col):
        """
        Finds duplicate phone numbers within the DataFrame and assigns an error code.
        """
        duplicate_mask = self.df.duplicated(subset=[self.phone_column], keep=False)
        duplicate_indices = self.df[duplicate_mask].index

        for idx in duplicate_indices:
            self.df.at[idx, phone_error_col] = self.PHONE_NUMBER_DUPLICATED_IN_SHEET

        return self

    def update_duplicate_usernames_in_sheet(self, dataset_username: list = None):
        user_set = set(dataset_username or [])

        for idx, row in self.df.iterrows():
            username = row[self.username_column]
            phone = row[self.phone_column]
            i = 1
            new_username = username
            while new_username in user_set:
                new_username = f"{username}{phone[-i:]}"
                i += 1
            user_set.add(new_username)
            self.df.at[idx, self.username_column] = new_username

        return self

    def cleanup_error_columns(self):
        """
        Removes intermediate error columns from the DataFrame.
        """
        cols_to_drop = ['name_error', 'phone_error']
        self.df = self.df.drop(columns=cols_to_drop, errors='ignore')
        return self

    def get_username_list(self):
        """
        Returns a list of all values from the username column.
        """
        return self.df[self.username_column].tolist()

    def get_phone_number_list(self):
        """
        Returns a list of all values from the phone_number column.
        """
        return self.df[self.phone_column].tolist()

    def to_list(self):
        """
        Converts the DataFrame to a list of dictionaries,
        and appends created_at, updated_at (UTC time).
        """
        records = self.df.to_dict('records')
        for record in records:
            now = get_now()
            record["created_at"] = now
            record["updated_at"] = now
            sleep(0.000001)

        return records


if __name__ == "__main__":
    # --- USE CLASS ---

    # 1. Tạo dữ liệu mẫu với trường hợp username trùng
    sample_data = {
        "Họ & Tên\n(Ví dụ: Nguyễn Văn A)": [
            "Nguyễn Văn Anh",
            "Nguyễn Văn Anh",  # Trùng tên
            "Nguyễn Văn Anh",  # Trùng tên
            "Trần Thị Hoài"
        ],
        "Số điện thoại\n(Ví dụ: 086867563)": [
            "0333223616",
            "0333323616",
            "0333322616",
            "0333322617"
        ]
    }
    df_can_kiem_tra = pd.DataFrame(sample_data)
    validator = DataFrameValidator(df_can_kiem_tra, 'Linfox', 1, ["CHECKER"])

    validator.validate()
    detailed_errors = validator.get_structured_errors()
    validator.check_duplicate_phones_in_sheet('0333322617')


    print("--- DANH SÁCH LỖI CHI TIẾT ---")
    print(json.dumps(detailed_errors, indent=2, ensure_ascii=False))

    validator.update_duplicate_usernames_in_sheet(['TTHoai_lf'])

    print("\n--- DATAFRAME SAU KHI XỬ LÝ ---")
    validator.cleanup_error_columns()
    print("\n--- DANH SÁCH CUỐI CÙNG ---")
    print(validator.cleanup_error_columns().to_list())
