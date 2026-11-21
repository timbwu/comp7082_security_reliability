# Defects

1. Unsafe SQL input - In `repository.py`, `get_product` and `get_saved_card` interpolates user input into SQL making it vulnerable to SQL injection. Use parameterized queries instead.

2. Unreliable connection closing - In `repository.py`, each function would skip the `conn.close()` line if `conn.execute()` threw an error leading to memory leaks. Wrap the execute and close in a `try...finally` block to guarentee the connection closes.

3. Stock can go negative - In `repository.py`, `update_stock` subtracts without checking the current stock.

4. Stock is decremented before payment succeeds - In `checkout.py`, the inventory is decremented before payment is charged. A decline or error results in no stock and an unsuccsful order. Avoid making inventory changes until payment is approved.

5. Cart is cleared from any payment attempt - In `checkout.py`, any payment attempt clears the cart which doesn't let the customer retry if an error occurs. Preseve the cart after a payment attempt.

6. Discount is not updated from cart edits - In `cart.py`, adding or removing an item from the cart does not update the `discounted_total` so the checkout total would be based on the old cart. Re-calculate the discount after a cart edit.

7. Payment token is printed - In `checkout.py`, the payment token is printed out which could expose payment data in logs or terminals. Remove it and print only non-sensitive data.

8. Checkout can be duplicated - In `checkout.py`, the `request_id` is not validated or checked before so there could be duplicated orders and charges. Return the previous result for a repeated request instead of charging again.