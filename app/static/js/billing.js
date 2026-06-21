document.addEventListener('DOMContentLoaded', () => {
    // UI Elements
    const inputCustomerName = document.getElementById('input-customer-name');
    const inputCustomerPhone = document.getElementById('input-customer-phone');
    const topbarSearchInput = document.getElementById('topbar-search-input');
    const searchProductInput = document.getElementById('search-product-input');
    const inputBarcode = document.getElementById('input-barcode');
    const btnAddToCart = document.getElementById('btn-add-to-cart');
    const productsListWrapper = document.getElementById('products-list-wrapper');
    const cartBody = document.getElementById('cart-body');
    const summarySubtotal = document.getElementById('summary-subtotal');
    const summaryGst = document.getElementById('summary-gst');
    const summaryDiscount = document.getElementById('summary-discount');
    const summaryTotalAmount = document.getElementById('summary-total-amount');
    const btnGenerateBill = document.getElementById('btn-generate-bill');
    const btnHoldOrder = document.getElementById('btn-hold-order');
    const btnClearCart = document.getElementById('btn-clear-cart');
    const alertBox = document.getElementById('alert-box');
    
    // Modal Elements
    const invoiceModal = document.getElementById('invoice-modal');
    const invoiceNumber = document.getElementById('invoice-number');
    const invoiceAmountDisplay = document.getElementById('invoice-amount-display');
    const whatsappSendLink = document.getElementById('whatsapp-send-link');
    const btnCloseModal = document.getElementById('btn-close-modal');

    // State
    let allProducts = [];
    let currentCart = [];
    let grandTotal = 0.00;
    let selectedPaymentMode = 'Cash';
    let isProcessing = false;

    // Helper: Show Alert
    function showAlert(message) {
        alertBox.textContent = message;
        alertBox.classList.remove('hide');
        setTimeout(() => alertBox.classList.add('hide'), 5000);
    }

    // Live Date and Time
    function updateDateTime() {
        const liveDateEl = document.getElementById('live-date');
        const liveTimeEl = document.getElementById('live-time');
        const now = new Date();
        if (liveDateEl) liveDateEl.textContent = now.toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' });
        if (liveTimeEl) liveTimeEl.textContent = now.toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit', hour12: true });
    }
    setInterval(updateDateTime, 1000);
    updateDateTime();

    // 1. Fetch Products
    async function fetchProducts() {
        try {
            const response = await fetch('/products');
            if (response.ok) {
                allProducts = await response.json();
                filterProducts();
            }
        } catch (error) {
            console.error('Error fetching products:', error);
            showAlert('Network error fetching products.');
        }
    }

    // 2. Filter & Render Products
    function filterProducts() {
        if (!productsListWrapper) return;
        const searchQuery = (searchProductInput ? searchProductInput.value : '').toLowerCase().trim();
        const topbarQuery = (topbarSearchInput ? topbarSearchInput.value : '').toLowerCase().trim();
        
        const filtered = allProducts.filter(p => {
            const nameMatch = p.name.toLowerCase().includes(searchQuery) && p.name.toLowerCase().includes(topbarQuery);
            const barcodeMatch = p.barcode.toLowerCase().includes(searchQuery) && p.barcode.toLowerCase().includes(topbarQuery);
            return nameMatch || barcodeMatch;
        });

        productsListWrapper.innerHTML = '';
        if (filtered.length === 0) {
            productsListWrapper.innerHTML = '<div class="empty-state">No products found.</div>';
            return;
        }

        filtered.forEach(prod => {
            const isOutOfStock = prod.quantity <= 0;
            const div = document.createElement('div');
            div.className = 'product-card';
            div.innerHTML = `
                <div class="prod-info">
                    <span class="prod-name">${prod.name}</span>
                    <span class="prod-cat">${prod.category} (${prod.quantity} left)</span>
                    <span class="prod-price">₹${parseFloat(prod.price).toFixed(2)}</span>
                </div>
                <button class="btn-card-add" data-barcode="${prod.barcode}" ${isOutOfStock ? 'disabled style="opacity:0.5;cursor:not-allowed;"' : ''}>Add</button>
            `;
            productsListWrapper.appendChild(div);
        });

        // Bind Add Buttons
        const addBtns = productsListWrapper.querySelectorAll('.btn-card-add');
        addBtns.forEach(btn => {
            btn.addEventListener('click', () => {
                addToCartByBarcode(btn.getAttribute('data-barcode'), 1);
            });
        });
    }

    // 3. Fetch Cart
    async function fetchCart() {
        try {
            const response = await fetch('/billing/cart');
            if (response.ok) {
                currentCart = await response.json();
                renderCart();
            }
        } catch (error) {
            console.error('Error fetching cart:', error);
        }
    }

    // 4. Render Cart
    function renderCart() {
        if (!cartBody) return;
        cartBody.innerHTML = '';
        grandTotal = 0.00;

        if (currentCart.length === 0) {
            cartBody.innerHTML = `<tr class="empty-row"><td colspan="5" class="empty-state">Cart is currently empty.</td></tr>`;
            updateTotals();
            return;
        }

        currentCart.forEach(item => {
            const subtotal = parseFloat(item.subtotal);
            grandTotal += subtotal;
            const price = parseFloat(item.unit_price).toFixed(2);

            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>
                    <div class="cart-prod-name">${item.product_name}</div>
                    <div class="cart-prod-barcode">${item.barcode}</div>
                </td>
                <td class="text-center">
                    <div class="qty-controls">
                        <button class="qty-btn btn-qty-minus" data-barcode="${item.barcode}" data-qty="${item.quantity}">-</button>
                        <input type="text" class="qty-input" value="${item.quantity}" readonly>
                        <button class="qty-btn btn-qty-plus" data-barcode="${item.barcode}">+</button>
                    </div>
                </td>
                <td class="text-right">₹${price}</td>
                <td class="text-right" style="font-weight: 600;">₹${subtotal.toFixed(2)}</td>
                <td class="text-center">
                    <button class="btn-remove" data-barcode="${item.barcode}">×</button>
                </td>
            `;
            cartBody.appendChild(tr);
        });

        updateTotals();

        // Bind Events
        cartBody.querySelectorAll('.btn-qty-minus').forEach(btn => {
            btn.addEventListener('click', () => decrementCartItem(btn.getAttribute('data-barcode'), parseInt(btn.getAttribute('data-qty'))));
        });
        cartBody.querySelectorAll('.btn-qty-plus').forEach(btn => {
            btn.addEventListener('click', () => addToCartByBarcode(btn.getAttribute('data-barcode'), 1));
        });
        cartBody.querySelectorAll('.btn-remove').forEach(btn => {
            btn.addEventListener('click', () => removeFromCart(btn.getAttribute('data-barcode')));
        });
    }

    // 5. Update Totals
    function updateTotals() {
        const grandTotalStr = `₹${grandTotal.toFixed(2)}`;
        if (summarySubtotal) summarySubtotal.textContent = grandTotalStr;
        if (summaryGst) summaryGst.textContent = '₹0.00';
        if (summaryDiscount) summaryDiscount.textContent = '₹0.00';
        if (summaryTotalAmount) summaryTotalAmount.textContent = grandTotalStr;
    }

    // 6. Add Item to Cart
    async function addToCartByBarcode(barcode, quantity) {
        if (isProcessing) return;
        if (!barcode) { showAlert('Please enter a barcode.'); return; }

        isProcessing = true;
        try {
            const response = await fetch('/billing/cart/add', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ barcode, quantity })
            });
            const data = await response.json();
            if (response.ok) {
                if (inputBarcode) inputBarcode.value = '';
                await fetchCart();
                await fetchProducts();
            } else {
                showAlert(data.detail || 'Failed to add product.');
            }
        } catch (error) {
            showAlert('Network error.');
        } finally {
            isProcessing = false;
        }
    }

    // 7. Decrement Item
    async function decrementCartItem(barcode, currentQty) {
        if (isProcessing) return;
        isProcessing = true;
        try {
            const removeResp = await fetch('/billing/cart/remove', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ barcode })
            });
            if (removeResp.ok && currentQty > 1) {
                await fetch('/billing/cart/add', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ barcode, quantity: currentQty - 1 })
                });
            }
            await fetchCart();
            await fetchProducts();
        } finally {
            isProcessing = false;
        }
    }

    // 8. Remove Item
    async function removeFromCart(barcode) {
        if (isProcessing) return;
        isProcessing = true;
        try {
            await fetch('/billing/cart/remove', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ barcode })
            });
            await fetchCart();
            await fetchProducts();
        } finally {
            isProcessing = false;
        }
    }

    // 9. Clear Cart
    async function clearCart() {
        if (currentCart.length === 0) return;
        if (isProcessing) return;
        isProcessing = true;
        try {
            for (const item of currentCart) {
                await fetch('/billing/cart/remove', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ barcode: item.barcode })
                });
            }
            await fetchCart();
            await fetchProducts();
        } finally {
            isProcessing = false;
        }
    }

    if (btnClearCart) btnClearCart.addEventListener('click', clearCart);
    if (btnHoldOrder) btnHoldOrder.addEventListener('click', clearCart);

    // 10. Generate Bill
    if (btnGenerateBill) {
        btnGenerateBill.addEventListener('click', async () => {
            if (currentCart.length === 0) {
                showAlert('Cart is empty.');
                return;
            }

            const customerName = inputCustomerName ? inputCustomerName.value.trim() : '';
            const customerPhone = inputCustomerPhone ? inputCustomerPhone.value.trim() : '';

            if (!customerName || !customerPhone) {
                showAlert('Customer Name and WhatsApp Number are mandatory.');
                return;
            }

            if (!/^\d{10}$/.test(customerPhone)) {
                showAlert('WhatsApp Number must be exactly 10 digits.');
                return;
            }

            if (isProcessing) return;
            isProcessing = true;

            try {
                const response = await fetch('/billing/generate', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        customer_name: customerName,
                        customer_phone: customerPhone,
                        customer_email: null // As per requirement, no email.
                    })
                });

                const data = await response.json();
                if (response.ok) {
                    showInvoiceModal(data, customerPhone);
                } else {
                    showAlert(data.detail || 'Failed to generate bill.');
                }
            } catch (error) {
                showAlert('Network error generating bill.');
            } finally {
                isProcessing = false;
            }
        });
    }

    // 11. Show Modal & Setup WhatsApp Link
    function showInvoiceModal(bill, phone) {
        if (!invoiceModal) return;

        if (invoiceNumber) invoiceNumber.textContent = `Invoice Number: SR-${bill.id.toString().padStart(6, '0')}`;
        if (invoiceAmountDisplay) invoiceAmountDisplay.textContent = `Amount: ₹${parseFloat(bill.total_amount).toFixed(2)}`;

        // Build WhatsApp Link
        if (whatsappSendLink) {
            const invoiceLink = window.location.origin + "/history";
            const text = `Thank you for shopping at Smart Retail.\n\nInvoice Number: SR-${bill.id.toString().padStart(6, '0')}\nAmount: ₹${parseFloat(bill.total_amount).toFixed(2)}\n\nView Invoice:\n${invoiceLink}`;
            const encodedText = encodeURIComponent(text);
            whatsappSendLink.href = `https://wa.me/91${phone}?text=${encodedText}`;
        }

        invoiceModal.classList.remove('hide');
    }

    // 12. Close Modal
    if (btnCloseModal) {
        btnCloseModal.addEventListener('click', () => {
            if (invoiceModal) invoiceModal.classList.add('hide');
            if (inputCustomerName) inputCustomerName.value = '';
            if (inputCustomerPhone) inputCustomerPhone.value = '';
            fetchCart();
            fetchProducts();
        });
    }

    // Event Listeners for inputs
    if (btnAddToCart) {
        btnAddToCart.addEventListener('click', () => {
            if (inputBarcode.value) addToCartByBarcode(inputBarcode.value.trim(), 1);
        });
    }

    if (inputBarcode) {
        inputBarcode.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && inputBarcode.value) {
                addToCartByBarcode(inputBarcode.value.trim(), 1);
            }
        });
    }

    if (topbarSearchInput) {
        topbarSearchInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                const query = topbarSearchInput.value.trim();
                const matched = allProducts.find(p => p.barcode === query);
                if (matched) {
                    addToCartByBarcode(matched.barcode, 1);
                    topbarSearchInput.value = '';
                }
            }
        });
        topbarSearchInput.addEventListener('input', filterProducts);
    }

    if (searchProductInput) searchProductInput.addEventListener('input', filterProducts);

    // Payment Mode Toggle
    const payBtns = document.querySelectorAll('.payment-mode-grid .pay-btn');
    payBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            payBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            selectedPaymentMode = btn.getAttribute('data-mode');
        });
    });

    // Init
    fetchProducts();
    fetchCart();
});
