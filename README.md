# Smart Retail - Project Foundation

A modern retail management system backend foundation built with FastAPI, SQLAlchemy, and PostgreSQL.

## Project Structure

```
smart-retail/
│
├── app/
│   ├── api/
│   │   ├── __init__.py
│   │   ├── health.py        # Health-check endpoints (API & Database connection test)
│   │   └── products.py      # Product REST CRUD API endpoints [NEW]
│   ├── database/
│   │   ├── __init__.py
│   │   └── session.py       # SQLAlchemy engine & session config
│   ├── models/
│   │   ├── __init__.py
│   │   └── product.py       # Product database model schema [NEW]
│   ├── schemas/
│   │   └── product.py       # Product Pydantic validation schemas [NEW]
│   ├── services/
│   │   └── product.py       # Business logic / Service layer implementation [NEW]
│   ├── templates/
│   │   └── index.html       # Single-page web dashboard template
│   ├── static/
│   │   ├── css/
│   │   │   └── style.css    # Premium glassmorphic styling
│   │   └── js/
│   │       └── app.js       # Asynchronous connection indicator scripts
│   ├── __init__.py
│   └── main.py              # Main FastAPI application entrypoint
│
├── .env                     # Local environment settings
├── requirements.txt         # Project package requirements
├── README.md                # Project documentation & instructions
└── run.bat                  # Windows startup batch file
```

## Prerequisites

1. **Python 3.9+** installed.
2. **PostgreSQL** running locally.
3. Database named `smart_retail` created in PostgreSQL.
   - Host: `localhost`
   - Port: `5432`
   - Username: `postgres`
   - Password: `root`

## Setup & Run Instructions

### 1. Database Creation
Before starting the backend, make sure you have created the database in PostgreSQL. You can run this command in your PostgreSQL console (psql) or query editor:
```sql
CREATE DATABASE smart_retail;
```

### 2. Configure Environment Variables
Verify or edit database credentials in the `.env` file at the root:
```ini
DATABASE_URL=postgresql://postgres:root@localhost:5432/smart_retail
```

### 3. Execution (Windows)
Double-click `run.bat` or run it via terminal to install dependencies and boot up the server:
```cmd
run.bat
```

### 4. Direct Manual Commands
If you prefer running manual commands:
```bash
# Install dependencies
pip install -r requirements.txt

# Start FastAPI server
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

## Access Points

- **JSON Health API**: [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
- **Detailed health status**: [http://127.0.0.1:8000/api/health](http://127.0.0.1:8000/api/health)
- **Web Dashboard**: [http://127.0.0.1:8000/dashboard](http://127.0.0.1:8000/dashboard)
- **Inventory Dashboard**: [http://127.0.0.1:8000/inventory-dashboard](http://127.0.0.1:8000/inventory-dashboard)
- **Swagger interactive API documentation**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

## Product Management API Endpoints

### 1. Create a Product
* **Route**: `POST /products`
* **Content-Type**: `application/json`
* **Request Body Example**:
```json
{
  "barcode": "890123456",
  "name": "Maggi",
  "category": "Noodles",
  "price": 20.00,
  "quantity": 50,
  "reorder_level": 10
}
```
* **Response Example (201 Created)**:
```json
{
  "barcode": "890123456",
  "name": "Maggi",
  "category": "Noodles",
  "price": 20.00,
  "quantity": 50,
  "reorder_level": 10,
  "id": 1,
  "created_at": "2026-06-11T10:00:00Z"
}
```

### 2. Retrieve All Products
* **Route**: `GET /products`
* **Response Example (200 OK)**:
```json
[
  {
    "barcode": "890123456",
    "name": "Maggi",
    "category": "Noodles",
    "price": 20.00,
    "quantity": 50,
    "reorder_level": 10,
    "id": 1,
    "created_at": "2026-06-11T10:00:00Z"
  }
]
```

### 3. Search Products (Case-Insensitive)
* **Route**: `GET /products/search?q=maggi`
* **Response Example (200 OK)**:
```json
[
  {
    "barcode": "890123456",
    "name": "Maggi",
    "category": "Noodles",
    "price": 20.00,
    "quantity": 50,
    "reorder_level": 10,
    "id": 1,
    "created_at": "2026-06-11T10:00:00Z"
  }
]
```

### 4. Low Stock Products
* **Route**: `GET /products/low-stock`
* **Description**: Returns all products where `quantity <= reorder_level`.
* **Response Example (200 OK)**:
```json
[
  {
    "barcode": "890123456",
    "name": "Maggi",
    "category": "Noodles",
    "price": 20.00,
    "quantity": 9,
    "reorder_level": 10,
    "id": 1,
    "created_at": "2026-06-11T10:00:00Z"
  }
]
```

### 5. Retrieve Product by ID
* **Route**: `GET /products/{id}`
* **Response Example (200 OK)**:
```json
{
  "barcode": "890123456",
  "name": "Maggi",
  "category": "Noodles",
  "price": 20.00,
  "quantity": 50,
  "reorder_level": 10,
  "id": 1,
  "created_at": "2026-06-11T10:00:00Z"
}
```
* **Response Example (404 Not Found)**:
```json
{
  "detail": "Product with ID 99999 not found"
}
```

### 6. Update Product
* **Route**: `PUT /products/{id}`
* **Content-Type**: `application/json`
* **Request Body Example** (All fields optional):
```json
{
  "price": 25.00,
  "quantity": 60
}
```
* **Response Example (200 OK)**:
```json
{
  "barcode": "890123456",
  "name": "Maggi",
  "category": "Noodles",
  "price": 25.00,
  "quantity": 60,
  "reorder_level": 10,
  "id": 1,
  "created_at": "2026-06-11T10:00:00Z"
}
```

### 7. Delete Product
* **Route**: `DELETE /products/{id}`
* **Response Example (200 OK)**:
```json
{
  "message": "Product deleted successfully"
}
```


