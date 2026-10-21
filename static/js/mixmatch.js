(function () {
    "use strict";

    var form = document.getElementById("mm-form");
    if (!form) return;

    var none = form.querySelector(".mm-none");
    var chips = Array.prototype.slice.call(form.querySelectorAll(".mm-chip"));
    var items = Array.prototype.slice.call(form.querySelectorAll(".mm-item"));

    /* ---------- filter kategori ---------- */
    function applyFilter(category) {
        var shown = 0;
        chips.forEach(function (chip) {
            chip.classList.toggle("is-active", chip.dataset.category === category);
        });
        items.forEach(function (el) {
            var match = !category || el.dataset.category === category;
            el.hidden = !match;
            if (match) shown += 1;
        });
        if (none) none.hidden = shown !== 0;
    }

    chips.forEach(function (chip) {
        chip.addEventListener("click", function () { applyFilter(chip.dataset.category); });
    });
})();