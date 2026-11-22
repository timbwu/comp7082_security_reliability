import sqlite3

import pytest
from checkout import CheckoutService
from models import CartLine
from payments import FakePaymentGateway
from setup_db import initialize
from repository import StoreRepository
from cart import ShoppingCart


@pytest.fixture
def store(tmp_path):
    db = tmp_path / "store.db"
    initialize(str(db))
    return StoreRepository(str(db))


def test_seed_product(tmp_path):
    db = tmp_path / "test.db"
    initialize(str(db))
    assert StoreRepository(str(db)).get_product("MOU-01").name == "Wireless mouse"


def test_cart_adds_valid_item(tmp_path):
    db = tmp_path / "test.db"
    initialize(str(db))
    cart = ShoppingCart("student", StoreRepository(str(db)))
    assert cart.add_item("USB-01", 2)
    assert len(cart.lines) == 1


def test_repository_uses_parameterized_queries(store):
    store.save_cart("student", [CartLine("MOU-01", "Wireless mouse", 29.95, 1)])
    assert store.get_product("'MOU-01' OR '1' = '1'") is None
    assert store.get_saved_cart("' OR 1=1 --") == []
    assert store.get_saved_cart("student") == [("MOU-01", 1)]


def test_repository_closes_connection_when_query_raises(store, monkeypatch):
    class FailingConnection:
        closed = False

        def execute(self, *_args):
            raise sqlite3.OperationalError("query failed")

        def close(self):
            self.closed = True

    connection = FailingConnection()
    monkeypatch.setattr(store, "connect", lambda: connection)

    with pytest.raises(sqlite3.OperationalError, match="query failed"):
        store.get_product("MOU-01")

    assert connection.closed


def test_update_stock_rejects_invalid_quantity(store, quantity):
    for quantity in [0, -1, True, 21]:
        assert store.update_stock("MOU-01", quantity) is False


def test_declined_checkout_preserves_stock_and_cart(store):
    cart = ShoppingCart("student", store)
    cart.add_item("MOU-01", 2)
    service = CheckoutService(store, FakePaymentGateway(should_approve=False))
    result = service.checkout(cart, "fake-token", "declined-1")
    assert result.status == "declined"
    assert store.get_product("MOU-01").stock == 20
    assert [(line.sku, line.quantity) for line in cart.lines] == [("MOU-01", 2)]


def test_approved_checkout_updates_stock(store):
    cart = ShoppingCart("student", store)
    cart.add_item("MOU-01", 2)
    service = CheckoutService(store, FakePaymentGateway())
    result = service.checkout(cart, "fake-token", "approved-1")
    assert result.status == "paid"
    assert store.get_product("MOU-01").stock == 18


def test_approved_checkout_clears_cart(store):
    cart = ShoppingCart("student", store)
    cart.add_item("MOU-01", 2)
    service = CheckoutService(store, FakePaymentGateway())
    result = service.checkout(cart, "fake-token", "approved-2")
    assert result.status == "paid"
    assert cart.lines == []
    assert store.get_saved_cart("student") == []


def test_repeated_request_id_does_not_charge_or_create_another_order(store):
    cart = ShoppingCart("student", store)
    cart.add_item("USB-01", 1)
    gateway = FakePaymentGateway()
    service = CheckoutService(store, gateway)
    first = service.checkout(cart, "fake-token", "repeat-1")
    second = service.checkout(cart, "fake-token", "repeat-1")
    assert second == first
    assert len(gateway.calls) == 1
    assert len(store.list_orders("student")) == 1


def test_checkout_rejects_blank_request_id_before_charging(store):
    cart = ShoppingCart("student", store)
    cart.add_item("USB-01", 1)
    gateway = FakePaymentGateway()
    service = CheckoutService(store, gateway)
    with pytest.raises(ValueError, match="request_id is required"):
        service.checkout(cart, "fake-token", "  ")

    assert gateway.calls == []
    assert store.list_orders("student") == []


def test_checkout_does_not_print_payment_token(store, capsys):
    cart = ShoppingCart("student", store)
    cart.add_item("USB-01", 1)
    service = CheckoutService(store, FakePaymentGateway())
    service.checkout(cart, "sensitive-test-token", "safe-1")
    assert "sensitive-test-token" not in capsys.readouterr().out


def test_discount_is_recalculated_after_adding_item(store):
    cart = ShoppingCart("student", store)
    cart.add_item("MOU-01", 1)
    cart.apply_discount("WELCOME10")
    cart.add_item("MOU-01", 1)
    assert cart.total() == pytest.approx(29.95 * 2 * 0.9)


def test_discount_is_recalculated_after_removing_item(store):
    cart = ShoppingCart("student", store)
    cart.add_item("MOU-01", 2)
    cart.apply_discount("WELCOME10")
    cart.remove_item("MOU-01", 1)
    assert cart.total() == pytest.approx(29.95 * 0.9)
