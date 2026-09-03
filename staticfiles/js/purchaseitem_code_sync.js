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
                if (costInput) costInput.value = data.cost_price;
                if (costText) costText.textContent = data.cost_price;
            })
            .catch(function (error) { console.error('Error fetching cost:', error); });
    }

    document.addEventListener('change', function (event) {
        var target = event.target;
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
