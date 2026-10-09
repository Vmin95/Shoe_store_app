# Shoe Store Mobile Application — Backend

**Status:** In Active Development

## Overview

A RESTful backend for a mobile shoe store application, developed using Python, Django REST Framework, and MySQL.

The application is designed to support an online shoe retail business by managing product catalogs, customer accounts, inventory, and order processing.

The project focuses on building reliable backend services, maintaining relational data integrity, and implementing transactional business logic.

## Technology Stack

- **Backend:** Python, Django, Django REST Framework
- **Database:** MySQL
- **Authentication:** Django Authentication and DRF Token Authentication
- **Development Tools:** IntelliJ IDEA, Git, GitHub
- **API Architecture:** RESTful API

## Implemented Features

### Product and Inventory Management
- Relational models for products, categories, and product variants
- Product variants identified by attributes such as size and SKU
- Inventory quantity tracking
- Product and category retrieval through REST API endpoints

### Customer Authentication
- Token-based authentication
- Protected checkout operations
- Customer profiles and associated delivery addresses

### Order Processing
- Authenticated checkout endpoint
- Order and order-item creation
- Product quantity validation
- Insufficient-stock error handling
- Inventory transaction records for completed orders

### Transactional Inventory Updates
- Atomic database transactions for order creation and inventory updates
- Automatic stock reduction during checkout
- Validation to prevent purchases exceeding available inventory
- Transactional consistency between orders and inventory changes

## API Endpoints

| Endpoint | Purpose |
|---|---|
| `POST /api/login/` | User authentication |
| `GET /api/categories/` | Retrieve product categories |
| `GET /api/products/` | Retrieve available products |
| `POST /api/orders/checkout/` | Submit an authenticated order |

Additional endpoints and functionality are under development.

## Backend Architecture

The application follows Django's modular structure:

- **Models:** Define relational database entities and relationships.
- **Serializers:** Validate and transform data exchanged through the API.
- **Views:** Process HTTP requests and responses.
- **Services:** Handle order processing, stock validation, and inventory transactions.
- **URLs:** Map API routes to their corresponding views.

## Local Development

### Prerequisites
- Python
- MySQL
- Git

### Installation

1. Clone the repository.
2. Navigate to the `shoe_store_mobile_backend` directory.
3. Create and activate a Python virtual environment.
4. Install dependencies:

   `pip install -r requirements.txt`

5. Configure environment variables using `.env.example` as a reference.
6. Create the required MySQL database.
7. Apply migrations:

   `python manage.py migrate`

8. Start the development server:

   `python manage.py runserver`

Database credentials and application secrets should be stored in a local `.env` file and never committed to version control.

## Development Roadmap

- [x] Design relational database models
- [x] Implement product and category APIs
- [x] Implement token-based authentication
- [x] Implement authenticated checkout
- [x] Implement transactional inventory updates
- [x] Validate insufficient-stock handling
- [ ] Expand automated API and unit testing
- [ ] Implement payment integration
- [ ] Develop mobile frontend
- [ ] Improve API documentation
- [ ] Prepare deployment configuration

## Project Purpose

This project provides hands-on experience developing backend systems for a real-world retail use case, with an emphasis on REST API design, relational databases, authentication, transactional processing, and inventory consistency.

The application is actively being developed and will continue to expand with additional e-commerce functionality.
