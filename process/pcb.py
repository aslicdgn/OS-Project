class PCB:
    def __init__(self, pid, app_name, state="NEW", priority=0, program_counter=0):
        self.pid = pid
        self.app_name = app_name
        self.state = state
        self.priority = priority
        self.program_counter = program_counter

    def __str__(self):
        return f"[PID: {self.pid}] {self.app_name} | State: {self.state} | Priority: {self.priority}"
    def __repr__(self):
        return f"PCB(pid={self.pid}, app_name={self.app_name}, state={self.state}, priority={self.priority})"
