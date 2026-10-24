// Notifikasi di navbar: buka-tutup panel, dan tombol "Mark all as read".

const notificationMenu = document.querySelector(".nt-menu");

if (notificationMenu) {
    const bell = notificationMenu.querySelector(".nt-bell");
    const panel = notificationMenu.querySelector(".nt-panel");

    function setPanelOpen(isOpen) {
        panel.hidden = !isOpen;
        bell.setAttribute("aria-expanded", String(isOpen));
        // ikon lonceng penuh saat panel terbuka, garis saat tertutup
        bell.querySelector("i").className = isOpen ? "fa-solid fa-bell" : "fa-regular fa-bell";
    }

    bell.addEventListener("click", (event) => {
        event.stopPropagation(); // supaya klik ini ga dianggap "klik di luar"
        setPanelOpen(panel.hidden);
    });

    // klik di dalam panel tidak menutup panel
    panel.addEventListener("click", (event) => event.stopPropagation());

    // klik di luar panel atau tekan Escape menutup panel
    document.addEventListener("click", () => setPanelOpen(false));
    document.addEventListener("keydown", (event) => {
        if (event.key === "Escape") {
            setPanelOpen(false);
        }
    });
}

// "Mark all as read" (di panel navbar dan di halaman notifikasi): kirim tanpa memuat ulang halaman
document.querySelectorAll(".nt-mark-form").forEach((form) => {
    form.addEventListener("submit", async (event) => {
        event.preventDefault();
        const token = form.querySelector("input[name=csrfmiddlewaretoken]").value;

        try {
            const response = await fetch(form.action, {
                method: "POST",
                headers: { "X-CSRFToken": token, "X-Requested-With": "fetch" },
            });
            if (!response.ok) {
                throw new Error("Request failed");
            }

            // hapus semua tanda "belum dibaca" di halaman ini
            document.querySelectorAll(".nt-item.is-unread").forEach((item) => item.classList.remove("is-unread"));
            document.querySelectorAll(".nt-dot, .nt-badge, .nt-mark-form").forEach((element) => element.remove());
        } catch (error) {
            form.submit(); // kalau gagal, kirim dengan cara biasa (halaman dimuat ulang)
        }
    });
});