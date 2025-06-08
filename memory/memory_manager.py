from threading import Lock
from utils.config import MEMORY_SIZE

__all__ = ["PageFault", "MemoryManager"]

class PageFault(Exception):
    pass


class MemoryManager:
    FRAME_SIZE = 512

    def __init__(self):
        self.total_frames: int = MEMORY_SIZE
        self._frames: list[int | None] = [None] * self.total_frames
        self._page_tables: dict[int, list[int]] = {}
        self._lock = Lock()

    @property
    def pages(self) -> list[int | None]:
        return self._frames

    def stats(self) -> dict[str, int]:
        used = sum(1 for f in self._frames if f is not None)

        return {
            "total": self.total_frames,
            "used": used,
            "free": self.total_frames - used,
        }

    def allocate(self, pid: int, num_pages: int) -> bool:
        with self._lock:
            free_frames = [i for i, owner in enumerate(self._frames) if owner is None]
            if len(free_frames) < num_pages:
                return False

            taken = free_frames[:num_pages]
            for idx in taken:
                self._frames[idx] = pid

            self._page_tables.setdefault(pid, []).extend(taken)
            return True

    def deallocate(self, pid: int) -> None:
        with self._lock:
            if pid not in self._page_tables:
                return
            for idx in self._page_tables[pid]:
                self._frames[idx] = None
            del self._page_tables[pid]

    def translate(self, pid: int, logical_address: int) -> int:
        page_no, offset = divmod(logical_address, self.FRAME_SIZE)
        try:
            frame_idx = self._page_tables[pid][page_no]
        except (KeyError, IndexError):
            raise PageFault(f"Page fault in PID {pid}: page {page_no} not mapped")
        return frame_idx * self.FRAME_SIZE + offset

    def snapshot(self) -> str:
        with self._lock:
            rows = []
            for i in range(0, self.total_frames, 16):
                chunk = ''.join('.' if f is None else '#' for f in self._frames[i:i+16])
                rows.append(chunk)
            return '\n'.join(rows)



