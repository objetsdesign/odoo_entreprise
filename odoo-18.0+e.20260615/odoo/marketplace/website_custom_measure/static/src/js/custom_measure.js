/* Validation côté client (min / max) du formulaire de mesures sur mesure. */
document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('.js_custom_measure_form').forEach(function (form) {
        form.addEventListener('submit', function (ev) {
            var valid = true;
            form.querySelectorAll('.js_measure_number').forEach(function (input) {
                var val = parseFloat(input.value);
                if (input.value === '') { return; }
                var min = input.getAttribute('min');
                var max = input.getAttribute('max');
                input.classList.remove('is-invalid');
                if (min !== null && min !== '' && val < parseFloat(min)) {
                    input.classList.add('is-invalid');
                    valid = false;
                }
                if (max !== null && max !== '' && val > parseFloat(max)) {
                    input.classList.add('is-invalid');
                    valid = false;
                }
            });
            if (!valid) {
                ev.preventDefault();
                alert("Certaines mesures sont hors des limites autorisées.");
            }
        });
    });
});
