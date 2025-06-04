import time

class File:
    def __init__(self, name, content=""):
        self.name = name
        self.content = content
        self.size = len(content.encode('utf-8'))  # byte cinsinden
        self.created_at = time.ctime()

    def write(self, content):
        self.content = content
        self.size = len(content.encode('utf-8'))


class Directory:
    def __init__(self, name):
        self.name = name
        self.files = {}  # Dosya adı -> File nesnesi
        self.subdirectories = {}  # Klasör adı -> Directory nesnesi
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

    def mkdir(self, name):
        self.current_directory.create_subdirectory(name)

    def cd(self, name):
        if name == "..":
            if len(self.path_stack) > 1:
                self.path_stack.pop()
        elif name in self.current_directory.subdirectories:
            self.path_stack.append(self.current_directory.subdirectories[name])
        else:
            print("Directory not found.")
        self.current_directory = self.path_stack[-1]

    def create_file(self, name):
        self.current_directory.create_file(name)

    def write_file(self, name, content):
        if name not in self.current_directory.files:
            self.create_file(name, content)
        else:
            self.current_directory.files[name].write(content)

    def read_file(self, name):
        file = self.current_directory.files.get(name)
        if file:
            return file.content
        else:
            return "File not found."

    def ls(self):
        dirs = list(self.current_directory.subdirectories.keys())
        files = list(self.current_directory.files.keys())
        return dirs, files
    
    def list_files(self):
        return [f"{f.name} ({f.size} bytes)" for f in self.current_directory.files.values()]

    def find(self, name, directory=None, path="root"):
        if directory is None:
            directory = self.root
        results = []
        # Dosya varsa
        if name in directory.files:
            results.append(f"{path}/{name} (file)")
        # Klasör varsa
        if name in directory.subdirectories:
            results.append(f"{path}/{name} (directory)")
        # Rekürsif ara
        for sub_name, sub_dir in directory.subdirectories.items():
            results.extend(self.find(name, sub_dir, f"{path}/{sub_name}"))
        return results

    def file_info(self, name):
        file = self.current_directory.files.get(name)
        if file:
            return {
                "name": file.name,
                "size": file.size,
                "created_at": file.created_at
            }
        else:
            return "File not found."
