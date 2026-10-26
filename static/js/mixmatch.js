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

    /* ---------- Reset & Shuffle ---------- */
    form.querySelector(".mm-reset").addEventListener("click", function () {
        Object.keys(slots).forEach(function (key) { setSlot(key, null); });
    });

    form.querySelector(".mm-shuffle").addEventListener("click", function () {
        Object.keys(slots).forEach(function (key) {
            var options = items.filter(function (el) { return el.dataset.slot === key && !el.disabled; });
            if (!options.length) return;
            var current = slotInput(key).value;
            // kalau ada pilihan lain, jangan ambil yang sama dengan yang sekarang
            var others = options.filter(function (el) { return el.dataset.id !== current; });
            var pool = others.length ? others : options;
            setSlot(key, pool[Math.floor(Math.random() * pool.length)]);
        });
    });

    /* ---------- validasi sebelum submit ---------- */
    var error = document.getElementById("mm-error");

    items.forEach(function (el) {
        el.addEventListener("click", function () { error.hidden = true; });
    });

    form.addEventListener("submit", function (event) {
        var filled = Object.keys(slots).some(function (key) { return slotInput(key).value !== ""; });
        if (!filled) {
            event.preventDefault();
            error.hidden = false;
            error.scrollIntoView({ behavior: "smooth", block: "center" });
        }
    });

    /* ---------- konfirmasi hapus outfit tersimpan ---------- */
    document.querySelectorAll(".mm-outfit-delete").forEach(function (deleteForm) {
        var overlay = document.getElementById("mm-overlay");
        var modalText = document.getElementById("mm-modal-text");
        var confirmYes = document.getElementById("mm-confirm-yes");
        var pendingForm = null;

        function closeModal() {
            overlay.hidden = true;
            document.body.style.overflow = "";
            pendingForm = null;
        }

        function openConfirm(deleteForm) {
            pendingForm = deleteForm;
            modalText.textContent = '"' + deleteForm.dataset.confirm + "\" will be removed from your saved outfits. This can't be undone.";
            overlay.hidden = false;
            document.body.style.overflow = "hidden";
            overlay.querySelector(".mm-modal-cancel").focus(); 
        }

        if (overlay) {
            document.querySelectorAll(".mm-outfit-delete").forEach(function (deleteForm) {
                deleteForm.addEventListener("submit", function (event) {
                    event.preventDefault();
                    openConfirm(deleteForm);
                });
            });

            confirmYes.addEventListener("click", function () {
                var deleteForm = pendingForm;
                closeModal();
                if (deleteForm) deleteForm.submit();   
            });

            overlay.addEventListener("click", function (event) {
                if (event.target === overlay || event.target.closest("[data-close]")) closeModal();
            });

            document.addEventListener("keydown", function (event) {
                if (event.key === "Escape" && !overlay.hidden) closeModal();
            });
        }
    });

    markPicked();
})();