// Landing page: isi tiap bagian muncul pelan dari bawah (fade-up) saat mulai terlihat di layar.
// Tanpa JS atau kalau pengguna memilih "reduce motion", semuanya langsung tampil biasa.
(function () {
    const items = document.querySelectorAll(".reveal");
    const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (!items.length || reduceMotion || !("IntersectionObserver" in window)) return;

    // class ini yang menyembunyikan .reveal, jadi baru dipasang setelah JS pasti jalan
    document.documentElement.classList.add("reveal-ready");

    const observer = new IntersectionObserver((entries) => {
        entries.forEach((entry) => {
            if (entry.isIntersecting) {
                entry.target.classList.add("is-visible");
                observer.unobserve(entry.target); // cukup sekali, tidak berulang saat scroll balik
            }
        });
    }, { threshold: 0.15, rootMargin: "0px 0px -40px 0px" });

    items.forEach((item) => observer.observe(item));
})();
