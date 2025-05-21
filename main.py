from process.pcb import PCB
from process.scheduler import Scheduler
from memory.memory_manager import MemoryManager
from filesystem.mobile_fs import FileSystem
from ui.display import display_pcb, display_memory

if __name__ == "__main__":
    scheduler = Scheduler()
    memory = MemoryManager(size=50)
    fs = FileSystem()

    app1 = PCB(pid=1, app_name="Camera", state="READY", priority=1)
    app2 = PCB(pid=2, app_name="Music", state="READY", priority=0)

    scheduler.add_process(app1)
    scheduler.add_process(app2)

    print("=== Queues ===")
    for qname, qlist in scheduler.list_queues().items():
        print(f"{qname.capitalize()}:")
        for pcb in qlist:
            display_pcb(pcb)

    memory.allocate(app1.pid, 5)
    memory.allocate(app2.pid, 3)
    print("\n=== Memory State ===")
    display_memory(memory)

    fs.create_file("photo1.jpg", "binarydata...")
    fs.create_file("song.mp3", "musicdata...")
    print("\n=== Files ===")
    print("Files:", fs.list_files())
