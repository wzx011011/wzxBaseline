"""Startup protocol tests using mocks only; no slicer process is launched."""
import unittest
from unittest.mock import Mock, patch

from test_framework.engine_params.src.slicerctl.session import EngineSession, EngineUnavailable


class SessionStartupTests(unittest.TestCase):
    def make_session(self):
        session = EngineSession("unused", "unused", [], "localhost", 12345)
        session.proc = Mock()
        session.client = Mock(timeout=30.0)
        session.injector = Mock()
        return session

    def test_queue_starts_only_after_ready(self):
        session = self.make_session()
        events = []

        def respond(*args, **kwargs):
            events.append("query")
            self.assertFalse(session.injector.start.called)
            return {"code": 0} if len(events) == 2 else {
                "code": 1, "error": "app not ready"
            }

        session.client.send_command.side_effect = respond
        with patch("test_framework.engine_params.src.slicerctl.session.time.sleep"):
            session.__enter__()
        self.assertEqual(events, ["query", "query"])
        session.injector.start.assert_called_once()
        self.assertEqual(session.client.send_command.call_args.args,
                         ("query_status", {"type": 0}))

    def test_timeout_cleans_up_without_starting_queue(self):
        session = self.make_session()
        session.startup_timeout = 1
        session.client.send_command.return_value = {"code": 1, "error": "app not ready"}
        with patch("test_framework.engine_params.src.slicerctl.session.time.monotonic",
                   side_effect=[0, 0, 2, 2]), patch(
                       "test_framework.engine_params.src.slicerctl.session.time.sleep"):
            with self.assertRaises(EngineUnavailable):
                session.__enter__()
        session.injector.start.assert_not_called()
        session.client.close.assert_called_once()
        session.proc.stop.assert_called_once()

    def test_unexpected_response_fails_immediately(self):
        session = self.make_session()
        session.client.send_command.return_value = {"code": 1, "error": "unknown command"}
        with self.assertRaises(EngineUnavailable):
            session.__enter__()
        session.client.send_command.assert_called_once()
        session.proc.stop.assert_called_once()

    def test_connection_failure_cleans_up(self):
        session = self.make_session()
        session.client.send_command.side_effect = ConnectionError("closed")
        with self.assertRaises(ConnectionError):
            session.__enter__()
        session.injector.start.assert_not_called()
        session.proc.stop.assert_called_once()

    def test_each_new_session_waits_for_ready(self):
        for _ in range(2):
            session = self.make_session()
            session.client.send_command.return_value = {"code": 0}
            session.__enter__()
            session.client.send_command.assert_called_once()
            session.__exit__(None, None, None)


if __name__ == "__main__":
    unittest.main()
