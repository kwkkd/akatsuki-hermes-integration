"""AkatsukiAgent adapter for Hermes compatibility."""

try:
    from hermes_agent import HermesAgent

    class AkatsukiAgent(HermesAgent):
        def __init__(self, model=None, tools=None, **kwargs):
            super().__init__(**kwargs)
            self._akatsuki_model = model
            self._akatsuki_tools = tools or []

        def chat(self, messages, **kwargs):
            return super().chat(messages, **kwargs)

except ImportError:
    from ..api.client import AkatsukiAPIClient
    from ..chat.tools import AkatsukiToolRegistry

    class AkatsukiAgent:
        def __init__(self, model=None, tools=None, **kwargs):
            self.model = model
            self.client = AkatsukiAPIClient()
            self.registry = AkatsukiToolRegistry()

        def chat(self, messages, **kwargs):
            return self.client.chat(messages, model=self.model)
