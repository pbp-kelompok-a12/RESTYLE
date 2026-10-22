(function () {
    "use strict";

    var form = document.getElementById("mm-form");
    if (!form) return;

    var none = form.querySelector(".mm-none");
    var chips = Array.prototype.slice.call(form.querySelectorAll(".mm-chip"));
    var items = Array.prototype.slice.call(form.querySelectorAll(".mm-item"));

    var slots = {};
    form.querySelectorAll(".mm-slot").forEach(function (el) { slots[el.dataset.slot] = el; });

    /* ---------- isi / kosongkan slot ---------- */
    function slotInput(key) { return slots[key].querySelector("input[type=hidden]"); }

    function setSlot(key, item) {
        var slot = slots[key];
        var piece = slot.querySelector(".mm-slot-piece");
        var img = piece.querySelector("img");
        var swatch = piece.querySelector(".mm-swatch");

        slotInput(key).value = item ? item.dataset.id : "";
        slot.classList.toggle("is-filled", !!item);
        piece.hidden = !item;
        slot.querySelector(".mm-slot-clear").hidden = !item;

        if (item) {
            var photo = item.dataset.photo;
            if (photo) {
                img.src = photo;
                img.alt = item.dataset.name;
                img.hidden = false;
                swatch.hidden = true;
            } else {
                img.removeAttribute("src");
                img.hidden = true;
                swatch.style.background = item.dataset.color;
                swatch.hidden = false;
            }
            piece.querySelector(".mm-slot-name").textContent = item.dataset.name;
        }
        markPicked();
    }

    function markPicked() {
        items.forEach(function (el) {
            var key = el.dataset.slot;
            el.classList.toggle("is-picked", !!slots[key] && slotInput(key).value === el.dataset.id);
        });
    }

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

    /* ---------- klik pakaian di panel kiri: masuk ke slot yang cocok ---------- */
    items.forEach(function (el) {
        el.addEventListener("click", function () {
            if (el.disabled || !slots[el.dataset.slot]) return;
            // klik lagi pakaian yang sama = lepas dari slot
            if (slotInput(el.dataset.slot).value === el.dataset.id) {
                setSlot(el.dataset.slot, null);
            } else {
                setSlot(el.dataset.slot, el);
            }
        });
    });

    /* ---------- tombol di slot ---------- */
    Object.keys(slots).forEach(function (key) {
        var slot = slots[key];
        slot.querySelector(".mm-slot-clear").addEventListener("click", function () { setSlot(key, null); });

        slot.querySelector(".mm-slot-add").addEventListener("click", function () {
            applyFilter(slot.dataset.categories.split(",")[0]);
            var panel = form.querySelector(".mm-closet");
            if (panel && window.matchMedia("(max-width: 1100px)").matches) {
                panel.scrollIntoView({ behavior: "smooth", block: "start" });
            }
        });
    });

    /* ---------- konfirmasi hapus outfit tersimpan ---------- */
    document.querySelectorAll(".mm-outfit-delete").forEach(function (deleteForm) {
        deleteForm.addEventListener("submit", function (event) {
            if (!window.confirm('Delete "' + deleteForm.dataset.confirm + '" from your saved outfits?')) {
                event.preventDefault();
            }
        });
    });

    markPicked();
})();