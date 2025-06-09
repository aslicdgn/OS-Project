from .scheduler import Scheduler

class PowerAwareScheduler(Scheduler):
    def next_process(self):
        candidates = list(self.foreground_queue) + list(self.background_queue)
        if not candidates:
            return None
        selected = min(candidates, key=lambda pcb: pcb.energy_usage)
        self.remove_process(selected.pid)
        return selected