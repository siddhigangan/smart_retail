# Smart Retail - Feature Matrix

The following table summarizes all implemented and not implemented features across modules:

| Module | Feature | Description | Status | Database Tables | API | UI Page |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **System Dashboard** | Connection Status | Checks FastAPI backend responsiveness. | Implemented | None | `GET /` | `/dashboard` |
| | Database status | Checks database health with `SELECT 1` query. | Implemented | None | `GET /api/health` | `/dashboard` |
| | Quick navigation | Grid cards to access specific system segments. | Implemented | None | None | `/dashboard` |
| | Reset Transaction History | Deletes bills, items, invoices, PDF receipts, and resets customer loyalty totals. | Implemented | `bills`, `bill_items`, `invoices`, `customers` | `POST /admin/reset-transactions` | `/dashboard` |
| **Inventory Dashboard** | Stock KPIs | Summary totals of stocks, warnings, empty locations, etc. | Implemented | `products`, `inventory_mappings` | None | `/inventory-dashboard` |
| | Filter buttons | Reloads listings by status warnings (Low stock, out of stock, Overstocked, Fast/Slow moving, Expiring, Shelf refill needed, warehouse empty). | Implemented | `products`, `inventory_mappings`, `bill_items` | `GET /inventory/filter` | `/inventory-dashboard` |
| | Product Table | Interactive lists showing aisles, quantities, status. | Implemented | `products`, `inventory_mappings` | `GET /inventory/filter` | `/inventory-dashboard` |
| **Inventory Analytics** | Analytics Cards | Total products, catalog valuation, utilizing indexes. | Implemented | `products`, `inventory_mappings` | None | `/inventory-analytics` |
| | Valuation Charts | Chart.js graphs displaying distributions and top lists. | Implemented | `products`, `inventory_mappings` | None | `/inventory-analytics` |
| | Focus Lists | Focus tables highlighting fast, slow, expiring, empty stocks. | Implemented | `products`, `inventory_mappings`, `bill_items` | None | `/inventory-analytics` |
| **Product Management** | Manual Product Entry | Forms to insert products with category suggestions and capacity stock splits. | Implemented | `products`, `inventory_mappings` | `POST /api/products-management/manual-add` | `/products-management` |
| | Bulk Import Wizard | Reads `.csv` or `.xlsx` files with duplicate checks, previews lists, and auto-maps shelves. | Implemented | `products`, `inventory_mappings`, `shelves` | `POST /api/products-management/import/validate`, `POST /api/products-management/import/commit` | `/products-management` |
| | Bulk Stock Update | Pasted texts or CSV file uploads to adjust quantities. | Implemented | `products`, `inventory_mappings` | `POST /api/products-management/bulk-update` | `/products-management` |
| | Inventory Adjustment | Purges damaged/lost items and registers audit log records. | Implemented | `products`, `inventory_mappings`, `adjustment_logs` | `POST /api/products-management/adjust` | `/products-management` |
| | Product Profile Details | Comprehensive lookup tabs for history, refills, adjustments, sales. | Implemented | `products`, `inventory_mappings`, `adjustment_logs`, `refill_logs`, `bill_items` | `GET /api/products-management/profile/{id}` | `/products-management` |
| | Product Edit/Delete | Modifies basic parameters or removes products and planograms. | Implemented | `products`, `inventory_mappings` | `PUT /api/products-management/edit/{id}`, `DELETE /api/products-management/delete/{id}` | `/products-management` |
| **POS Billing** | Scan Barcode | Input scanners adding items to cashier cart list. | Implemented | `products` | `POST /api/billing/cart/add` | `/billing` |
| | Cart Updates | Modifies checkout counts with stock limits checking. | Implemented | `products` | `POST /api/billing/cart/remove` | `/billing` |
| | Loyalty Lookup | Automatically loads customer profiles by contact. | Implemented | `customers` | `POST /api/billing/generate` | `/billing` |
| | Payment Modes | Cash (calculates return change), UPI, Card, and split combinations payments. | Implemented | `bills`, `bill_items` | `POST /api/billing/generate` | `/billing` |
| | Invoice Retrieval Page | Public-facing receipt retrieval page with browser printing triggers. | Implemented | `invoices` | None | `/invoice/{invoice_number}` |
| **Loyalty System** | Points Calculation | Automatically adds 1 point for every Rs. 10 spent. | Implemented | `customers`, `bills` | `POST /api/billing/generate` | `/billing` |
| | Points Lookup | Retrieves total points balances during billing checkouts. | Implemented | `customers` | None | `/billing` |
| | Coupon Codes | Redeemable voucher coupons or custom discount rates. | **Not Implemented** | None | None | None |
| **Shelf Replenishment** | Replenishment Table | Lists shelf allocations and refill indicators. | Implemented | `inventory_mappings`, `shelves` | `GET /shelf` | `/shelf-management` |
| | Refill Stock | Moves stock from warehouse backroom to active shelf. | Implemented | `inventory_mappings`, `refill_logs` | `POST /shelf/refill/{product_id}` | `/shelf-management` |
| | Refill History | Modal logs showing refill datetimes and counts. | Implemented | `refill_logs` | `GET /refill/history` | `/shelf-management` |
| **WhatsApp Module** | Receipts logs | Format and print professional receipts to terminal. | Implemented | `invoices` | `POST /api/billing/generate` | `/billing` |
| | Public Invoice URL | Retrieval URL links pointing to dedicated page. | Implemented | `invoices` | None | `/invoice/{invoice_number}` |
| | Direct SMS/WhatsApp | Automated messages dispatching directly to customer phone number. | **Not Implemented** (Simulated in local mock development mode) | None | None | None |
