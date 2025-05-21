class MemoryManager:
    def __init__(self, size=256):
        self.size = size
        self.pages = [None] * size

    def allocate(self, pid, size):
        allocated = 0
        for i in range(self.size):
            if self.pages[i] is None and allocated < size:
                self.pages[i] = pid
                allocated += 1
        if allocated < size:
            print (f"Not enough memory to allocate {size} pages for PID {pid}.")
            return False
        return True
    
    def deallocate(self, pid):
        for i in range(self.size):
            if self.pages[i] == pid:
                self.pages[i] = None
