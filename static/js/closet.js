(function () {
    "use strict";

    var photoInput = document.getElementById("photo-input");
    if (!photoInput) return;

    var preview = document.getElementById("photo-preview");
    var placeholder = document.getElementById("photo-placeholder");

    photoInput.addEventListener("change", function () {
        var file = photoInput.files[0];
        if (!file) return;
        preview.src = URL.createObjectURL(file);
        preview.hidden = false;
        placeholder.hidden = true;
    });
})();