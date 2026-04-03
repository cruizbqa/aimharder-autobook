from abc import ABC, abstractmethod
import requests

class Authenticator(ABC):
    @abstractmethod
    def login(self, session: requests.Session) -> bool:
        """Log in to the service and populate the session with credentials."""
        pass

    @abstractmethod
    def logout(self, session: requests.Session) -> None:
        """Log out from the service."""
        pass
