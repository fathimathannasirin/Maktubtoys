(function () {
    'use strict';

    function syncPair(codeSelect, productSelect) {
        if (codeSelect.dataset.syncBound) return;
        codeSelect.dataset.syncBound = 'true';
        productSelect.dataset.syncBound = 'true';

        function updateCost(productId, selectElement) {
            if (!productId) return;
            
            var row = selectElement.closest('.form-row') || selectElement.closest('tr');
            if (!row) return;

            // Targets both the readonly paragraph and the editable input
            var costText = row.querySelector('.field-unit_cost p, .field-unit_cost .readonly');
            var costInput = row.querySelector('input[name$="-unit_cost"]'); 
            
            fetch('/store/get-product-cost/?product_id=' + productId)
                .then(response => response.json())
                .then(data => {
                    if (data.cost_price !== undefined) {
                        if (costText) costText.innerText = data.cost_price;
                        if (costInput) costInput.value = data.cost_price;
                    }
                })
                .catch(error => console.error('Error fetching cost:', error));
        }

        codeSelect.addEventListener('change', function () {
            if (this.value && productSelect.value !== this.value) {
                productSelect.value = this.value;
                productSelect.dispatchEvent(new Event('change', { bubbles: true }));
            }
            updateCost(this.value, this);
        });

        productSelect.addEventListener('change', function () {
            if (this.value && codeSelect.value !== this.value) {
                codeSelect.value = this.value;
                codeSelect.dispatchEvent(new Event('change', { bubbles: true }));
            }
            updateCost(this.value, this);
        });
    }

    function bindAllRows(root) {
        var productSelects = (root || document).querySelectorAll('select[name$="-product"]');
        productSelects.forEach(function (productSelect) {
            var codeName = productSelect.name.replace(/-product$/, '-product_code');
            var codeSelect = document.querySelector('select[name="' + codeName + '"]');
            if (codeSelect && productSelect) {
                syncPair(codeSelect, productSelect);
            }
        });
    }

    function init() {
        bindAllRows(document);
        document.addEventListener('formset:added', function (event) {
            bindAllRows(event.target.closest ? event.target : document);
        });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();