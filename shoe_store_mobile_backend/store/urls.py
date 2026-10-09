# Django's path() function is used to define individual URL routes.
from django.urls import path

# DefaultRouter automatically creates standard REST API routes
# for Django REST Framework ViewSets.
from rest_framework.routers import DefaultRouter

# Django REST Framework provides this built-in view for token login.
# A valid username/password is exchanged for an authentication token.
from rest_framework.authtoken.views import obtain_auth_token

# Import the views that handle requests for each API endpoint.
from .views import (
    CategoryViewSet,
    ProductViewSet,
    CheckoutView,
    MyOrdersView,
    RegisterView,
    AddressListCreateView,
    AddressDetailView,
)


# ---------------------------------------------------------
# API ROUTER
# ---------------------------------------------------------

# DefaultRouter automatically generates REST-style URLs for
# ViewSets such as CategoryViewSet and ProductViewSet.
router = DefaultRouter()


# Register the category endpoints.
#
# This automatically creates routes such as:
#
# GET  /api/categories/
# GET  /api/categories/<id>/
router.register(
    'categories',
    CategoryViewSet
)


# Register the product endpoints.
#
# This automatically creates routes such as:
#
# GET  /api/products/
# GET  /api/products/<id>/
router.register(
    'products',
    ProductViewSet
)


# ---------------------------------------------------------
# CUSTOM API ROUTES
# ---------------------------------------------------------

# These views use APIView rather than ViewSet, so they are
# connected to URLs manually with path().
urlpatterns = [

    # -----------------------------------------------------
    # CUSTOMER ACCOUNT
    # -----------------------------------------------------

    # Create a new customer account.
    #
    # POST /api/register/
    path(
        'register/',
        RegisterView.as_view(),
        name='register'
    ),

    # Authenticate an existing user.
    #
    # POST /api/login/
    #
    # The client sends a username and password.
    # If valid, Django returns an authentication token that
    # the mobile app can use for protected API requests.
    path(
        'login/',
        obtain_auth_token,
        name='api-login'
    ),


    # -----------------------------------------------------
    # CUSTOMER ADDRESSES
    # -----------------------------------------------------

    # Work with the authenticated customer's address collection.
    #
    # GET  /api/addresses/
    #      -> List the customer's addresses
    #
    # POST /api/addresses/
    #      -> Create a new address
    path(
        'addresses/',
        AddressListCreateView.as_view(),
        name='addresses'
    ),

    # Work with one specific address.
    #
    # <int:pk> captures the address's integer primary key
    # from the URL and passes it to AddressDetailView.
    #
    # Examples:
    #
    # GET    /api/addresses/2/
    # PUT    /api/addresses/2/
    # PATCH  /api/addresses/2/
    # DELETE /api/addresses/2/
    #
    # AddressDetailView also verifies that the requested
    # address belongs to the authenticated customer.
    path(
        'addresses/<int:pk>/',
        AddressDetailView.as_view(),
        name='address-detail'
    ),


    # -----------------------------------------------------
    # CUSTOMER ORDERS
    # -----------------------------------------------------

    # Return the authenticated customer's order history.
    #
    # GET /api/orders/
    path(
        'orders/',
        MyOrdersView.as_view(),
        name='my-orders'
    ),

    # Create a new order through the checkout workflow.
    #
    # POST /api/orders/checkout/
    #
    # CheckoutView validates the request and then calls our
    # create_order() service, which handles order creation
    # and inventory updates.
    path(
        'orders/checkout/',
        CheckoutView.as_view(),
        name='checkout'
    ),
]


# Add all automatically generated router URLs to urlpatterns.
#
# This is what makes the registered category and product
# ViewSet routes available alongside our custom routes above.
urlpatterns += router.urls