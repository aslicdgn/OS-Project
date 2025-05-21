class FileSystem:
    def __init__(self):
        self.files = {}

    def create_file(self, filename, content=""):
        self.files[filename] = content

    def read_file(self, filename):
        return self.files.get(filename, "")

    def delete_file(self, filename):
        if filename in self.files:
            del self.files[filename]

    def list_files(self):
        return list(self.files.keys())
