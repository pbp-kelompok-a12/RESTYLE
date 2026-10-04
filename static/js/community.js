// kotak tulis post: tombol post, pilih foto, dan preview foto

const composer = document.querySelector("#composer");

if (composer) {
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