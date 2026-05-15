document.addEventListener("DOMContentLoaded", function () {
    const form = document.getElementById("product_form") || document.querySelector("form");
    const buttons = document.querySelectorAll('input[type="submit"]');

    function checkFields() {
        let allValid = true;

        // 1. Define the specific fields that MUST be filled
        // We use [name] to target the actual data fields
        const requiredNames = [
            'product_code', 
            'product_name_en', 
            'product_name_ar', 
            'slug', 
            'description_en', 
            'description_ar', 
            'price', 
            'stock', 
            'category'
        ];

        // 2. Check main text/select fields
        requiredNames.forEach(name => {
            const field = form.querySelector(`[name="${name}"]`);
            if (field && field.value.trim() === "") {
                allValid = false;
            }
        });

        // 3. Check the Main Image field
        // In Django admin, if an image already exists, the input might be empty 
        // but the "Clear" checkbox or preview exists. 
        // We check if it's a new form or if a file is selected.
        const imageField = form.querySelector('input[name="images"]');
        const hasExistingImage = document.querySelector('.file-upload a'); // Django's default link to existing file
        
        if (imageField && !imageField.files.length && !hasExistingImage) {
            allValid = false;
        }

        // Update button states
        buttons.forEach(btn => {
            btn.disabled = !allValid;
            // Optional: visual feedback
            btn.style.opacity = allValid ? "1" : "0.5";
            btn.style.cursor = allValid ? "pointer" : "not-allowed";
        });
    }

    // Run on input, change, and initially
    form.addEventListener("input", checkFields);
    form.addEventListener("change", checkFields);
    
    // Initial check (in case it's an "Edit" page with pre-filled data)
    checkFields();
});