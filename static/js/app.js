/* ============================================================
   app.js - المنطق العام للواجهة (فواتير ديناميكية، قيود، تنبيهات)
   ============================================================ */

document.addEventListener("DOMContentLoaded", function () {
    initFlashAutoHide();
    initInvoiceItemsTable();
    initJournalLinesTable();
    initExpenseForm();
});

/* ---------- إخفاء التنبيهات تلقائياً ---------- */
function initFlashAutoHide() {
    document.querySelectorAll(".flash").forEach(function (el) {
        setTimeout(function () {
            el.style.transition = "opacity 0.4s ease";
            el.style.opacity = "0";
            setTimeout(function () { el.remove(); }, 400);
        }, 4000);
    });
}

/* ============================================================
   جدول بنود الفاتورة (إضافة/حذف صف + حساب الإجمالي تلقائي)
   ============================================================ */
function initInvoiceItemsTable() {
    const table = document.getElementById("invoice-items-table");
    if (!table) return;

    const addBtn = document.getElementById("add-item-row");
    const tbody = table.querySelector("tbody");
    const subtotalEl = document.getElementById("invoice-subtotal");
    const taxRateInput = document.getElementById("tax_rate");
    const taxTotalEl = document.getElementById("invoice-tax-total");
    const grandTotalEl = document.getElementById("invoice-grand-total");
    const productsData = window.PRODUCTS_DATA || [];

    function rowTemplate() {
        const row = document.createElement("tr");
        row.innerHTML = `
            <td>
                <select name="product_id[]" class="product-select">
                    <option value="">-- بدون منتج --</option>
                    ${productsData.map(p => `<option value="${p.id}" data-price="${p.sale_price}">${p.name}</option>`).join("")}
                </select>
            </td>
            <td><input type="text" name="item_description[]" placeholder="وصف البند"></td>
            <td><input type="number" name="quantity[]" class="qty-input" value="1" min="0.01" step="0.01"></td>
            <td><input type="number" name="unit_price[]" class="price-input" value="0" min="0" step="0.01"></td>
            <td class="numeric line-total">0.00</td>
            <td><button type="button" class="btn danger remove-row" style="padding:5px 10px;">حذف</button></td>
        `;
        return row;
    }

    function recalcRow(row) {
        const qty = parseFloat(row.querySelector(".qty-input").value) || 0;
        const price = parseFloat(row.querySelector(".price-input").value) || 0;
        const total = qty * price;
        row.querySelector(".line-total").textContent = total.toFixed(2);
        recalcInvoiceTotals();
    }

    function recalcInvoiceTotals() {
        let subtotal = 0;
        tbody.querySelectorAll("tr").forEach(function (row) {
            const qty = parseFloat(row.querySelector(".qty-input")?.value) || 0;
            const price = parseFloat(row.querySelector(".price-input")?.value) || 0;
            subtotal += qty * price;
        });
        const taxRate = parseFloat(taxRateInput?.value) || 0;
        const taxTotal = subtotal * taxRate / 100;
        const grandTotal = subtotal + taxTotal;

        if (subtotalEl) subtotalEl.textContent = subtotal.toFixed(2);
        if (taxTotalEl) taxTotalEl.textContent = taxTotal.toFixed(2);
        if (grandTotalEl) grandTotalEl.textContent = grandTotal.toFixed(2);
    }

    tbody.addEventListener("input", function (e) {
        if (e.target.classList.contains("qty-input") || e.target.classList.contains("price-input")) {
            recalcRow(e.target.closest("tr"));
        }
    });

    tbody.addEventListener("change", function (e) {
        if (e.target.classList.contains("product-select")) {
            const row = e.target.closest("tr");
            const selected = e.target.selectedOptions[0];
            const price = selected ? selected.dataset.price : null;
            if (price) {
                row.querySelector(".price-input").value = parseFloat(price).toFixed(2);
                recalcRow(row);
            }
        }
    });

    tbody.addEventListener("click", function (e) {
        if (e.target.classList.contains("remove-row")) {
            e.target.closest("tr").remove();
            recalcInvoiceTotals();
        }
    });

    if (addBtn) {
        addBtn.addEventListener("click", function () {
            tbody.appendChild(rowTemplate());
        });
    }

    if (taxRateInput) {
        taxRateInput.addEventListener("input", recalcInvoiceTotals);
    }

    // صف ابتدائي واحد لو الجدول فاضي
    if (tbody.children.length === 0) {
        tbody.appendChild(rowTemplate());
    }
    recalcInvoiceTotals();
}

/* ============================================================
   جدول بنود القيد اليومي (إضافة/حذف صف + التحقق من التوازن)
   ============================================================ */
function initJournalLinesTable() {
    const table = document.getElementById("journal-lines-table");
    if (!table) return;

    const addBtn = document.getElementById("add-line-row");
    const tbody = table.querySelector("tbody");
    const totalDebitEl = document.getElementById("total-debit");
    const totalCreditEl = document.getElementById("total-credit");
    const balanceWarning = document.getElementById("balance-warning");
    const submitBtn = document.getElementById("journal-submit-btn");
    const accountsData = window.ACCOUNTS_DATA || [];

    function rowTemplate() {
        const row = document.createElement("tr");
        row.innerHTML = `
            <td>
                <select name="account_id[]" required>
                    <option value="">-- اختر حساب --</option>
                    ${accountsData.map(a => `<option value="${a.id}">${a.code} - ${a.name}</option>`).join("")}
                </select>
            </td>
            <td><input type="text" name="line_description[]" placeholder="وصف"></td>
            <td><input type="number" name="debit[]" class="debit-input" value="0" min="0" step="0.01"></td>
            <td><input type="number" name="credit[]" class="credit-input" value="0" min="0" step="0.01"></td>
            <td><button type="button" class="btn danger remove-row" style="padding:5px 10px;">حذف</button></td>
        `;
        return row;
    }

    function recalcBalance() {
        let totalDebit = 0, totalCredit = 0;
        tbody.querySelectorAll("tr").forEach(function (row) {
            totalDebit += parseFloat(row.querySelector(".debit-input")?.value) || 0;
            totalCredit += parseFloat(row.querySelector(".credit-input")?.value) || 0;
        });
        if (totalDebitEl) totalDebitEl.textContent = totalDebit.toFixed(2);
        if (totalCreditEl) totalCreditEl.textContent = totalCredit.toFixed(2);

        const balanced = Math.abs(totalDebit - totalCredit) < 0.001 && totalDebit > 0;
        if (balanceWarning) {
            balanceWarning.style.display = balanced ? "none" : "block";
        }
        if (submitBtn) {
            submitBtn.disabled = !balanced;
            submitBtn.style.opacity = balanced ? "1" : "0.5";
        }
    }

    tbody.addEventListener("input", function (e) {
        // مدين وحده أو دائن وحده مش الاتنين في نفس السطر
        if (e.target.classList.contains("debit-input") && parseFloat(e.target.value) > 0) {
            const row = e.target.closest("tr");
            row.querySelector(".credit-input").value = 0;
        }
        if (e.target.classList.contains("credit-input") && parseFloat(e.target.value) > 0) {
            const row = e.target.closest("tr");
            row.querySelector(".debit-input").value = 0;
        }
        recalcBalance();
    });

    tbody.addEventListener("click", function (e) {
        if (e.target.classList.contains("remove-row")) {
            e.target.closest("tr").remove();
            recalcBalance();
        }
    });

    if (addBtn) {
        addBtn.addEventListener("click", function () {
            tbody.appendChild(rowTemplate());
        });
    }

    // ابدأ بسطرين افتراضيين (مدين ودائن)
    if (tbody.children.length === 0) {
        tbody.appendChild(rowTemplate());
        tbody.appendChild(rowTemplate());
    }
    recalcBalance();
}

/* ============================================================
   نموذج المصروفات - حساب سريع
   ============================================================ */
function initExpenseForm() {
    const form = document.getElementById("expense-form");
    if (!form) return;
    // مساحة لأي منطق مستقبلي خاص بالمصروفات (مثلاً تكرار شهري)
}
