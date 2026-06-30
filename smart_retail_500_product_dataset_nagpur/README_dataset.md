# Smart Retail 500 Product Synthetic Dataset

This dataset simulates a realistic 2–3 floor small mart/supermarket in Nagpur, Maharashtra.

## Files
- products_500_planogram.csv: Main 500-product product master with floor, aisle, rack, shelf, stock, shelf capacity, warehouse stock, prices, GST, suppliers, movement class.
- shelves_planogram.csv: Shelf-level planogram structure.
- product_replacements.csv: Alternative products for out-of-stock recommendations.
- customers_synthetic.csv: Synthetic customer list with WhatsApp numbers and loyalty points.
- bills_synthetic.csv: Synthetic bill headers for testing reports and loyalty.
- bill_items_synthetic.csv: Synthetic bill line items for analytics and market basket analysis.
- market_basket_pairs.csv: Frequently-bought-together pairs for product placement recommendations.
- seed_products_500_current_schema.sql: Direct seed file for your current products table.
- seed_extended_planogram_tables.sql: Extended shelf and planogram tables.

## Recommended import order
1. Run seed_products_500_current_schema.sql first to test your current inventory/billing system.
2. Later run seed_extended_planogram_tables.sql when you implement shelf management.
3. Use bills_synthetic.csv and bill_items_synthetic.csv for analytics and AI testing.

## Planogram logic
Ground Floor: fresh, dairy, bakery, beverages, checkout impulse.
First Floor: biscuits, snacks, staples, cooking essentials, tea/coffee, instant food.
Second Floor: personal care, skin care, oral care, cleaning, household, stationery.

Products are not random. They are placed by category adjacency and buying behavior.
