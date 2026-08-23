document.addEventListener('change', function(e) {
    // 1. Check if the changed element is the main image or a gallery image
    const isCategoryImage = e.target.name === 'image';
    const isMainImage = e.target.name === 'images';
    const isGalleryImage = e.target.name.includes('productgallery');

    if (e.target.type === 'file' && (isCategoryImage || isMainImage || isGalleryImage)) {
        const file = e.target.files[0];
        if (file) {
            // 2. Find the correct preview element
            let preview;
            
            if (isMainImage || isCategoryImage) {
                // For the main product image, look in the same fieldset
                const fieldset = e.target.closest('fieldset');
                preview = fieldset.querySelector('.admin-preview-image');
            } else {
                // For gallery rows, look in the same row (tr)
                const row = e.target.closest('tr') || e.target.closest('.form-row');
                preview = row.querySelector('.preview-img');
            }

            // 3. Update the source instantly
            if (preview) {
                preview.src = URL.createObjectURL(file);
                preview.style.display = 'block';
                
                // Optional: Hide any "No Image" text if it exists
                const label = preview.parentElement.querySelector('span');
                if (label) label.style.display = 'none';
            }
        }
    }
});