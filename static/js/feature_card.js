// Feature card: tombol panah menaikkan / menurunkan panel detail.
document.querySelectorAll(".fc-card").forEach((card) => {
    const toggle = card.querySelector(".fc-toggle");

    toggle.addEventListener("click", () => {
        const isOpen = card.classList.toggle("is-open");
        toggle.setAttribute("aria-expanded", String(isOpen));
        toggle.setAttribute("aria-label", isOpen ? "Hide details" : "Show details");
    });
});