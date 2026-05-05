# skill_base/base_skill.py

from abc import ABC, abstractmethod
from typing import Any


class SkillBase(ABC):
    """
    Interface-like base class for all skills.

    Every skill must provide:
    - name
    - description
    - run(user_prompt)
    """

    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @property
    @abstractmethod
    def author(self) -> str:
        pass

    @property
    @abstractmethod
    def parse_strings(self) -> str:
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        pass

    @abstractmethod
    def run(self, user_prompt: str, **kwargs: Any) -> str:
        """
        pass in user prompt and any arguments required to run the skill.
        """
        pass