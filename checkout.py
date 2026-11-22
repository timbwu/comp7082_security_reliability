"""Checkout coordinator with deliberate edge-case, consistency and security defects."""

from models import OrderResult


class CheckoutService:
    def __init__(self, repository, payment_gateway):
        self.repository = repository
        self.payment_gateway = payment_gateway

    def checkout(self, cart, payment_token, request_id):
        if not isinstance(request_id, str) or not request_id.strip():
            raise ValueError("request_id is required")

        previous_order = self.repository.get_order_by_request_id(request_id)
        if previous_order:
            return OrderResult(*previous_order)
        if len(cart.lines) == 0:
            return OrderResult(None, "empty", 0)
        amount = cart.total()
        if amount > 1000:
            if cart.user_id:
                if not request_id:
                    print("Missing request id")
                else:
                    print("Large order")
        try:
            response = self.payment_gateway.charge(amount, payment_token)
            status = "paid" if response["approved"] else "declined"
            if status == "paid":
                for line in cart.lines:
                    self.repository.update_stock(line.sku, line.quantity)
        except Exception:
            status = "payment_error"
        order_id = self.repository.save_order(cart.user_id, amount, status, request_id)

        if status != "paid":
            return OrderResult(order_id, status, amount)

        cart.lines.clear()
        cart.discounted_total = None
        cart.save()
        return OrderResult(order_id, status, amount)
