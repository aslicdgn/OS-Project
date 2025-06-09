import time
import threading
import uuid
from collections import OrderedDict
from cryptography.fernet import Fernet
from .user import UserManager, PermissionManager, EncryptedFile

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

    def create_file(self, name, content=""):
        self.files[name] = File(name, content)

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

    def create_file(self, name, content=""):
        self.current_directory.files[name] = File(name, content, self.storage, self.cache)

    def create_encrypted_file(self, name, content="", key=None):
        user = self.user_manager.get_current_user()
        if not user:
            raise PermissionError("You must be logged in to create an encrypted file.")

        encrypted_file = EncryptedFile(name, content, key=key, owner=user.username)
        self.current_directory.files[name] = encrypted_file
        self.permission_manager.set_permissions(self.get_current_path() + "/" + name, owner=user.username)

    def write_file(self, name, content):
        if name not in self.current_directory.files:
            self.create_file(name, content)
        else:
            file = self.current_directory.files[name]
            file.write(content)

    def write_encrypted_file(self, name, content):
        user = self.user_manager.get_current_user()
        path = self.get_current_path() + "/" + name
        if not self.permission_manager.check_write(path, user.username):
            raise PermissionError("You do not have write access to this file.")

        file = self.current_directory.files.get(name)
        if isinstance(file, EncryptedFile):
            file.write(content)
        else:
            raise TypeError("This file is not encrypted.")

    def read_file(self, name):
        file = self.current_directory.files.get(name)
        return file.read().decode('utf-8') if file else "File not found."

    def read_encrypted_file(self, name):
        user = self.user_manager.get_current_user()
        path = self.get_current_path() + "/" + name
        if not self.permission_manager.check_read(path, user.username):
            raise PermissionError("You do not have read access to this file.")

        file = self.current_directory.files.get(name)
        if isinstance(file, EncryptedFile):
            return file.read().decode('utf-8')
        else:
            raise TypeError("This file is not encrypted.")

    def ls(self):
        with self.lock:
            dirs = list(self.current_directory.subdirectories.keys())
            files = list(self.current_directory.files.keys())
            return dirs, files

    def list_files(self):
        with self.lock:
            return [f"{f.name} ({f.size} bytes)" for f in self.current_directory.files.values()]

    def find(self, name, directory=None, path="root"):
        with self.lock:
            if directory is None:
                directory = self.root
            results = []
            if name in directory.files:
                results.append(f"{path}/{name} (file)")
            if name in directory.subdirectories:
                results.append(f"{path}/{name} (directory)")
            for sub_name, sub_dir in directory.subdirectories.items():
                results.extend(self.find(name, sub_dir, f"{path}/{sub_name}"))
            return results

    def file_info(self, name):
        with self.lock:
            file = self.current_directory.files.get(name)
            if file:
                return {
                    "name": file.name,
                    "size": file.size,
                    "created_at": file.created_at
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
            else:
                raise FileNotFoundError(f"File '{name}' not found.")

    def delete_directory(self, name):
        with self.lock:
            if name in self.current_directory.subdirectories:
                del self.current_directory.subdirectories[name]
            else:
                raise FileNotFoundError(f"Directory '{name}' not found.")