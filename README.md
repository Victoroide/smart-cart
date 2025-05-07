# FICCT E-commerce Backend

A powerful and flexible e-commerce platform built with Django REST Framework, offering comprehensive APIs for product management, user authentication, shopping cart functionality, payment processing, customer feedback, and reporting.

## 🚀 Features

- **Product Management**: Catalog, categories, brands, inventory tracking
- **User Authentication**: JWT-based authentication system
- **Shopping Cart & Orders**: Complete order processing lifecycle
- **Payment Integration**: Stripe and PayPal payment gateways
- **Customer Loyalty System**: Tiered customer rewards and discounts
- **Delivery Management**: Order shipping and tracking
- **Feedback System**: Product and delivery ratings
- **Advanced Search**: AI-powered product search and recommendations using Pinecone and OpenAI
- **Comprehensive Reporting**: Generate sales, inventory and order reports in PDF/Excel
- **API Documentation**: Interactive API docs with Swagger UI

## 📋 Prerequisites

- Python 3.11+
- PostgreSQL
- Stripe and PayPal developer accounts
- OpenAI API Key
- Pinecone API Key

## 🔧 Installation

1. Clone the repository
```bash
git clone https://github.com/yourusername/ficct-ecommerce.git
cd ficct-ecommerce
```

2. Create and activate virtual environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies
```bash
pip install -r requirements.txt
```

4. Configure environment variables (create a `.env` file)
```
SECRET_KEY=your-secret-key
DEBUG=True
DATABASE_URL=postgresql://user:password@localhost:5432/dbname
STRIPE_API_KEY=your-stripe-key
STRIPE_WEBHOOK_SECRET=your-stripe-webhook-secret
PAYPAL_CLIENT_ID=your-paypal-client-id
PAYPAL_CLIENT_SECRET=your-paypal-client-secret
OPENAI_API_KEY=your-openai-api-key
PINECONE_API_KEY=your-pinecone-api-key
PINECONE_INDEX_NAME=your-pinecone-index
```

5. Run migrations
```bash
python manage.py migrate
```

6. Create a superuser
```bash
python manage.py createsuperuser
```

7. Run the server
```bash
python manage.py runserver
```

## 🐳 Docker Deployment

You can also run the application using Docker:

```bash
docker-compose up -d
```

Or build and run the Docker image directly:

```bash
docker build -t ficct-ecommerce .
docker run -p 8000:8000 ficct-ecommerce
```

## 📁 Project Structure

```
app/
  ├── authentication/    # User authentication and customer loyalty
  ├── chatbot/           # AI-powered shopping assistant
  ├── orders/            # Orders, payments, deliveries, feedback
  ├── parameter/         # System parameters and settings
  ├── products/          # Products, categories, brands, inventory
  ├── reports/           # Report generation (PDF/Excel)
base/                    # Core Django settings
core/                    # Shared functionality
services/                # Business logic services
  ├── discount_service.py
  ├── openai_service.py
  ├── pinecone_service.py
  ├── recommendation_service.py
```

## 🔌 API Documentation

The API is documented using Swagger UI, which can be accessed at:

```
http://localhost:8000/docs/
```

Key API endpoints include:

- `/api/auth/` - Authentication endpoints
- `/api/products/` - Product management
- `/api/finance/` - Orders and transactions
- `/api/payments/` - Payment processing
- `/api/delivery/` - Shipping and delivery
- `/api/feedback/` - Customer reviews and ratings
- `/api/reports/` - Report generation

## ⚙️ Configuration

The application supports various configuration options through environment variables:

- Database settings
- Payment gateway configuration
- Storage options (local or cloud)
- Authentication settings
- Third-party service integration

## 🧪 Running Tests

```bash
python manage.py test
```
