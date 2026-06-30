document.addEventListener('DOMContentLoaded', () => {
    // Core inputs
    const inputCustomerName = document.getElementById('input-customer-name');
    const inputCustomerPhone = document.getElementById('input-customer-phone');
    const topbarSearchInput = document.getElementById('topbar-search-input');
    const searchProductInput = document.getElementById('search-product-input');
    const inputBarcode = document.getElementById('input-barcode');
    const btnAddToCart = document.getElementById('btn-add-to-cart');
    const productsListWrapper = document.getElementById('products-list-wrapper');
    const cartBody = document.getElementById('cart-body');
    
    // Summaries
    const summarySubtotal = document.getElementById('summary-subtotal');
    const summaryGst = document.getElementById('summary-gst');
    const summaryDiscount = document.getElementById('summary-discount');
    const summaryTotalAmount = document.getElementById('summary-total-amount');
    
    // Main POS actions
    const btnGenerateBill = document.getElementById('btn-generate-bill');
    const btnClearCart = document.getElementById('btn-clear-cart');
    const btnCancelBill = document.getElementById('btn-cancel-bill');
    const alertBox = document.getElementById('alert-box');

    // Controls
    const btnHoldBill = document.getElementById('btn-hold-bill');
    const btnResumeBill = document.getElementById('btn-resume-bill');
    const btnSuspendBill = document.getElementById('btn-suspend-bill');
    const btnCancelledBills = document.getElementById('btn-cancelled-bills');

    // Payment components
    const payCashBox = document.getElementById('pay-cash-box');
    const paySplitBox = document.getElementById('pay-split-box');
    const inputCashReceived = document.getElementById('input-cash-received');
    const cashStatusLabel = document.getElementById('cash-status-label');
    const cashStatusValue = document.getElementById('cash-status-value');
    
    const splitTypeSelect = document.getElementById('split-type-select');
    const splitLbl1 = document.getElementById('split-lbl-1');
    const splitLbl2 = document.getElementById('split-lbl-2');
    const inputSplit1 = document.getElementById('input-split-1');
    const inputSplit2 = document.getElementById('input-split-2');
    const splitRemainingValue = document.getElementById('split-remaining-value');

    // Modals
    const invoiceModal = document.getElementById('invoice-modal');
    const invoiceNumber = document.getElementById('invoice-number');
    const invoiceAmountDisplay = document.getElementById('invoice-amount-display');
    const invoiceMethodDisplay = document.getElementById('invoice-method-display');
    const whatsappSendLink = document.getElementById('whatsapp-send-link');
    const whatsappStatusBadge = document.getElementById('whatsapp-status-badge');
    const btnCloseModal = document.getElementById('btn-close-modal');

    const resumeModal = document.getElementById('resume-modal');
    const resumeListBody = document.getElementById('resume-list-body');
    const cancelledModal = document.getElementById('cancelled-modal');
    const cancelledListBody = document.getElementById('cancelled-list-body');

    // Application state
    let allProducts = [];
    let currentCart = [];
    let grandTotal = 0.00;
    let selectedPaymentMode = 'Cash';
    let isProcessing = false;

    // Helper: Show alert banner
    function showAlert(message) {
        if (!alertBox) return;
        alertBox.textContent = message;
        alertBox.classList.remove('hide');
        setTimeout(() => alertBox.classList.add('hide'), 6000);
    }

    // Live Clock
    function updateDateTime() {
        const liveDateEl = document.getElementById('live-date');
        const liveTimeEl = document.getElementById('live-time');
        const now = new Date();
        if (liveDateEl) liveDateEl.textContent = now.toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' });
        if (liveTimeEl) liveTimeEl.textContent = now.toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit', hour12: true });
    }
    setInterval(updateDateTime, 1000);
    updateDateTime();

    // 1. Load Products from server
    async function fetchProducts() {
        try {
            const response = await fetch('/products');
            if (response.ok) {
                allProducts = await response.json();
                filterProducts();
            }
        } catch (error) {
            console.error('Error fetching products:', error);
            showAlert('Network error fetching products catalog.');
        }
    }

    // 2. Render and filter catalogue listing
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
                    <span class="prod-name" style="font-size: 0.85rem; font-weight:600;">${prod.name}</span>
                    <span class="prod-cat" style="font-size: 0.75rem;">Barcode: ${prod.barcode} | ${prod.quantity} left</span>
                    <span class="prod-price" style="font-size: 0.85rem; color:#2E8B57; font-weight:700;">₹${parseFloat(prod.price).toFixed(2)}</span>
                </div>
                <button class="btn-card-add" data-barcode="${prod.barcode}" ${isOutOfStock ? 'disabled style="opacity:0.4;cursor:not-allowed;"' : ''}>Add</button>
            `;
            productsListWrapper.appendChild(div);
        });

        // Add to cart click event
        productsListWrapper.querySelectorAll('.btn-card-add').forEach(btn => {
            btn.addEventListener('click', () => {
                addToCartByBarcode(btn.getAttribute('data-barcode'), 1);
            });
        });
    }

    // 3. Fetch Cart state
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

    // 4. Render active cart table rows
    function renderCart() {
        if (!cartBody) return;
        cartBody.innerHTML = '';
        grandTotal = 0.00;

        if (currentCart.length === 0) {
            cartBody.innerHTML = `<tr class="empty-row"><td colspan="5" class="empty-state">Cart is currently empty. Add products.</td></tr>`;
            updateTotals();
            calculatePayments();
            return;
        }

        currentCart.forEach(item => {
            const subtotal = parseFloat(item.subtotal);
            grandTotal += subtotal;
            const price = parseFloat(item.unit_price).toFixed(2);

            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>
                    <div class="cart-prod-name" style="font-size: 0.85rem; font-weight: 600;">${item.product_name}</div>
                    <div class="cart-prod-barcode" style="font-size: 0.75rem; color: #64748B;">${item.barcode}</div>
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
        calculatePayments();

        // Bind Qty adjusters
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

    // 5. Update grand total numbers
    function updateTotals() {
        const totalStr = `₹${grandTotal.toFixed(2)}`;
        if (summarySubtotal) summarySubtotal.textContent = totalStr;
        if (summaryGst) summaryGst.textContent = '₹0.00';
        if (summaryDiscount) summaryDiscount.textContent = '₹0.00';
        if (summaryTotalAmount) summaryTotalAmount.textContent = totalStr;
    }

    // 6. Payment Modes toggle logic
    const payBtns = document.querySelectorAll('.payment-methods-grid .pay-method-btn');
    payBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            payBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            selectedPaymentMode = btn.getAttribute('data-mode');

            if (selectedPaymentMode === 'Cash') {
                payCashBox.classList.remove('hide');
                paySplitBox.classList.add('hide');
            } else if (selectedPaymentMode === 'Split') {
                payCashBox.classList.add('hide');
                paySplitBox.classList.remove('hide');
                updateSplitLabels();
            } else {
                // Card or UPI
                payCashBox.classList.add('hide');
                paySplitBox.classList.add('hide');
            }
            calculatePayments();
        });
    });

    // Cash received inputs handler
    if (inputCashReceived) {
        inputCashReceived.addEventListener('input', calculatePayments);
    }

    // Split selectors trigger
    if (splitTypeSelect) {
        splitTypeSelect.addEventListener('change', () => {
            updateSplitLabels();
            calculatePayments();
        });
    }

    if (inputSplit1) inputSplit1.addEventListener('input', calculatePayments);
    if (inputSplit2) inputSplit2.addEventListener('input', calculatePayments);

    // Update Split field label names
    function updateSplitLabels() {
        const type = splitTypeSelect.value;
        if (type === 'Cash-UPI') {
            splitLbl1.textContent = 'Cash Split (₹)';
            splitLbl2.textContent = 'UPI Split (₹)';
        } else if (type === 'Cash-Card') {
            splitLbl1.textContent = 'Cash Split (₹)';
            splitLbl2.textContent = 'Card Split (₹)';
        } else {
            splitLbl1.textContent = 'UPI Split (₹)';
            splitLbl2.textContent = 'Card Split (₹)';
        }
    }

    // Automated cash changes and payment validations
    function calculatePayments() {
        let isPaymentValid = false;

        if (currentCart.length === 0) {
            btnGenerateBill.disabled = true;
            btnGenerateBill.style.opacity = 0.5;
            return;
        }

        if (selectedPaymentMode === 'Cash') {
            const receivedVal = parseFloat(inputCashReceived.value) || 0.00;
            const difference = receivedVal - grandTotal;

            if (difference >= 0) {
                cashStatusLabel.textContent = 'Change to Return:';
                cashStatusLabel.className = 'success-text';
                cashStatusValue.textContent = `₹${difference.toFixed(2)}`;
                cashStatusValue.className = 'payment-display-value success-text';
                isPaymentValid = true;
            } else {
                cashStatusLabel.textContent = 'Remaining Amount:';
                cashStatusLabel.className = 'error-text';
                cashStatusValue.textContent = `₹${Math.abs(difference).toFixed(2)}`;
                cashStatusValue.className = 'payment-display-value error-text';
                isPaymentValid = false;
            }
        } else if (selectedPaymentMode === 'Split') {
            const splitVal1 = parseFloat(inputSplit1.value) || 0.00;
            const splitVal2 = parseFloat(inputSplit2.value) || 0.00;
            const totalPaid = splitVal1 + splitVal2;
            const remaining = grandTotal - totalPaid;

            if (Math.abs(remaining) < 0.01) {
                splitRemainingValue.textContent = '₹0.00 (Paid)';
                splitRemainingValue.className = 'payment-display-value success-text';
                isPaymentValid = true;
            } else if (remaining > 0) {
                splitRemainingValue.textContent = `₹${remaining.toFixed(2)}`;
                splitRemainingValue.className = 'payment-display-value error-text';
                isPaymentValid = false;
            } else {
                splitRemainingValue.textContent = `Overpaid by ₹${Math.abs(remaining).toFixed(2)}`;
                splitRemainingValue.className = 'payment-display-value error-text';
                isPaymentValid = false;
            }
        } else {
            // UPI / Card assumes full online transaction verification
            isPaymentValid = true;
        }

        if (isPaymentValid) {
            btnGenerateBill.disabled = false;
            btnGenerateBill.style.opacity = 1.0;
        } else {
            btnGenerateBill.disabled = true;
            btnGenerateBill.style.opacity = 0.5;
        }
    }

    // 7. Add Cart Items barcode trigger
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
            showAlert('Network error occurred.');
        } finally {
            isProcessing = false;
        }
    }

    // Decrement
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

    // Remove
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

    // Standard local clears
    async function clearActiveCartOnly() {
        try {
            for (const item of currentCart) {
                await fetch('/billing/cart/remove', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ barcode: item.barcode })
                });
            }
            if (inputCustomerName) inputCustomerName.value = '';
            if (inputCustomerPhone) inputCustomerPhone.value = '';
            if (inputCashReceived) inputCashReceived.value = '';
            if (inputSplit1) inputSplit1.value = '';
            if (inputSplit2) inputSplit2.value = '';
            await fetchCart();
            await fetchProducts();
        } catch (e) {
            console.error("Cart clear error", e);
        }
    }

    if (btnClearCart) {
        btnClearCart.addEventListener('click', async () => {
            if (confirm("Are you sure you want to clear the active cart?")) {
                await clearActiveCartOnly();
            }
        });
    }

    // 8. Bill Controls logic using localStorage

    // HOLD BILL
    if (btnHoldBill) {
        btnHoldBill.addEventListener('click', async () => {
            if (currentCart.length === 0) {
                showAlert('Cart is empty, nothing to Hold.');
                return;
            }
            const name = inputCustomerName.value.trim();
            const phone = inputCustomerPhone.value.trim();
            if (!name || !phone) {
                showAlert('Customer Name and WhatsApp Number are mandatory to Hold a bill.');
                return;
            }

            const heldBill = {
                id: Date.now(),
                type: 'Hold',
                timestamp: new Date().toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' }),
                customer_name: name,
                customer_phone: phone,
                items: JSON.parse(JSON.stringify(currentCart)),
                amount: grandTotal
            };

            let list = JSON.parse(localStorage.getItem('pos_held_bills')) || [];
            list.push(heldBill);
            localStorage.setItem('pos_held_bills', JSON.stringify(list));

            await clearActiveCartOnly();
            alert('Bill successfully parked on HOLD.');
        });
    }

    // SUSPEND BILL
    if (btnSuspendBill) {
        btnSuspendBill.addEventListener('click', async () => {
            if (currentCart.length === 0) {
                showAlert('Cart is empty, nothing to Suspend.');
                return;
            }
            const name = inputCustomerName.value.trim();
            const phone = inputCustomerPhone.value.trim();
            if (!name || !phone) {
                showAlert('Customer Name and WhatsApp Number are mandatory to Suspend a bill.');
                return;
            }

            const suspendedBill = {
                id: Date.now(),
                type: 'Suspend',
                timestamp: new Date().toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' }),
                customer_name: name,
                customer_phone: phone,
                items: JSON.parse(JSON.stringify(currentCart)),
                amount: grandTotal
            };

            let list = JSON.parse(localStorage.getItem('pos_held_bills')) || [];
            list.push(suspendedBill);
            localStorage.setItem('pos_held_bills', JSON.stringify(list));

            await clearActiveCartOnly();
            alert('Bill successfully SUSPENDED.');
        });
    }

    // RESUME BILL MODAL
    if (btnResumeBill) {
        btnResumeBill.addEventListener('click', () => {
            const list = JSON.parse(localStorage.getItem('pos_held_bills')) || [];
            resumeListBody.innerHTML = '';

            if (list.length === 0) {
                resumeListBody.innerHTML = '<tr><td colspan="5" class="empty-state">No held or suspended bills.</td></tr>';
            } else {
                list.forEach((bill, idx) => {
                    const tr = document.createElement('tr');
                    tr.innerHTML = `
                        <td>${bill.timestamp}</td>
                        <td>
                            <div><strong>${bill.customer_name}</strong></div>
                            <div style="font-size: 0.75rem; color:#64748B;">${bill.customer_phone}</div>
                        </td>
                        <td><span class="badge ${bill.type === 'Hold' ? 'badge-yellow' : 'badge-red'}" style="padding: 2px 6px; font-size: 0.7rem;">${bill.type}</span></td>
                        <td style="font-weight:600;">₹${bill.amount.toFixed(2)}</td>
                        <td>
                            <button class="btn btn-primary btn-xs" onclick="resumeParkedBill(${bill.id})" style="padding:4px 8px; font-size:0.75rem;">Resume</button>
                        </td>
                    `;
                    resumeListBody.appendChild(tr);
                });
            }
            resumeModal.classList.remove('hide');
        });
    }

    // Resume execution
    window.resumeParkedBill = async function(billId) {
        let list = JSON.parse(localStorage.getItem('pos_held_bills')) || [];
        const index = list.findIndex(b => b.id === billId);
        if (index === -1) return;

        const bill = list[index];
        // Load customer data
        inputCustomerName.value = bill.customer_name;
        inputCustomerPhone.value = bill.customer_phone;

        // Clear active cart and load these items sequentially
        await clearActiveCartOnly();
        
        for (const item of bill.items) {
            await fetch('/billing/cart/add', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ barcode: item.barcode, quantity: item.quantity })
            });
        }

        // Remove from localStorage
        list.splice(index, 1);
        localStorage.setItem('pos_held_bills', JSON.stringify(list));

        resumeModal.classList.add('hide');
        await fetchCart();
        await fetchProducts();
    };

    // CANCEL BILL ACTION
    if (btnCancelBill) {
        btnCancelBill.addEventListener('click', async () => {
            if (currentCart.length === 0) {
                showAlert('Cart is empty.');
                return;
            }
            if (confirm("Are you sure you want to CANCEL/VOID this bill? This action is logged.")) {
                const name = inputCustomerName.value.trim() || 'Walk-in Customer';
                const phone = inputCustomerPhone.value.trim() || '-';
                
                const cancelledBill = {
                    id: Date.now(),
                    timestamp: new Date().toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' }),
                    customer_name: name,
                    customer_phone: phone,
                    amount: grandTotal
                };

                let list = JSON.parse(localStorage.getItem('pos_cancelled_bills')) || [];
                list.push(cancelledBill);
                localStorage.setItem('pos_cancelled_bills', JSON.stringify(list));

                await clearActiveCartOnly();
                alert('Bill voided and logged.');
            }
        });
    }

    // CANCELLED BILLS MODAL VIEW
    if (btnCancelledBills) {
        btnCancelledBills.addEventListener('click', () => {
            const list = JSON.parse(localStorage.getItem('pos_cancelled_bills')) || [];
            cancelledListBody.innerHTML = '';

            if (list.length === 0) {
                cancelledListBody.innerHTML = '<tr><td colspan="4" class="empty-state">No cancelled bills in this session.</td></tr>';
            } else {
                list.slice().reverse().forEach(bill => {
                    const tr = document.createElement('tr');
                    tr.innerHTML = `
                        <td>${bill.timestamp}</td>
                        <td><strong>${bill.customer_name}</strong></td>
                        <td>${bill.customer_phone}</td>
                        <td style="font-weight:600; color: #B91C1C;">₹${bill.amount.toFixed(2)}</td>
                    `;
                    cancelledListBody.appendChild(tr);
                });
            }
            cancelledModal.classList.remove('hide');
        });
    }

    // 9. Complete checkout & call POST /billing/generate
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

            // Payment verification before submitting
            let paymentPayload = {
                payment_method: selectedPaymentMode,
                cash_received: null,
                change_returned: null,
                split_cash: null,
                split_upi: null,
                split_card: null
            };

            if (selectedPaymentMode === 'Cash') {
                const cashRec = parseFloat(inputCashReceived.value) || 0.00;
                if (cashRec < grandTotal) {
                    showAlert('Insufficient Cash received.');
                    return;
                }
                paymentPayload.cash_received = cashRec;
                paymentPayload.change_returned = cashRec - grandTotal;
            } else if (selectedPaymentMode === 'Split') {
                const splitVal1 = parseFloat(inputSplit1.value) || 0.00;
                const splitVal2 = parseFloat(inputSplit2.value) || 0.00;
                const splitTotal = splitVal1 + splitVal2;
                
                if (Math.abs(splitTotal - grandTotal) >= 0.01) {
                    showAlert('Split totals must equal Grand Total.');
                    return;
                }

                const splitType = splitTypeSelect.value;
                if (splitType === 'Cash-UPI') {
                    paymentPayload.split_cash = splitVal1;
                    paymentPayload.split_upi = splitVal2;
                } else if (splitType === 'Cash-Card') {
                    paymentPayload.split_cash = splitVal1;
                    paymentPayload.split_card = splitVal2;
                } else {
                    paymentPayload.split_upi = splitVal1;
                    paymentPayload.split_card = splitVal2;
                }
            }

            if (isProcessing) return;
            isProcessing = true;
            btnGenerateBill.disabled = true;
            btnGenerateBill.innerText = "Processing...";

            try {
                const response = await fetch('/billing/generate', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        customer_name: customerName,
                        customer_phone: customerPhone,
                        ...paymentPayload
                    })
                });

                const data = await response.json();
                if (response.ok) {
                    showInvoiceModal(data, customerPhone);
                } else {
                    showAlert(data.detail || 'Failed to complete transaction.');
                    btnGenerateBill.disabled = false;
                }
            } catch (error) {
                showAlert('Network error completing transaction.');
                btnGenerateBill.disabled = false;
            } finally {
                isProcessing = false;
                btnGenerateBill.innerText = "Complete Payment";
                calculatePayments();
            }
        });
    }

    // 10. Show modal invoice & trigger WhatsApp link setup
    function showInvoiceModal(bill, phone) {
        if (!invoiceModal) return;

        if (invoiceNumber) invoiceNumber.textContent = `SR-${bill.id.toString().padStart(6, '0')}`;
        if (invoiceAmountDisplay) invoiceAmountDisplay.textContent = `₹${parseFloat(bill.total_amount).toFixed(2)}`;
        
        let methodStr = bill.payment_method;
        if (bill.payment_method === 'Split') {
            const parts = [];
            if (bill.split_cash) parts.push(`Cash (₹${parseFloat(bill.split_cash).toFixed(2)})`);
            if (bill.split_upi) parts.push(`UPI (₹${parseFloat(bill.split_upi).toFixed(2)})`);
            if (bill.split_card) parts.push(`Card (₹${parseFloat(bill.split_card).toFixed(2)})`);
            methodStr = `Split: ${parts.join(' + ')}`;
        }
        if (invoiceMethodDisplay) invoiceMethodDisplay.textContent = methodStr;

        // Reset WhatsApp badge
        if (whatsappStatusBadge) {
            whatsappStatusBadge.textContent = 'Pending';
            whatsappStatusBadge.className = 'badge badge-yellow';
        }

        // WhatsApp redirect parameters
        if (whatsappSendLink) {
            const invoiceLink = window.location.origin + "/history";
            const textMsg = `Thank you for shopping at Smart Retail.\n\nInvoice Number: SR-${bill.id.toString().padStart(6, '0')}\nAmount: ₹${parseFloat(bill.total_amount).toFixed(2)}\nPayment: ${methodStr}\n\nView invoice here:\n${invoiceLink}`;
            const encoded = encodeURIComponent(textMsg);
            whatsappSendLink.href = `https://wa.me/91${phone}?text=${encoded}`;
        }

        invoiceModal.classList.remove('hide');
    }

    // WhatsApp badge status change when link clicked
    if (whatsappSendLink) {
        whatsappSendLink.addEventListener('click', () => {
            if (whatsappStatusBadge) {
                whatsappStatusBadge.textContent = 'Sent';
                whatsappStatusBadge.className = 'badge badge-green';
            }
        });
    }

    // 11. Reset modal screen
    if (btnCloseModal) {
        btnCloseModal.addEventListener('click', async () => {
            invoiceModal.classList.add('hide');
            inputCustomerName.value = '';
            inputCustomerPhone.value = '';
            if (inputCashReceived) inputCashReceived.value = '';
            if (inputSplit1) inputSplit1.value = '';
            if (inputSplit2) inputSplit2.value = '';
            
            // Clear cart
            await clearActiveCartOnly();
        });
    }

    // Inputs events
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

    // Initial load
    fetchProducts();
    fetchCart();
});
