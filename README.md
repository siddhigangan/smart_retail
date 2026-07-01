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
├── tests/
│   └── test_services.py     # Automated backend & service validation tests
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

### 3. Database Seeding (Nagpur 500-Product Dataset)
Run the seeding script to set up all tables and import the 500-product master, customers list, transaction history, shelves, and inventory planograms:
```cmd
venv\Scripts\python seed_shelf_data.py
```

### 4. Execution (Windows)
Double-click `run.bat` or run it via terminal to install dependencies and boot up the server:
```cmd
run.bat
```

### 5. Direct Manual Commands
If you prefer running manual commands:
```bash
# Install dependencies
pip install -r requirements.txt

# Start FastAPI server
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

## Shelf Refill Workflow
The **Shelf Management & Replenishment** system simulates moving stock from warehouse storage to customer-facing shelves:
1. **Purchase stock deduction**: When a cashier processes a transaction (using the billing checkout screen), the quantity of purchased items is automatically decremented from both the total product stock and the physical shelf (`current_shelf_quantity`).
2. **Low shelf stock warning**: When `current_shelf_quantity <= minimum_shelf_quantity`, the shelf status turns into **Yellow: Refill Required** on the dashboard.
3. **Refill trigger**: Operators click **Refill Shelf** which sends a request to `POST /shelf/refill/{product_id}`.
4. **Stock replenishment**: The system moves inventory from the warehouse (`warehouse_quantity`) to the shelf (`current_shelf_quantity`) up to the shelf capacity, logging the transaction details in the `refill_logs` table. If the warehouse runs out of stock, the status transitions to **Red: Warehouse Empty**.

## Payment & Checkout Workflow
The **Supermarket POS system** supports robust checkout payment operations:
1. **Mandatory Customer Info**: Cashiers must enter Customer Name and a valid 10-digit WhatsApp phone number (Email has been fully removed).
2. **Multiple Payment Methods**:
   - **Cash**: Cashiers type the "Cash Received" amount, and the system automatically calculates either the "Change to Return" or the "Remaining Amount" dynamically. Invoices are blocked until full payment is received.
   - **UPI / Card**: Quick single-tap transactions with instant receipt generation.
   - **Split Payments**: Allows combining two modes: Cash + UPI, Cash + Card, or UPI + Card. Remaining balances are calculated dynamically and checkout is locked until exactly 100% of the total amount is split.
3. **Bill Controls**:
   - **Hold Bill / Suspend Bill**: Park current active cart data with customer details to serve the next customer. Restored instantly using **Resume Bill**.
   - **Cancel Bill**: Allows cashiers to void/cancel an active cart, saving details into a session audit log viewable via **Cancelled Bills**.
4. **WhatsApp Dispatch**: Post-checkout, cashiers can dispatch invoices instantly to customer WhatsApp numbers. The UI displays **WhatsApp Status** as `Pending` until dispatched, which then toggles to `Sent`.

## Inventory Analytics Dashboard
The **Inventory Analytics** dashboard serves as the central control room for store managers, offering:
1. **Critical KPI Summaries**: Instantly tracks inventory valuation (calculated at cost price), product line counts, low stock items, out-of-stock items, dead stock lines, overstocked products, and dynamic utilization percentages for both storefront shelves and backroom warehouses.
2. **Interactive Visualizations (Chart.js)**: Doughnut, bar, and pie charts visualise stock/value allocations and category distribution dynamically.
3. **Tabular Operational Lists**: Shows categorised reports:
   - **Fast Moving Products**: Items requiring frequent shelf replenishment checks.
   - **Slow Moving Products**: Low-frequency sales items.
   - **Dead Stock**: Products flagged with no active customer demand.
   - **Expiring Soon**: Batches sorted by their expiration dates to prevent wastage.
   - **Warehouse Empty**: Alerts listing slots where backroom stocks have depleted.
4. **Dynamic Filters**: Quick filtering by Category, Floor Level, and Movement Class instantly updates all KPIs, charts, and tables without reloading context.

## Inventory Dashboard Quick Filters
The **Inventory Dashboard** ([/inventory-dashboard](http://127.0.0.1:8000/inventory-dashboard)) has been updated with high-performance quick-action buttons below the metrics section:
1. **Quick Filters**: All Products, Low Stock, Out of Stock, Overstocked, Fast Moving, Slow Moving, Expiring Soon, Warehouse Empty, and Shelf Refill Needed.
2. **Badges Count**: Each button displays a live item count. KPI metric cards (Total Products, Total Quantity, Low Stock Warnings, Out of Stock, Shelf Refill Needed, and Warehouse Empty) are automatically updated in sync with filters.
3. **Graceful Analytics Fallbacks**: If sales histories or batch expiries are not yet generated, clicking *Fast/Slow Moving* or *Expiring Soon* displays a professional placeholder message explaining how to activate tracking.
4. **AJAX Dynamic Updates**: Uses non-blocking backend JSON requests to `/inventory/filter?type=...` to dynamically refresh metrics and tables without full-page reloads.

## PDF Invoice Generator & Mock WhatsApp Dispatch
The **Invoicing System** generates professional PDF invoices on checkout and logs mock WhatsApp messages:
1. **Local File Storage**: PDF receipts are programmatically generated using `reportlab` and saved locally under `app/static/invoices/` using format `INV-YYYYMMDD-[SERIAL].pdf`. The implementation uses a swappable `InvoiceStorageService` architecture for future cloud integration.
2. **Metadata Logs**: Stores invoice metadata (`invoice_number`, `invoice_url`, `pdf_path`, `customer_name`, `customer_phone`, `total_amount`, `whatsapp_status = MOCK_SENT`, `created_at`) in PostgreSQL.
3. **Receipt Retrieval Screen**: The web route `/invoice/{invoice_number}` renders a corporate green/white template displaying the items table (quantities, prices, GST, discounts), loyalty points earned, a print window trigger, and a PDF downloader link.
4. **Simulated WhatsApp Dispatch**: In development mode, the checkout system prints the outbound customer SMS/WhatsApp message containing the invoice url directly to the stdout console.

## Reset Transactional Data
For local development, an admin data purge tool has been created:
1. **Clear Tables**: Deletes all records from `bill_items`, `bills`, and `invoices` tables.
2. **Local Receipts Purge**: Deletes all generated PDF files under `app/static/invoices/`.
3. **Reset Customers**: Resets customer loyalty totals (`total_points = 0`) to baseline.
4. **Trigger Mechanism**: Access the reset button via the main **System Health Dashboard** (`/dashboard`). Prompts for user confirmation before executing a `POST` request to `/admin/reset-transactions`.

## Product Management Module
A complete ERP-style catalog and inventory manager is served at `/products-management`:
1. **Manual Add Product**: Add new products with automatic fields (mrp, selling_price, brand, gst %, sub_category).
2. **Shelf Recommendation**: Upon category selection, queries the database to recommend shelves matching the category zone, sorted by highest remaining capacity.
3. **Stock Split & Distribution**: Splits the total quantity of new/imported products into shelf stock (limited by shelf capacity) and backroom warehouse stock automatically.
4. **Bulk Imports**: Upload `.csv` or `.xlsx` files using a multi-step validation engine (Upload -> Validate -> Preview -> Commit). Unprovided shelves are assigned using the best recommended category matches.
5. **Bulk Stock Update**: Adjust stock levels via file uploads or simple textbox lines (Format: `Barcode, NewQuantity, Reason`).
6. **Inventory Adjustments**: Adjust stock levels (positive or negative) with reasons (*Damaged*, *Expired*, *Lost*, *Theft*, *Returned*) which create audit records in `adjustment_logs`.

## Access Points

- **JSON Health API**: [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
- **Detailed health status**: [http://127.0.0.1:8000/api/health](http://127.0.0.1:8000/api/health)
- **Web Dashboard**: [http://127.0.0.1:8000/dashboard](http://127.0.0.1:8000/dashboard)
- **Inventory Dashboard**: [http://127.0.0.1:8000/inventory-dashboard](http://127.0.0.1:8000/inventory-dashboard)
- **Shelf Management Dashboard**: [http://127.0.0.1:8000/shelf-management](http://127.0.0.1:8000/shelf-management)
- **Inventory Analytics Dashboard**: [http://127.0.0.1:8000/inventory-analytics](http://127.0.0.1:8000/inventory-analytics)
- **Products Management Dashboard**: [http://127.0.0.1:8000/products-management](http://127.0.0.1:8000/products-management)
- **Invoice Retrieval Page**: [http://127.0.0.1:8000/invoice/{invoice_number}](http://127.0.0.1:8000/invoice/INV-20260630-0001)
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

## Verification & Testing

The repository contains an automated service validation suite to check backend correctness (database, models, schemas, and logic).

To execute the test suite locally:
```bash
# Verify services using virtual environment Python
venv\Scripts\python tests/test_services.py
```

## Compatibility & Framework Notes

* **Starlette 1.0.0+ Template Response**: In Starlette v1.0.0+ (and newer versions of FastAPI), `TemplateResponse` requires the `request` object as the first positional argument (i.e. `TemplateResponse(request, name, context)`). The deprecated signature `TemplateResponse(name, context)` will raise a caching Type Error: `cannot use 'tuple' as a dict key (unhashable type: 'dict')` in Jinja2. This has been fully corrected in [main.py](file:///d:/Startup/smart-retail/app/main.py).
