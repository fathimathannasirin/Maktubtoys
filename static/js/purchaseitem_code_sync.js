(function () {
    'use strict';

    function fieldSuffix(name, suffix) {
        return name.endsWith(suffix);
    }

    function syncPair(codeSelect, productSelect) {
        if (codeSelect.dataset.syncBound) return;
        codeSelect.dataset.syncBound = 'true';
        productSelect.dataset.syncBound = 'true';

        // പ്രോഡക്റ്റ് മാറുമ്പോൾ കോസ്റ്റ് അപ്‌ഡേറ്റ് ചെയ്യാനുള്ള ഫംഗ്‌ഷൻ
        function updateCost(productId, selectElement) {
            if (!productId) return;
            
            var row = selectElement.closest('.form-row') || selectElement.closest('tr');
            if (!row) return;

            // അഡ്മിൻ readonly ഫീൽഡ് കണ്ടുപിടിക്കുന്നു
            var costField = row.querySelector('.field-unit_cost p'); 
            
            if (costField) {
                fetch('/admin/get-product-cost/' + productId + '/')
                    .then(response => response.json())
                    .then(data => {
                        if (data.cost_price) {
                            costField.innerText = data.cost_price;
                        }
                    })
                    .catch(error => console.error('Error fetching cost:', error));
            }
        }

        codeSelect.addEventListener('change', function () {
            if (this.value && productSelect.value !== this.value) {
                productSelect.value = this.value;
                productSelect.dispatchEvent(new Event('change', { bubbles: true }));
                updateCost(this.value, this); // കോസ്റ്റ് അപ്‌ഡേറ്റ് ചെയ്യുന്നു
            }
        });

        productSelect.addEventListener('change', function () {
            if (this.value && codeSelect.value !== this.value) {
                codeSelect.value = this.value;
                codeSelect.dispatchEvent(new Event('change', { bubbles: true }));
                updateCost(this.value, this); // കോസ്റ്റ് അപ്‌ഡേറ്റ് ചെയ്യുന്നു
            }
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

        // Re-bind whenever Django admin adds a new inline row.
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