from abc import ABC, abstractmethod

class Notifier(ABC):
    @abstractmethod
    def send_message(self, message: str) -> None:
        """Send a notification message."""
        pass
