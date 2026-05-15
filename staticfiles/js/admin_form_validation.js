(function() {
    document.addEventListener("DOMContentLoaded", function () {
        // 1. Find the main admin form (works for any model)
        const form = document.querySelector("#content-main form") || document.querySelector("form");
        if (!form) return;

        // 2. Select all save buttons
        const submitButtons = form.querySelectorAll('input[type="submit"], button[type="submit"]');

        function validateForm() {
            let isFormValid = true;

            // 3. Find ALL required fields automatically
            // Django adds the 'required' attribute to any field that is NOT blank=True
            const requiredFields = form.querySelectorAll('input[required], select[required], textarea[required]');

            requiredFields.forEach(field => {
                // Skip fields that are hidden (like those in collapsed sections)
                if (field.offsetWidth === 0 && field.offsetHeight === 0) return;

                if (field.type === 'file') {
                    // Check if a file is uploaded OR if a link to an existing file exists
                    const hasExistingFile = field.closest('.file-upload')?.querySelector('a');
                    if (!field.files.length && !hasExistingFile) {
                        isFormValid = false;
                    }
                } else if (!field.value.trim()) {
                    isFormValid = false;
                }
            });

            // 4. Update Button State
            submitButtons.forEach(btn => {
                if (btn) {
                    btn.disabled = !isFormValid;
                    btn.style.opacity = isFormValid ? "1" : "0.5";
                    btn.style.cursor = isFormValid ? "pointer" : "not-allowed";
                }
            });
        }

        // 5. Trigger validation on any user interaction
        form.addEventListener("input", validateForm);
        form.addEventListener("change", validateForm);

        // Initial check for 'Edit' pages where data is already filled
        validateForm();
    });
})();