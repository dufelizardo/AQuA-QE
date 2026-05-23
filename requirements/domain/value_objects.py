from __future__ import annotations
from enum import Enum
from dataclasses import dataclass


class RequirementType(Enum):
    FUNCTIONAL = "RF"
    NON_FUNCTIONAL = "RNF"
    BUSINESS_RULE = "RN"
    CONSTRAINT = "CONSTRAINT"
    ASSUMPTION = "ASSUMPTION"


class Priority(Enum):
    MUST = "MUST"
    SHOULD = "SHOULD"
    COULD = "COULD"
    WONT = "WONT"


class RequirementStatus(Enum):
    DRAFT = "DRAFT"
    REVIEW = "REVIEW"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    OBSOLETE = "OBSOLETE"


@dataclass(frozen=True)
class QualityScore:
    clarity: float
    completeness: float
    testability: float
    consistency: float

    def __post_init__(self) -> None:
        for name, val in self.__dict__.items():
            if not (0.0 <= val <= 100.0):
                raise ValueError(f"QualityScore.{name} deve estar entre 0 e 100, recebido: {val}")

    @property
    def overall(self) -> float:
        return round(
            (self.clarity + self.completeness + self.testability + self.consistency) / 4, 2
        )

    def blocks_approval(self) -> bool:
        return self.clarity < 60.0


@dataclass(frozen=True)
class RequirementVersion:
    major: int
    minor: int
    changelog: str

    def __str__(self) -> str:
        return f"v{self.major}.{self.minor}"

    def next_minor(self, changelog: str) -> "RequirementVersion":
        return RequirementVersion(self.major, self.minor + 1, changelog)

    def next_major(self, changelog: str) -> "RequirementVersion":
        return RequirementVersion(self.major + 1, 0, changelog)
