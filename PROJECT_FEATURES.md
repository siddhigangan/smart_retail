# Smart Retail - Software Feature Documentation

## 1. Project Overview

Smart Retail is a professional, ERP-style supermarket Point of Sale (POS) and inventory management application. The system integrates checkout processes, inventory tracking, automatic shelf planogram suggestions, stock replenishment workflows, invoicing, and customer loyalty management.

### Technology Stack
* **Backend Framework**: FastAPI (Python 3.12+)
* **Database Layer**: PostgreSQL database managed via SQLAlchemy ORM (v2.0+) and connection pools.
* **Frontend UI**: Responsive HTML5, Vanilla JavaScript, and custom CSS3 styles. Adopts a modern corporate green-and-white theme (`#2E8B57` SeaGreen).
* **Document Engine**: ReportLab library for PDF invoice generation.
* **Integrations**: Brevo API for transactional email receipts, Textbelt API (mock structure) for SMS receipts, and simulated WhatsApp receipt console logging for local development.

### Architecture & Folder Structure
The project is built using a clean separation of concerns:
```
d:\Startup\smart-retail
├── app/
│   ├── api/             # REST API endpoint routers
│   ├── database/        # SessionLocal configuration and DB engines
│   ├── models/          # SQLAlchemy Database model classes
│   ├── schemas/         # Pydantic validation schemas
│   ├── services/        # Core business logic handlers and aggregations
│   ├── static/          # Shared CSS stylesheets, JS scripts, and invoice PDFs
│   └── templates/       # HTML template views (Jinja2)
├── tests/               # Automated unit tests suites
├── requirements.txt     # Python dependency configuration
└── README.md            # System overview and deployment handbook
```

---

## 2. Modules

### A. System Dashboard
* **Purpose**: General connection health hub and landing page for developers/managers.
* **Working**: Runs client-side AJAX calls to the health API to confirm backend and database accessibility. Displays indicators and quick navigation links.
* **Files involved**: [index.html](file:///d:/Startup/smart-retail/app/templates/index.html), [app.js](file:///d:/Startup/smart-retail/app/static/js/app.js)
* **Routes**: `GET /dashboard`
* **Database tables used**: None

### B. Inventory Dashboard
* **Purpose**: Read-only listing dashboard for the store owner to check stock warnings, low counts, and group states.
* **Working**: Displays quick-action button filters (Low Stock, Expiring, Out of Stock) and binds an AJAX query engine to reload table lists dynamically.
* **Files involved**: [inventory.html](file:///d:/Startup/smart-retail/app/templates/inventory.html), [inventory.py (service)](file:///d:/Startup/smart-retail/app/services/inventory.py)
* **Routes**: `GET /inventory-dashboard`, `GET /inventory/filter`
* **Database tables used**: `products`, `inventory_mappings`

### C. Inventory Analytics Dashboard
* **Purpose**: Visual management graphs displaying catalog valuations, category distribution shares, and movement rates.
* **Working**: Groups products by categories and tracks dynamic movement states. Renders distribution charts via Chart.js.
* **Files involved**: [inventory_analytics.html](file:///d:/Startup/smart-retail/app/templates/inventory_analytics.html), [analytics.py (service)](file:///d:/Startup/smart-retail/app/services/analytics.py)
* **Routes**: `GET /inventory-analytics`
* **Database tables used**: `products`, `inventory_mappings`, `shelves`, `bill_items`

### D. Product Management
* **Purpose**: The catalog configuration dashboard to create, edit, delete, import, or adjust items.
* **Working**: Supports manual inserts with shelf recommendation scores and automatic shelf/warehouse stock splits. Features bulk CSV/XLSX uploads, bulk stock updates, and logs manual inventory adjustments.
* **Files involved**: [products_management.html](file:///d:/Startup/smart-retail/app/templates/products_management.html), [products_management.py (service)](file:///d:/Startup/smart-retail/app/services/product_management.py), [products_management.py (router)](file:///d:/Startup/smart-retail/app/api/products_management.py)
* **Routes**: `GET /products-management`, plus sub-routes under `/api/products-management/`
* **Database tables used**: `products`, `inventory_mappings`, `shelves`, `adjustment_logs`

### E. Cashier POS Billing
* **Purpose**: Checkout cart compiler for cashier desks.
* **Working**: Scans barcodes, manages cashier shopping carts, checks real-time quantities, and processes payments (Cash, UPI, Card, Split). Emits generated invoices, customer loyalty points, and prints WhatsApp receipts.
* **Files involved**: [billing.html](file:///d:/Startup/smart-retail/app/templates/billing.html), [billing.js](file:///d:/Startup/smart-retail/app/static/js/billing.js), [billing.py (service)](file:///d:/Startup/smart-retail/app/services/billing.py), [billing.py (router)](file:///d:/Startup/smart-retail/app/api/billing.py)
* **Routes**: `GET /billing`, plus sub-routes under `/api/billing/`
* **Database tables used**: `products`, `inventory_mappings`, `bills`, `bill_items`, `customers`, `invoices`

### F. Shelf Management
* **Purpose**: Shelf and warehouse stock coordinator.
* **Working**: Lists aisle allocations and current quantities. When items drop below minimum bounds, the refill action transfers warehouse units to the shelf.
* **Files involved**: [shelf_management.html](file:///d:/Startup/smart-retail/app/templates/shelf_management.html), [shelf.py (service)](file:///d:/Startup/smart-retail/app/services/shelf.py), [shelf.py (router)](file:///d:/Startup/smart-retail/app/api/shelf.py)
* **Routes**: `GET /shelf-management`, plus `/api/shelf` sub-routes
* **Database tables used**: `products`, `inventory_mappings`, `shelves`, `refill_logs`

---

## 3. Dashboard (/dashboard)
Renders a dashboard highlighting system health diagnostics:
* **Backend Connection Status**: Resolves whether the FastAPI application is reachable.
* **Database Connection Status**: Runs a test database query `SELECT 1` to verify PostgreSQL responsiveness.
* **Detail Grid**: Renders real-time latency diagnostics.
* **Quick Navigation Grid**: Direct navigation cards targeting the Product Manager, Cashier POS, Inventory Dashboard, Analytics Dashboard, and Shelf Replenishment pages.
* **Purge Button**: A "Reset Transaction History" button. Prompts with a confirmation modal, then deletes all transactional records (bills, items, invoices, PDF files) and resets customer loyalty point totals to 0.

---

## 4. Inventory Dashboard (/inventory-dashboard)
Displays real-time KPIs and tables for viewing inventory levels:
* **KPI Summaries**: Counts total unique products, total stock quantity, low-stock items, out-of-stock items, shelf refill warnings, and empty warehouse counts.
* **Quick Filter Action Buttons**: Binds AJAX queries to filter the product list dynamically:
  1. *All Products*: Shows all items.
  2. *Low Stock*: Items where total quantity <= reorder_level.
  3. *Out of Stock*: Items with quantity = 0.
  4. *Overstocked*: Items with quantity > reorder_level * 5.
  5. *Fast Moving*: Displays dynamic fast-moving items (top 20% of sold products).
  6. *Slow Moving*: Displays slow-moving items (bottom 20% of sold products).
  7. *Expiring Soon*: Items expiring within 30 days.
  8. *Warehouse Empty*: Items where warehouse_quantity = 0.
  9. *Shelf Refill Needed*: Items where shelf quantity <= minimum shelf warning.
* **Tabular Details**: Lists item names, categories, aisle locations, current stock quantities, selling prices, and health tags.

---

## 5. Product Management (/products-management)
A management workspace for catalog edits:
* **Manual Product Entry**: Opens a modal form to record product attributes.
* **Automatic Shelf Recommendation**: Selecting a category queries all shelves matching that category zone, sorted by available capacity (`100 - sum(current_shelf_quantity)`).
* **Automatic Stock Split**: Entering the total quantity and max shelf capacity automatically splits allocation (e.g. Total 120 with capacity 20 assigns 20 to shelf and 100 to the warehouse).
* **Excel & CSV Bulk Import**:
  1. *Upload*: Uploads a `.csv` or `.xlsx` file.
  2. *Validate*: Checks for duplicate barcodes (in DB or file), negative prices, and missing names/categories.
  3. *Preview*: Segregates records into Valid, Duplicate, and Invalid rows.
  4. *Commit*: Imports valid rows. Missing shelf mappings are automatically resolved to category-matching shelves with the highest remaining capacity.
* **Bulk Stock Update**: Corrects quantities via CSV upload or text entry (Format: `Barcode, NewQuantity, Reason`).
* **Inventory Adjustment**: Purges lost, damaged, expired, or stolen units, generating logs in `adjustment_logs`.

---

## 6. Billing Module (/billing)
A Cashier Checkout interface:
* **Barcode Input**: Scans barcodes and dynamically adds products to the checkout list.
* **Cart Summary**: Lists items, quantities, selling prices, and subtotals.
* **Quantity Controls**: Increases, decreases, or removes items with real-time stock checks.
* **Payment Methods**:
  * *Cash*: Automatically calculates **Change to Return** or shows **Remaining Amount** if the cash received is insufficient.
  * *UPI / Card*: Records the single transaction mode amount.
  * *Split Payment*: Supports split payments (Cash + UPI + Card), tracking the remaining amount dynamically.
* **Loyalty Lookup**: Entering a phone number retrieves customer points and applies automatic rewards.
* **Checkout Invoice Generation**: Creates transaction records in the database, decrements inventory stock, updates customer points, generates a programmatic PDF invoice via ReportLab, and writes the file locally to `app/static/invoices/`.

---

## 7. Loyalty System
* **Customer Creation**: When a customer's phone number is entered during checkout, the system retrieves their profile or creates a new customer record.
* **Loyalty Points Calculation**: Customers earn **1 point for every Rs. 10 spent** (`math.floor(total_amount / 10)`).
* **Points Balance Update**: Accrued points are added to the customer's database record.
* **Coupon Logic**: *Not Implemented* (No coupon codes or redemption mechanics exist in the codebase).

---

## 8. Shelf Management (/shelf-management)
Coordinates shelf replenishments:
* **Planogram Mappings**: Displays product mappings containing floor numbers, aisles, racks, shelf numbers, shelf capacities, current quantities, and warehouse quantities.
* **Status Badges**: Shows `Healthy` or `Refill Needed` (if current quantity <= minimum warning limit).
* **Refill Operation**: Triggers refilling. Calculates the replenishment delta (`shelf_capacity - current_shelf_quantity`), deducts it from the warehouse stock, adds it to the shelf, and writes audit details to `refill_logs`.

---

## 9. WhatsApp Module
* **Invoices Generation**: Generates PDF receipts dynamically on checkout and saves them under `app/static/invoices/`.
* **Professional Mart Receipt Message**: Construct a formatted WhatsApp invoice message containing:
  * Mart name and customer greeting.
  * Invoice serial number and date/time.
  * Payment method detail breakdown (Cash, UPI, Card, or Split).
  * Quantity of items purchased, grand total, and loyalty points earned.
  * A dedicated retrieval link: `http://127.0.0.1:8000/invoice/{invoice_number}`
* **Mock Development Mode**: Prints the WhatsApp receipt directly to the terminal stdout and logs `whatsapp_status = MOCK_SENT`.

---

## 10. Database Schema

### Table: `products`
* **Purpose**: Central catalog database.
* **Columns**:
  * `id` (INTEGER, Primary Key)
  * `barcode` (VARCHAR, Unique Index)
  * `name` (VARCHAR, Not Null)
  * `category` (VARCHAR, Not Null)
  * `price` (NUMERIC(10,2)) - Selling Price
  * `quantity` (INTEGER) - Total Quantity (Shelf + Warehouse)
  * `reorder_level` (INTEGER)
  * `movement_class` (VARCHAR(50))
  * `expiry_date` (DATE)
  * `cost_price` (NUMERIC(10,2))
  * `max_stock_capacity` (INTEGER)
  * `brand` (VARCHAR(100))
  * `sub_category` (VARCHAR(100))
  * `description` (TEXT)
  * `unit` (VARCHAR(50))
  * `pack_size` (VARCHAR(100))
  * `supplier` (VARCHAR(100))
  * `mrp` (NUMERIC(10,2))
  * `gst` (NUMERIC(10,2))
  * `hsn_code` (VARCHAR(50))
  * `expiry_required` (BOOLEAN)
  * `created_at` (TIMESTAMP)

### Table: `customers`
* **Purpose**: Loyalty profiles data.
* **Columns**:
  * `id` (INTEGER, Primary Key)
  * `name` (VARCHAR(100))
  * `phone` (VARCHAR(15), Unique Index)
  * `email` (VARCHAR(255))
  * `total_points` (INTEGER)
  * `created_at` (TIMESTAMP)

### Table: `bills`
* **Purpose**: General checkout sales records.
* **Columns**:
  * `id` (INTEGER, Primary Key)
  * `total_amount` (NUMERIC(10,2))
  * `customer_id` (INTEGER, Foreign Key -> `customers.id`)
  * `customer_name` (VARCHAR(100))
  * `customer_phone` (VARCHAR(15))
  * `customer_email` (VARCHAR(255))
  * `payment_method` (VARCHAR(50))
  * `cash_received` (NUMERIC(10,2))
  * `change_returned` (NUMERIC(10,2))
  * `split_cash` (NUMERIC(10,2))
  * `split_upi` (NUMERIC(10,2))
  * `split_card` (NUMERIC(10,2))
  * `created_at` (TIMESTAMP)

### Table: `bill_items`
* **Purpose**: Sales transaction line items.
* **Columns**:
  * `id` (INTEGER, Primary Key)
  * `bill_id` (INTEGER, Foreign Key -> `bills.id`)
  * `product_id` (INTEGER, Foreign Key -> `products.id`)
  * `quantity` (INTEGER)
  * `unit_price` (NUMERIC(10,2))
  * `subtotal` (NUMERIC(10,2))

### Table: `shelves`
* **Purpose**: Planogram shelf records.
* **Columns**:
  * `id` (INTEGER, Primary Key)
  * `floor_number` (INTEGER)
  * `aisle` (VARCHAR(100))
  * `rack` (VARCHAR(50))
  * `shelf_number` (VARCHAR(100), Unique Index)
  * `category` (VARCHAR(100))

### Table: `inventory_mappings`
* **Purpose**: Mappings linking products to shelves.
* **Columns**:
  * `id` (INTEGER, Primary Key)
  * `product_id` (INTEGER, Foreign Key -> `products.id` ON DELETE CASCADE, Unique)
  * `shelf_id` (INTEGER, Foreign Key -> `shelves.id` ON DELETE CASCADE)
  * `shelf_capacity` (INTEGER)
  * `current_shelf_quantity` (INTEGER)
  * `warehouse_quantity` (INTEGER)
  * `minimum_shelf_quantity` (INTEGER)
  * `last_refilled_at` (TIMESTAMP)

### Table: `refill_logs`
* **Purpose**: Audit log of warehouse-to-shelf refilling operations.
* **Columns**:
  * `id` (INTEGER, Primary Key)
  * `product_id` (INTEGER, Foreign Key -> `products.id` ON DELETE CASCADE)
  * `quantity_moved` (INTEGER)
  * `before_quantity` (INTEGER) - Shelf quantity before refill
  * `after_quantity` (INTEGER) - Shelf quantity after refill
  * `warehouse_before` (INTEGER) - Warehouse quantity before refill
  * `warehouse_after` (INTEGER) - Warehouse quantity after refill
  * `refilled_at` (TIMESTAMP)

### Table: `invoices`
* **Purpose**: PDF invoices metadata and receipt logs.
* **Columns**:
  * `id` (INTEGER, Primary Key)
  * `invoice_number` (VARCHAR(50), Unique Index)
  * `invoice_url` (VARCHAR(255))
  * `pdf_path` (VARCHAR(555))
  * `customer_name` (VARCHAR(100))
  * `customer_phone` (VARCHAR(15))
  * `total_amount` (NUMERIC(10,2))
  * `whatsapp_status` (VARCHAR(50))
  * `created_at` (TIMESTAMP)

### Table: `adjustment_logs`
* **Purpose**: Audit records for manual inventory stock adjustments.
* **Columns**:
  * `id` (INTEGER, Primary Key)
  * `product_id` (INTEGER, Foreign Key -> `products.id` ON DELETE CASCADE)
  * `barcode` (VARCHAR(50))
  * `quantity_changed` (INTEGER)
  * `before_quantity` (INTEGER)
  * `after_quantity` (INTEGER)
  * `reason` (VARCHAR(100))
  * `adjusted_at` (TIMESTAMP)

---

## 11. API Documentation

### A. Health & Diagnostics
* `GET /api/health`: Tests backend API responsiveness and runs a `SELECT 1` database query to verify connection pool states.

### B. Catalog Products
* `POST /products`: Creates a new product record.
* `GET /products`: Retrieves all catalog products.
* `GET /products/search?q=...`: Case-insensitive search on name, barcode, or category.
* `GET /products/low-stock`: Returns items where quantity <= reorder_level.
* `GET /products/{id}`: Returns product details by database ID.
* `PUT /products/{id}`: Updates product details.
* `DELETE /products/{id}`: Deletes a product.

### C. Cashier Checkout Cart
* `POST /api/billing/cart/add`: Appends an item to the cart (checks stock availability).
* `POST /api/billing/cart/remove`: Removes an item from the cart.
* `GET /api/billing/cart`: Returns the active shopping cart items.
* `POST /api/billing/generate`: Processes checkout payment, decrements stocks, awards loyalty points, generates the PDF invoice, and prints a mock WhatsApp message.
* `GET /api/billing/history`: Returns historical sales records.

### D. Shelf planogram
* `GET /shelf`: Returns shelf mappings with optional query filters (floor, category, search, low stock warning).
* `GET /shelf/low`: Returns shelves where current shelf quantity <= minimum warning.
* `POST /shelf/refill/{product_id}`: Refills shelf quantity from warehouse stock.
* `GET /refill/history`: Returns shelf replenishment histories.

### E. Products Manager Admin Module
* `GET /api/products-management/recommend-shelves?category=...`: Returns recommended shelves for category, sorted by remaining capacity.
* `GET /api/products-management/template`: Downloads the CSV template for imports.
* `POST /api/products-management/manual-add`: Saves a manual product and assigns shelf mappings.
* `POST /api/products-management/import/validate`: Validates CSV/XLSX records, reporting Valid, Duplicate, and Invalid rows.
* `POST /api/products-management/import/commit`: Commits valid records.
* `POST /api/products-management/bulk-update`: Updates product quantities in bulk and records audit histories.
* `POST /api/products-management/adjust`: Adjusts stock levels and records details to `adjustment_logs`.
* `GET /api/products-management/profile/{product_id}`: Returns product profile info, pricing, warehouse splits, refill history, sales history, and adjustments.
* `PUT /api/products-management/edit/{id}`: Updates product and inventory mapping allocations.
* `DELETE /api/products-management/delete/{id}`: Deletes product and mapping records.
* `POST /admin/reset-transactions`: Deletes all bills, bill items, invoices, PDF receipts, and resets customer loyalty totals to 0.

---

## 12. UI Pages

### A. General Landing Dashboard
* **Route**: `/dashboard`
* **Purpose**: Health connection dashboard and navigation hub.
* **Components**: Connection dots, status text panels, latency diagnostics cards, navigation links grid, and the transactional reset button.

### B. Products Catalog Manager
* **Route**: `/products-management`
* **Purpose**: Core catalog management dashboard.
* **Components**: Toolbar buttons (Add, Import, Update, Adjust, Template download), search inputs, dropdown filters, catalog table, manual add form modal, import validation wizard modal, bulk text update modal, single adjustment modal, and profile viewer modal.

### C. Cashier Checkout Billing
* **Route**: `/billing`
* **Purpose**: POS checkout interface.
* **Components**: Barcode search scanner, customer info cards, checkout cart items table, payment selectors, receipt details modal with a click-to-copy WhatsApp link.

### D. Inventory Dashboard
* **Route**: `/inventory-dashboard`
* **Purpose**: Read-only listing dashboard for stock warning checks.
* **Components**: Counts KPI summaries, quick action filter tags (Low stock, expiring, overstock, etc.), and inventory listing table.

### E. Inventory Analytics Dashboard
* **Route**: `/inventory-analytics`
* **Purpose**: Analytics and performance graphs dashboard.
* **Components**: Financial valuation cards, warehouse/shelf utilization counts, movement category charts (distribution, shares, value), and listing tables for fast, slow, expiring, and warehouse empty lists.

### F. Shelf Replenishment Dashboard
* **Route**: `/shelf-management`
* **Purpose**: planogram replenishment coordinator.
* **Components**: Shelf listings table, search query filters, refill actions, and refilling history modal.

### G. Invoice View Retrieval Page
* **Route**: `/invoice/{invoice_number}`
* **Purpose**: Public printable receipt view page.
* **Components**: Invoice headers, date/time blocks, customer details, purchased items details table, subtotal/GST/grand totals, loyalty points earned, a print window button, and a PDF downloader link.

---

## 13. User Workflow

```
[Owner/Manager]
       │
       ▼
 1. Add Product (Manual / Bulk Import) ──► Recommends Category Zone Shelf
       │                                  ──► Splits Stock: Shelf vs Warehouse
       ▼
 2. Cashier POS billing (Checkout)    ──► Reads barcode scan
       │                                  ──► Checks inventory quantities
       │                                  ──► Automatically awards loyalty points
       │                                  ──► Calculates Cash change / Split payment share
       ▼
 3. Invoice Generation                 ──► Compiles programmatic ReportLab PDF
       │                                  ──► Saves PDF locally to static folder
       │                                  ──► Prints receipt message to terminal console
       ▼
 4. Shelf Replenishment                ──► Inventory Dashboard shows warnings
                                          ──► Replenish triggers Warehouse -> Shelf moves
```

---

## 14. Validations
* **Duplicate Barcode Check**: Rejects duplicate barcode entries (on manual add, bulk update, and import file validation steps).
* **Price Validations**: Prevents negative values for selling price, cost price, and MRP.
* **Quantity Validations**: Prevents negative values for stock levels and reorder limits.
* **Missing Fields**: Enforces name, category, and shelf selections.
* **Billing Stock Check**: Prevents checkouts exceeding current inventory levels.
* **Cash received**: Prevents checkout completion if the cash received is less than the bill total.

---

## 15. External Integrations
* **Brevo API**: Transactional SMTP email client sending receipt templates to customers.
* **WhatsApp**: Mock development environment formatting professional receipt messages and printing them to terminal stdout.
* **Textbelt API**: Mock API framework for SMS receipts.
* **PostgreSQL Database**: Persistent storage engine for tables, relationships, and queries.
* **FastAPI Web Framework**: REST API routers, dependency injectors, static mounts, and Jinja2 templates.

---

## 16. Feature Checklist
* [x] System Health Monitoring Dashboard
* [x] Products Catalog Manager (Manual Add, Edits, Deletions)
* [x] Automatic Shelf Planogram Suggestion (Sorted by remaining capacity)
* [x] Automatic Stock Distribution Split (Shelf vs Warehouse)
* [x] Bulk Imports Wizard (CSV & XLSX files validation, preview, and commit)
* [x] Bulk Stock Updates (Pasted text lines or CSV uploads)
* [x] Inventory Adjustments Audits (Damaged, Expired, Lost, Stolen)
* [x] Supermarket POS Cashier Checkout Cart
* [x] Multi-Payment Methods (Cash, Card, UPI, Split Payments)
* [x] Cash Change Return Calculator
* [x] Dynamic Checkout Sales Velocity Classification (Fast / Slow Moving calculation)
* [x] Customer Loyalty System (1 point per Rs. 10 spent)
* [x] Dynamic Shelf Replenishment (Warehouse-to-shelf refill logs)
* [x] Programmatic PDF Invoice generation (ReportLab engine)
* [x] Local PDF Invoice Static Storage
* [x] Printable Invoice Retrieval Screen
* [x] Format Mart Receipt WhatsApp logs (printed to developer console)
* [x] Admin Transaction Purge Utility (Reset transactional data)

---

## 17. Potential Future Enhancements
Based on the current architecture, these extensions can be implemented:
1. **SMS Service Adapter**: Enable SMS delivery by swapping the mock TextBelt adapter in `SMSService` with a provider like Twilio.
2. **Invoice Cloud Storage**: Swap the local static path adapter in `InvoiceStorageService` with a cloud storage provider like AWS S3 or Cloudinary.
3. **Real WhatsApp API Dispatcher**: Integrate a provider like Twilio WhatsApp API to dispatch messages to customers' phones instead of printing them mock-mode to the terminal console.
4. **Loyalty Coupon Logic**: Add validation schemas to calculate coupon discounts during checkouts.
