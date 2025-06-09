from process.scheduler import Scheduler
from process.pcb import PCB
import random
ENERGY_USAGE = {
    "Camera": 5,
    "Music": 3,
}
class ProcessManager:
    def __init__(self, scheduler, start_pid=1):
        self.scheduler = scheduler
        self.pid_counter = start_pid

    def create_process(self, app_name: str, priority=0) -> PCB:
        base_energy = ENERGY_USAGE.get(app_name, 5)
        energy_usage = max(1, base_energy + random.randint(-1, 1))
        pcb = PCB(
            pid=self.pid_counter,
            app_name=app_name,
            state="READY",
            priority=priority,
            energy_usage=energy_usage
        )
        self.scheduler.add_process(pcb)
        print(f"Created: {pcb}")
        self.pid_counter += 1
        return pcb

    def terminate_process(self, pid: int) -> bool:
        queues = self.scheduler.list_queues()
        for queue in queues.values():
            for pcb in queue:
                if pcb.pid == pid:
                    pcb.state = "TERMINATED"
                    self.scheduler.remove_process(pid)
                    print(f"Terminated: [PID: {pid}] {pcb.app_name}")
                    return True
        print(f"PID {pid} not found")
        return False

    def switch_process(self) -> PCB:
        pcb = self.scheduler.next_process()
        if pcb:
            pcb.state = "RUNNING"
            print(f"Switched to: {pcb}")
            return pcb
        print("No process to switch to.")
        return None
