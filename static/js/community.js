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


// button "Reply" di bawah comment nampilin kotak balasan kecil
document.querySelectorAll(".cm-toggle-reply").forEach((button) => {
    const form = button.closest(".cm-comment-main").querySelector(".cm-reply-inline");

    button.addEventListener("click", () => {
        form.hidden = !form.hidden;
        if (!form.hidden) {
            form.querySelector('input[name="content"]').focus();
        }
    });
});


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

// tag closet items: buka-tutup daftar pakaian, maksimal 5, dan tampilkan jumlah yang dipilih
document.querySelectorAll(".cm-tag-toggle").forEach((button) => {
    const form = button.closest("form");
    const picker = form.querySelector(".cm-tag-picker");
    const label = button.querySelector(".cm-tag-toggle-label");
    const hint = picker.querySelector(".cm-tag-hint");
    const MAX_TAGS = 5;

    function updateTags() {
        const count = form.querySelectorAll('input[name="tagged_items"]:checked').length;
        label.textContent = count > 0 ? `Tagged (${count})` : "Tag closet items";
    }

    button.addEventListener("click", () => {
        picker.hidden = !picker.hidden;
        button.setAttribute("aria-expanded", String(!picker.hidden));
    });

    picker.addEventListener("change", (event) => {
        const checked = form.querySelectorAll('input[name="tagged_items"]:checked');
        if (checked.length > MAX_TAGS) {
            event.target.checked = false; // batalkan centang yang ke-6
            hint.textContent = `You can tag up to ${MAX_TAGS} items.`;
        } else if (hint) {
            hint.textContent = "Pick up to 5 items you're wearing.";
        }
        updateTags();
    });

    // Cancel di form edit mengembalikan centang ke keadaan awal
    form.addEventListener("reset", () => setTimeout(updateTags));

    updateTags();
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
    box.scrollIntoView({ behavior: "smooth", block: "center" });
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