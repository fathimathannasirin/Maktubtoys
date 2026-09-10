(function () {
    'use strict';

    document.addEventListener('click', function (event) {
        var trigger = event.target.closest('.sidebar-pin-trigger');
        var dropdowns = document.querySelectorAll('.sidebar-pin-dropdown');

        dropdowns.forEach(function (dropdown) {
            if (!trigger || !trigger.parentElement.contains(dropdown)) dropdown.hidden = true;
        });

        if (trigger) {
            var dropdown = trigger.parentElement.querySelector('.sidebar-pin-dropdown');
            dropdown.hidden = !dropdown.hidden;
            trigger.setAttribute('aria-expanded', String(!dropdown.hidden));
            event.preventDefault();
            event.stopPropagation();
        }
    });
})();
