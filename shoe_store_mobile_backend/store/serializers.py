# Django's built-in User model handles usernames, emails,
# passwords, and authentication.
from django.contrib.auth.models import User

# transaction.atomic lets us group database operations together.
# If one operation fails, all operations in the transaction are rolled back.
from django.db import transaction

# Django REST Framework serializers convert between:
# - Python/Django objects
# - JSON data sent to and from the mobile app
from rest_framework import serializers

# Import the database models that these serializers work with.
from .models import (
    Category,
    Product,
    ProductVariant,
    Order,
    OrderItem,
    Customer,
    Address,
    Cart,
    CartItem,
)


# ---------------------------------------------------------
# PRODUCT VARIANT SERIALIZER
# ---------------------------------------------------------

class ProductVariantSerializer(serializers.ModelSerializer):
    """
    Converts ProductVariant objects into JSON.

    A product variant represents one specific sellable version
    of a shoe, such as:

        Air Jordan 1
        Size: 9
        Color: Black
        SKU: AJ1-RH-BLK-090

    Inventory is tracked at the variant level because different
    shoe sizes can have different quantities available.
    """

    class Meta:
        # Connect this serializer to the ProductVariant model.
        model = ProductVariant

        # These fields will appear in API responses.
        fields = [
            'id',
            'sku',
            'size',
            'color',
            'price',
            'quantity_on_hand',
            'reorder_level',
            'is_active',
        ]


# ---------------------------------------------------------
# PRODUCT SERIALIZER
# ---------------------------------------------------------

class ProductSerializer(serializers.ModelSerializer):
    """
    Converts Product objects into JSON.

    Products contain the main shoe information, while individual
    sizes/colors are stored as ProductVariant records.
    """

    # Include all ProductVariant records that belong to this product.
    #
    # many=True means one Product can have multiple variants.
    # read_only=True means API clients cannot create variants through
    # this nested field.
    variants = ProductVariantSerializer(
        many=True,
        read_only=True
    )

    # Return the category name in addition to the category ID.
    #
    # source='category.name' tells DRF to follow the Product's
    # category relationship and retrieve its name.
    category_name = serializers.CharField(
        source='category.name',
        read_only=True
    )

    class Meta:
        model = Product

        fields = [
            'id',
            'category',
            'category_name',
            'name',
            'brand',
            'description',
            'image_url',
            'is_active',
            'variants',
        ]


# ---------------------------------------------------------
# CATEGORY SERIALIZER
# ---------------------------------------------------------

class CategorySerializer(serializers.ModelSerializer):
    """
    Converts Category objects into JSON.

    Categories allow products to be grouped into sections such
    as Sneakers, Boots, Sandals, etc.
    """

    class Meta:
        model = Category

        fields = [
            'id',
            'name',
            'description',
            'image_url',
            'is_active',
        ]


# ---------------------------------------------------------
# CHECKOUT INPUT SERIALIZERS
# ---------------------------------------------------------

class CheckoutItemSerializer(serializers.Serializer):
    """
    Validates one product item sent during checkout.

    Example JSON:

        {
            "product_variant_id": 1,
            "quantity": 2
        }

    Notice that the customer does NOT send a price.
    The backend retrieves the real price from the database so
    someone cannot manipulate the mobile request and choose
    their own price.
    """

    # ID of the exact shoe variant being purchased.
    product_variant_id = serializers.IntegerField()

    # Customers must order at least one item.
    quantity = serializers.IntegerField(min_value=1)


class CheckoutSerializer(serializers.Serializer):
    """
    Validates the complete checkout request sent by the mobile app.
    """

    # Saved address the customer wants to use for shipping.
    shipping_address_id = serializers.IntegerField()

    # Saved address the customer wants to use for billing.
    billing_address_id = serializers.IntegerField()

    # An order may contain multiple different product variants.
    items = CheckoutItemSerializer(many=True)


# ---------------------------------------------------------
# ORDER ITEM SERIALIZER
# ---------------------------------------------------------

class OrderItemSerializer(serializers.ModelSerializer):
    """
    Converts individual OrderItem records into JSON.

    An OrderItem represents one line inside an order.
    """

    # Get the product name through:
    #
    # OrderItem
    #   -> ProductVariant
    #       -> Product
    #           -> name
    product_name = serializers.CharField(
        source='product_variant.product.name',
        read_only=True
    )

    # Include the SKU of the exact variant that was purchased.
    sku = serializers.CharField(
        source='product_variant.sku',
        read_only=True
    )

    # Include the selected shoe size.
    size = serializers.CharField(
        source='product_variant.size',
        read_only=True
    )

    class Meta:
        model = OrderItem

        fields = [
            'id',
            'product_variant',
            'product_name',
            'sku',
            'size',
            'quantity',
            'unit_price',
            'discount',
            'subtotal',
        ]


# ---------------------------------------------------------
# ORDER SERIALIZER
# ---------------------------------------------------------

class OrderSerializer(serializers.ModelSerializer):
    """
    Converts an Order and its OrderItems into JSON.

    This serializer is used both for checkout confirmation and
    for the customer's My Orders screen.
    """

    # Include all OrderItem records belonging to this order.
    items = OrderItemSerializer(
        many=True,
        read_only=True
    )

    class Meta:
        model = Order

        fields = [
            'id',
            'order_number',
            'status',
            'payment_status',
            'subtotal',
            'discount_total',
            'shipping_fee',
            'tax_total',
            'total_amount',
            'order_date',
            'items',
        ]


# ---------------------------------------------------------
# CUSTOMER REGISTRATION SERIALIZER
# ---------------------------------------------------------

class RegisterSerializer(serializers.Serializer):
    """
    Validates account-registration data and creates both:

        1. Django User
        2. Customer profile

    The Django User stores authentication information.
    The Customer model stores information specific to shoppers.
    """

    username = serializers.CharField(max_length=150)

    # EmailField automatically checks that the value looks
    # like a valid email address.
    email = serializers.EmailField()

    # write_only=True prevents the password from ever appearing
    # in API responses.
    password = serializers.CharField(
        write_only=True,
        min_length=8
    )

    first_name = serializers.CharField(max_length=150)
    last_name = serializers.CharField(max_length=150)

    def validate_username(self, value):
        """
        Prevent duplicate usernames.

        __iexact makes this comparison case-insensitive, so:
        'NewCustomer' and 'newcustomer' are treated as duplicates.
        """

        if User.objects.filter(
                username__iexact=value
        ).exists():
            raise serializers.ValidationError(
                "A user with this username already exists."
            )

        return value

    def validate_email(self, value):
        """
        Prevent multiple accounts from registering with the
        same email address.
        """

        if User.objects.filter(
                email__iexact=value
        ).exists():
            raise serializers.ValidationError(
                "A user with this email already exists."
            )

        return value

    @transaction.atomic
    def create(self, validated_data):
        """
        Create both the Django User and Customer profile.

        transaction.atomic guarantees that either BOTH records
        are created or NEITHER is created.

        For example, if Customer creation fails after User creation,
        Django rolls back the User record too.
        """

        # create_user() is important because Django securely
        # hashes the password before storing it.
        #
        # We should never store the raw password ourselves.
        user = User.objects.create_user(
            username=validated_data["username"],
            email=validated_data["email"],
            password=validated_data["password"],
            first_name=validated_data["first_name"],
            last_name=validated_data["last_name"],
        )

        # Create the shopping/customer profile linked to the
        # authentication account.
        customer = Customer.objects.create(
            user=user,
        )

        return customer


# ---------------------------------------------------------
# ADDRESS SERIALIZER
# ---------------------------------------------------------

class AddressSerializer(serializers.ModelSerializer):
    """
    Converts customer Address objects to and from JSON.

    The customer field is intentionally NOT exposed here.

    The backend determines which customer owns an address from
    the authentication token rather than trusting a customer ID
    sent by the mobile app.
    """

    class Meta:
        model = Address

        fields = [
            'id',
            'full_name',
            'phone',
            'address_line_1',
            'address_line_2',
            'city',
            'state',
            'postal_code',
            'country',
            'address_type',
            'is_default',
        ]

        # Database IDs are generated by Django/MySQL.
        # The mobile app is allowed to read them but not choose them.
        read_only_fields = ['id']

    # ---------------------------------------------------------
# CART SERIALIZERS
# ---------------------------------------------------------

class CartItemSerializer(serializers.ModelSerializer):
    # Pull useful product information through the ProductVariant
    # relationship so the mobile app does not need extra API calls.
    product_name = serializers.CharField(
        source='product_variant.product.name',
        read_only=True,
    )

    sku = serializers.CharField(
        source='product_variant.sku',
        read_only=True,
    )

    size = serializers.CharField(
        source='product_variant.size',
        read_only=True,
    )

    color = serializers.CharField(
        source='product_variant.color',
        read_only=True,
    )

    # Always get the current price from our database.
    # The customer/mobile app does not supply the price.
    price = serializers.DecimalField(
        source='product_variant.price',
        max_digits=10,
        decimal_places=2,
        read_only=True,
    )

    class Meta:
        model = CartItem
        fields = [
            'id',
            'product_variant',
            'product_name',
            'sku',
            'size',
            'color',
            'price',
            'quantity',
        ]


class CartSerializer(serializers.ModelSerializer):
    # Include all CartItem objects belonging to this cart.
    #
    # "items" works because CartItem.cart uses:
    # related_name='items'
    items = CartItemSerializer(
        many=True,
        read_only=True,
    )

    class Meta:
        model = Cart
        fields = [
            'id',
            'is_active',
            'items',
        ]
        