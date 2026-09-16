## Kelompok 12-A

### Anggota
| Nama | NPM |
|---|---|
|Salwa Hafiza Aqila|2506624392|
|Hasya Azzahra Rangkuti|2506617512|
|Salsabilla Hasan|2506548660|
|Aulia Nur Shiva|2506619316|
|Fadly Atief Nauval|2506624940|

### Deskripsi Aplikasi
RE:STYLE :  Sustainable Digital Wardrobe Platform

RE:STYLE adalah platform digital wardrobe yang dirancang untuk membantu pengguna, khususnya mahasiswa yang mengadopsi gaya hidup berkelanjutan melalui pengelolaan pakaian pribadi (slow fashion & conscious shopping). Di tengah maraknya tren fast fashion, kebiasaan membeli pakaian secara impulsif (impulsive buying) sering kali membuat lemari penuh, tapi kita tetap merasa tidak punya baju untuk dipakai. Banyak mahasiswa kesulitan mendata pakaian yang mereka miliki, bingung memadupadankan (mix & match) baju yang ada, atau tanpa sadar membeli pakaian baru yang modelnya mirip dengan yang sudah mereka punya. Hal ini berujung pada penumpukan limbah tekstil dan pemborosan uang.  

Sebagai digital wardrobe assistant, RE:STYLE hadir untuk mengatasi masalah tersebut melalui beberapa fitur utama:  
- Digital Closet (Wardrobe Management): Mendata dan mengelompokkan koleksi pakaian pribadi berdasarkan warna, kategori, gaya, hingga status ketersediaan (siap pakai atau sedang dicuci).  
- Mix & Match Outfit Builder: Membantu pengguna merangkai kombinasi atasan, bawahan, sepatu, dan aksesori agar pakaian yang ada bisa dipakai secara maksimal.  
- Weekly Outfit Planner: Mengatur jadwal pemakaian pakaian mingguan secara terstruktur agar tidak monoton, yang terintegrasi dengan data cuaca real-time (Open-Meteo API) untuk rekomendasi outfit harian yang sesuai kondisi cuaca.
- Conscious Shopping Reminder: Memberikan pengingat otomatis saat pengguna mau membeli baju baru yang mirip dengan koleksi di lemari, untuk mencegah pembelian impulsif.  
- Fashion Community: Ruang diskusi antarpengguna untuk saling berbagi inspirasi styling, mix and match, dan ide pakaian sehari-hari.

Aplikasi ini memberikan manfaat nyata bagi masyarakat dengan mendorong penggunaan ulang (re-use) pakaian untuk menekan limbah tekstil fast fashion, membantu efisiensi finansial melalui kontrol pembelian impulsif, serta membangun kesadaran eco-mindfulness di lingkungan mahasiswa. 



### Deskripsi Modul dan Pembagian Kerja

| Modul | Penanggung Jawab | Deskripsi | Create | Read | Update | Delete |
|---|---|---|---|---|---|---|
| **Modul 1: Digital Closet (Wardrobe Management)** | Aulia Nur Shiva | Fitur inti untuk mengelola data pakaian pengguna, lengkap dengan filter berdasarkan warna, kategori, dan style. Kategori pakaian diisi/dipilih manual oleh pengguna (bukan deteksi otomatis via AI). | Menambah data pakaian baru (nama, kategori, warna, style, material, foto, status ketersediaan). Kategori dipilih manual dari dropdown | Melihat daftar pakaian, detail satu pakaian, serta memfilter berdasarkan warna/kategori | Mengubah data pakaian yang sudah ada (termasuk mengubah status: siap pakai/sedang dicuci) | Menghapus data pakaian dari koleksi |
| **Modul 2: Mix & Match Outfit Builder** | Salwa Hafiza Aqila | Fitur untuk merangkai kombinasi outfit dari pakaian yang ada di Digital Closet (atasan, bawahan, sepatu, aksesori). | Membuat kombinasi outfit baru dari pakaian yang tersedia | Melihat daftar outfit yang sudah dibuat beserta detail kombinasinya | Mengubah/mengganti item dalam suatu kombinasi outfit | Menghapus outfit yang sudah disimpan |
| **Modul 3: Weekly Outfit Planner & Weather Recommendation** | Fadly Atief Nauval | Fitur untuk merencanakan pemakaian outfit per hari dalam kalender mingguan, terintegrasi Open-Meteo API untuk rekomendasi sesuai cuaca. Sistem otomatis mengecualikan pakaian berstatus "Laundry" dari pilihan. | Menambahkan jadwal outfit untuk hari/tanggal tertentu | Melihat jadwal mingguan serta rekomendasi outfit berdasarkan data cuaca real-time | Mengubah outfit yang dijadwalkan pada hari tertentu | Menghapus/membatalkan jadwal outfit pada hari tertentu |
| **Modul 4: Conscious Shopping Reminder & Autentikasi** | Hasya Azzahra Rangkuti | Fitur wishlist untuk mencegah pembelian impulsif, dilengkapi sistem login/logout/autentikasi pengguna. Saat item wishlist ditambahkan, sistem menampilkan pakaian di Digital Closet dengan kategori & warna yang sama sebagai pengingat. | Menambah item wishlist (nama, kategori, warna, foto/link); registrasi akun baru | Melihat daftar wishlist beserta pengingat kemiripan dari Digital Closet; login pengguna | Mengubah data item wishlist | Menghapus item wishlist; logout pengguna |
| **Modul 5: Fashion Community & Admin Panel** | Salsabilla Hasan | Forum diskusi antarpengguna untuk berbagi inspirasi styling, mix & match, dan ide pakaian sehari-hari. Modul ini juga mencakup Admin Panel: fitur moderasi yang memungkinkan Admin melihat dan menghapus post/komentar yang melanggar. | Membuat post baru (dengan foto), menambahkan komentar, memberikan rating pada outfit pengguna lain | Melihat daftar post, detail post beserta komentar dan rating; Admin dapat melihat seluruh post/komentar untuk keperluan moderasi | Mengubah post atau komentar milik sendiri | Menghapus post, komentar, atau rating milik sendiri; Admin dapat menghapus post/komentar pengguna lain yang melanggar |

### ⁠Sumber/dokumentasi Public API yang dipakai
Open-Meteo API



### Jenis dan Peran Pengguna Aplikasi

1. Pengguna (Mahasiswa)

Pengguna utama RE:STYLE adalah mahasiswa yang ingin mengelola pakaian pribadi dan menerapkan gaya hidup yang lebih berkelanjutan. Pengguna dapat:

* Mengelola koleksi pakaian pribadi melalui Digital Closet.
* Membuat dan menyimpan kombinasi outfit melalui Mix & Match Outfit Builder.
* Merencanakan penggunaan pakaian melalui Weekly Outfit Planner.
* Mendapatkan pengingat saat mempertimbangkan pembelian pakaian yang serupa dengan koleksi yang sudah dimiliki.
* Membagikan serta melihat inspirasi styling dari pengguna lain melalui Fashion Community.
* Melihat informasi cuaca untuk membantu menentukan pakaian yang sesuai.

2. Admin

Admin bertugas mengelola dan menjaga konten serta data yang terdapat pada platform. Admin dapat:

* Mengelola data dan konten yang dibagikan dalam Fashion Community.
* Memoderasi konten atau postingan pengguna.
* Mengelola data yang diperlukan agar fitur-fitur RE:STYLE dapat berjalan dengan baik.



### Link Deployment PWS
https://pws.cs.ui.ac.id/web/project/aulia.nur51/restyle



### Link Figma
https://www.figma.com/design/iyZj0ZO4xLOuL4vXyHW49w/Untitled?node-id=0-1&t=PNawZmEwwjxpivVc-1

