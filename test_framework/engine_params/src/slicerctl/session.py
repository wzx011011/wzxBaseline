from .client import SlicerProc
from .client import EngineClient
from .injector import CommandInjector


# ----------------- 起 Server + 建 Client + 起队列 -----------------
class EngineSession:
    """with EngineSession(...) as (client, injector):"""

    def __init__(self, exe_path, log_path, cli_args,
                 host, port,
                 timeout=30.0,
                 inter_command_delay=0.2, retries=1, backoff=0.5):
        self.proc = SlicerProc(exe_path,
                               log_path,
                               cli_args,
                               host,
                               port)
        self.client = EngineClient(host=host, port=port, timeout=timeout)
        self.injector = CommandInjector(self.client,
                                        inter_command_delay=inter_command_delay,
                                        retries=retries, backoff=backoff)

    def __enter__(self):
        self.proc.start_if_needed()
        self.client.connect()
        self.injector.start()
        return self.client, self.injector

    def __exit__(self, exc_type, exc, tb):
        try:
            self.injector.stop()
            self.client.close()
        finally:
            self.proc.stop()
        return False
