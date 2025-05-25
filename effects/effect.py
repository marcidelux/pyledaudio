from abc import ABC, abstractmethod
from typing import List, Optional
from .protocol import Command

class Effect(ABC):
    @abstractmethod
    def update(self, band_levels: Optional[bytes] = None) -> None:
        """Calculate the effect based on the provided band levels."""
        pass

    @abstractmethod
    def get_commands(self) -> List[Command]:
        """Return a list of commands to be sent to the LED strips."""
        pass