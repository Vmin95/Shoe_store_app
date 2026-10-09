# Shoe Store Mobile Backend

Django REST API backend for a mobile-first shoe ordering and inventory application.

## Phase 1 scope
- Customers and addresses
- Products, categories, and size/color variants
- Carts and cart items
- Orders and order items
- Payments
- Inventory transaction history
- Admin/staff tracking

## Setup
1. Create a Python virtual environment.
2. Install dependencies: `pip install -r requirements.txt`
3. Copy `.env.example` to `.env` and fill in database settings.
4. Create the MySQL database and user.
5. Run `python manage.py makemigrations` and `python manage.py migrate`.
6. Create an admin user with `python manage.py createsuperuser`.
7. Start with `python manage.py runserver`.

## Architecture
Mobile app -> Django REST API -> MySQL

The data model intentionally tracks inventory at the product-variant level so each shoe size/color can have its own SKU and stock quantity.
