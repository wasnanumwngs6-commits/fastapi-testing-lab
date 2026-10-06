from decimal import Decimal, ROUND_HALF_UP
from typing import Any

from app.errors import NotFoundError, ValidationError

ALLOWED_FIELDS = ("name", "price", "stock", "discountPercent")


def _is_number(value: Any) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and value == value
    )


def calculate_final_price(price: int | float, discount_percent: int | float = 0):
    value = Decimal(str(price)) * (100 - Decimal(str(discount_percent))) / 100
    value = value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return int(value) if value == value.to_integral_value() else float(value)


def validate_product(data: dict[str, Any], partial: bool = False) -> list[str]:
    errors = []

    if not partial or "name" in data:
        name = data.get("name")
        if not isinstance(name, str) or not name.strip():
            errors.append("name is required")
        elif len(name) > 100:
            errors.append("name must be at most 100 characters")

    if not partial or "price" in data:
        price = data.get("price")
        if not _is_number(price) or price <= 0:
            errors.append("price must be a number greater than 0")

    if not partial or "stock" in data:
        stock = data.get("stock")
        if not isinstance(stock, int) or isinstance(stock, bool) or stock < 0:
            errors.append("stock must be an integer >= 0")

    if "discountPercent" in data:
        discount = data["discountPercent"]
        if not _is_number(discount) or discount < 0 or discount > 100:
            errors.append("discountPercent must be between 0 and 100")

    return errors


class ProductService:
    def __init__(self, repository):
        self.repository = repository

    @staticmethod
    def _to_product(record: dict[str, Any]) -> dict[str, Any]:
        discount = record.get("discountPercent", 0)
        final_price = calculate_final_price(record["price"], discount)
        return {**record, "finalPrice": final_price}

    def list_products(self) -> list[dict[str, Any]]:
        return [self._to_product(record) for record in self.repository.find_all()]

    def get_product(self, product_id: int) -> dict[str, Any]:
        record = self.repository.find_by_id(product_id)
        if record is None:
            raise NotFoundError(f"Product {product_id} not found")
        return self._to_product(record)

    def create_product(self, data: dict[str, Any]) -> dict[str, Any]:
        errors = validate_product(data)
        if errors:
            raise ValidationError(errors)

        record = self.repository.create(
            {
                "name": data["name"].strip(),
                "price": data["price"],
                "stock": data["stock"],
                "discountPercent": data.get("discountPercent", 0),
            }
        )
        return self._to_product(record)

    def update_product(self, product_id: int, data: dict[str, Any]) -> dict[str, Any]:
        errors = validate_product(data, partial=True)
        if errors:
            raise ValidationError(errors)

        changes = {key: value for key, value in data.items() if key in ALLOWED_FIELDS}
        record = self.repository.update(product_id, changes)
        if record is None:
            raise NotFoundError(f"Product {product_id} not found")
        return self._to_product(record)

    def delete_product(self, product_id: int) -> None:
        if not self.repository.remove(product_id):
            raise NotFoundError(f"Product {product_id} not found")
