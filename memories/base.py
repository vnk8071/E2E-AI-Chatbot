from abc import ABC, abstractmethod


class MemoryBase(ABC):
    """Base class for all memories."""

    @abstractmethod
    def key(self):
        """Return all keys in the memory."""
        pass

    @abstractmethod
    def get_answer(self, question):
        """Return the answer for the question."""
        pass

    @abstractmethod
    def add_chat_history(self, question, answer):
        """Add a pair of (question, answer) to the memory."""
        pass

    @abstractmethod
    def check_length(self, key):
        """Check if the memory is full."""
        pass
