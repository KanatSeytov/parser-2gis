import tkinter as tk
from typing import Any


class CustomEntry(tk.Entry):
    """Custom entry widget that report on internal widget commands."""
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        # Create a proxy for the underlying widget
        self._orig = self._w + '_orig'
        self.tk.call('rename', self._w, self._orig)
        self.tk.createcommand(self._w, self._proxy)

    def _proxy(self, command: Any, *args) -> Any:
        # Let the actual widget perform the requested action
        cmd = (self._orig, command) + args

        try:
            result = self.tk.call(cmd)
        except tk.TclError:
            result = ''

        # Generate an event if something was added or deleted
        if command in ('insert', 'delete', 'replace'):
            self.event_generate('<<Change>>', when='tail')

        return result
