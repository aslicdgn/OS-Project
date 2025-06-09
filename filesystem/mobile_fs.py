import time
import threading
import uuid
from collections import OrderedDict
from cryptography.fernet import Fernet
from .user import UserManager, PermissionManager, EncryptedFile
import os

BLOCK_SIZE = 512

class BlockStorage:
    def __init__(self):
        self.blocks = {}

    def store(self, data):
        block_ids = []
        for i in range(0, len(data), BLOCK_SIZE):
            block = data[i:i+BLOCK_SIZE]
            block_id = str(uuid.uuid4())
            self.blocks[block_id] = block
            block_ids.append(block_id)
        return block_ids

    def retrieve(self, block_ids):
        return b''.join(self.blocks[bid] for bid in block_ids if bid in self.blocks)

    def delete(self, block_ids):
        for bid in block_ids:
            self.blocks.pop(bid, None)


class BlockCache:
    def __init__(self, capacity=10):
        self.cache = OrderedDict()
        self.capacity = capacity

    def get(self, block_id):
        if block_id in self.cache:
            self.cache.move_to_end(block_id)
            return self.cache[block_id]
        return None

    def put(self, block_id, data):
        self.cache[block_id] = data
        self.cache.move_to_end(block_id)
        if len(self.cache) > self.capacity:
            self.cache.popitem(last=False)


class File:
    def __init__(self, name, content="", storage=None, cache=None):
        self.name = name
        self.created_at = time.ctime()
        self.blocks = []
        self.size = 0
        self.storage = storage
        self.cache = cache
        if content:
            self.write(content)

    def write(self, content):
        data = content.encode('utf-8') if isinstance(content, str) else content
        if self.blocks:
            self.storage.delete(self.blocks)
        self.blocks = self.storage.store(data)
        self.size = len(data)

    def read(self):
        content = []
        for block_id in self.blocks:
            cached = self.cache.get(block_id) if self.cache else None
            if cached:
                content.append(cached)
            else:
                block = self.storage.blocks.get(block_id, b'')
                content.append(block)
                if self.cache:
                    self.cache.put(block_id, block)
        return b''.join(content)


class Directory:
    def __init__(self, name):
        self.name = name
        self.files = {}
        self.subdirectories = {}
        self.created_at = time.ctime()

    def create_file(self, name, content="", storage=None, cache=None):
        self.files[name] = File(name, content, storage, cache)

    def create_subdirectory(self, dir_name):
        if dir_name not in self.subdirectories:
            self.subdirectories[dir_name] = Directory(dir_name)


class FileSystem:
    def __init__(self):
        self.root = Directory("root")
        self.current_directory = self.root
        self.path_stack = [self.root]
        self.lock = threading.Lock()
        self.storage = BlockStorage()
        self.cache = BlockCache(capacity=20)
        self.user_manager = UserManager()
        self.permission_manager = PermissionManager()
        self.encrypted_flags = {}

    def get_current_path(self):
        return "/".join([d.name for d in self.path_stack])

    def get_tree_structure(self, directory=None):
        with self.lock:
            if directory is None:
                directory = self.root
            result = {
                'type': 'dir',
                'name': directory.name,
                'children': []
            }
            for subdir in directory.subdirectories.values():
                result['children'].append(self.get_tree_structure(subdir))
            for file in directory.files.values():
                result['children'].append({
                    'type': 'file',
                    'name': file.name,
                    'size': file.size,
                    'encrypted': self.is_encrypted(file.name)
                })
            return result

    def mkdir(self, name):
        with self.lock:
            self.current_directory.create_subdirectory(name)

    def cd(self, name):
        with self.lock:
            if name == "..":
                if len(self.path_stack) > 1:
                    self.path_stack.pop()
            elif name in self.current_directory.subdirectories:
                self.path_stack.append(self.current_directory.subdirectories[name])
            else:
                print("Directory not found.")
            self.current_directory = self.path_stack[-1]

    def is_encrypted(self, filename):
        return self.encrypted_flags.get(filename, False)
    
    def check_password(self, filename, password):
        file = self.current_directory.files.get(filename)
        if file is None:
            raise FileNotFoundError(f"File '{filename}' not found.")

        if not isinstance(file, EncryptedFile) or not hasattr(file, "check_password"):
            raise TypeError("This file is not encrypted or does not support password checking.")

        return file.check_password(password)



    def set_encrypted_flag(self, filename, encrypted=True):
        self.encrypted_flags[filename] = encrypted

    def encrypt_content(self, content, password):
        key = Fernet.generate_key()
        cipher = Fernet(key)
        data = content.encode('utf-8') if isinstance(content, str) else content
        encrypted = cipher.encrypt(data)
        return encrypted

    def create_file(self, name, content=""):
        self.current_directory.create_file(name, content, storage=self.storage, cache=self.cache)
        self.set_encrypted_flag(name, False)

    def write_file(self, name, content, password=None):
        if password:
            key = EncryptedFile.derive_key_from_password(password)
            if name not in self.current_directory.files or not isinstance(self.current_directory.files[name], EncryptedFile):
                enc_file = EncryptedFile(name, content, key=key, owner=self.user_manager.get_current_user())
                self.current_directory.files[name] = enc_file
                self.set_encrypted_flag(name, True)
            else:
                file = self.current_directory.files[name]
                if isinstance(file, EncryptedFile):
                    if file.key != key:
                        raise PermissionError("Wrong password for existing encrypted file.")
                    file.write(content)
                else:
                    raise TypeError("Existing file is not encrypted.")
            self.set_encrypted_flag(name, True)
        else:
            if name not in self.current_directory.files or isinstance(self.current_directory.files[name], EncryptedFile):
                self.create_file(name, content)
                self.set_encrypted_flag(name, False)
            else:
                file = self.current_directory.files[name]
                file.write(content)
            self.set_encrypted_flag(name, False)


    def read_file(self, name, password=None):
        file = self.current_directory.files.get(name)
        if not file:
            return "File not found."
        
        ext = os.path.splitext(name)[1].lower()
        if ext not in ['.txt', '.py', '.json', '.md']:
            return "[Unsupported or binary file type.]"

        if self.is_encrypted(name):
            if not isinstance(file, EncryptedFile):
                raise TypeError("File encryption state mismatch.")

            if password is None:
                raise PermissionError("Password required to decrypt this file.")

            if not file.check_password(password):
                raise PermissionError("Invalid password.")

            decrypted = file.read()
            try:
                return decrypted.decode('utf-8')
            except UnicodeDecodeError:
                return "[Decryption successful, but content is not UTF-8 text.]"

        else:
            data = file.read()
            try:
                return data.decode('utf-8')
            except UnicodeDecodeError:
                return "[Binary file] Cannot decode as UTF-8 text."


    def file_info(self, name):
        with self.lock:
            file = self.current_directory.files.get(name)
            if file:
                return {
                    "name": file.name,
                    "size": file.size,
                    "created_at": file.created_at,
                    "encrypted": self.is_encrypted(name)
                }
            else:
                return "File not found."

    def dir_info(self, name):
        with self.lock:
            directory = self.current_directory.subdirectories.get(name)
            if directory:
                return {
                    "name": directory.name,
                    "created_at": directory.created_at,
                    "folders": len(directory.subdirectories),
                    "files": len(directory.files)
                }
            else:
                return "Directory not found."

    def delete_file(self, name):
        with self.lock:
            if name in self.current_directory.files:
                del self.current_directory.files[name]
                self.encrypted_flags.pop(name, None)
            else:
                raise FileNotFoundError(f"File '{name}' not found.")

    def delete_directory(self, name):
        with self.lock:
            if name in self.current_directory.subdirectories:
                del self.current_directory.subdirectories[name]
            else:
                raise FileNotFoundError(f"Directory '{name}' not found.")
