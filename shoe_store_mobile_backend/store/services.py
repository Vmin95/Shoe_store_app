# Decimal is used for money calculations.
# It avoids floating-point rounding problems that can happen with float.
from decimal import Decimal

# uuid4 generates a highly unique value that we use as part
# of the customer-facing order number.
from uuid import uuid4

# transaction.atomic lets us group the entire checkout workflow
# into a single database transaction.
from django.db import transaction

# Import the models involved in order creation and inventory updates.
from .models import (
    Order,
    OrderItem,
    ProductVariant,
    InventoryTransaction,
)


# ---------------------------------------------------------
# CUSTOM CHECKOUT ERROR
# ---------------------------------------------------------

class InsufficientStockError(Exception):
    """
    Custom exception raised when a customer tries to order
    more inventory than is currently available.

    Using a custom exception makes it easy for the API view
    to distinguish an inventory problem from other errors.
    """
    pass

# ---------------------------------------------------------
# SHIPPING CALCULATION
# ---------------------------------------------------------

FREE_SHIPPING_THRESHOLD = Decimal("100.00")
STANDARD_SHIPPING_FEE = Decimal("9.99")

# ---------------------------------------------------------
# TAX CALCULATION
# ---------------------------------------------------------

# Temporary California sales tax rate for the portfolio version.
#
# A real production store would normally use a tax service because
# sales tax can vary by state, county, city, and other rules.
CA_TAX_RATE = Decimal("0.0725")

def calculate_shipping(subtotal):
    """
    Calculate the shipping charge for an order.

    Orders of $100 or more receive free standard shipping.
    Orders below $100 are charged the standard shipping fee.
    """

    if subtotal >= FREE_SHIPPING_THRESHOLD:
        return Decimal("0.00")

    return STANDARD_SHIPPING_FEE

def calculate_tax(subtotal, shipping_address):
    """
    Calculate sales tax based on the customer's shipping address.

    For the current portfolio version:
    - California orders use the configured California tax rate.
    - Other states currently return $0.00.

    A production application could later replace this function
    with a dedicated tax calculation service.
    """

    # Normalize the state value so "ca", "CA", and "Ca"
    # are treated the same way.
    state = shipping_address.state.strip().upper()

    if state == "CA":
        tax = subtotal * CA_TAX_RATE

        # Money should always be rounded to two decimal places.
        return tax.quantize(Decimal("0.01"))

    return Decimal("0.00")

# ---------------------------------------------------------
# ORDER CREATION / CHECKOUT SERVICE
# ---------------------------------------------------------

@transaction.atomic
def create_order(*, customer, shipping_address, billing_address, items):
    """
    Creates an order and updates inventory as one atomic operation.

    Example items:

        [
            {"product_variant_id": 1, "quantity": 2},
            {"product_variant_id": 3, "quantity": 1},
        ]

    The @transaction.atomic decorator guarantees that either:

        - the order, order items, inventory updates, and inventory
          transactions ALL succeed

    OR:

        - everything is rolled back if any step fails.

    This prevents partially completed orders from being saved.
    """

    # -----------------------------------------------------
    # CREATE THE ORDER HEADER
    # -----------------------------------------------------

    # Create the main Order record first.
    #
    # Totals are calculated later after all order items have
    # been processed.
    order = Order.objects.create(
        customer=customer,
        shipping_address=shipping_address,
        billing_address=billing_address,

        # Generate an order number such as:
        # ORD-F5ED48A973
        #
        # uuid4().hex creates a long random hexadecimal string.
        # [:10] keeps the first 10 characters.
        # upper() makes the order number easier to read.
        order_number=f"ORD-{uuid4().hex[:10].upper()}",

        # The order begins as pending until payment processing
        # confirms that it has been paid.
        status="pending",
        payment_status="pending",
    )

    # Start the order subtotal at exactly $0.00.
    subtotal = Decimal("0.00")


    # -----------------------------------------------------
    # PROCESS EACH ITEM IN THE ORDER
    # -----------------------------------------------------

    for item in items:

        # Pull the requested variant ID and quantity from the
        # validated checkout data.
        variant_id = item["product_variant_id"]
        quantity = item["quantity"]


        # Extra defensive validation.
        #
        # CheckoutSerializer already requires quantity >= 1,
        # but the service also protects itself in case it is
        # called somewhere else in the application.
        if quantity < 1:
            raise ValueError(
                "Quantity must be at least 1."
            )


        # -------------------------------------------------
        # LOCK AND RETRIEVE THE PRODUCT VARIANT
        # -------------------------------------------------

        variant = (
            ProductVariant.objects

            # select_for_update() locks this database row
            # until the current transaction finishes.
            #
            # This helps prevent two customers from both
            # purchasing the final available pair at the
            # same time.
            .select_for_update()

            # Only retrieve an active product variant with
            # the requested ID.
            .get(
                id=variant_id,
                is_active=True
            )
        )


        # -------------------------------------------------
        # CHECK AVAILABLE INVENTORY
        # -------------------------------------------------

        # Do not allow the order if requested quantity exceeds
        # the stock currently available.
        if variant.quantity_on_hand < quantity:
            raise InsufficientStockError(
                f"Not enough stock for {variant.sku}. "
                f"Available: {variant.quantity_on_hand}, "
                f"requested: {quantity}."
            )


        # -------------------------------------------------
        # CALCULATE PRICE
        # -------------------------------------------------

        # Always retrieve the price directly from the database.
        #
        # The mobile app does NOT get to tell the backend what
        # price it wants to pay.
        unit_price = variant.price

        # Calculate the subtotal for this specific line item.
        line_subtotal = unit_price * quantity


        # -------------------------------------------------
        # CREATE ORDER ITEM
        # -------------------------------------------------

        OrderItem.objects.create(
            order=order,
            product_variant=variant,
            quantity=quantity,

            # Store the purchase-time price directly on the
            # OrderItem.
            #
            # If the product price changes later, historical
            # orders still show what the customer actually paid.
            unit_price=unit_price,

            # Discounts are not implemented yet, so the current
            # value is always zero.
            discount=Decimal("0.00"),

            subtotal=line_subtotal,
        )


        # -------------------------------------------------
        # REDUCE INVENTORY
        # -------------------------------------------------

        # Subtract the purchased quantity from stock.
        variant.quantity_on_hand -= quantity

        # Save only the fields that actually changed.
        #
        # updated_at is also included because ProductVariant
        # inherits from TimeStampedModel.
        variant.save(
            update_fields=[
                "quantity_on_hand",
                "updated_at",
            ]
        )


        # -------------------------------------------------
        # RECORD INVENTORY HISTORY
        # -------------------------------------------------

        # Every stock movement is recorded separately.
        #
        # This gives us an audit trail showing WHY inventory
        # changed instead of only storing the current quantity.
        InventoryTransaction.objects.create(
            product_variant=variant,

            # This inventory change happened because of a sale.
            transaction_type="sale",

            # Negative quantity means inventory was removed.
            quantity_change=-quantity,

            # Link the inventory transaction back to the
            # business event that caused it.
            reference_type="order",
            reference_id=order.order_number,

            notes=(
                f"Inventory reduced for order "
                f"{order.order_number}"
            ),
        )


        # Add this item's subtotal to the running order subtotal.
        subtotal += line_subtotal


        # -----------------------------------------------------
        # CALCULATE SHIPPING AND FINAL TOTAL
        # -----------------------------------------------------

        # Calculate shipping after all order items have been processed
        # because the shipping rule depends on the final subtotal.
        shipping_fee = calculate_shipping(subtotal)

        # Save the calculated financial values on the Order.
        order.subtotal = subtotal
        order.shipping_fee = shipping_fee

        # Calculate tax using the customer's shipping address.
        tax_total = calculate_tax(
            subtotal,
            shipping_address
        )

        order.tax_total = tax_total

        # Final order total includes merchandise, shipping, and tax.
        order.total_amount = (
            subtotal
            + shipping_fee
            + tax_total
        )

        order.save(
            update_fields=[
                "subtotal",
                "shipping_fee",
                "tax_total",
                "total_amount",
                "updated_at",
            ]
        )


        # Return the completed Order object to the API view.
        return order