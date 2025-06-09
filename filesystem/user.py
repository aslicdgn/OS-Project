import hashlib

class User:
    def __init__(self, username, password, is_admin=False):
        self.username = username
        self.password_hash = self._hash_password(password)
        self.is_admin = is_admin

    def _hash_password(self, password):
        return hashlib.sha256(password.encode()).hexdigest()

    def verify_password(self, password):
        return self.password_hash == self._hash_password(password)


class UserManager:
    def __init__(self):
        self.users = {}
        self.current_user = None

    def register(self, username, password, is_admin=False):
        if username in self.users:
            raise ValueError("Username already exists.")
        self.users[username] = User(username, password, is_admin)

    def login(self, username, password):
        user = self.users.get(username)
        if user and user.verify_password(password):
            self.current_user = user
            return True
        return False

    def logout(self):
        self.current_user = None

    def is_logged_in(self):
        return self.current_user is not None

    def get_current_user(self):
        return self.current_user
    

class PermissionManager:
    def __init__(self):
        self.permissions = {}  # path -> {'owner': user, 'read': set(), 'write': set()}

    def set_permissions(self, path, owner, read_users=None, write_users=None):
        self.permissions[path] = {
            'owner': owner,
            'read': set(read_users or [owner]),
            'write': set(write_users or [owner])
        }

    def check_read(self, path, user):
        perms = self.permissions.get(path)
        return perms and (user in perms['read'] or user == perms['owner'])

    def check_write(self, path, user):
        perms = self.permissions.get(path)
        return perms and (user in perms['write'] or user == perms['owner'])

    def remove(self, path):
        if path in self.permissions:
            del self.permissions[path]

import base64
from hashlib import sha256
from cryptography.fernet import Fernet

class EncryptedFile:
    def __init__(self, name, content="", key=None, owner=None):
        if key is None:
            raise ValueError("Key must be provided for EncryptedFile.")
        self.name = name
        self.key = key
        self.fernet = Fernet(self.key)
        self.owner = owner
        self._encrypted = self.fernet.encrypt(content.encode() if isinstance(content, str) else content)

    def read(self):
        return self.fernet.decrypt(self._encrypted)

    def write(self, content):
        data = content.encode() if isinstance(content, str) else content
        self._encrypted = self.fernet.encrypt(data)

    def get_size(self):
        return len(self._encrypted)

    @staticmethod
    def derive_key_from_password(password):
        hash = sha256(password.encode()).digest()
        return base64.urlsafe_b64encode(hash)

    def check_password(self, password):
        try:
            key = self.derive_key_from_password(password)
            if key != self.key:
                return False
            # Anahtar aynı ise decrypt deneyelim
            fernet = Fernet(key)
            fernet.decrypt(self._encrypted)
            return True
        except Exception:
            return False
