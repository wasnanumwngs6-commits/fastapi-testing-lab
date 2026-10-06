from unittest.mock import Mock

import pytest

from app.errors import NotFoundError, ValidationError
from app.services.product_service import (
    ProductService,
    calculate_final_price,
    validate_product,
)


@pytest.mark.parametrize(
    "price, discount, expected",
    [
        (1000, 0, 1000),
        (1000, 10, 900),
        (5990, 15, 5091.5),
        (99.99, 10, 89.99),
        (500, 100, 0),
    ],
)
def test_calculate_final_price(price, discount, expected):
    assert calculate_final_price(price, discount) == expected


def test_calculate_final_price_uses_zero_discount_by_default():
    assert calculate_final_price(250) == 250


VALID_INPUT = {"name": "Monitor", "price": 5990, "stock": 3, "discountPercent": 15}


def test_validate_product_valid_input_returns_empty_list():
    assert validate_product(VALID_INPUT) == []


@pytest.mark.parametrize(
    "expected_message, data",
    [
        ("name is required", {**VALID_INPUT, "name": ""}),
        ("name must be at most 100 characters", {**VALID_INPUT, "name": "x" * 101}),
        ("price must be a number greater than 0", {**VALID_INPUT, "price": 0}),
        ("price must be a number greater than 0", {**VALID_INPUT, "price": "100"}),
        ("stock must be an integer >= 0", {**VALID_INPUT, "stock": 1.5}),
        (
            "discountPercent must be between 0 and 100",
            {**VALID_INPUT, "discountPercent": 150},
        ),
    ],
)
def test_validate_product_invalid_input(expected_message, data):
    assert expected_message in validate_product(data)


def test_validate_product_partial_checks_only_given_fields():
    assert validate_product({"stock": 5}, partial=True) == []
    assert validate_product({"stock": -1}, partial=True) == [
        "stock must be an integer >= 0"
    ]


@pytest.fixture
def repository():
    return Mock()


@pytest.fixture
def service(repository):
    return ProductService(repository)


def test_create_product_saves_valid_data(service, repository):
    repository.create.side_effect = lambda data: {"id": 10, **data}
    result = service.create_product(
        {"name": "  Monitor  ", "price": 5990, "stock": 3, "discountPercent": 15}
    )

    repository.create.assert_called_once_with(
        {"name": "Monitor", "price": 5990, "stock": 3, "discountPercent": 15}
    )
    assert result["id"] == 10
    assert result["finalPrice"] == 5091.5


def test_create_product_rejects_invalid_data(service, repository):
    with pytest.raises(ValidationError):
        service.create_product({"name": "", "price": -1, "stock": 1})
    repository.create.assert_not_called()


def test_create_product_validation_error_lists_every_invalid_field(service):
    with pytest.raises(ValidationError) as exc_info:
        service.create_product({"name": "", "price": -1, "stock": -5})
    assert len(exc_info.value.details) == 3


def test_get_product_not_found_raises(service, repository):
    repository.find_by_id.return_value = None

    with pytest.raises(NotFoundError):
        service.get_product(999)
    repository.find_by_id.assert_called_once_with(999)


def test_update_product_passes_only_allowed_fields_and_recalculates(
    service, repository
):
    repository.update.return_value = {
        "id": 1,
        "name": "Mouse",
        "price": 1000,
        "stock": 5,
        "discountPercent": 20,
    }

    result = service.update_product(1, {"discountPercent": 20, "role": "hacker"})

    repository.update.assert_called_once_with(1, {"discountPercent": 20})
    assert result["finalPrice"] == 800


def test_delete_product_not_found_raises(service, repository):
    repository.remove.return_value = False

    with pytest.raises(NotFoundError, match="Product 42 not found"):
        service.delete_product(42)
