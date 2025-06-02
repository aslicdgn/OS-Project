import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import tkinter as tk
from tkinter import ttk
from process.pcb import PCB
from process.scheduler import Scheduler
from process.manager import ProcessManager
from memory.memory_manager import MemoryManager
from filesystem.mobile_fs import FileSystem

from concurrency.background_tasks import CameraTask, MusicTask, SchedulerTask

class OSVisualizer(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Mini Mobile OS - Single User")
        self.geometry("1080x600")

        self.scheduler = Scheduler()
        self.process_manager = ProcessManager(self.scheduler)
        self.memory = MemoryManager(size=50)
        self.fs = FileSystem()

        self.bg_camera = CameraTask(self.fs)
        self.bg_music = MusicTask(self.memory, pid=99)
        self.bg_scheduler = SchedulerTask(self.scheduler)

        self.setup_ui()
        self.refresh()



    def setup_ui(self):
        self.info_frame = ttk.LabelFrame(self, text="System State")
        self.info_frame.pack(fill="x", padx=10, pady=5)

        self.process_text = tk.Text(self.info_frame, height=6, width=80)
        self.process_text.pack()

        self.memory_label = ttk.LabelFrame(self, text="Memory")
        self.memory_label.pack(fill="x", padx=10, pady=5)

        self.memory_canvas = tk.Canvas(self.memory_label, height=50)
        self.memory_canvas.pack(fill="x")

        self.file_frame = ttk.LabelFrame(self, text="File System")
        self.file_frame.pack(fill="both", expand=True, padx=10, pady=5)

        self.file_text = tk.Text(self.file_frame, height=10, width=80)
        self.file_text.pack()

        self.control_frame = ttk.LabelFrame(self, text="Controls")
        self.control_frame.pack(fill="x", padx=10, pady=5)

        ttk.Button(self.control_frame, text="Launch Camera", command=self.launch_camera).pack(side="left", padx=3)
        ttk.Button(self.control_frame, text="Launch Music", command=self.launch_music).pack(side="left", padx=3)
        ttk.Button(self.control_frame, text="Close Camera", command=lambda: self.close_process_by_name("Camera")).pack(side="left", padx=3)
        ttk.Button(self.control_frame, text="Close Music", command=lambda: self.close_process_by_name("Music")).pack(side="left", padx=3)
        ttk.Button(self.control_frame, text="Start Background Tasks", command=self.start_background_tasks).pack(side="left", padx=3)
        ttk.Button(self.control_frame, text="Stop Tasks", command=self.stop_background_tasks).pack(side="left", padx=3)
        ttk.Button(self.control_frame, text="Close All", command=self.close_all_processes).pack(side="left", padx=3)
        ttk.Button(self.control_frame, text="X", command=self.quit).pack(side="left", padx=1)

    def launch_camera(self):
        app = PCB(pid=1, app_name="Camera", state="READY", priority=1)
        self.scheduler.add_process(app)
        self.memory.allocate(app.pid, 5)
        self.fs.create_file("photo1.jpg", "binarydata...")
        self.refresh()

    def launch_music(self):
        app = PCB(pid=2, app_name="Music", state="READY", priority=0)
        self.scheduler.add_process(app)
        self.memory.allocate(app.pid, 3)
        self.fs.create_file("song.mp3", "musicdata...")
        self.refresh()

    def refresh(self):
        self.update_process_display()
        self.update_memory_display()
        self.update_file_display()

        self.after(1000, self.refresh)

    def update_process_display(self):
        self.process_text.delete("1.0", tk.END)
        queues = self.scheduler.list_queues()
        for name, q in queues.items():
            self.process_text.insert(tk.END, f"{name.capitalize()} Queue:\n")
            for pcb in q:
                self.process_text.insert(tk.END, f"  {pcb}\n")
            self.process_text.insert(tk.END, "\n")

    def update_memory_display(self):
        self.memory_canvas.delete("all")
        cell_width = 10
        for i, page in enumerate(self.memory.pages):
            color = "lightgray" if page is None else "skyblue"
            self.memory_canvas.create_rectangle(i*cell_width, 10, (i+1)*cell_width, 40, fill=color, outline="black")
            if page is not None:
                self.memory_canvas.create_text(i*cell_width+5, 25, text=str(page), font=("Arial", 6))

    def update_file_display(self):
        self.file_text.delete("1.0", tk.END)
        self.file_text.insert(tk.END, f"Files: {', '.join(self.fs.list_files())}\n")
        
    def close_process_by_name(self, app_name):
        queues = self.scheduler.list_queues()
        for queue in queues.values():
            for pcb in queue:
                if pcb.app_name == app_name:
                    self.process_manager.terminate_process(pcb.pid)
                    self.memory.deallocate(pcb.pid)
                    self.refresh()
                    return
        print(f"No running process found with name '{app_name}'")

    def close_all_processes(self):
        pids = [pcb.pid for q in self.scheduler.list_queues().values() for pcb in q]
        for pid in pids:
            self.process_manager.terminate_process(pid)
            self.memory.deallocate(pid)
        self.refresh()

    def start_background_tasks(self):
        print("[Main] Arka plan görevleri başlatılıyor...")
        self.bg_camera.start()
        self.bg_music.start()
        self.bg_scheduler.start()

    def stop_background_tasks(self):
        print("[Main] Arka plan görevleri durduruluyor...")
        self.bg_camera.stop()
        self.bg_music.stop()
        self.bg_scheduler.stop()

if __name__ == "__main__":
    app = OSVisualizer()
    app.mainloop()


