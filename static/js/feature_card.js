// Feature card: panel detail naik saat card disorot mouse (atau difokus lewat keyboard).
// Di layar sentuh yang tidak punya hover, tombol panah tetap dipakai untuk buka / tutup.
(function () {
    const canHover = window.matchMedia("(hover: hover) and (pointer: fine)");

    document.querySelectorAll(".fc-card").forEach((card) => {
        const toggle = card.querySelector(".fc-toggle");

        function setOpen(isOpen) {
            card.classList.toggle("is-open", isOpen);
            toggle.setAttribute("aria-expanded", String(isOpen));
            toggle.setAttribute("aria-label", isOpen ? "Hide details" : "Show details");
        }

        // hanya fokus dari keyboard (Tab) yang dihitung, bukan fokus akibat klik / ketukan
        function hasKeyboardFocus() {
            return Boolean(card.querySelector(":focus-visible"));
        }

        card.addEventListener("mouseenter", () => {
            if (canHover.matches) setOpen(true);
        });
        card.addEventListener("mouseleave", () => {
            if (canHover.matches && !hasKeyboardFocus()) setOpen(false);
        });

        card.addEventListener("focusin", () => {
            if (hasKeyboardFocus()) setOpen(true);
        });
        card.addEventListener("focusout", (event) => {
            if (!card.contains(event.relatedTarget) && !card.matches(":hover")) setOpen(false);
        });

        toggle.addEventListener("click", () => {
            if (canHover.matches) return; // dengan mouse, card sudah terbuka lewat hover
            setOpen(!card.classList.contains("is-open"));
        });
    });
})();
