(function () {
    'use strict';

    function setCost(productId, row) {
        if (!productId) return;
        var costInput = row.querySelector('input[name$="-unit_cost"]');
        var costText = row.querySelector('.field-unit_cost p, .field-unit_cost .readonly');

        fetch('/store/get-product-cost/?product_id=' + encodeURIComponent(productId))
            .then(function (response) { return response.json(); })
            .then(function (data) {
                if (!data || data.cost_price === undefined) return;
                if (costInput) {
                    costInput.value = data.cost_price;
                    costInput.dispatchEvent(new Event('input', { bubbles: true }));
                }
                if (costText) costText.textContent = data.cost_price;
            })
            .catch(function (error) { console.error('Error fetching cost:', error); });
    }
    function updateProductDropdowns() {
        var supplierSelect = document.querySelector('select[name="supplier"]');
        var warehouseSelect = document.querySelector('select[name="warehouse"]');

        var supplierId = supplierSelect ? supplierSelect.value : '';
        var warehouseId = warehouseSelect ? warehouseSelect.value : '';

        if (!supplierId && !warehouseId) return;

        fetch('/store/get-filtered-products/?supplier_id=' + encodeURIComponent(supplierId) + '&warehouse_id=' + encodeURIComponent(warehouseId))
            .then(function (response) { return response.json(); })
            .then(function (data) {
                var products = data.products || [];

                document.querySelectorAll('select[name$="-product"], select[name$="-product_code"]').forEach(function (select) {
                    var currentValue = select.value;
                    var isCodeField = select.name.endsWith('-product_code');

                    select.innerHTML = '<option value="">---------</option>';

                    products.forEach(function (prod) {
                        var opt = document.createElement('option');
                        opt.value = prod.id;
                        opt.textContent = isCodeField ? prod.code : prod.name;
                        if (String(prod.id) === String(currentValue)) {
                            opt.selected = true;
                        }
                        select.appendChild(opt);
                    });
                });
            })
            .catch(function (error) { console.error('Error fetching filtered products:', error); });
    }

    document.addEventListener('change', function (event) {
        var target = event.target;
        if (target.name === 'supplier' || target.name === 'warehouse') {
            updateProductDropdowns();
            return;
        }
        var row = target && (target.closest('tr') || target.closest('.form-row'));
        if (!row || !target.matches('select[name$="-product_code"], select[name$="-product"]')) return;

        var codeSelect = row.querySelector('select[name$="-product_code"]');
        var productSelect = row.querySelector('select[name$="-product"]');
        var productId = target.value;

        if (target === codeSelect && productSelect && productSelect.value !== productId) {
            productSelect.value = productId;
            productSelect.dispatchEvent(new Event('change', { bubbles: true }));
        } else if (target === productSelect && codeSelect && codeSelect.value !== productId) {
            codeSelect.value = productId;
        }
        setCost(productId, row);
    });
})();
