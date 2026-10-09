from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404

from .models import Category, Product, Address, Order
from .serializers import (
    CategorySerializer,
    ProductSerializer,
    CheckoutSerializer,
    OrderSerializer,
    RegisterSerializer,
    AddressSerializer,
)
from .services import create_order, InsufficientStockError


# -----------------------------
# PRODUCT CATALOG
# -----------------------------

class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    # Only return categories that are currently active.
    queryset = Category.objects.filter(is_active=True)
    serializer_class = CategorySerializer


class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    # Return only active products.
    #
    # select_related('category') reduces extra database queries
    # when accessing each product's category.
    #
    # prefetch_related('variants') efficiently loads all shoe
    # sizes/colors associated with each product.
    queryset = (
        Product.objects
        .filter(is_active=True)
        .select_related('category')
        .prefetch_related('variants')
    )

    serializer_class = ProductSerializer


# -----------------------------
# CHECKOUT
# -----------------------------

class CheckoutView(APIView):
    # Customers must be logged in before they can place an order.
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # Validate the checkout data sent from the mobile app.
        serializer = CheckoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Get the Customer profile connected to the authenticated Django User.
        customer = request.user.customer_profile

        # Make sure the shipping address actually belongs to this customer.
        shipping_address = get_object_or_404(
            Address,
            id=serializer.validated_data["shipping_address_id"],
            customer=customer,
        )

        # Make sure the billing address also belongs to this customer.
        billing_address = get_object_or_404(
            Address,
            id=serializer.validated_data["billing_address_id"],
            customer=customer,
        )

        try:
            # The service handles the important business logic:
            # - creates the order
            # - creates order items
            # - checks available stock
            # - decreases inventory
            # - records inventory transactions
            order = create_order(
                customer=customer,
                shipping_address=shipping_address,
                billing_address=billing_address,
                items=serializer.validated_data["items"],
            )

        except InsufficientStockError as exc:
            # Return a clean API error instead of allowing inventory
            # to drop below zero.
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Send the completed order back to the mobile app.
        return Response(
            OrderSerializer(order).data,
            status=status.HTTP_201_CREATED,
        )


# -----------------------------
# CUSTOMER ORDER HISTORY
# -----------------------------

class MyOrdersView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        customer = request.user.customer_profile

        # Only return orders belonging to the logged-in customer.
        #
        # prefetch_related loads the order items, product variants,
        # and product information efficiently.
        orders = (
            Order.objects
            .filter(customer=customer)
            .prefetch_related(
                'items__product_variant__product'
            )
            .order_by('-order_date')
        )

        return Response(
            OrderSerializer(orders, many=True).data
        )


# -----------------------------
# CUSTOMER REGISTRATION
# -----------------------------

class RegisterView(APIView):
    # A user cannot already be logged in if they are creating
    # their first account, so registration is publicly accessible.
    permission_classes = []

    def post(self, request):
        # Validate username, email, password, and customer information.
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # RegisterSerializer creates both the Django User
        # and the linked Customer profile.
        customer = serializer.save()

        return Response(
            {
                "message": "Account created successfully.",
                "username": customer.user.username,
                "email": customer.user.email,
            },
            status=status.HTTP_201_CREATED,
        )


# -----------------------------
# ADDRESS LIST / CREATE
# -----------------------------

class AddressListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        customer = request.user.customer_profile

        # Only return addresses belonging to the authenticated customer.
        # Default addresses appear first.
        addresses = (
            Address.objects
            .filter(customer=customer)
            .order_by('-is_default', '-created_at')
        )

        return Response(
            AddressSerializer(addresses, many=True).data
        )

    def post(self, request):
        customer = request.user.customer_profile

        serializer = AddressSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # A customer should only have one default address.
        # If this new address is marked as default,
        # remove the default flag from their existing addresses first.
        if serializer.validated_data.get("is_default", False):
            Address.objects.filter(
                customer=customer,
                is_default=True,
            ).update(is_default=False)

        # Automatically attach the address to the logged-in customer.
        # The client does not get to choose customer_id.
        address = serializer.save(
            customer=customer
        )

        return Response(
            AddressSerializer(address).data,
            status=status.HTTP_201_CREATED,
        )


# -----------------------------
# ADDRESS DETAIL / UPDATE / DELETE
# -----------------------------

class AddressDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_address(self, request, pk):
        customer = request.user.customer_profile

        # This ownership check is reused by GET, PUT, PATCH, and DELETE.
        # A customer cannot access another customer's address by changing the ID.
        return get_object_or_404(
            Address,
            pk=pk,
            customer=customer,
        )

    def get(self, request, pk):
        address = self.get_address(request, pk)

        return Response(
            AddressSerializer(address).data
        )

    def put(self, request, pk):
        address = self.get_address(request, pk)

        # PUT expects the complete address representation.
        serializer = AddressSerializer(
            address,
            data=request.data,
        )
        serializer.is_valid(raise_exception=True)

        # If this address is being made the default,
        # clear the default flag from the customer's other addresses.
        if serializer.validated_data.get("is_default", False):
            Address.objects.filter(
                customer=request.user.customer_profile,
                is_default=True,
            ).exclude(pk=address.pk).update(is_default=False)

        serializer.save()

        return Response(serializer.data)

    def patch(self, request, pk):
        address = self.get_address(request, pk)

        serializer = AddressSerializer(
            address,
            data=request.data,
            partial=True,
        )
        serializer.is_valid(raise_exception=True)

    # If this address is being made the default,
    # clear the default flag from every other address
    # belonging to this customer.
        if serializer.validated_data.get("is_default", False):
            Address.objects.filter(
                customer=request.user.customer_profile,
                is_default=True,
            ).exclude(pk=address.pk).update(is_default=False)

        serializer.save()

        return Response(serializer.data)

    def delete(self, request, pk):
        address = self.get_address(request, pk)

        # Delete only after confirming that the address belongs
        # to the authenticated customer.
        address.delete()

        return Response(
            status=status.HTTP_204_NO_CONTENT
        )