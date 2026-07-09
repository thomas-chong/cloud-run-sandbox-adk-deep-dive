import pytest
from rule_engine import UnsafeExpression, evaluate_rule


def test_comparison_and_boolean_rules() -> None:
    record = {"amount": 125, "country": "HK", "risk": 0.82}
    assert evaluate_rule("amount > 100 and risk >= 0.8", record)
    assert not evaluate_rule("country == 'US'", record)


def test_unknown_names_are_rejected_with_domain_error() -> None:
    with pytest.raises(UnsafeExpression, match="unknown name"):
        evaluate_rule("missing_field > 0", {"amount": 10})


def test_calls_and_attribute_access_are_rejected() -> None:
    with pytest.raises(UnsafeExpression, match="unsupported syntax"):
        evaluate_rule("amount.__class__.__mro__", {"amount": 10})
    with pytest.raises(UnsafeExpression, match="unsupported syntax"):
        evaluate_rule("open('/etc/passwd').read()", {"amount": 10})


def test_only_scalar_record_values_are_accepted() -> None:
    with pytest.raises(UnsafeExpression, match="scalar"):
        evaluate_rule("items == []", {"items": []})
