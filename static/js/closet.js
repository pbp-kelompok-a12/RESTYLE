(function () {
    "use strict";

    /* menu titik tiga di card */
    function closeMenus() {
        document.querySelectorAll(".cl-menu-list").forEach(function (list) {
            list.hidden = true;
            var btn = list.previousElementSibling;
            if (btn) btn.setAttribute("aria-expanded", "false");
        });
    }

    document.addEventListener("click", function (e) {
        var btn = e.target.closest(".cl-menu-button");
        if (btn) {
            var list = btn.nextElementSibling;
            var wasOpen = !list.hidden;
            closeMenus();
            list.hidden = wasOpen;
            btn.setAttribute("aria-expanded", String(!wasOpen));
            return;
        }
        if (!e.target.closest(".cl-menu-list")) closeMenus();
    });

    document.addEventListener("keydown", function (e) {
        if (e.key === "Escape") closeMenus();
    });

    /* preview foto di form */
    var photoInput = document.getElementById("photo-input");
    if (photoInput) {
        var preview = document.getElementById("photo-preview");
        var placeholder = document.getElementById("photo-placeholder");
        photoInput.addEventListener("change", function () {
            var file = photoInput.files[0];
            if (!file) return;
            preview.src = URL.createObjectURL(file);
            preview.hidden = false;
            placeholder.hidden = true;
        });
    }
})();