(function () {
    'use strict';

    function lookupConfig() {
        var meta = document.querySelector('meta[name="warehousing-product-lookup"]');
        return {
            url: meta ? meta.getAttribute('content') : '',
            returnable: meta ? meta.getAttribute('data-returnable') === '1' : /\/return\//.test(window.location.pathname),
        };
    }

    function fieldValue(name) {
        var select = document.querySelector('select[name="' + name + '"]');
        if (select && select.value) return select.value;
        var input = document.querySelector('input[name="' + name + '"]');
        if (input && input.value) return input.value;
        var byId = document.getElementById('id_' + name);
        return byId && byId.value ? byId.value : '';
    }

    function lookupUrl(searchTerm) {
        var config = lookupConfig();
        var url = config.url || window.location.pathname.replace(/\/(?:add|(?:\d+)\/change)\/?$/, '/lookup-products/');
        var params = new URLSearchParams({
            supplier_id: fieldValue('supplier'),
            warehouse_id: fieldValue('warehouse'),
            q: searchTerm || '',
        });
        if (config.returnable) params.set('returnable', '1');
        return url + (url.indexOf('?') === -1 ? '?' : '&') + params.toString();
    }

    function loadProducts(searchTerm) {
        return fetch(lookupUrl(searchTerm), { credentials: 'same-origin' })
            .then(function (response) { return response.json(); })
            .then(function (data) { return data.products || []; });
    }

    function inlineRows() {
        return Array.from(document.querySelectorAll('.tabular tbody tr')).filter(function (row) {
            if (row.classList.contains('empty-form') || row.classList.contains('add-row')) return false;
            var deleted = row.querySelector('input[name$="-DELETE"]');
            return !deleted || !deleted.checked;
        });
    }

    function firstEmptyRow() {
        return inlineRows().find(function (row) {
            var product = row.querySelector('select[name$="-product"], select[name$="-product_code"]');
            return product && !product.value;
        });
    }

    function addInlineRow() {
        var addLink = document.querySelector('.add-row a');
        if (addLink) addLink.click();
    }

    function setSelectValue(select, value, label) {
        if (!select || !value) return;
        var option = Array.from(select.options).find(function (item) {
            return String(item.value) === String(value);
        });
        if (!option) {
            option = new Option(label, value, true, true);
            select.add(option);
        }
        select.value = String(value);
        if (window.django && django.jQuery) {
            django.jQuery(select).val(String(value)).trigger('change');
        } else {
            select.dispatchEvent(new Event('change', { bubbles: true }));
        }
    }

    function setCost(row, cost) {
        if (!row) return;
        var costInput = row.querySelector('input[name$="-unit_cost"]');
        var costText = row.querySelector('.field-unit_cost p, .field-unit_cost .readonly');
        var value = cost === undefined || cost === null ? '' : cost;
        if (costInput) costInput.value = value;
        if (costText) costText.textContent = value;
    }

    function setQuantity(row, quantity) {
        var quantityInput = row.querySelector('input[name$="-quantity"]');
        if (quantityInput && (!quantityInput.value || Number(quantityInput.value) === 0)) {
            quantityInput.value = quantity;
        }
    }

    function selectProduct(product) {
        var already = inlineRows().some(function (row) {
            var productSelect = row.querySelector('select[name$="-product"]');
            return productSelect && String(productSelect.value) === String(product.id);
        });
        if (already) return;

        var row = firstEmptyRow();
        if (!row) {
            addInlineRow();
            row = firstEmptyRow();
        }
        if (!row) return;

        var codeSelect = row.querySelector('select[name$="-product_code"]');
        var productSelect = row.querySelector('select[name$="-product"]');
        setSelectValue(codeSelect, product.id, product.code || product.name);
        setSelectValue(productSelect, product.id, product.name);
        setQuantity(row, 1);
        setCost(row, product.cost_price);
    }

    function renderResults(toolbar, products, message) {
        var results = toolbar.querySelector('.product-search-results');
        results.innerHTML = '';
        if (!products.length) {
            if (message) {
                var empty = document.createElement('div');
                empty.className = 'product-search-result';
                empty.textContent = message;
                results.appendChild(empty);
                results.hidden = false;
                return;
            }
            results.hidden = true;
            return;
        }
        products.forEach(function (product) {
            var result = document.createElement('button');
            result.type = 'button';
            result.className = 'product-search-result';
            result.innerHTML = '<strong></strong><span></span><em></em>';
            result.querySelector('strong').textContent = product.code || '';
            result.querySelector('span').textContent = product.name || '';
            result.querySelector('em').textContent = 'Cost: ' + (product.cost_price || 0);
            result.addEventListener('click', function () {
                selectProduct(product);
                results.hidden = true;
            });
            results.appendChild(result);
        });
        results.hidden = false;
    }

    function addSearchToolbar() {
        var inlineGroup = Array.from(document.querySelectorAll('.inline-group')).find(function (group) {
            return group.querySelector('[name$="-product"], [name$="-product_code"]');
        });
        if (!inlineGroup || inlineGroup.querySelector('.product-inline-search')) return;

        var toolbar = document.createElement('div');
        toolbar.className = 'product-inline-search';
        toolbar.innerHTML =
            '<div class="product-search-input-wrap">' +
            '<input type="search" placeholder="Type a product name or code" autocomplete="off" aria-label="Search products">' +
            '<div class="product-search-results" hidden></div>' +
            '</div>' +
            '<button type="button" class="search-button">Search</button>' +
            '<button type="button" class="clear-search">Clear</button>';
        var table = inlineGroup.querySelector('.tabular');
        inlineGroup.insertBefore(toolbar, table || inlineGroup.firstChild);

        var input = toolbar.querySelector('input');
        var timer;
        var search = function () {
            var term = input.value.trim();
            if (!term) {
                toolbar.querySelector('.product-search-results').hidden = true;
                return;
            }
            if (!fieldValue('supplier')) {
                renderResults(toolbar, [], 'Select a supplier first, then type to search that supplier\'s products.');
                return;
            }
            loadProducts(term).then(function (products) {
                renderResults(
                    toolbar,
                    products,
                    products.length ? '' : 'No products found for this supplier.'
                );
            }).catch(function (error) {
                console.error('Error searching products:', error);
            });
        };

        toolbar.querySelector('.search-button').addEventListener('click', search);
        input.addEventListener('input', function () {
            clearTimeout(timer);
            timer = setTimeout(search, 120);
        });
        input.addEventListener('focus', function () {
            if (input.value.trim()) search();
        });
        toolbar.querySelector('.clear-search').addEventListener('click', function () {
            input.value = '';
            toolbar.querySelector('.product-search-results').hidden = true;
        });
        input.addEventListener('keydown', function (event) {
            if (event.key === 'Enter') {
                event.preventDefault();
                search();
            }
        });
        document.addEventListener('click', function (event) {
            if (!toolbar.contains(event.target)) toolbar.querySelector('.product-search-results').hidden = true;
        });
    }

    document.addEventListener('change', function (event) {
        var target = event.target;
        if (!target || !target.name) return;
        var row = target.closest('tr') || target.closest('.form-row');
        if (!row || !target.matches('select[name$="-product_code"], select[name$="-product"]')) return;
        var codeSelect = row.querySelector('select[name$="-product_code"]');
        var productSelect = row.querySelector('select[name$="-product"]');
        var productId = target.value;
        if (target === codeSelect && productSelect && productSelect.value !== productId) {
            productSelect.value = productId;
        }
        if (target === productSelect && codeSelect && codeSelect.value !== productId) {
            codeSelect.value = productId;
        }
        if (!productId) return;
        var params = new URLSearchParams({
            supplier_id: fieldValue('supplier'),
            warehouse_id: fieldValue('warehouse'),
            product_id: productId,
        });
        if (lookupConfig().returnable) params.set('returnable', '1');
        var base = lookupConfig().url || lookupUrl('').split('?')[0];
        fetch(base + '?' + params.toString(), { credentials: 'same-origin' })
            .then(function (response) { return response.json(); })
            .then(function (data) {
                var match = (data.products || []).find(function (item) { return String(item.id) === String(productId); });
                if (match) {
                    setCost(row, match.cost_price);
                    setQuantity(row, 1);
                }
            })
            .catch(function (error) { console.error('Error fetching cost:', error); });
    });

    document.addEventListener('DOMContentLoaded', addSearchToolbar);
    if (window.django && django.jQuery) {
        django.jQuery(document).on('formset:added', addSearchToolbar);
    }
})();
