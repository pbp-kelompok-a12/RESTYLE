// kotak tulis post: tombol post, pilih foto, dan preview foto

const composer = document.querySelector("#composer");

if (composer && composer.querySelector("textarea")) {    
    const textarea = composer.querySelector("textarea");
    const postButton = composer.querySelector("#post-button");
    const photoButton = composer.querySelector("#photo-button");
    const photoInput = composer.querySelector("#photo-input");
    const previews = composer.querySelector("#photo-previews");
    const hint = composer.querySelector("#photo-hint");

    const MAX_PHOTOS = 3;
    let photos = []; // daftar foto yang sedang dipilih

    // tombol post baru aktif kalau sudah ada tulisan
    function updatePostButton() {
        postButton.disabled = textarea.value.trim() === "";
    }

    // kotak tulisan ikut meninggi mengikuti isinya
    function resizeTextarea() {
        textarea.style.height = "auto";
        textarea.style.height = textarea.scrollHeight + "px";
    }

    // gambar ulang preview dan menyamakan isi input file dengan daftar foto
    function showPhotos() {
        const transfer = new DataTransfer();
        photos.forEach((photo) => transfer.items.add(photo));
        photoInput.files = transfer.files;

        previews.innerHTML = "";
        photos.forEach((photo, index) => {
            const item = document.createElement("div");
            item.className = "cm-photo-preview";

            const image = document.createElement("img");
            image.src = URL.createObjectURL(photo);
            image.alt = photo.name;

            const removeButton = document.createElement("button");
            removeButton.type = "button";
            removeButton.setAttribute("aria-label", "Remove photo");
            removeButton.innerHTML = '<i class="fa-solid fa-xmark"></i>';
            removeButton.addEventListener("click", () => {
                photos.splice(index, 1);
                hint.hidden = true;
                showPhotos();
            });

            item.append(image, removeButton);
            previews.append(item);
        });

        previews.hidden = photos.length === 0;
    }

    textarea.addEventListener("input", () => {
        updatePostButton();
        resizeTextarea();
    });

    photoButton.addEventListener("click", () => photoInput.click());

    photoInput.addEventListener("change", () => {
        photos = photos.concat(Array.from(photoInput.files));

        if (photos.length > MAX_PHOTOS) {
            photos = photos.slice(0, MAX_PHOTOS);
            hint.textContent = "Up to 3 photos per post. Extra photos were left out.";
            hint.hidden = false;
        } else {
            hint.hidden = true;
        }

        showPhotos();
    });

    updatePostButton();
}


// comment: buka-tutup daftar komentar dan kotak balasan.

function setCommentsOpen(post, isOpen) {
    post.querySelector(".cm-comments").hidden = !isOpen;
    post.querySelector(".cm-toggle-comments").setAttribute("aria-expanded", String(isOpen));
}

// button "replies" di tiap post membuka atau menutup commentnya
document.querySelectorAll(".cm-post").forEach((post) => {
    const toggleButton = post.querySelector("button.cm-toggle-comments");
    if (!toggleButton) {
        return;
    }
    toggleButton.addEventListener("click", () => {
        const isOpenNow = !post.querySelector(".cm-comments").hidden;
        setCommentsOpen(post, !isOpenNow);
    });
});

// kotak reply melayang: satu kotak dipakai untuk semua tombol "Write a reply..." dan "Reply".
// Tombolnya membawa data-url (alamat kirim), data-parent (kalau membalas komentar),
// data-to (@username), dan data-quote (potongan tulisan yang dibalas).
const replyDialog = document.querySelector(".cm-reply-dialog");
if (replyDialog) {
    const replyForm = replyDialog.querySelector("form");
    const quote = replyDialog.querySelector(".cm-reply-quote");

    document.querySelectorAll(".cm-reply-open").forEach((button) => {
        button.addEventListener("click", () => {
            replyForm.reset(); // kosongkan sisa reply sebelumnya: tulisan, foto, dan tag
            replyForm.action = button.dataset.url;
            replyForm.elements.parent.value = button.dataset.parent || "";
            replyDialog.querySelector(".cm-reply-to").textContent = button.dataset.to;
            quote.textContent = button.dataset.quote;
            quote.hidden = !button.dataset.quote;
            replyDialog.showModal();
            replyForm.querySelector("textarea").focus();
        });
    });

    replyDialog.querySelector(".cm-reply-dialog-close").addEventListener("click", () => replyDialog.close());
    replyDialog.addEventListener("click", (event) => {
        if (event.target === replyDialog) replyDialog.close(); // klik di area gelap di luar kotak
    });
}

// setelah ngirim comment, alamat halaman berakhiran #post-12
// komentar post itu langsung dibuka supaya komentar barunya terlihat
if (location.hash.startsWith("#post-")) {
    const post = document.getElementById(location.hash.slice(1));
    if (post) {
        setCommentsOpen(post, true);
    }
}

// edit: tombol "Edit" menukar tulisan dengan kotak edit, "Cancel" mengembalikannya
document.querySelectorAll(".cm-toggle-edit").forEach((button) => {
    const box = button.closest(".cm-post-main, .cm-comment-main");
    const view = box.querySelector(".cm-editable");
    const form = box.querySelector(".cm-edit-form");

    function setEditing(isEditing) {
        form.hidden = !isEditing;
        view.hidden = isEditing;
        if (isEditing) {
            form.querySelector("textarea").focus();
        }
    }

    button.addEventListener("click", () => setEditing(form.hidden));
    form.querySelector(".cm-cancel-edit").addEventListener("click", () => setEditing(false));
});

// edit foto di post: tambah foto baru, tandai foto lama untuk dihapus, maksimal 3 foto
document.querySelectorAll(".cm-edit-form").forEach((form) => {
    const photoInput = form.querySelector(".cm-edit-photo-input");
    if (!photoInput) {
        return; // form edit komentar tidak punya foto
    }
    const addButton = form.querySelector(".cm-edit-add-photo");
    const newPhotos = form.querySelector(".cm-edit-new-photos");
    const hint = form.querySelector(".cm-edit-hint");
    const saveButton = form.querySelector('button[type="submit"]');
    const MAX_PHOTOS = 3;

    // gambar ulang preview foto baru dan cek jumlah foto
    function updatePhotos() {
        newPhotos.innerHTML = "";
        Array.from(photoInput.files).forEach((photo) => {
            const item = document.createElement("div");
            item.className = "cm-photo-preview";

            const image = document.createElement("img");
            image.src = URL.createObjectURL(photo);
            image.alt = photo.name;

            item.append(image);
            newPhotos.append(item);
        });

        const keptPhotos = form.querySelectorAll('input[name="remove_photos"]:not(:checked)').length;
        const total = keptPhotos + photoInput.files.length;
        const tooMany = total > MAX_PHOTOS;

        hint.textContent = tooMany
            ? `Too many photos (${total}). Remove some so there are at most ${MAX_PHOTOS}.`
            : "Tap a photo to remove it. Up to 3 photos per post.";
        saveButton.disabled = tooMany;
    }

    addButton.addEventListener("click", () => photoInput.click());
    // "change" dari input foto dan dari centang "hapus" sama-sama sampai ke form
    form.addEventListener("change", updatePhotos);
    // Cancel mengembalikan form ke keadaan awal
    form.querySelector(".cm-cancel-edit").addEventListener("click", () => {
        form.reset();
        updatePhotos();
    });
});


// foto di post: klik untuk melihat ukuran penuh, klik lagi atau tekan Escape untuk menutup
if (document.querySelector(".cm-photos img")) {
    const lightbox = document.createElement("dialog");
    lightbox.className = "cm-lightbox";
    lightbox.innerHTML = `
        <button type="button" class="cm-lightbox-close" aria-label="Close photo">
            <i class="fa-solid fa-xmark"></i>
        </button>
        <img alt="">`;
    document.body.append(lightbox);
    const lightboxImage = lightbox.querySelector("img");

    document.querySelectorAll(".cm-photos img").forEach((photo) => {
        photo.addEventListener("click", () => {
            lightboxImage.src = photo.src;
            lightboxImage.alt = photo.alt;
            lightbox.showModal();
        });
    });

    lightbox.addEventListener("click", () => lightbox.close());
}

// tag closet items: pop-up "Tag from my closet" dengan pencarian, filter kategori, dan maksimal 5 pilihan.
// Pakaian yang dipilih tampil sebagai chip di form, dan chip bisa dihapus dengan tanda x.
document.querySelectorAll(".cm-tag-toggle").forEach((button) => {
    const form = button.closest("form");
    const dialog = form.querySelector(".cm-closet-dialog");
    const selected = form.querySelector(".cm-tag-selected");
    const label = button.querySelector(".cm-tag-toggle-label");
    const boxes = Array.from(form.querySelectorAll('input[name="tagged_items"]'));
    const count = dialog.querySelector(".cm-closet-count");
    const search = dialog.querySelector(".cm-closet-search input");
    const filters = dialog.querySelectorAll(".cm-closet-filter");
    const noMatch = dialog.querySelector(".cm-closet-none");
    const MAX_TAGS = 5;
    let category = "";
    let checkedWhenOpened = []; // untuk mengembalikan pilihan kalau pop-up ditutup tanpa "Add to post"

    function checkedBoxes() {
        return boxes.filter((box) => box.checked);
    }

    // chip pakaian terpilih di bawah kotak tulisan
    function showSelected() {
        selected.innerHTML = "";
        checkedBoxes().forEach((box) => {
            const chip = document.createElement("span");
            chip.className = "cm-tag";
            if (box.dataset.photo) {
                const photo = document.createElement("img");
                photo.src = box.dataset.photo;
                photo.alt = "";
                chip.append(photo);
            } else {
                const dot = document.createElement("span");
                dot.className = "cm-tag-dot";
                dot.style.backgroundColor = box.dataset.color;
                chip.append(dot);
            }
            chip.append(document.createTextNode(box.dataset.name));

            const remove = document.createElement("button");
            remove.type = "button";
            remove.className = "cm-tag-remove";
            remove.setAttribute("aria-label", `Remove ${box.dataset.name}`);
            remove.innerHTML = '<i class="fa-solid fa-xmark"></i>';
            remove.addEventListener("click", () => {
                box.checked = false;
                updateTags();
            });
            chip.append(remove);
            selected.append(chip);
        });
    }

    function updateTags() {
        const total = checkedBoxes().length;
        label.textContent = total > 0 ? `Tagged (${total})` : "Tag closet items";
        if (count) {
            count.textContent = `${total} selected · max ${MAX_TAGS}`;
            count.classList.remove("is-full");
        }
        showSelected();
    }

    // sembunyikan pakaian yang tidak cocok dengan kata yang dicari dan kategori yang dipilih
    function filterItems() {
        const word = search ? search.value.trim().toLowerCase() : "";
        let shown = 0;
        boxes.forEach((box) => {
            const item = box.closest(".cm-closet-item");
            const match = item.dataset.name.includes(word) && (!category || item.dataset.category === category);
            item.hidden = !match;
            if (match) shown += 1;
        });
        if (noMatch) noMatch.hidden = shown > 0;
    }

    button.addEventListener("click", () => {
        checkedWhenOpened = checkedBoxes();
        dialog.showModal();
    });

    dialog.addEventListener("change", (event) => {
        if (checkedBoxes().length > MAX_TAGS) {
            event.target.checked = false; // batalkan centang yang ke-6
            count.textContent = `You can tag up to ${MAX_TAGS} items.`;
            count.classList.add("is-full");
            return;
        }
        updateTags();
    });

    if (search) {
        search.addEventListener("input", filterItems);
    }

    filters.forEach((filter) => {
        filter.addEventListener("click", () => {
            category = filter.dataset.category;
            filters.forEach((other) => other.classList.toggle("is-active", other === filter));
            filterItems();
        });
    });

    // "Add to post" menyimpan pilihan; tombol x, Esc, atau klik di luar pop-up membatalkannya
    const done = dialog.querySelector(".cm-closet-done");
    if (done) {
        done.addEventListener("click", () => dialog.close("done"));
    }
    dialog.querySelector(".cm-closet-close").addEventListener("click", () => dialog.close());
    dialog.addEventListener("click", (event) => {
        if (event.target === dialog) dialog.close(); // klik di area gelap di luar kotak
    });
    dialog.addEventListener("close", () => {
        if (dialog.returnValue !== "done") {
            boxes.forEach((box) => {
                box.checked = checkedWhenOpened.includes(box);
            });
        }
        dialog.returnValue = "";
        updateTags();
    });

    // Cancel di form edit mengembalikan centang ke keadaan awal
    form.addEventListener("reset", () => setTimeout(updateTags));

    updateTags();
});

// foto di reply: satu foto JPG/PNG (maksimal 5 MB), tampil kecil sebelum dikirim dan bisa dibatalkan
document.querySelectorAll(".cm-reply-rich").forEach((form) => {
    const input = form.querySelector(".cm-reply-photo-input");
    const button = form.querySelector(".cm-reply-photo-button");
    const preview = form.querySelector(".cm-reply-photo-preview");
    const previewImage = preview.querySelector("img");
    const hint = form.querySelector(".cm-reply-photo-hint");
    const MAX_SIZE = 5 * 1024 * 1024;

    function clearPhoto() {
        input.value = "";
        preview.hidden = true;
        button.classList.remove("has-photo");
    }

    button.addEventListener("click", () => input.click());

    input.addEventListener("change", () => {
        const photo = input.files[0];
        hint.hidden = true;
        if (!photo) {
            clearPhoto();
            return;
        }
        if (!["image/jpeg", "image/png"].includes(photo.type) || photo.size > MAX_SIZE) {
            hint.textContent = "Photos must be JPG or PNG, 5 MB or smaller.";
            hint.hidden = false;
            clearPhoto();
            return;
        }
        previewImage.src = URL.createObjectURL(photo);
        preview.hidden = false;
        button.classList.add("has-photo");
    });

    preview.querySelector(".cm-reply-photo-remove").addEventListener("click", clearPhoto);
    form.addEventListener("reset", () => {
        clearPhoto();
        hint.hidden = true;
    });
});


// tag di post: klik untuk melihat detail pakaiannya (bisa dilihat semua orang)
if (document.querySelector(".cm-tag-button")) {
    const itemDialog = document.createElement("dialog");
    itemDialog.className = "cm-item-dialog";
    itemDialog.innerHTML = `
        <button type="button" class="cm-item-close" aria-label="Close">
            <i class="fa-solid fa-xmark"></i>
        </button>
        <img class="cm-item-photo" alt="">
        <span class="cm-item-swatch"></span>
        <h3 class="cm-item-name"></h3>
        <dl class="cm-item-info"></dl>
        <a class="cm-item-link" href="#">Open in my closet</a>`;
    document.body.append(itemDialog);

    const photo = itemDialog.querySelector(".cm-item-photo");
    const swatch = itemDialog.querySelector(".cm-item-swatch");
    const info = itemDialog.querySelector(".cm-item-info");
    const closetLink = itemDialog.querySelector(".cm-item-link");

    document.querySelectorAll(".cm-tag-button").forEach((button) => {
        button.addEventListener("click", () => {
            const item = button.dataset; // isi dari atribut data-... di tombolnya

            // pakai foto kalau ada, kalau tidak tampilkan kotak warnanya
            photo.hidden = !item.photo;
            photo.src = item.photo;
            photo.alt = item.name;
            swatch.hidden = Boolean(item.photo);
            swatch.style.backgroundColor = item.colorHex;

            itemDialog.querySelector(".cm-item-name").textContent = item.name;

            info.innerHTML = "";
            const rows = [
                ["Category", item.category],
                ["Color", item.color],
                ["Material", item.material],
                ["Style", item.styles],
            ];
            rows.forEach(([label, value]) => {
                if (!value) {
                    return; // lewati data yang kosong
                }
                const term = document.createElement("dt");
                term.textContent = label;
                const detail = document.createElement("dd");
                detail.textContent = value;
                info.append(term, detail);
            });

            // link ke closet hanya muncul untuk pemilik pakaiannya
            closetLink.hidden = !item.closetUrl;
            closetLink.href = item.closetUrl || "#";

            itemDialog.showModal();
        });
    });

    itemDialog.querySelector(".cm-item-close").addEventListener("click", () => itemDialog.close());
    // klik di latar gelap (di luar kotak) juga menutup
    itemDialog.addEventListener("click", (event) => {
        if (event.target === itemDialog) {
            itemDialog.close();
        }
    });
}

// foto profil: begitu foto dipilih, langsung dikirim (tanpa perlu tombol Save)
document.querySelectorAll(".community-avatar-form input[type=file]").forEach((input) => {
    input.addEventListener("change", () => {
        if (input.files.length > 0) {
            input.form.submit();
        }
    });
});

// Hapus: tanya dulu sebelum benar-benar menghapus
document.querySelectorAll("form[data-confirm]").forEach((form) => {
    form.addEventListener("submit", (event) => {
        if (!confirm(form.dataset.confirm)) {
            event.preventDefault();
        }
    });
});


// Menu titik tiga: buka-tutup, dan tutup otomatis saat klik di luar atau tekan Escape.
function closeAllMenus() {
    document.querySelectorAll(".cm-menu-list").forEach((list) => {
        list.hidden = true;
    });
    document.querySelectorAll(".cm-menu-button").forEach((button) => {
        button.setAttribute("aria-expanded", "false");
    });
}

document.querySelectorAll(".cm-menu").forEach((menu) => {
    const button = menu.querySelector(".cm-menu-button");
    const list = menu.querySelector(".cm-menu-list");

    button.addEventListener("click", (event) => {
        event.stopPropagation(); // supaya klik ini ga dianggap "klik di luar"
        const willOpen = list.hidden;
        closeAllMenus();
        list.hidden = !willOpen;
        button.setAttribute("aria-expanded", String(willOpen));
    });
});

document.addEventListener("click", closeAllMenus);

document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") {
        closeAllMenus();
    }
});

// Like dan Save: kirim ke server tanpa memuat ulang halaman, lalu perbarui tombolnya.
document.querySelectorAll("button.cm-react").forEach((button) => {
    button.addEventListener("click", async () => {
        if (button.dataset.loginUrl) {
            window.location.assign(button.dataset.loginUrl);
            return;
        }

        const token = button.closest(".cm-post").querySelector("input[name=csrfmiddlewaretoken]").value;

        try {
            const response = await fetch(button.dataset.url, {
                method: "POST",
                headers: { "X-CSRFToken": token },
            });
            const result = await response.json();

            button.classList.toggle("is-active", result.active);

            const count = button.querySelector(".cm-count");
            if (count) {
                count.textContent = result.count;
            }

            const saveLabel = button.querySelector(".cm-save-label");
            if (saveLabel) {
                saveLabel.textContent = result.active ? "Saved" : "Save";
            }
        } catch (error) {
            alert("Something went wrong. Please refresh the page and try again.");
        }
    });
});

// Tombol "New post" dan "Post": gulir ke kotak tulis post dan langsung siap mengetik.
function focusComposer() {
    const box = document.querySelector("#composer");
    if (!box) {
        return false; // halaman ini tidak punya kotak tulis post
    }
    box.scrollIntoView({ behavior: "smooth", block: "start" });
    box.querySelector("textarea").focus({ preventScroll: true });
    return true;
}

document.querySelectorAll('a[href$="#composer"]').forEach((link) => {
    link.addEventListener("click", (event) => {
        if (focusComposer()) {
            event.preventDefault();
        }
    });
});

// Datang dari tombol "Ask the community" (alamatnya /community/?ask=...):
// langsung gulir ke kotak tulis post dengan kursor di akhir tulisan, siap mengetik.
if (new URLSearchParams(window.location.search).has("ask") && focusComposer()) {
    const textarea = document.querySelector("#composer textarea");
    textarea.setSelectionRange(textarea.value.length, textarea.value.length);
    textarea.dispatchEvent(new Event("input")); // tombol Post aktif dan tinggi kotak menyesuaikan isi
}

// Datang dari halaman lain dengan alamat berakhiran #composer (misalnya tombol "Ask the community"):
// langsung gulir ke kotak tulis post dengan kursor di akhir tulisan, siap mengetik.
// Ditunggu sampai halaman selesai dimuat, karena browser sendiri melompat ke #composer
// di akhir pemuatan dan lompatan itu menghapus fokus yang dipasang lebih awal.
window.addEventListener("load", () => {
    if (window.location.hash !== "#composer" || !focusComposer()) {
        return;
    }
    const textarea = document.querySelector("#composer textarea");
    textarea.setSelectionRange(textarea.value.length, textarea.value.length);
    textarea.dispatchEvent(new Event("input")); // tombol Post aktif dan tinggi kotak menyesuaikan isi
});

// Follow: kirim ke server tanpa memuat ulang halaman, lalu ubah tombolnya.
document.querySelectorAll(".cm-follow").forEach((button) => {
    button.addEventListener("click", async () => {
        if (button.dataset.loginUrl) {
            window.location.assign(button.dataset.loginUrl);
            return;
        }

        const token = document.querySelector("input[name=csrfmiddlewaretoken]").value;

        try {
            const response = await fetch(button.dataset.url, {
                method: "POST",
                headers: { "X-CSRFToken": token },
            });
            const result = await response.json();

            const wasFollowing = button.classList.contains("is-active");
            button.classList.toggle("is-active", result.active);
            button.classList.toggle("primary-btn", result.active);
            button.classList.toggle("tertiary-btn", !result.active);
            button.querySelector(".cm-follow-label").textContent = result.active ? "Following" : "Follow";
            const followersCount = document.querySelector("[data-followers-count]");
            if (followersCount && wasFollowing !== result.active) {
                const count = Number(followersCount.textContent);
                followersCount.textContent = String(count + (result.active ? 1 : -1));
            }
        } catch (error) {
            alert("Something went wrong. Please refresh the page and try again.");
        }
    });
});