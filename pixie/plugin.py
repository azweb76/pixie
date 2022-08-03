from typing import Dict
from .runtime import PixieRuntime
from .steps import PixieStep


class PixiePlugin:
    def init(runtime: PixieRuntime):
        pass


class PixiePluginContext(dict):
    steps: Dict[str, PixieStep] = {}
    
    def add_step(self, step_name: str, step: PixieStep):
        self.steps[step_name] = step
