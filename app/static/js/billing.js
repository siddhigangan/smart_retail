document.addEventListener('DOMContentLoaded', () => {
    // Left column elements
    const inputBarcode = document.getElementById('input-barcode');
    const btnAddToCart = document.getElementById('btn-add-to-cart');
    const searchProductInput = document.getElementById('search-product-input');
    const categoryFilterSelect = document.getElementById('category-filter-select');
    const productsListWrapper = document.getElementById('products-list-wrapper');
    const btnViewAllProducts = document.getElementById('btn-view-all-products');
    const alertBox = document.getElementById('alert-box');

    // Topbar search input
    const topbarSearchInput = document.getElementById('topbar-search-input');

    // Middle column (Cart) elements
    const cartCountTitle = document.getElementById('cart-count-title');
    const btnClearCartTop = document.getElementById('btn-clear-cart-top');
    const cartBody = document.getElementById('cart-body');
    const summarySubtotal = document.getElementById('summary-subtotal');
    const summaryDiscount = document.getElementById('summary-discount');
    const summaryGst = document.getElementById('summary-gst');
    const summaryTotalAmount = document.getElementById('summary-total-amount');

    // Right column elements
    const grandTotalAmount = document.getElementById('grand-total-amount');
    const inputTender = document.getElementById('input-tender');
    const changeReturnDisplay = document.getElementById('change-return-display');
    const tenderCalculatorCard = document.getElementById('tender-calculator-card');
    const btnGenerateBill = document.getElementById('btn-generate-bill');
    const btnHoldOrder = document.getElementById('btn-hold-order');
    const btnClearCartBottom = document.getElementById('btn-clear-cart-bottom');

    // Customer Info fields
    const inputCustomerName = document.getElementById('input-customer-name');
    const inputCustomerPhone = document.getElementById('input-customer-phone');
    const inputCustomerEmail = document.getElementById('input-customer-email');

    // Invoice modal elements
    const invoiceModal = document.getElementById('invoice-modal');
    const invoiceDate = document.getElementById('invoice-date');
    const invoiceNumber = document.getElementById('invoice-number');
    const invoiceCustomerName = document.getElementById('invoice-customer-name');
    const invoiceCustomerPhone = document.getElementById('invoice-customer-phone');
    const invoiceItemsBody = document.getElementById('invoice-items-body');
    const invoiceTotalAmount = document.getElementById('invoice-total-amount');
    const invoiceCashTendered = document.getElementById('invoice-cash-tendered');
    const invoiceChangeDue = document.getElementById('invoice-change-due');
    const btnCloseModal = document.getElementById('btn-close-modal');

    // Loyalty & notification elements
    const loyaltyBadge = document.getElementById('loyalty-badge');
    const loyaltyPointsText = document.getElementById('loyalty-points-text');
    const loyaltyTotalText = document.getElementById('loyalty-total-text');
    const notificationStatusRow = document.getElementById('notification-status-row');
    const smsStatusBadge = document.getElementById('sms-status-badge');
    const emailStatusBadge = document.getElementById('email-status-badge');

    // State management
    let allProducts = [];
    let currentCart = [];
    let grandTotal = 0.00;
    let selectedPaymentMode = 'Cash';
    let isProcessing = false;

    // Helper: Product Image Mapping
    function getProductImage(barcode) {
        if (barcode === '1001') return '/static/images/maggi_noodles.png';
        if (barcode === '1002') return '/static/images/amul_milk.png';
        if (barcode === '1003') return '/static/images/britannia_bread.png';
        return '/static/images/default_product.png';
    }

    // Helper: Display alert messages
    function showAlert(message, type = 'danger') {
        if (!alertBox) return;
        alertBox.textContent = message;
        alertBox.className = `alert-box ${type}`;
        alertBox.classList.remove('hide');
        setTimeout(() => {
            alertBox.classList.add('hide');
        }, 5000);
    }

    // Live Date and Time update
    function updateDateTime() {
        const liveDateEl = document.getElementById('live-date');
        const liveTimeEl = document.getElementById('live-time');
        if (!liveDateEl || !liveTimeEl) return;

        const now = new Date();
        const options = { day: '2-digit', month: 'short', year: 'numeric' };
        const dateStr = now.toLocaleDateString('en-IN', options);
        const timeStr = now.toLocaleTimeString('en-IN', {
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit',
            hour12: true
        });

        liveDateEl.textContent = dateStr;
        liveTimeEl.textContent = timeStr;
    }
    setInterval(updateDateTime, 1000);
    updateDateTime();

    // 1. Fetch All Products
    async function fetchProducts() {
        try {
            const response = await fetch('/products');
            if (response.ok) {
                allProducts = await response.json();
                populateCategories();
                filterProducts();
            } else {
                showAlert('Failed to load products list.');
            }
        } catch (error) {
            console.error('Error fetching products:', error);
            showAlert('Network error fetching products.');
        }
    }

    // 2. Populate Categories dropdown dynamically
    function populateCategories() {
        if (!categoryFilterSelect) return;
        const categories = [...new Set(allProducts.map(p => p.category))].filter(Boolean);
        
        // Clear all except the first option
        categoryFilterSelect.innerHTML = '<option value="">All Categories</option>';
        
        categories.forEach(cat => {
            const opt = document.createElement('option');
            opt.value = cat;
            opt.textContent = cat;
            categoryFilterSelect.appendChild(opt);
        });
    }

    // 3. Filter and render product list cards
    function filterProducts() {
        if (!productsListWrapper) return;

        const searchQuery = searchProductInput ? searchProductInput.value.toLowerCase().trim() : '';
        const topbarQuery = topbarSearchInput ? topbarSearchInput.value.toLowerCase().trim() : '';
        const selectedCat = categoryFilterSelect ? categoryFilterSelect.value : '';

        // Match either search query, topbar search query, and category
        const filtered = allProducts.filter(p => {
            const nameMatch = p.name.toLowerCase().includes(searchQuery) && p.name.toLowerCase().includes(topbarQuery);
            const barcodeMatch = p.barcode.toLowerCase().includes(searchQuery) && p.barcode.toLowerCase().includes(topbarQuery);
            const categoryMatch = !selectedCat || p.category === selectedCat;

            return (nameMatch || barcodeMatch) && categoryMatch;
        });

        renderProductCards(filtered);
    }

    // 4. Render product cards in Left Panel
    function renderProductCards(productsList) {
        productsListWrapper.innerHTML = '';

        if (productsList.length === 0) {
            productsListWrapper.innerHTML = '<div class="empty-state">No products found</div>';
            return;
        }

        productsList.forEach(prod => {
            const card = document.createElement('div');
            card.className = 'product-list-card-item';
            
            const isOutOfStock = prod.quantity <= 0;
            const price = parseFloat(prod.price).toFixed(2);
            
            card.innerHTML = `
                <div class="product-thumb-detail">
                    <img src="${getProductImage(prod.barcode)}" class="product-thumb-img" alt="${prod.name}">
                    <div class="product-title-category">
                        <span class="prod-card-title">${prod.name}</span>
                        <span class="prod-card-category">${prod.category} (${prod.quantity} left)</span>
                    </div>
                </div>
                <div style="display: flex; align-items: center; gap: 8px;">
                    <span class="prod-card-price">₹${price}</span>
                    <button class="btn-card-add-outline" data-barcode="${prod.barcode}" ${isOutOfStock ? 'disabled style="opacity: 0.5; cursor: not-allowed;"' : ''}>+</button>
                </div>
            `;
            productsListWrapper.appendChild(card);
        });

        // Add Event Listeners to the add buttons
        const addCardBtns = productsListWrapper.querySelectorAll('.btn-card-add-outline');
        addCardBtns.forEach(btn => {
            btn.addEventListener('click', (e) => {
                const barcode = btn.getAttribute('data-barcode');
                addToCartByBarcode(barcode, 1);
            });
        });
    }

    // 5. Fetch Cart items
    async function fetchCart() {
        try {
            const response = await fetch('/billing/cart');
            if (response.ok) {
                currentCart = await response.json();
                renderCart();
            } else {
                showAlert('Failed to load cart items.');
            }
        } catch (error) {
            console.error('Error fetching cart:', error);
            showAlert('Network error fetching cart.');
        }
    }

    // 6. Render Cart table rows & Update Totals
    function renderCart() {
        if (!cartBody) return;
        cartBody.innerHTML = '';
        grandTotal = 0.00;

        // Set cart count
        const totalItemsCount = currentCart.reduce((acc, curr) => acc + curr.quantity, 0);
        if (cartCountTitle) {
            cartCountTitle.textContent = `Active Cart (${totalItemsCount})`;
        }

        if (currentCart.length === 0) {
            cartBody.innerHTML = `
                <tr class="empty-row">
                    <td colspan="5" class="empty-state">Cart is currently empty. Scan a barcode to start billing.</td>
                </tr>
            `;
            updateTotals();
            return;
        }

        currentCart.forEach(item => {
            const subtotal = parseFloat(item.subtotal);
            grandTotal += subtotal;
            const price = parseFloat(item.unit_price).toFixed(2);

            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td class="cart-product-cell">
                    <img src="${getProductImage(item.barcode)}" class="cart-product-img" alt="${item.product_name}">
                    <div>
                        <div style="font-weight: 600;">${item.product_name}</div>
                        <div style="font-size: 0.75rem; color: var(--text-mut);">${item.barcode}</div>
                    </div>
                </td>
                <td class="text-center" style="width: 130px;">
                    <div class="qty-selector">
                        <button class="qty-btn btn-qty-minus" data-barcode="${item.barcode}" data-qty="${item.quantity}">-</button>
                        <input type="text" class="qty-input" value="${item.quantity}" readonly>
                        <button class="qty-btn btn-qty-plus" data-barcode="${item.barcode}">+</button>
                    </div>
                </td>
                <td class="text-right">₹${price}</td>
                <td class="text-right" style="font-weight: 600;">₹${subtotal.toFixed(2)}</td>
                <td class="text-center">
                    <button class="btn-cart-remove" data-barcode="${item.barcode}">
                        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor">
                            <path stroke-linecap="round" stroke-linejoin="round" d="m14.74 9-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 0 1-2.244 2.077H8.084a2.25 2.25 0 0 1-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 0 0-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 0 1 3.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 0 0-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 0 0-7.5 0" />
                        </svg>
                    </button>
                </td>
            `;
            cartBody.appendChild(tr);
        });

        updateTotals();

        // Bind Quantity decrement button
        const minusBtns = cartBody.querySelectorAll('.btn-qty-minus');
        minusBtns.forEach(btn => {
            btn.addEventListener('click', (e) => {
                const barcode = btn.getAttribute('data-barcode');
                const qty = parseInt(btn.getAttribute('data-qty'));
                decrementCartItem(barcode, qty);
            });
        });

        // Bind Quantity increment button
        const plusBtns = cartBody.querySelectorAll('.btn-qty-plus');
        plusBtns.forEach(btn => {
            btn.addEventListener('click', (e) => {
                const barcode = btn.getAttribute('data-barcode');
                incrementCartItem(barcode);
            });
        });

        // Bind Remove button
        const removeBtns = cartBody.querySelectorAll('.btn-cart-remove');
        removeBtns.forEach(btn => {
            btn.addEventListener('click', (e) => {
                const barcode = btn.getAttribute('data-barcode');
                removeFromCart(barcode);
            });
        });
    }

    // 7. Update Cart totals & Calculators
    function updateTotals() {
        const grandTotalStr = `₹${grandTotal.toFixed(2)}`;
        
        if (summarySubtotal) summarySubtotal.textContent = grandTotalStr;
        if (summaryDiscount) summaryDiscount.textContent = '₹0.00';
        if (summaryGst) summaryGst.textContent = '₹0.00';
        if (summaryTotalAmount) summaryTotalAmount.textContent = grandTotalStr;
        if (grandTotalAmount) grandTotalAmount.textContent = grandTotalStr;

        calculateChange();
    }

    // 8. Add Item to Cart
    async function addToCartByBarcode(barcode, quantity) {
        if (isProcessing) return;
        if (!barcode) {
            showAlert('Please enter or scan a product barcode.');
            return;
        }

        isProcessing = true;
        try {
            const response = await fetch('/billing/cart/add', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ barcode, quantity })
            });

            const data = await response.json();

            if (response.ok) {
                showAlert('Product added to cart.', 'success');
                if (inputBarcode) inputBarcode.value = '';
                await fetchCart();
                // Refresh product levels
                await fetchProducts();
            } else {
                showAlert(data.detail || 'Failed to add product.');
            }
        } catch (error) {
            console.error('Error adding to cart:', error);
            showAlert('Network error adding product to cart.');
        } finally {
            isProcessing = false;
        }
    }

    // Bind manually entered barcode
    if (btnAddToCart) {
        btnAddToCart.addEventListener('click', () => {
            const barcode = inputBarcode.value.trim();
            addToCartByBarcode(barcode, 1);
        });
    }

    if (inputBarcode) {
        inputBarcode.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                const barcode = inputBarcode.value.trim();
                addToCartByBarcode(barcode, 1);
            }
        });
    }

    // Topbar search barcode detection
    if (topbarSearchInput) {
        topbarSearchInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                const query = topbarSearchInput.value.trim();
                // Check if it matches a barcode in allProducts
                const matched = allProducts.find(p => p.barcode === query);
                if (matched) {
                    addToCartByBarcode(matched.barcode, 1);
                    topbarSearchInput.value = '';
                }
            }
        });
    }

    // 9. Increment cart item quantity by 1
    async function incrementCartItem(barcode) {
        await addToCartByBarcode(barcode, 1);
    }

    // 10. Decrement cart item quantity
    async function decrementCartItem(barcode, currentQty) {
        if (isProcessing) return;
        isProcessing = true;
        try {
            // Remove completely
            const removeResponse = await fetch('/billing/cart/remove', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ barcode })
            });

            if (!removeResponse.ok) {
                const data = await removeResponse.json();
                showAlert(data.detail || 'Failed to adjust quantity.');
                isProcessing = false;
                return;
            }

            // Re-add with decremented quantity if > 1
            if (currentQty > 1) {
                const addResponse = await fetch('/billing/cart/add', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ barcode, quantity: currentQty - 1 })
                });

                if (!addResponse.ok) {
                    const data = await addResponse.json();
                    showAlert(data.detail || 'Failed to adjust quantity.');
                }
            }

            showAlert('Cart quantity updated.', 'success');
            await fetchCart();
            await fetchProducts();
        } catch (error) {
            console.error('Error decrementing quantity:', error);
            showAlert('Network error adjusting quantity.');
        } finally {
            isProcessing = false;
        }
    }

    // 11. Remove product from cart completely
    async function removeFromCart(barcode) {
        if (isProcessing) return;
        isProcessing = true;
        try {
            const response = await fetch('/billing/cart/remove', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ barcode })
            });

            if (response.ok) {
                showAlert('Product removed from cart.', 'success');
                await fetchCart();
                await fetchProducts();
            } else {
                const data = await response.json();
                showAlert(data.detail || 'Failed to remove product.');
            }
        } catch (error) {
            console.error('Error removing product:', error);
            showAlert('Network error removing product.');
        } finally {
            isProcessing = false;
        }
    }

    // 12. Clear Cart function
    async function clearCart() {
        if (currentCart.length === 0) {
            showAlert('Cart is already empty.');
            return;
        }

        if (isProcessing) return;
        isProcessing = true;

        try {
            // Remove items iteratively
            for (const item of currentCart) {
                await fetch('/billing/cart/remove', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ barcode: item.barcode })
                });
            }

            showAlert('Cart cleared successfully.', 'success');
            clearTenderInputs();
            await fetchCart();
            await fetchProducts();
        } catch (error) {
            console.error('Error clearing cart:', error);
            showAlert('Error clearing all cart items.');
        } finally {
            isProcessing = false;
        }
    }

    // Bind Clear Cart buttons
    if (btnClearCartTop) btnClearCartTop.addEventListener('click', clearCart);
    if (btnClearCartBottom) btnClearCartBottom.addEventListener('click', clearCart);

    // 13. Handle Payment Mode Toggles
    const payBtns = document.querySelectorAll('.payment-mode-grid .pay-btn');
    payBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            payBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');

            selectedPaymentMode = btn.getAttribute('data-mode');

            if (selectedPaymentMode === 'Cash') {
                if (tenderCalculatorCard) tenderCalculatorCard.classList.remove('hide');
                clearTenderInputs();
            } else {
                // Hide calculator card for UPI/Card
                if (tenderCalculatorCard) tenderCalculatorCard.classList.add('hide');
                if (inputTender) inputTender.value = '';
                calculateChange();
            }
        });
    });

    // 14. Quick Cash Buttons handler
    const cashBtns = document.querySelectorAll('.quick-cash-grid .cash-btn');
    cashBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            // Change payment mode to Cash automatically
            const cashModeBtn = document.querySelector('.payment-mode-grid .pay-btn[data-mode="Cash"]');
            if (cashModeBtn && !cashModeBtn.classList.contains('active')) {
                cashModeBtn.click();
            }

            if (btn.id === 'btn-custom-cash') {
                if (inputTender) {
                    inputTender.focus();
                    inputTender.select();
                }
                return;
            }

            const amount = btn.getAttribute('data-cash');
            if (inputTender) {
                inputTender.value = amount;
                calculateChange();
            }
        });
    });

    // Recalculate change on typing tender input
    if (inputTender) {
        inputTender.addEventListener('input', calculateChange);
    }

    function calculateChange() {
        if (!inputTender || !changeReturnDisplay) return;

        let tenderVal = 0;
        if (selectedPaymentMode === 'Cash') {
            const rawText = inputTender.value.trim();
            tenderVal = parseFloat(rawText.replace(/[^\d.]/g, '')) || 0;
        } else {
            // UPI or Card has exact tender match
            tenderVal = grandTotal;
        }

        const changeReturn = tenderVal - grandTotal;
        if (changeReturn > 0 && grandTotal > 0) {
            changeReturnDisplay.textContent = `₹${changeReturn.toFixed(2)}`;
        } else {
            changeReturnDisplay.textContent = `₹0.00`;
        }
    }

    function clearTenderInputs() {
        if (inputTender) inputTender.value = '';
        if (changeReturnDisplay) changeReturnDisplay.textContent = '₹0.00';
    }

    // 15. Hold Order Mock Action
    if (btnHoldOrder) {
        btnHoldOrder.addEventListener('click', () => {
            if (currentCart.length === 0) {
                showAlert('Cannot hold empty cart.');
                return;
            }
            showAlert('Order successfully put on hold (Mocked).', 'success');
            clearTenderInputs();
            currentCart = [];
            renderCart();
            // Clear cart backend too
            clearCart();
        });
    }

    // 16. Generate Bill (Checkout)
    if (btnGenerateBill) {
        btnGenerateBill.addEventListener('click', async () => {
            if (currentCart.length === 0) {
                showAlert('Cannot generate bill. Cart is empty.');
                return;
            }

            // Verify cash tender if cash payment mode
            if (selectedPaymentMode === 'Cash' && inputTender) {
                const rawText = inputTender.value.trim();
                const tenderVal = parseFloat(rawText.replace(/[^\d.]/g, '')) || 0;
                if (tenderVal < grandTotal) {
                    showAlert('Tendered cash amount is less than Grand Total.');
                    return;
                }
            }

            if (isProcessing) return;
            isProcessing = true;

            try {
                // Read customer fields
                const customerName = inputCustomerName ? inputCustomerName.value.trim() : null;
                const customerPhone = inputCustomerPhone ? inputCustomerPhone.value.trim() : null;
                const customerEmail = inputCustomerEmail ? inputCustomerEmail.value.trim() : null;

                const response = await fetch('/billing/generate', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        customer_name: customerName || null,
                        customer_phone: customerPhone || null,
                        customer_email: customerEmail || null
                    })
                });

                const data = await response.json();

                if (response.ok) {
                    showInvoiceModal(data);
                } else {
                    showAlert(data.detail || 'Failed to generate bill.');
                }
            } catch (error) {
                console.error('Error generating bill:', error);
                showAlert('Network error generating bill.');
            } finally {
                isProcessing = false;
            }
        });
    }

    // 17. Render and open invoice printing modal
    function showInvoiceModal(bill) {
        if (!invoiceModal) return;

        // Date and Number details
        if (invoiceDate) {
            invoiceDate.textContent = `Date: ${new Date(bill.created_at).toLocaleString('en-IN')}`;
        }
        if (invoiceNumber) {
            invoiceNumber.textContent = `Bill No: SR-${bill.id.toString().padStart(6, '0')}`;
        }

        // Customer info in receipt
        if (invoiceCustomerName) {
            if (bill.customer_name) {
                invoiceCustomerName.textContent = bill.customer_name;
                invoiceCustomerName.classList.remove('hide');
            } else {
                invoiceCustomerName.classList.add('hide');
            }
        }
        if (invoiceCustomerPhone) {
            if (bill.customer_phone) {
                invoiceCustomerPhone.textContent = `Ph: ${bill.customer_phone}`;
                invoiceCustomerPhone.classList.remove('hide');
            } else {
                invoiceCustomerPhone.classList.add('hide');
            }
        }

        // Loyalty points badge
        if (loyaltyBadge && loyaltyPointsText && loyaltyTotalText) {
            if (bill.loyalty_points_earned > 0) {
                loyaltyPointsText.textContent = `🏅 +${bill.loyalty_points_earned} Loyalty Points Earned!`;
                loyaltyTotalText.textContent = `Total: ${bill.customer_total_points} pts`;
                loyaltyBadge.classList.remove('hide');
            } else {
                loyaltyBadge.classList.add('hide');
            }
        }

        // SMS & Email notification status badges
        const hasNotification = bill.sms_sent || bill.email_sent;
        if (notificationStatusRow && hasNotification) {
            notificationStatusRow.classList.remove('hide');
            if (smsStatusBadge && bill.customer_phone) {
                smsStatusBadge.textContent = bill.sms_sent ? '📱 SMS Sent' : '📱 SMS Failed';
                smsStatusBadge.className = `notif-badge ${bill.sms_sent ? 'sent' : 'failed'}`;
                smsStatusBadge.classList.remove('hide');
            }
            if (emailStatusBadge && bill.customer_email) {
                emailStatusBadge.textContent = bill.email_sent ? '📧 Email Sent' : '📧 Email Failed';
                emailStatusBadge.className = `notif-badge ${bill.email_sent ? 'sent' : 'failed'}`;
                emailStatusBadge.classList.remove('hide');
            }
        } else if (notificationStatusRow) {
            notificationStatusRow.classList.add('hide');
        }

        // Table items list
        if (invoiceItemsBody) {
            invoiceItemsBody.innerHTML = '';
            
            bill.items.forEach(item => {
                const matched = allProducts.find(p => p.id === item.product_id);
                const name = matched ? matched.name : `Product #${item.product_id}`;

                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td>${name}</td>
                    <td class="text-center">${item.quantity}</td>
                    <td class="text-right">₹${parseFloat(item.unit_price).toFixed(2)}</td>
                    <td class="text-right">₹${parseFloat(item.subtotal).toFixed(2)}</td>
                `;
                invoiceItemsBody.appendChild(tr);
            });
        }

        // Totals
        const totalAmount = parseFloat(bill.total_amount);
        let tenderedAmt = totalAmount;
        let changeDueAmt = 0.00;

        if (selectedPaymentMode === 'Cash' && inputTender) {
            const rawText = inputTender.value.trim();
            tenderedAmt = parseFloat(rawText.replace(/[^\d.]/g, '')) || totalAmount;
            changeDueAmt = tenderedAmt - totalAmount;
        }

        if (invoiceTotalAmount) invoiceTotalAmount.textContent = `₹${totalAmount.toFixed(2)}`;
        if (invoiceCashTendered) invoiceCashTendered.textContent = `₹${tenderedAmt.toFixed(2)}`;
        if (invoiceChangeDue) invoiceChangeDue.textContent = `₹${(changeDueAmt > 0 ? changeDueAmt : 0.00).toFixed(2)}`;

        // Open modal
        invoiceModal.classList.remove('hide');
    }

    // 18. Close invoice modal and reset states
    if (btnCloseModal) {
        btnCloseModal.addEventListener('click', () => {
            if (invoiceModal) invoiceModal.classList.add('hide');
            clearTenderInputs();
            // Clear customer fields
            if (inputCustomerName) inputCustomerName.value = '';
            if (inputCustomerPhone) inputCustomerPhone.value = '';
            if (inputCustomerEmail) inputCustomerEmail.value = '';
            // Hide badges
            if (loyaltyBadge) loyaltyBadge.classList.add('hide');
            if (notificationStatusRow) notificationStatusRow.classList.add('hide');
            fetchCart();
            fetchProducts();
            if (inputBarcode) {
                inputBarcode.value = '';
                inputBarcode.focus();
            }
        });
    }

    // Search and category change event triggers
    if (searchProductInput) searchProductInput.addEventListener('input', filterProducts);
    if (topbarSearchInput) topbarSearchInput.addEventListener('input', filterProducts);
    if (categoryFilterSelect) categoryFilterSelect.addEventListener('change', filterProducts);

    // View All button clears filters
    if (btnViewAllProducts) {
        btnViewAllProducts.addEventListener('click', () => {
            if (searchProductInput) searchProductInput.value = '';
            if (topbarSearchInput) topbarSearchInput.value = '';
            if (categoryFilterSelect) categoryFilterSelect.value = '';
            filterProducts();
        });
    }

    // Focus input on load
    if (inputBarcode) inputBarcode.focus();

    // Initial state loading
    fetchProducts();
    fetchCart();
});
