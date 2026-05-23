import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import pytest, uuid
from quality.domain.scorer import QualityScorer, QualityInputs
from quality.domain.entities import QualityPolicy, QualityReport
from quality.contracts import GateStatus, PolicyRule, QualityDimensionScore


class TestQualityScorer:
    def test_clarity_penalized_by_issues(self):
        scorer = QualityScorer()
        inputs = QualityInputs(project_id="p1", avg_clarity=80.0, total_issues=5, total_reqs=10)
        assert scorer.compute_clarity(inputs) == 70.0

    def test_traceability_ratio(self):
        scorer = QualityScorer()
        inputs = QualityInputs(project_id="p1", total_reqs=10, linked_reqs=8)
        assert scorer.compute_traceability(inputs) == 80.0

    def test_accessibility_aa_minus_penalty(self):
        scorer = QualityScorer()
        inputs = QualityInputs(project_id="p1", wcag_level="AA", wcag_issues=2)
        assert scorer.compute_accessibility(inputs) == 79.0

    def test_all_scores_bounded_0_100(self):
        scorer = QualityScorer()
        inputs = QualityInputs(
            project_id="p1", avg_clarity=10.0, avg_completeness=10.0,
            avg_testability=10.0, avg_consistency=10.0,
            total_issues=100, critical_issues=50, total_reqs=5,
            linked_reqs=0, coverage_score=0.0, wcag_level="A", wcag_issues=20,
        )
        for dim, val in scorer.compute_all(inputs).items():
            assert 0.0 <= val <= 100.0, f"{dim}: {val} fora de [0, 100]"

    def test_zero_reqs_traceability_returns_zero(self):
        scorer = QualityScorer()
        inputs = QualityInputs(project_id="p1", total_reqs=0, linked_reqs=0)
        assert scorer.compute_traceability(inputs) == 0.0


class TestQualityPolicy:
    def test_passes_above_threshold(self):
        policy = QualityPolicy("p", "proj", [PolicyRule("clarity", 60.0, True)])
        assert policy.evaluate_dimension("clarity", 80.0) == GateStatus.PASSED

    def test_fails_below_blocking_threshold(self):
        policy = QualityPolicy("p", "proj", [PolicyRule("clarity", 60.0, True)])
        assert policy.evaluate_dimension("clarity", 50.0) == GateStatus.FAILED

    def test_warning_on_non_blocking(self):
        policy = QualityPolicy("p", "proj", [PolicyRule("consistency", 70.0, False)])
        assert policy.evaluate_dimension("consistency", 60.0) == GateStatus.WARNING

    def test_passes_with_no_rule(self):
        policy = QualityPolicy("p", "proj", [])
        assert policy.evaluate_dimension("anything", 0.0) == GateStatus.PASSED

    def test_policy_rule_rejects_threshold_above_100(self):
        with pytest.raises(ValueError):
            PolicyRule("clarity", threshold=110.0, blocking=True)


class TestQualityReport:
    def test_integrity_hash_computed_on_creation(self):
        report = QualityReport(id=str(uuid.uuid4()), project_id="p1",
                                overall_status=GateStatus.PASSED, dimension_scores=[], policy_violations=[])
        assert len(report.integrity_hash) == 64

    def test_same_content_same_hash(self):
        rid = str(uuid.uuid4())
        r1  = QualityReport(rid, "p1", GateStatus.PASSED, [], [])
        r2  = QualityReport(rid, "p1", GateStatus.PASSED, [], [])
        assert r1.integrity_hash == r2.integrity_hash

    def test_is_approved_only_when_passed(self):
        r = QualityReport(str(uuid.uuid4()), "p1", GateStatus.FAILED, [], [])
        assert r.is_approved() is False
