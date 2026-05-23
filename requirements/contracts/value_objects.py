# Re-export para contextos downstream importarem sem depender de requirements.domain diretamente
from requirements.domain.value_objects import RequirementType, Priority, RequirementStatus, QualityScore, RequirementVersion

__all__ = ["RequirementType", "Priority", "RequirementStatus", "QualityScore", "RequirementVersion"]
