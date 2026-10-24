Marquee3k.init();

const navToggle = document.querySelector(".nav-toggle");
const siteHeader = document.querySelector(".site-header");

if (navToggle && siteHeader) {
    navToggle.addEventListener("click", () => {
        const isOpen = siteHeader.classList.toggle("nav-open");
        navToggle.setAttribute("aria-expanded", isOpen);
        navToggle.innerHTML = isOpen
            ? '<i class="fa-solid fa-xmark"></i>'
            : '<i class="fa-solid fa-bars"></i>';
    });

    document.querySelectorAll(".nav-act a").forEach((link) => {
        link.addEventListener("click", () => {
            siteHeader.classList.remove("nav-open");
            navToggle.setAttribute("aria-expanded", "false");
            navToggle.innerHTML = '<i class="fa-solid fa-bars"></i>';
        });
    });
}

const appNav = document.querySelector(".app-nav");
const appNavToggle = document.querySelector(".app-nav-toggle");

if (appNav && appNavToggle) {
    const setNavOpen = (isOpen) => {
        appNav.classList.toggle("nav-open", isOpen);
        appNavToggle.setAttribute("aria-expanded", String(isOpen));
        appNavToggle.setAttribute("aria-label", isOpen ? "Close menu" : "Open menu");
        appNavToggle.innerHTML = isOpen
            ? '<i class="fa-solid fa-xmark"></i>'
            : '<i class="fa-solid fa-bars"></i>';
    };

    appNavToggle.addEventListener("click", () => setNavOpen(!appNav.classList.contains("nav-open")));
    document.querySelectorAll(".app-nav-links a").forEach((link) => {
        link.addEventListener("click", () => setNavOpen(false));
    });
    document.addEventListener("keydown", (e) => { if (e.key === "Escape") setNavOpen(false); });
}