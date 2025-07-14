# Moneda - E-commerce Platform

Moneda is a modern e-commerce platform built with Flask and MongoDB, designed for selling industrial products with company-specific pricing and inventory management.

## Features

- User authentication (login, registration, password reset)
- Company selection and management
- Product catalog with categories and search
- Shopping cart functionality
- Order management
- Admin dashboard
- RESTful API

## Project Structure

```
moneda/
├── app/                          # Main application package
│   ├── __init__.py              # Application factory
│   ├── config.py                # Configuration settings
│   ├── models/                  # Database models
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── company.py
│   │   ├── product.py
│   │   └── order.py
│   │
│   ├── routes/                  # Application routes
│   │   ├── __init__.py
│   │   ├── auth.py             # Authentication routes
│   │   ├── main.py             # Main application routes
│   │   └── api/                # API endpoints
│   │
│   ├── static/                  # Static files (CSS, JS, images)
│   │   ├── css/
│   │   ├── js/
│   │   └── img/
│   │
│   ├── templates/               # Jinja2 templates
│   │   ├── base.html
│   │   ├── auth/
│   │   ├── main/
│   │   └── admin/
│   │
│   ├── utils/                   # Utility functions
│   │   ├── __init__.py
│   │   ├── decorators.py
│   │   ├── email.py
│   │   └── helpers.py
│   │
│   └── forms/                   # WTForms classes
│       ├── __init__.py
│       ├── auth_forms.py
│       └── main_forms.py
│
├── tests/                      # Unit and integration tests
├── migrations/                 # Database migrations
├── .env.example               # Example environment variables
├── .gitignore
├── requirements.txt           # Project dependencies
├── config.py                  # Configuration (not in version control)
└── run.py                     # Application entry point
```

## Getting Started

### Prerequisites

- Python 3.8+
- MongoDB 4.4+
- pip (Python package manager)

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/moneda.git
   cd moneda
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create a `.env` file based on `.env.example` and configure your environment variables:
   ```bash
   cp .env.example .env
   ```

5. Set up the database:
   - Make sure MongoDB is running
   - Run the following commands to initialize the database:
     ```bash
     python -c "from app import create_app; app = create_app(); app.app_context().push()"
     python -c "from app.models import db; db.create_all()"
     ```

### Running the Application

1. Start the development server:
   ```bash
   python run.py
   ```

2. Open your browser and navigate to:
   ```
   http://localhost:5000
   ```

### Running Tests

```bash
pytest
```

### Production Deployment

For production deployment, consider using:

- Gunicorn or uWSGI as the WSGI server
- Nginx as the reverse proxy
- Supervisor for process management
- Docker for containerization

Example with Gunicorn:
```bash
gunicorn -w 4 -b 0.0.0.0:5000 run:app
```

## Environment Variables

Create a `.env` file in the root directory with the following variables:

```
# Flask
FLASK_APP=run.py
FLASK_ENV=development
SECRET_KEY=your-secret-key-here

# Database
MONGODB_URI=mongodb://localhost:27017/moneda
MONGO_URI=mongodb://localhost:27017/moneda

# Email
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-email-password
MAIL_DEFAULT_SENDER=your-email@gmail.com

# Admin
ADMIN_EMAIL=admin@example.com
ADMIN_PASSWORD=changeme

# Frontend
FRONTEND_URL=http://localhost:3000
```

## API Documentation

API documentation is available at `/api/docs` when running in development mode.

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [Flask](https://flask.palletsprojects.com/)
- [MongoDB](https://www.mongodb.com/)
- [MongoEngine](https://mongoengine.org/)
- [Bootstrap](https://getbootstrap.com/)
- [Font Awesome](https://fontawesome.com/)
