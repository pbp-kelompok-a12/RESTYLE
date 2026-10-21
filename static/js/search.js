// Kotak search di navbar: menyimpan pencarian terakhir di browser
// lalu menampilkannya sebagai daftar "Recent searches".
(function () {
    const form = document.querySelector(".app-nav-search");
    const panel = form && form.querySelector(".sr-recent");
    if (!panel) return;

    const input = form.querySelector("input[name='q']");
    const clearInput = form.querySelector(".sr-clear");
    const list = panel.querySelector(".sr-recent-list");
    const STORAGE_KEY = "restyle-recent-searches";
    const MAX_ITEMS = 5;

    function load() {
        try {
            return JSON.parse(localStorage.getItem(STORAGE_KEY)) || [];
        } catch (error) {
            return [];
        }
    }

    function save(words) {
        try {
            localStorage.setItem(STORAGE_KEY, JSON.stringify(words));
        } catch (error) {
            // browser menolak menyimpan (misalnya mode private), tidak apa-apa
        }
    }

    function render() {
        const words = load();
        list.innerHTML = "";
        words.forEach(function (word) {
            const item = document.createElement("li");

            const link = document.createElement("a");
            link.href = form.action + "?q=" + encodeURIComponent(word);
            link.innerHTML = '<i class="fa-solid fa-magnifying-glass"></i>';
            link.append(document.createTextNode(word));  // aman dari HTML iseng

            const remove = document.createElement("button");
            remove.type = "button";
            remove.className = "sr-recent-remove";
            remove.setAttribute("aria-label", "Remove " + word);
            remove.innerHTML = '<i class="fa-solid fa-xmark"></i>';
            remove.addEventListener("click", function (event) {
                event.stopPropagation();
                save(load().filter(function (other) { return other !== word; }));
                render();
                input.focus();
            });

            item.append(link, remove);
            list.append(item);
        });
        panel.hidden = words.length === 0 || (document.activeElement !== input && !panel.contains(document.activeElement));
    }

    function updateClearButton() {
        clearInput.hidden = input.value === "";
    }

    input.addEventListener("focus", render);
    input.addEventListener("input", updateClearButton);

    clearInput.addEventListener("click", function () {
        input.value = "";
        updateClearButton();
        input.focus();
    });

    panel.querySelector(".sr-recent-clear").addEventListener("click", function () {
        save([]);
        render();
    });

    // simpan kata yang dicari; yang paling baru di paling atas, tanpa dobel
    form.addEventListener("submit", function (event) {
        const word = input.value.trim();
        if (!word) {
            event.preventDefault();
            return;
        }
        const words = load().filter(function (other) { return other.toLowerCase() !== word.toLowerCase(); });
        words.unshift(word);
        save(words.slice(0, MAX_ITEMS));
    });

    // tutup daftar kalau klik di luar atau tekan Esc
    document.addEventListener("click", function (event) {
        if (!form.contains(event.target)) panel.hidden = true;
    });
    form.addEventListener("keydown", function (event) {
        if (event.key === "Escape") {
            panel.hidden = true;
            input.blur();
        }
    });

    updateClearButton();
})();
