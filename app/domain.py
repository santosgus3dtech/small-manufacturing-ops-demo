from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP


MONEY = Decimal("0.01")


def money(value: Decimal) -> Decimal:
    return value.quantize(MONEY, rounding=ROUND_HALF_UP)


@dataclass(frozen=True)
class QuoteInputs:
    material_cost_per_gram: Decimal
    part_weight_grams: Decimal
    machine_hours: Decimal
    machine_hour_cost: Decimal
    labor_minutes: Decimal
    labor_hour_cost: Decimal
    packaging_cost: Decimal
    failure_rate_percent: Decimal
    margin_percent: Decimal
    quantity: int

    def validate(self) -> None:
        numeric = (
            self.material_cost_per_gram,
            self.part_weight_grams,
            self.machine_hours,
            self.machine_hour_cost,
            self.labor_minutes,
            self.labor_hour_cost,
            self.packaging_cost,
            self.failure_rate_percent,
            self.margin_percent,
        )
        if any(value < 0 for value in numeric):
            raise ValueError("Quote inputs cannot be negative")
        if self.quantity < 1:
            raise ValueError("Quantity must be at least one")
        if self.failure_rate_percent >= 100:
            raise ValueError("Failure rate must be below 100 percent")


def calculate_quote(inputs: QuoteInputs) -> dict[str, Decimal | int]:
    inputs.validate()
    material = inputs.material_cost_per_gram * inputs.part_weight_grams
    machine = inputs.machine_hours * inputs.machine_hour_cost
    labor = (inputs.labor_minutes / Decimal(60)) * inputs.labor_hour_cost
    direct_cost = material + machine + labor + inputs.packaging_cost
    risk_buffer = direct_cost * inputs.failure_rate_percent / Decimal(100)
    unit_cost = direct_cost + risk_buffer
    unit_price = unit_cost * (Decimal(1) + inputs.margin_percent / Decimal(100))
    return {
        "quantity": inputs.quantity,
        "material_cost": money(material),
        "machine_cost": money(machine),
        "labor_cost": money(labor),
        "packaging_cost": money(inputs.packaging_cost),
        "risk_buffer": money(risk_buffer),
        "unit_cost": money(unit_cost),
        "unit_price": money(unit_price),
        "total_price": money(unit_price * inputs.quantity),
    }
