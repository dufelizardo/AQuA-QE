from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List
from requirements.contracts.requirement_snapshot import RequirementSnapshot
from testing.contracts import TestType, TestTechnique


@dataclass
class ScenarioBlueprint:
    requirement_id:         str
    acceptance_criteria_id: str
    title_hint:             str
    test_type:              TestType
    technique:              TestTechnique
    context_hint:           str
    automation_candidate:   bool = False


class ITechnique(ABC):
    @abstractmethod
    def generate_blueprints(self, snap: RequirementSnapshot) -> List[ScenarioBlueprint]: ...


class EquivalencePartitionTechnique(ITechnique):
    def generate_blueprints(self, snap: RequirementSnapshot) -> List[ScenarioBlueprint]:
        blueprints = []
        for ac in snap.acceptance_criteria:
            blueprints.append(ScenarioBlueprint(
                requirement_id=snap.id, acceptance_criteria_id=ac.id,
                title_hint=f"Cenário válido: {ac.description[:60]}",
                test_type=TestType.FUNCTIONAL, technique=TestTechnique.EQUIVALENCE,
                context_hint=f"Dado: {ac.given}\nQuando: {ac.when}\nEntão: {ac.then}\nGere cenário com entrada VÁLIDA.",
                automation_candidate=True,
            ))
            if snap.is_critical():
                blueprints.append(ScenarioBlueprint(
                    requirement_id=snap.id, acceptance_criteria_id=ac.id,
                    title_hint=f"Cenário inválido: {ac.description[:60]}",
                    test_type=TestType.NEGATIVE, technique=TestTechnique.EQUIVALENCE,
                    context_hint=f"Dado: {ac.given}\nGere cenário com entrada INVÁLIDA.",
                    automation_candidate=True,
                ))
        return blueprints


class BoundaryValueTechnique(ITechnique):
    _LIMIT_KEYWORDS = ["máximo","mínimo","limite","até","pelo menos","no máximo","no mínimo","entre","faixa"]

    def generate_blueprints(self, snap: RequirementSnapshot) -> List[ScenarioBlueprint]:
        blueprints = []
        for ac in snap.acceptance_criteria:
            text = (ac.description + ac.when + ac.then).lower()
            if not any(kw in text for kw in self._LIMIT_KEYWORDS):
                continue
            for boundary, hint in [
                ("no limite inferior", "valor exatamente no limite mínimo permitido"),
                ("abaixo do limite",   "valor abaixo do limite mínimo (deve falhar)"),
                ("no limite superior", "valor exatamente no limite máximo permitido"),
                ("acima do limite",    "valor acima do limite máximo (deve falhar)"),
            ]:
                is_neg = "abaixo" in boundary or "acima" in boundary
                blueprints.append(ScenarioBlueprint(
                    requirement_id=snap.id, acceptance_criteria_id=ac.id,
                    title_hint=f"Valor limite — {boundary}: {ac.description[:40]}",
                    test_type=TestType.NEGATIVE if is_neg else TestType.FUNCTIONAL,
                    technique=TestTechnique.BOUNDARY_VALUE,
                    context_hint=f"Critério: {ac.description}\nGere cenário testando o {hint}.",
                    automation_candidate=True,
                ))
        return blueprints


class DecisionTableTechnique(ITechnique):
    _COND_KEYWORDS = ["se ","quando ","caso ","e "," ou ","desde que"]

    def generate_blueprints(self, snap: RequirementSnapshot) -> List[ScenarioBlueprint]:
        text = snap.description.lower()
        cond_count = sum(1 for kw in self._COND_KEYWORDS if kw in text)
        if cond_count < 2:
            return []
        first_ac_id = snap.acceptance_criteria[0].id if snap.acceptance_criteria else ""
        blueprints = []
        for label, hint in [
            ("Todas as condições verdadeiras", "todas as condições simultaneamente satisfeitas"),
            ("Primeira condição falsa",         "apenas a primeira condição não satisfeita"),
            ("Nenhuma condição satisfeita",     "nenhuma condição satisfeita"),
        ]:
            blueprints.append(ScenarioBlueprint(
                requirement_id=snap.id, acceptance_criteria_id=first_ac_id,
                title_hint=f"Decisão — {label}",
                test_type=TestType.FUNCTIONAL, technique=TestTechnique.DECISION_TABLE,
                context_hint=f"Requisito: {snap.description[:200]}\nGere cenário com {hint}.",
                automation_candidate=snap.is_critical(),
            ))
        return blueprints


def select_techniques(snap: RequirementSnapshot) -> List[ITechnique]:
    techniques: List[ITechnique] = [EquivalencePartitionTechnique()]
    if snap.acceptance_criteria:
        techniques.append(BoundaryValueTechnique())
    if snap.req_type.value == "RF":
        techniques.append(DecisionTableTechnique())
    return techniques
