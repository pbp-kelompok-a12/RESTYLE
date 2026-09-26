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