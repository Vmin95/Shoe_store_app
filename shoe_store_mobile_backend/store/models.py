# Django settings lets us reference the configured User model
# without hard-coding django.contrib.auth.models.User.
from django.conf import settings

# Django's ORM model classes are defined through models.Model
# and the various field types below.
from django.db import models

# MinValueValidator is used to prevent invalid negative prices
# and zero/negative quantities where appropriate.
from django.core.validators import MinValueValidator


# ---------------------------------------------------------
# SHARED TIMESTAMP BASE MODEL
# ---------------------------------------------------------

class TimeStampedModel(models.Model):
    """
    Abstract base model that automatically adds created/updated
    timestamps to models that inherit from it.

    Because Meta.abstract = True, Django will NOT create a separate
    database table called TimeStampedModel.
    """

    # Automatically records when the row is first created.
    created_at = models.DateTimeField(auto_now_add=True)

    # Automatically updates whenever the row is saved.
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


# ---------------------------------------------------------
# CUSTOMER
# ---------------------------------------------------------

class Customer(TimeStampedModel):
    """
    Stores customer-specific information.

    Authentication information such as username, email, and password
    lives in Django's User model. This model extends that account with
    information specific to the shoe store.
    """

    # OneToOneField means one Django User can have exactly one
    # Customer profile.
    #
    # related_name='customer_profile' is why we can write:
    # request.user.customer_profile
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='customer_profile'
    )

    # Optional customer phone number.
    phone = models.CharField(
        max_length=30,
        blank=True
    )

    # Allows a customer account to be disabled without deleting it.
    is_active = models.BooleanField(default=True)

    def __str__(self):
        # Django Admin will display the email when available,
        # otherwise it falls back to the username.
        return self.user.email or self.user.username


# ---------------------------------------------------------
# ADDRESS
# ---------------------------------------------------------

class Address(TimeStampedModel):
    """
    Stores shipping or billing addresses belonging to customers.
    """

    # Restricts address_type to one of these allowed values.
    ADDRESS_TYPES = [
        ('shipping', 'Shipping'),
        ('billing', 'Billing'),
    ]

    # One customer may have multiple saved addresses.
    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        related_name='addresses'
    )

    full_name = models.CharField(max_length=150)

    phone = models.CharField(
        max_length=30,
        blank=True
    )

    address_line_1 = models.CharField(max_length=255)

    # Apartment/unit/etc. is optional.
    address_line_2 = models.CharField(
        max_length=255,
        blank=True
    )

    city = models.CharField(max_length=120)

    state = models.CharField(max_length=120)

    postal_code = models.CharField(max_length=20)

    # Two-letter country code such as US, CA, GB.
    country = models.CharField(
        max_length=2,
        default='US'
    )

    address_type = models.CharField(
        max_length=20,
        choices=ADDRESS_TYPES
    )

    # Marks the customer's preferred/default address.
    is_default = models.BooleanField(default=False)


# ---------------------------------------------------------
# CATEGORY
# ---------------------------------------------------------

class Category(TimeStampedModel):
    """
    Groups products into sections such as Sneakers or Boots.
    """

    # unique=True prevents duplicate category names.
    name = models.CharField(
        max_length=120,
        unique=True
    )

    description = models.TextField(blank=True)

    image_url = models.URLField(blank=True)

    # Allows categories to be hidden without deleting them.
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


# ---------------------------------------------------------
# PRODUCT
# ---------------------------------------------------------

class Product(TimeStampedModel):
    """
    Stores the main product information shared by all variants.

    Example:
        Air Jordan 1 Retro High

    Size/color-specific inventory belongs in ProductVariant.
    """

    # A product belongs to one category.
    #
    # PROTECT prevents deleting a category while products
    # still reference it.
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name='products'
    )

    name = models.CharField(max_length=180)

    brand = models.CharField(
        max_length=120,
        blank=True
    )

    description = models.TextField(blank=True)

    image_url = models.URLField(blank=True)

    # Allows a product to be hidden from the store without deleting
    # its historical database record.
    is_active = models.BooleanField(default=True)

    def __str__(self):
        # strip() avoids an extra leading space if brand is blank.
        return f'{self.brand} {self.name}'.strip()


# ---------------------------------------------------------
# PRODUCT VARIANT
# ---------------------------------------------------------

class ProductVariant(TimeStampedModel):
    """
    Represents a specific sellable version of a product.

    Example:
        Product: Air Jordan 1 Retro High
        Size: 9
        Color: Black
        SKU: AJ1-RH-BLK-090

    Inventory is stored here because different sizes/colors can have
    different quantities available.
    """

    # One product may have many variants.
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='variants'
    )

    # SKU uniquely identifies this exact variant.
    sku = models.CharField(
        max_length=80,
        unique=True
    )

    size = models.CharField(max_length=30)

    color = models.CharField(
        max_length=80,
        blank=True
    )

    # DecimalField is preferred for money instead of float
    # because it avoids floating-point precision errors.
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )

    # Current physical inventory available for sale.
    quantity_on_hand = models.PositiveIntegerField(default=0)

    # Threshold used later for low-stock warnings.
    reorder_level = models.PositiveIntegerField(default=0)

    is_active = models.BooleanField(default=True)

    class Meta:
        # Prevents duplicate variants such as:
        # Product 1 + Size 9 + Black appearing more than once.
        constraints = [
            models.UniqueConstraint(
                fields=['product', 'size', 'color'],
                name='unique_product_variant'
            )
        ]

    def __str__(self):
        return f'{self.product} - {self.size} {self.color}'.strip()


# ---------------------------------------------------------
# CART
# ---------------------------------------------------------

class Cart(TimeStampedModel):
    """
    Stores a customer's active shopping cart.
    """

    # OneToOneField means each customer currently has one cart.
    customer = models.OneToOneField(
        Customer,
        on_delete=models.CASCADE,
        related_name='cart'
    )

    is_active = models.BooleanField(default=True)


# ---------------------------------------------------------
# CART ITEM
# ---------------------------------------------------------

class CartItem(TimeStampedModel):
    """
    Represents one product variant inside a customer's cart.
    """

    # One cart may contain multiple CartItem records.
    cart = models.ForeignKey(
        Cart,
        on_delete=models.CASCADE,
        related_name='items'
    )

    # PROTECT prevents a product variant from being deleted
    # while it is still referenced by a cart item.
    product_variant = models.ForeignKey(
        ProductVariant,
        on_delete=models.PROTECT,
        related_name='cart_items'
    )

    # Quantity must always be at least 1.
    quantity = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1)]
    )

    class Meta:
        # Prevents the same product variant from appearing twice
        # in the same cart. Instead, its quantity should be increased.
        constraints = [
            models.UniqueConstraint(
                fields=['cart', 'product_variant'],
                name='unique_cart_variant'
            )
        ]


# ---------------------------------------------------------
# ORDER
# ---------------------------------------------------------

class Order(TimeStampedModel):
    """
    Represents a completed or in-progress customer order.
    """

    # Allowed order workflow states.
    STATUSES = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
        ('refunded', 'Refunded'),
    ]

    # Payment state is tracked separately from order fulfillment state.
    PAYMENT_STATUSES = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]

    # PROTECT preserves historical orders even if someone later
    # tries to delete the customer.
    customer = models.ForeignKey(
        Customer,
        on_delete=models.PROTECT,
        related_name='orders'
    )

    # Addresses are protected because historical orders should retain
    # the address information they referenced.
    billing_address = models.ForeignKey(
        Address,
        on_delete=models.PROTECT,
        related_name='billing_orders'
    )

    shipping_address = models.ForeignKey(
        Address,
        on_delete=models.PROTECT,
        related_name='shipping_orders'
    )

    # Public-facing unique order identifier.
    order_number = models.CharField(
        max_length=32,
        unique=True
    )

    # Records the time the order was placed.
    order_date = models.DateTimeField(auto_now_add=True)

    status = models.CharField(
        max_length=20,
        choices=STATUSES,
        default='pending'
    )

    # Financial totals are stored on the order for quick access.
    subtotal = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    discount_total = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    shipping_fee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    tax_total = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    total_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    payment_status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUSES,
        default='pending'
    )

    # Optional internal or customer-facing notes.
    notes = models.TextField(blank=True)


# ---------------------------------------------------------
# ORDER ITEM
# ---------------------------------------------------------

class OrderItem(TimeStampedModel):
    """
    Represents one line item inside an order.
    """

    # If an Order is deleted, its OrderItems are deleted too.
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='items'
    )

    # PROTECT preserves the purchased product reference.
    product_variant = models.ForeignKey(
        ProductVariant,
        on_delete=models.PROTECT,
        related_name='order_items'
    )

    quantity = models.PositiveIntegerField(
        validators=[MinValueValidator(1)]
    )

    # Important: unit_price is stored here at purchase time.
    #
    # If the shoe price later changes, old orders still preserve
    # the price the customer actually paid.
    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    discount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    # Stores the calculated amount for this specific line.
    subtotal = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )


# ---------------------------------------------------------
# PAYMENT
# ---------------------------------------------------------

class Payment(TimeStampedModel):
    """
    Stores individual payment attempts or transactions for an order.
    """

    STATUSES = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]

    # An order may potentially have multiple payment records,
    # such as a failed attempt followed by a successful attempt.
    order = models.ForeignKey(
        Order,
        on_delete=models.PROTECT,
        related_name='payments'
    )

    # Example values later could include card, PayPal, etc.
    payment_method = models.CharField(max_length=40)

    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    payment_status = models.CharField(
        max_length=20,
        choices=STATUSES,
        default='pending'
    )

    # External payment processor transaction/reference ID.
    transaction_id = models.CharField(
        max_length=120,
        blank=True
    )

    # Only populated after a successful payment.
    paid_at = models.DateTimeField(
        null=True,
        blank=True
    )


# ---------------------------------------------------------
# INVENTORY TRANSACTION
# ---------------------------------------------------------

class InventoryTransaction(models.Model):
    """
    Creates an audit trail of every inventory movement.

    Instead of only knowing the current quantity_on_hand, this table
    records WHY inventory changed.

    Examples:
        Sale       -> -2
        Restock    -> +10
        Return     -> +1
        Adjustment -> -1
    """

    TYPES = [
        ('restock', 'Restock'),
        ('sale', 'Sale'),
        ('return', 'Return'),
        ('adjustment', 'Adjustment'),
        ('cancel', 'Cancel'),
    ]

    # The specific product variant whose inventory changed.
    product_variant = models.ForeignKey(
        ProductVariant,
        on_delete=models.PROTECT,
        related_name='inventory_transactions'
    )

    # Optional user/admin responsible for creating the transaction.
    #
    # SET_NULL preserves the transaction history even if that
    # user account is later deleted.
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='inventory_transactions'
    )

    transaction_type = models.CharField(
        max_length=20,
        choices=TYPES
    )

    # Positive numbers add stock.
    # Negative numbers remove stock.
    quantity_change = models.IntegerField()

    # These reference fields allow the inventory transaction
    # to point back to the business event that caused it.
    #
    # Example:
    # reference_type = "order"
    # reference_id   = "ORD-F5ED48A973"
    reference_type = models.CharField(
        max_length=40,
        blank=True
    )

    reference_id = models.CharField(
        max_length=80,
        blank=True
    )

    notes = models.TextField(blank=True)

    # Records exactly when the stock movement occurred.
    transaction_date = models.DateTimeField(auto_now_add=True)