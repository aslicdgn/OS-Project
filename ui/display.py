def display_pcb(pcb):
    print(pcb)

def display_memory(memory_manager):
    for i, page in enumerate(memory_manager.pages):
        if page is not None:
            print(f"Page {i}: PID {page}")
