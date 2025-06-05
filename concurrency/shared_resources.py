from queue import Queue
from threading import Condition

shared_photo_queue = Queue()
queue_condition = Condition()
