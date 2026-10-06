from decimal import Decimal

import pytest

from app.domain import QuoteInputs, calculate_quote


def sample(**overrides):
    values = {
        "material_cost_per_gram": Decimal("0.10"),
        "part_weight_grams": Decimal("100"),
        "machine_hours": Decimal("2"),
        "machine_hour_cost": Decimal("3"),
        "labor_minutes": Decimal("30"),
        "labor_hour_cost": Decimal("20"),
        "packaging_cost": Decimal("4"),
        "failure_rate_percent": Decimal("10"),
        "margin_percent": Decimal("50"),
        "quantity": 2,
    }
    values.update(overrides)
    return QuoteInputs(**values)


def test_quote_breakdown_is_deterministic():
    result = calculate_quote(sample())
    assert result["unit_cost"] == Decimal("33.00")
    assert result["unit_price"] == Decimal("49.50")
    assert result["total_price"] == Decimal("99.00")


def test_invalid_failure_rate_is_rejected():
    with pytest.raises(ValueError):
        calculate_quote(sample(failure_rate_percent=Decimal("100")))
