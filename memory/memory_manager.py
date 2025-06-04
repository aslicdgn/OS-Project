import threading


class MemoryManager:
    def __init__(self, size=256):
        self.size = size
        self.pages = [None] * size
        self.lock = threading.Lock()

    def allocate(self, pid, size):
        with self.lock:
            allocated = 0
            for i in range(self.size):
                if self.pages[i] is None and allocated < size:
                    self.pages[i] = pid
                    allocated += 1
            if allocated < size:
                print(f"Not enough memory to allocate {size} pages for PID {pid}.")
                return False
            return True

    def deallocate(self, pid):
        with self.lock:
            for i in range(self.size):
                if self.pages[i] == pid:
                    self.pages[i] = None
