"""Two simple smoke tests"""

from cart import ShoppingCart
from repository import StoreRepository
from setup_db import initialize


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
