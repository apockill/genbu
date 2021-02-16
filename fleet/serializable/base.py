from typing import Dict, Any

from abc import ABC, abstractmethod, abstractclassmethod


class BaseSerializable(ABC):
    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        """Convert the class to a serializable python object"""

    @classmethod
    @abstractmethod
    def from_dict(cls, obj: Dict[str, Any]) -> 'BaseSerializable':
        """Get the class from a serializable object"""
