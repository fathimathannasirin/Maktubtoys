(function () {
    'use strict';

    function syncPair(codeSelect, productSelect) {
        if (codeSelect.dataset.syncBound) return;
        codeSelect.dataset.syncBound = 'true';
        productSelect.dataset.syncBound = 'true';

        codeSelect.addEventListener('change', function () {
            if (this.value && productSelect.value !== this.value) {
                productSelect.value = this.value;
                productSelect.dispatchEvent(new Event('change', { bubbles: true }));
            }
        });

        productSelect.addEventListener('change', function () {
            if (this.value && codeSelect.value !== this.value) {
                codeSelect.value = this.value;
                codeSelect.dispatchEvent(new Event('change', { bubbles: true }));
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
