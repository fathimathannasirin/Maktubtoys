(function () {
    'use strict';

    var endpoint = '/store/get-filtered-products/';

    function populateProductDropdowns(products) {
        document.querySelectorAll('select[name$="-product"], select[name$="-product_code"]').forEach(function (select) {
            var currentValue = select.value;
            var isCodeField = select.name.endsWith('-product_code');
            select.innerHTML = '<option value="">---------</option>';
            products.forEach(function (product) {
                var option = document.createElement('option');
                option.value = product.id;
                option.textContent = isCodeField ? product.code : product.name;
                option.title = product.code + ' - ' + product.name;
                if (String(product.id) === String(currentValue)) option.selected = true;
                select.appendChild(option);
            });
        });
    }

    function loadProducts(searchTerm) {
        var supplierSelect = document.querySelector('select[name="supplier"]');
        var warehouseSelect = document.querySelector('select[name="warehouse"]');
        var supplierId = supplierSelect ? supplierSelect.value : '';
        var warehouseId = warehouseSelect ? warehouseSelect.value : '';
        var url = endpoint + '?supplier_id=' + encodeURIComponent(supplierId) +
            '&warehouse_id=' + encodeURIComponent(warehouseId) + '&q=' + encodeURIComponent(searchTerm || '');
        return fetch(url)
            .then(function (response) { return response.json(); })
            .then(function (data) {
                populateProductDropdowns(data.products || []);
                return data.products || [];
            });
    }

    function firstAvailableRow() {
        var rows = Array.from(document.querySelectorAll('.tabular tbody tr')).filter(function (row) {
            var deleted = row.querySelector('input[name$="-DELETE"]');
            return !deleted || !deleted.checked;
        });
        return rows.find(function (row) {
            var product = row.querySelector('select[name$="-product"]');
            return product && !product.value;
        }) || rows[rows.length - 1];
    }

    function selectProduct(product) {
        var row = firstAvailableRow();
        if (!row) return;
        var codeSelect = row.querySelector('select[name$="-product_code"]');
        var productSelect = row.querySelector('select[name$="-product"]');
        [codeSelect, productSelect].forEach(function (select) {
            if (!select) return;
            var option = Array.from(select.options).find(function (item) { return String(item.value) === String(product.id); });
            if (!option) {
                option = new Option(select.name.endsWith('-product_code') ? product.code : product.name, product.id);
                select.add(option);
            }
            select.value = String(product.id);
            select.dispatchEvent(new Event('change', { bubbles: true }));
        });
        setCost(product.id, row, product.cost_price);
    }

    function renderResults(toolbar, products) {
        var results = toolbar.querySelector('.product-search-results');
        results.innerHTML = '';
        products.forEach(function (product) {
            var result = document.createElement('button');
            result.type = 'button';
            result.className = 'product-search-result';
            result.innerHTML = '<strong></strong><span></span><em></em>';
            result.querySelector('strong').textContent = product.code;
            result.querySelector('span').textContent = product.name;
            result.querySelector('em').textContent = product.cost_price === null ? '' : 'Cost: ' + product.cost_price;
            result.addEventListener('click', function () {
                selectProduct(product);
                results.hidden = true;
            });
            results.appendChild(result);
        });
        results.hidden = products.length === 0;
    }

    function addSearchToolbar() {
        var inlineGroup = document.querySelector('.inline-group:has([name$="-product_code"])');
        if (!inlineGroup || inlineGroup.querySelector('.product-inline-search')) return;
        var toolbar = document.createElement('div');
        toolbar.className = 'product-inline-search';
        toolbar.innerHTML = '<div class="product-search-input-wrap"><input type="search" placeholder="Search product name or code" aria-label="Search products"><div class="product-search-results" hidden></div></div>' +
            '<button type="button" class="search-button">Search</button><button type="button" class="clear-search">Clear</button>';
        inlineGroup.insertBefore(toolbar, inlineGroup.querySelector('.tabular'));
        var input = toolbar.querySelector('input');
        var timer;
        var search = function () {
            loadProducts(input.value).then(function (products) {
                renderResults(toolbar, products);
            }).catch(function (error) { console.error('Error searching products:', error); });
        };
        toolbar.querySelector('.search-button').addEventListener('click', search);
        input.addEventListener('input', function () {
            clearTimeout(timer);
            timer = setTimeout(search, 180);
        });
        toolbar.querySelector('.clear-search').addEventListener('click', function () {
            input.value = '';
            toolbar.querySelector('.product-search-results').hidden = true;
            loadProducts('').catch(function (error) { console.error('Error clearing product search:', error); });
        });
        input.addEventListener('keydown', function (event) {
            if (event.key === 'Enter') {
                event.preventDefault();
                toolbar.querySelector('.search-button').click();
            }
        });
        document.addEventListener('click', function (event) {
            if (!toolbar.contains(event.target)) toolbar.querySelector('.product-search-results').hidden = true;
        });
    }

    function setCost(productId, row, knownCost) {
        if (!productId) return;
        var costInput = row.querySelector('input[name$="-unit_cost"]');
        var costText = row.querySelector('.field-unit_cost p, .field-unit_cost .readonly');

        if (knownCost !== undefined && knownCost !== null) {
            if (costInput) costInput.value = knownCost;
            if (costText) costText.textContent = knownCost;
            return;
        }
        fetch('/store/get-product-cost/?product_id=' + encodeURIComponent(productId))
            .then(function (response) { return response.json(); })
            .then(function (data) {
                if (!data || data.cost_price === undefined) return;
                if (costInput) costInput.value = data.cost_price;
                if (costText) costText.textContent = data.cost_price;
            })
            .catch(function (error) { console.error('Error fetching cost:', error); });
    }

    function updateProductDropdowns() {
        loadProducts('').catch(function (error) { console.error('Error loading products:', error); });
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
        if (target === codeSelect && productSelect && productSelect.value !== productId) productSelect.value = productId;
        if (target === productSelect && codeSelect && codeSelect.value !== productId) codeSelect.value = productId;
        setCost(productId, row);
    });

    document.addEventListener('DOMContentLoaded', function () {
        addSearchToolbar();
        updateProductDropdowns();
    });

    if (window.django && django.jQuery) {
        django.jQuery(document).on('formset:added', function () { addSearchToolbar(); });
    }
})();
