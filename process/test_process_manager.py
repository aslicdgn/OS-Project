import unittest
from unittest.mock import MagicMock
from process.pcb import PCB
from process.manager import ProcessManager

class TestProcessManager(unittest.TestCase):
    def setUp(self):
        self.mock_scheduler = MagicMock()
        self.mock_scheduler.list_queues.return_value = {}
        self.mock_scheduler.next_process.return_value = None
        self.process_manager = ProcessManager(self.mock_scheduler, start_pid=1)

    def test_create_process(self):
        pcb = self.process_manager.create_process("TestApp", priority=5)
        self.assertEqual(pcb.pid, 1)
        self.assertEqual(pcb.app_name, "TestApp")
        self.assertEqual(pcb.state, "READY")
        self.assertEqual(pcb.priority, 5)
        self.mock_scheduler.add_process.assert_called_with(pcb)

    def test_terminate_process_found(self):
        pcb = PCB(pid=1, app_name="TestApp", state="READY", priority=0)
        self.mock_scheduler.list_queues.return_value = {"queue": [pcb]}
        
        result = self.process_manager.terminate_process(1)
        self.assertTrue(result)
        self.assertEqual(pcb.state, "TERMINATED")
        self.mock_scheduler.remove_process.assert_called_with(1)

    def test_terminate_process_not_found(self):
        self.mock_scheduler.list_queues.return_value = {"queue": []}
        result = self.process_manager.terminate_process(99)
        self.assertFalse(result)
        self.mock_scheduler.remove_process.assert_not_called()

    def test_switch_process_with_process(self):
        pcb = PCB(pid=1, app_name="TestApp", state="READY", priority=0)
        self.mock_scheduler.next_process.return_value = pcb

        switched_pcb = self.process_manager.switch_process()
        self.assertIs(switched_pcb, pcb)
        self.assertEqual(switched_pcb.state, "RUNNING")

    def test_switch_process_no_process(self):
        self.mock_scheduler.next_process.return_value = None
        switched_pcb = self.process_manager.switch_process()
        self.assertIsNone(switched_pcb)

if __name__ == '__main__':
    unittest.main()
