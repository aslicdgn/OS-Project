import time
import threading
from filesystem.mobile_fs import FileSystem
from memory.memory_manager import MemoryManager
from process.pcb import PCB
from process.scheduler import Scheduler
from concurrency.shared_resources import shared_photo_queue, queue_condition

class CameraTask(threading.Thread):
    def __init__(self, fs: FileSystem, log_fn=None):
        super().__init__(daemon=True)
        self.fs = fs
        self.log_fn = log_fn
        self.counter = 1
        self.running = True

    def run(self):
        while self.running:
            time.sleep(2)
            filename = f"photo_{self.counter}.jpg"
            self.fs.create_file(filename, "image-data")

            with queue_condition:
                shared_photo_queue.put(filename)
                queue_condition.notify()

            msg = f"[CameraTask] {filename} created and added to the queue."
            print(msg)
            if self.log_fn:
                self.log_fn(msg)
            self.counter += 1

    def stop(self):
        self.running = False


class MusicTask(threading.Thread):
    def __init__(self, memory: MemoryManager, pid: int):
        super().__init__(daemon=True)
        self.memory = memory
        self.pid = pid
        self.running = True
        self.size = 1

    def run(self):
        while self.running:
            time.sleep(3)
            success = self.memory.allocate(self.pid, self.size)
            print(f"[Music] {self.size} page(s) allocated → Success? {success}")

    def stop(self):
        self.running = False


class SchedulerTask(threading.Thread):
    def __init__(self, scheduler: Scheduler):
        super().__init__(daemon=True)
        self.scheduler = scheduler
        self.pid_counter = 100
        self.running = True

    def run(self):
        while self.running:
            time.sleep(4)
            process = PCB(pid=self.pid_counter, app_name=f"BG_{self.pid_counter}", priority=0)
            self.scheduler.add_process(process)
            print(f"[Scheduler] {process.app_name} added to background queue.")
            self.pid_counter += 1

    def stop(self):
        self.running = False

class PhotoConsumer(threading.Thread):
    def __init__(self, log_fn=None, update_fn=None):
        super().__init__(daemon=True)
        self.log_fn = log_fn
        self.update_fn = update_fn
        self.running = True

    def run(self):
        while self.running:
            try:
                with queue_condition:
                    while shared_photo_queue.empty():
                        queue_condition.wait()
                    filename = shared_photo_queue.get()

                time.sleep(2)  # Simüle edilmiş işlem süresi
                msg = f"[PhotoConsumer] {filename} processed."
                print(msg)
                if self.log_fn:
                    self.log_fn(msg)
                if self.update_fn:
                    self.update_fn()

            except Exception as e:
                continue  # Herhangi bir beklenmeyen hata olursa atla
    def stop(self):
        self.running = False
