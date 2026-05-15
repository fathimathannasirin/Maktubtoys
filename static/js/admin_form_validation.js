(function() {
    document.addEventListener("DOMContentLoaded", function () {
        const form = document.querySelector("#content-main form") || document.querySelector("form");
        if (!form) return;

        const submitButtons = form.querySelectorAll('input[type="submit"], button[type="submit"]');
        let nameIsUnique = true;
        let codeIsUnique = true;

        function checkUniqueness(input, fieldName) {
            const value = input.value.trim();
            if (value.length === 0) {
                resetInputState(input);
                nameIsUnique = (fieldName === 'product_name') ? true : nameIsUnique;
                codeIsUnique = (fieldName === 'product_code') ? true : codeIsUnique;
                validateForm();
                return;
            }

            const pathArray = window.location.pathname.split('/');
            const productId = !isNaN(pathArray[pathArray.length - 3]) ? pathArray[pathArray.length - 3] : '';

            // IMPROVEMENT 1: Use a relative URL so it works regardless of /en/ or /ar/
            // This ensures your fetch doesn't fail if the language changes
            const url = `/store/check-unique/?field=${fieldName}&value=${encodeURIComponent(value)}&product_id=${productId}`;

            fetch(url)
                .then(response => {
                    if (!response.ok) throw new Error("Server Error");
                    return response.json();
                })
                .then(data => {
                    resetInputState(input);
                    
                    if (data.exists) {
                        if (fieldName === 'product_name') nameIsUnique = false;
                        if (fieldName === 'product_code') codeIsUnique = false;

                        input.style.border = "2px solid red";
                        const errorMsg = document.createElement('p');
                        errorMsg.className = 'unique-error';
                        errorMsg.style.cssText = 'color: red; font-size: 11px; margin: 4px 0 0 0; font-weight: bold; display: block;';
                        errorMsg.innerText = `⚠️ This ${fieldName.replace('_', ' ')} is already taken!`;
                        input.parentNode.appendChild(errorMsg);
                    } else {
                        if (fieldName === 'product_name') nameIsUnique = true;
                        if (fieldName === 'product_code') codeIsUnique = true;
                    }
                    validateForm(); 
                })
                .catch(err => {
                    console.error("Check failed. Ensure your Django server is running.");
                });
        }

        function resetInputState(input) {
            input.style.border = "";
            const existingMsg = input.parentNode.querySelector('.unique-error');
            if (existingMsg) existingMsg.remove();
        }

        function validateForm() {
            let isFormValid = true;
            const requiredFields = form.querySelectorAll('input[required], select[required], textarea[required]');
            
            requiredFields.forEach(field => {
                if (field.offsetWidth === 0 && field.offsetHeight === 0) return;
                if (!field.value.trim()) isFormValid = false;
            });

            // If either field is not unique, the form is invalid
            if (!nameIsUnique || !codeIsUnique) isFormValid = false;

            submitButtons.forEach(btn => {
                btn.disabled = !isFormValid;
                btn.style.opacity = isFormValid ? "1" : "0.5";
                btn.style.cursor = isFormValid ? "pointer" : "not-allowed";
            });
        }

        const nameInput = document.querySelector('input[name="product_name_en"]') || 
                          document.querySelector('input[name="product_name_ar"]') || 
                          document.querySelector('input[name="product_name"]');
        const codeInput = document.querySelector('input[name="product_code"]');

        [nameInput, codeInput].forEach(input => {
            if (!input) return;

            // IMPROVEMENT 2: Change 'blur' to 'change' or use both. 
            // 'blur' triggers when you click away.
            input.addEventListener('blur', function() {
                const fieldType = input.name.includes('name') ? 'product_name' : 'product_code';
                checkUniqueness(input, fieldType);
            });

            // Re-validate general fields while typing
            input.addEventListener('input', validateForm);
        });

        form.addEventListener("input", validateForm);
        validateForm();
    });
})();