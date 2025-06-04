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
        # Status Bar
        self.status_frame = ttk.Frame(self)
        self.status_frame.pack(fill="x", padx=10, pady=(10, 0))
        
        # Background tasks status
        self.bg_status = ttk.Label(self.status_frame, text="Background Tasks: Stopped", 
                                 foreground="red", relief="sunken", padding=5)
        self.bg_status.pack(side="left", padx=2)
        
        # Memory status
        self.mem_status = ttk.Label(self.status_frame, text="Memory: 0/0 KB", 
                                  relief="sunken", padding=5)
        self.mem_status.pack(side="left", padx=2)
        
        # Process count
        self.proc_status = ttk.Label(self.status_frame, text="Processes: 0", 
                                   relief="sunken", padding=5)
        self.proc_status.pack(side="left", padx=2)
        
        # System time
        self.time_status = ttk.Label(self.status_frame, text="System Time: 00:00:00", 
                                   relief="sunken", padding=5)
        self.time_status.pack(side="right", padx=2)
        
        # System State Frame
        self.info_frame = ttk.LabelFrame(self, text="System State")
        self.info_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Process and Memory Panels
        top_panel = ttk.Frame(self.info_frame)
        top_panel.pack(fill="both", expand=True)
        
        # Process Panel
        proc_frame = ttk.LabelFrame(top_panel, text="Processes")
        proc_frame.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        
        self.process_text = tk.Text(proc_frame, height=10, width=50)
        self.process_text.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Memory Panel
        mem_frame = ttk.LabelFrame(top_panel, text="Memory")
        mem_frame.pack(side="right", fill="both", expand=True, padx=5, pady=5)
        
        # Memory visualization
        self.memory_canvas = tk.Canvas(mem_frame, height=150, bg='white')
        self.memory_canvas.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Memory stats
        self.mem_stats = ttk.Label(mem_frame, text="Total: 0 KB | Used: 0 KB | Free: 0 KB")
        self.mem_stats.pack(fill="x", padx=5, pady=(0, 5))
        
        # File System and Logs
        bottom_panel = ttk.Frame(self.info_frame)
        bottom_panel.pack(fill="both", expand=True)
        
        # File System Panel
        fs_frame = ttk.LabelFrame(bottom_panel, text="File System")
        fs_frame.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        
        self.file_text = tk.Text(fs_frame, height=8, width=50)
        self.file_text.pack(fill="both", expand=True, padx=5, pady=5)
        
        # System Log Panel
        log_frame = ttk.LabelFrame(bottom_panel, text="System Log")
        log_frame.pack(side="right", fill="both", expand=True, padx=5, pady=5)
        
        self.log_text = tk.Text(log_frame, height=8, width=50, state='disabled', 
                               bg='black', fg='lightgray')
        self.log_text.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Controls Frame
        self.control_frame = ttk.LabelFrame(self, text="Controls")
        self.control_frame.pack(fill="x", padx=10, pady=5)

        # Application control buttons
        ttk.Label(self.control_frame, text="Applications:").pack(side="left", padx=(0, 5))
        ttk.Button(self.control_frame, text="Launch Camera", 
                 command=self.launch_camera).pack(side="left", padx=2)
        ttk.Button(self.control_frame, text="Launch Music", 
                 command=self.launch_music).pack(side="left", padx=2)
        
        # Separator
        ttk.Separator(self.control_frame, orient='vertical').pack(side='left', padx=5, fill='y')
        
        # Process control buttons
        ttk.Label(self.control_frame, text="Process Control:").pack(side="left", padx=5)
        ttk.Button(self.control_frame, text="Close Camera", 
                 command=lambda: self.close_process_by_name("Camera")).pack(side="left", padx=2)
        ttk.Button(self.control_frame, text="Close Music", 
                 command=lambda: self.close_process_by_name("Music")).pack(side="left", padx=2)
        ttk.Button(self.control_frame, text="Close All", 
                 command=self.close_all_processes).pack(side="left", padx=2)
        
        # Separator
        ttk.Separator(self.control_frame, orient='vertical').pack(side='left', padx=5, fill='y')
        
        # Background tasks
        ttk.Label(self.control_frame, text="Tasks:").pack(side="left", padx=5)
        ttk.Button(self.control_frame, text="Start Background Tasks", 
                 command=self.start_background_tasks).pack(side="left", padx=2)
        ttk.Button(self.control_frame, text="Stop Tasks", 
                 command=self.stop_background_tasks).pack(side="left", padx=2)
        
        # Exit button with more padding
        ttk.Separator(self.control_frame, orient='vertical').pack(side='left', padx=5, fill='y')
        ttk.Button(self.control_frame, text="X", 
                 command=self.quit, width=3).pack(side="right", padx=(10, 0))

    def launch_camera(self):
        app = PCB(pid=1, app_name="Camera", state="READY", priority=1)
        self.scheduler.add_process(app)
        self.memory.allocate(app.pid, 5)
        self.fs.create_file("photo1.jpg", content="binarydata...")
        self.refresh()

    def launch_music(self):
        app = PCB(pid=2, app_name="Music", state="READY", priority=0)
        self.scheduler.add_process(app)
        self.memory.allocate(app.pid, 3)
        self.fs.create_file("song.mp3", content="musicdata...")
        self.refresh()

    def log_message(self, message):
        """Add a message to the system log"""
        self.log_text.config(state='normal')
        timestamp = self.get_current_time()
        self.log_text.insert('end', f"[{timestamp}] {message}\n")
        self.log_text.see('end')
        self.log_text.config(state='disabled')
    
    def get_current_time(self):
        """Get current time in HH:MM:SS format"""
        from datetime import datetime
        return datetime.now().strftime("%H:%M:%S")

    def update_status_bar(self):
        """Update all status bar information"""
        # Update background tasks status
        bg_running = any([t.is_alive() if hasattr(t, 'is_alive') else False 
                         for t in [self.bg_camera, self.bg_music, self.bg_scheduler]])
        bg_text = "Background Tasks: Running" if bg_running else "Background Tasks: Stopped"
        self.bg_status.config(text=bg_text, 
                            foreground="green" if bg_running else "red")
        
        # Update memory status
        used = sum(1 for p in self.memory.pages if p is not None)
        total = len(self.memory.pages)
        self.mem_status.config(text=f"Memory: {used}/{total} KB")
        
        # Update process count
        proc_count = sum(len(q) for q in self.scheduler.list_queues().values())
        self.proc_status.config(text=f"Processes: {proc_count}")
        
        # Update time
        self.time_status.config(text=f"System Time: {self.get_current_time()}")
    
    def refresh(self):
        self.update_process_display()
        self.update_memory_display()
        self.update_file_display()
        self.update_status_bar()
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
        width = self.memory_canvas.winfo_width()
        height = self.memory_canvas.winfo_height()
        
        # Draw memory blocks
        cell_width = max(10, width / len(self.memory.pages))
        for i, page in enumerate(self.memory.pages):
            x1 = i * cell_width
            x2 = (i + 1) * cell_width
            
            # Different colors for different processes
            if page is None:
                color = "#f0f0f0"  # Free memory
            else:
                # Generate a color based on process ID for better visualization
                import hashlib
                color = f"#{hashlib.md5(str(page).encode()).hexdigest()[:6]}"
            
            self.memory_canvas.create_rectangle(x1, 10, x2, height-30, 
                                              fill=color, outline="#ccc")
            if page is not None:
                self.memory_canvas.create_text(x1 + cell_width/2, height-15, 
                                             text=str(page), font=("Arial", 7))
        
        # Update memory stats
        used = sum(1 for p in self.memory.pages if p is not None)
        total = len(self.memory.pages)
        self.mem_stats.config(
            text=f"Total: {total} KB | Used: {used} KB | Free: {total - used} KB | "
                 f"Usage: {used/total*100:.1f}%" if total > 0 else "0%")

    def update_file_display(self):
        self.file_text.delete("1.0", tk.END)
        files = self.fs.list_files()
        self.file_text.insert(tk.END, "Files:\n")
        for f in files:
            self.file_text.insert(tk.END, f"  {f}\n")
        
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
        self.log_message("Starting background tasks...")
        try:
            if not hasattr(self.bg_camera, 'is_alive') or not self.bg_camera.is_alive():
                self.bg_camera.start()
                self.log_message("Camera task started")
            if not hasattr(self.bg_music, 'is_alive') or not self.bg_music.is_alive():
                self.bg_music.start()
                self.log_message("Music task started")
            if not hasattr(self.bg_scheduler, 'is_alive') or not self.bg_scheduler.is_alive():
                self.bg_scheduler.start()
                self.log_message("Scheduler task started")
        except Exception as e:
            self.log_message(f"Error starting background tasks: {str(e)}")

    def stop_background_tasks(self):
        self.log_message("Stopping background tasks...")
        try:
            self.bg_camera.stop()
            self.bg_music.stop()
            self.bg_scheduler.stop()
            self.log_message("All background tasks stopped")
        except Exception as e:
            self.log_message(f"Error stopping background tasks: {str(e)}")

if __name__ == "__main__":
    app = OSVisualizer()
    app.mainloop()


