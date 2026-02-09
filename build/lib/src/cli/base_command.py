from abc import ABC, abstractmethod
import argparse
from typing import Optional

class BaseCommand(ABC):
    """
    Abstract base class for all CLI commands.
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Command name used in CLI (e.g., 'campaign')."""
        pass
    
    @property
    @abstractmethod
    def help(self) -> str:
        """Help text displayed in argparse."""
        pass

    @abstractmethod
    def register_arguments(self, parser: argparse.ArgumentParser) -> None:
        """Register arguments for this command sub-parser."""
        pass

    @abstractmethod
    def execute(self, args: argparse.Namespace) -> None:
        """Execute the command logic."""
        pass
