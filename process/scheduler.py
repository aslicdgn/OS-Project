from collections import deque

class Scheduler:
    def __init__(self):
        self.foreground_queue = deque()
        self.background_queue = deque()

    def add_process(self, pcb):
        if pcb.priority > 0:
            self.foreground_queue.append(pcb)
        else:
            self.background_queue.append(pcb)

    def next_process(self):
        if self.foreground_queue:
            return self.foreground_queue.popleft()
        elif self.background_queue:
            return self.background_queue.popleft()
        return None
    
    def remove_process(self, pid):
        for queue in (self.foreground_queue, self.background_queue):
            for pcb in list(queue):
                if pcb.pid == pid:
                    queue.remove(pcb)
                    return True
        return False
    
    def close_all_processes(self):
        self.foreground_queue.clear()
        self.background_queue.clear()
        return True

    def list_queues(self):
        return {
            "foreground": list(self.foreground_queue),
            "background": list(self.background_queue)
        }
