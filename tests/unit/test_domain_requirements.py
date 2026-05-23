import pytest
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from tests.conftest import make_requirement, make_quality_score
from requirements.domain.value_objects import QualityScore, RequirementVersion, RequirementStatus, Priority


class TestQualityScore:
    def test_overall_is_average(self):
        score = QualityScore(80.0, 60.0, 70.0, 90.0)
        assert score.overall == 75.0

    def test_blocks_approval_when_clarity_below_60(self):
        score = QualityScore(clarity=59.9, completeness=80.0, testability=80.0, consistency=80.0)
        assert score.blocks_approval() is True

    def test_does_not_block_at_exactly_60(self):
        score = QualityScore(clarity=60.0, completeness=80.0, testability=80.0, consistency=80.0)
        assert score.blocks_approval() is False

    def test_raises_on_score_above_100(self):
        with pytest.raises(ValueError):
            QualityScore(clarity=101.0, completeness=50.0, testability=50.0, consistency=50.0)

    def test_raises_on_negative_score(self):
        with pytest.raises(ValueError):
            QualityScore(clarity=-1.0, completeness=50.0, testability=50.0, consistency=50.0)

    def test_boundary_0_accepted(self):
        score = QualityScore(0.0, 0.0, 0.0, 0.0)
        assert score.overall == 0.0

    def test_boundary_100_accepted(self):
        score = QualityScore(100.0, 100.0, 100.0, 100.0)
        assert score.overall == 100.0


class TestRequirementVersion:
    def test_str_representation(self):
        v = RequirementVersion(2, 3, "fix")
        assert str(v) == "v2.3"

    def test_next_minor_increments(self):
        v = RequirementVersion(1, 0, "init")
        nxt = v.next_minor("update")
        assert nxt.major == 1 and nxt.minor == 1

    def test_next_major_resets_minor(self):
        v = RequirementVersion(1, 5, "x")
        nxt = v.next_major("breaking")
        assert nxt.major == 2 and nxt.minor == 0

    def test_immutability(self):
        v = RequirementVersion(1, 0, "init")
        v.next_minor("x")
        assert v.minor == 0  # original não mudou


class TestRequirementEntity:
    def test_refine_advances_minor_version(self):
        req = make_requirement()
        req.refine(title="Novo título", changelog="Refinamento")
        assert str(req.version) == "v1.1"
        assert req.status == RequirementStatus.REVIEW

    def test_refine_rejected_raises(self):
        req = make_requirement(status=RequirementStatus.REJECTED)
        with pytest.raises(ValueError, match="não pode ser refinado"):
            req.refine(title="x")

    def test_refine_obsolete_raises(self):
        req = make_requirement(status=RequirementStatus.OBSOLETE)
        with pytest.raises(ValueError):
            req.refine(title="x")

    def test_approve_with_good_score(self):
        req = make_requirement(status=RequirementStatus.REVIEW, quality_score=make_quality_score(clarity=75.0))
        req.approve("user-1")
        assert req.status == RequirementStatus.APPROVED

    def test_approve_blocked_by_low_clarity(self):
        req = make_requirement(status=RequirementStatus.REVIEW, quality_score=make_quality_score(clarity=55.0))
        with pytest.raises(ValueError, match="clareza"):
            req.approve("user-1")

    def test_approve_at_clarity_boundary(self):
        req = make_requirement(status=RequirementStatus.REVIEW, quality_score=make_quality_score(clarity=60.0))
        req.approve("user-1")
        assert req.status == RequirementStatus.APPROVED

    def test_refine_then_approve_full_cycle(self):
        req = make_requirement()
        req.refine(description="Melhorado", changelog="v2")
        req.update_quality(make_quality_score(clarity=90.0))
        req.approve("tech-lead")
        assert req.status == RequirementStatus.APPROVED
        assert req.version.minor == 1
