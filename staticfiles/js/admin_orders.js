document.addEventListener('DOMContentLoaded', function() {
    // FIX: Ensure this variable name is consistent throughout the script
    const orderTotalField = document.querySelector('#id_order_total');
    const taxField = document.querySelector('#id_tax');

    // Lock the main totals immediately so they cannot be typed into
    if (orderTotalField) {
        orderTotalField.readOnly = true;
        orderTotalField.style.backgroundColor = "#f8f9fa"; 
    }
    if (taxField) {
        taxField.readOnly = true;
        taxField.style.backgroundColor = "#f8f9fa";
    }

    document.addEventListener('change', function(e) {
        // When a Product is selected
        if (e.target.name && e.target.name.includes('product')) {
            let row = e.target.closest('tr');
            let productId = e.target.value;
            let priceField = row.querySelector('input[name*="product_price"]');
            let variationField = row.querySelector('select[name*="variations"]');

            if (productId && priceField) {
                fetch(`/store/get-product-data/?product_id=${productId}`)
                    .then(response => response.json())
                    .then(data => {
                        // Populate the Product Price and lock it
                        priceField.value = data.price;
                        priceField.readOnly = true;
                        priceField.style.backgroundColor = "#f8f9fa";

                        // Enable variations ONLY if they exist for this product
                        if (variationField) {
                            if (data.has_variations) {
                                variationField.disabled = false;
                                variationField.style.backgroundColor = "white";
                            } else {
                                variationField.disabled = true;
                                variationField.style.backgroundColor = "#eee";
                                variationField.value = ""; 
                            }
                        }
                        calculateGrandTotal();
                    });
            }
        }

        if (e.target.name && e.target.name.includes('quantity')) {
            calculateGrandTotal();
        }
    });

    function calculateGrandTotal() {
        let total = 0;
        let rows = document.querySelectorAll('.dynamic-orderproduct_set'); 
        
        rows.forEach(row => {
            if (!row.classList.contains('empty-form')) {
                let p = parseFloat(row.querySelector('input[name*="product_price"]').value) || 0;
                let q = parseFloat(row.querySelector('input[name*="quantity"]').value) || 0;
                total += (p * q);
            }
        });

        if (orderTotalField) {
            orderTotalField.value = total.toFixed(2);
            // Example 5% tax calculation
            if (taxField) taxField.value = (total * 0.05).toFixed(2);
        }
    }
});