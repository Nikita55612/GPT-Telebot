from datetime import datetime as dt
import os
import json
import sys
import shutil
import config


class UsersCRUD:
    def __init__(self):
        self.DEFAULT_PROFILE = {
            "tokens": config.START_USER_TOKENS,
            "limit_tokens": config.START_USER_LIMIT_TOKENS,
            "balance": 0,
            "ref_percent": config.START_USER_REF_PERCENT,
            "sub_ref_percent": config.START_USER_SUB_REF_PERCENT,
            "ref_users": [],
            "sub_ref_users": [],
            "ref_amount": 0,
            "ref_balance": 0,
            "ref_output": 0,
            "ref_parent": None,
            "role": "Без роли",
            "voice_acting": False,
            "days_before_resetting_tokens": config.DAYS_BEFORE_RESETTING_TOKENS,
            "translation": True,
            "temperature": 0.1,
            "model": config.START_USER_MODEL,
            "status": config.START_USER_STATUS,
            "context": [],
            "max_context_size": config.START_USER_MAX_CONTEXT_SIZE,
            "max_context_buffer": config.START_USER_MAX_CONTEXT_BUFFER,
            "max_tokens": config.START_USER_MAX_TOKENS,
            "payments": {},
            "last_payment_verification": str(dt.now()),
            "channel_subscription": False
        }
        self.users_dir = config.USERS_DIR
        os.mkdir(self.users_dir) if not os.path.exists(self.users_dir) else ...
        if config.USERS_BACKUP:
            try:
                shutil.copytree(self.users_dir, f"users_backup_data//{self.users_dir}")
            except FileExistsError:
                shutil.rmtree(f"users_backup_data//{self.users_dir}")
                shutil.copytree(self.users_dir, f"users_backup_data//{self.users_dir}")
        self.users = os.listdir(path=self.users_dir)
        self.cache = {}
        for user in self.users:
            read_user = self.read_user(user)
            for p in self.DEFAULT_PROFILE:
                if p not in read_user:
                    read_user[p] = self.DEFAULT_PROFILE[p]
            self.update_user(user, read_user)

    def init_default_profile(self):
        init = self.DEFAULT_PROFILE.copy()
        init["registration_date"] = str(dt.now())
        init["last_limit_reset"] = str(dt.now())
        return init

    def create_user(self, user_id: str):
        try:
            os.mkdir(os.path.join(self.users_dir, user_id))
            dp = self.init_default_profile()
            with open(f"{self.users_dir}//{user_id}//profile.json", "w") as f:
                json.dump(dp, f, indent=4)
            with open(f"{self.users_dir}//{user_id}//history.json", "w") as f:
                json.dump([], f, indent=4)
            self.users.append(user_id)
            if self.get_cache_size() > config.CACHE_MAX_SIZE:
                self.clear_cache()
            self.cache[user_id] = dp
            return dp
        except FileExistsError:
            return self.DEFAULT_PROFILE

    def read_user(self, user_id: str):
        if user_id in self.cache:
            return self.cache[user_id]
        try:
            with open(f"{self.users_dir}//{user_id}//profile.json", "r") as f:
                return json.load(f)
        except FileNotFoundError:
            return self.create_user(user_id)

    def update_user(self, user_id: str, data: dict):
        with open(f"{self.users_dir}//{user_id}//profile.json", "w") as f:
            json.dump(data, f, indent=4)
        self.cache[user_id] = data

    def read_oll_users(self):
        users = {}
        for i in self.users:
            users[i] = self.read_user(i)
        return users

    def read_oll_users_history(self):
        users_history = {}
        for i in self.users:
            users_history[i] = self.read_user_history(i)
        return users_history

    def read_user_history(self, user_id: str):
        try:
            with open(f"{self.users_dir}//{user_id}//history.json", "r") as f:
                return json.load(f)
        except FileNotFoundError:
            self.create_user(user_id)
            return []

    def update_user_history(self, user_name: str, data: dict):
        with open(f"{self.users_dir}//{user_name}//history.json", "w") as f:
            json.dump(data, f, indent=4)

    def delete_user_history(self, user_id: str):
        with open(f"{self.users_dir}//{user_id}//history.json", "w") as f:
            json.dump([], f, indent=4)

    def get_oll_users_statistics(self):
        pass

    def get_user_statistics(self, user_id: str):
        pass

    def get_cache_size(self):
        return sys.getsizeof(self.cache)

    def clear_cache(self):
        self.cache.clear()

    def dir(self):
        return self.__dir__()
