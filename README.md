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
| **Modul 1: Digital Closet (Wardrobe Management)** | Aulia Nur Shiva | Fitur inti untuk mengelola data pakaian pengguna, lengkap dengan filter berdasarkan warna, kategori, dan style. Kategori pakaian diisi/dipilih manual oleh pengguna (bukan deteksi otomatis via AI). | Menambah data pakaian baru (nama, kategori, warna, style, material, foto, status ketersediaan). Kategori dipilih manual dari dropdown | Melihat daftar pakaian, detail satu pakaian, serta memfilter berdasarkan warna/kategori | Mengubah data (mengedit) pakaian yang sudah ada | Menghapus data pakaian dari koleksi |
| **Modul 2: Mix & Match Outfit Builder** | Salwa Hafiza Aqila | Fitur untuk merangkai kombinasi outfit dari pakaian yang ada di Digital Closet (atasan, bawahan, sepatu, aksesori). | Membuat kombinasi outfit baru dari pakaian yang tersedia | Melihat daftar outfit yang sudah dibuat beserta detail kombinasinya | Mengubah/mengganti item dalam suatu kombinasi outfit | Menghapus outfit yang sudah disimpan |
| **Modul 3: Weekly Outfit Planner & Weather Recommendation** | Fadly Atief Nauval | Fitur untuk merencanakan pemakaian outfit per hari dalam kalender mingguan, terintegrasi Open-Meteo API untuk rekomendasi sesuai cuaca berdasarkan lokasi menggunakan OpenStreetMap dengan pengolahan datanya melalui Nominatim. Sistem otomatis mengecualikan pakaian berstatus "Laundry" dari pilihan. | Menambahkan jadwal outfit untuk hari/tanggal tertentu | Melihat jadwal mingguan serta rekomendasi outfit berdasarkan data cuaca real-time | Mengubah outfit yang dijadwalkan pada hari tertentu | Menghapus/membatalkan jadwal outfit pada hari tertentu |
| **Modul 4: Conscious Shopping Reminder & Autentikasi** | Hasya Azzahra Rangkuti | Fitur wishlist interaktif untuk mencegah pembelian impulsif melalui pengingat *Conscious Shopping*. Sistem otomatis mendeteksi kemiripan barang di Digital Closet berdasarkan kategori dan warna (baik saat menambah item di Wishlist maupun saat menyimpan pakaian dari Community). Dilengkapi pop-up peringatan *Conscious Alert* ber-maskot bunglon, *deep-linking* terfilter langsung ke Closet, modal detail interaktif, serta sistem login/logout/autentikasi pengguna. | Menambah item wishlist (nama, foto, kategori, warna, bahan, *style tags*, *season*, *weather*, brand, harga, *purchase link*, *target purchase date*); registrasi akun baru; menambah item ke wishlist langsung dari Community. | Melihat daftar wishlist; statistik *Closest Matches*; modal *view detail* dengan *chip* barang mirip yang bisa diklik untuk *redirect* langsung ke Digital Closet; *filter bar* dinamis (*search*, warna, *style*, *season*, *weather*, *status*); pop-up pengingat *Conscious Alert*; login pengguna. | Mengubah data item wishlist melalui modal *edit* (beserta pembaruan foto dan format harga real-time). | Menghapus item wishlist melalui modal konfirmasi; membatalkan/menghapus item dari wishlist; logout pengguna. |
| **Modul 5: Fashion Community** | Salsabilla Hasan | Forum diskusi antarpengguna untuk berbagi inspirasi styling, mix & match, dan ide pakaian sehari-hari. | Membuat post baru (dengan foto), menambahkan komentar, memberikan like pada outfit pengguna lain | Melihat daftar post, detail post beserta komentar dan like | Mengubah post atau komentar milik sendiri | Menghapus post, komentar, atau like milik sendiri |
| **Modul 6: Admin Panel (Moderasi Konten)** | Dikerjakan bersama (seluruh anggota kelompok) | Fitur moderasi yang memungkinkan Admin menjaga kualitas Fashion Community dengan melihat dan menghapus post/komentar yang melanggar aturan. | Admin membuat akun/hak akses admin dan mengelola konten melalui panel khusus | Admin melihat seluruh post dan komentar pengguna untuk keperluan moderasi | Admin meninjau dan menandai konten yang melanggar | Admin menghapus post/komentar pengguna lain yang melanggar |

## Fitur tambahan community
1. Search: mencari post atau pengguna berdasarkan teks, nama, atau item Digital Closet yang ditandai.
2. Notifications: pemberitahuan untuk like, balasan, follow, dan mention.
3. Saved posts: menyimpan post sebagai inspirasi dan melihatnya di halaman tersendiri.
4. Follow dan profil pengguna: mengikuti pengguna, melihat profil, serta daftar followers/following.
5. Tag item Digital Closet di post dan balasan.
6. Mention @username: saran username, tautan mention, dan notifikasi mention.
7. Foto pada balasan, selain foto di post.
8. Foto profil khusus Community.

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

### Penggunaan AI dan Sumber Eksternal

1. Modul 1: Digital Closet (Wardrobe Management) - Aulia Nur Shiva

Dalam pengembangan modul Digital Closet, saya menggunakan AI (Claude dan ChatGPT) sebagai alat bantu selama proses implementasi dan pengembangan fitur, terutama pada bagian JavaScript dan penyempurnaan interface.

Pada awalnya, implementasi fitur Digital Closet mengacu pada tutorial PBP yang mancakup fitur mirip/serupa, seperti menambahkan, mengedit, mencari item. Implementasi awal form yang saya gunakan yaitu menggunakan halaman form terpisah. Namun, untuk membuat interaksi yang lebih nyaman bagi user, saya mengeksplorasi penggunakan popup atau modal sebagai alternatif. Dalam proses ini, saya mencari sumber eksternal yaitu YouTube dan menggunakan AI untuk membantu memberikan arahan mengenai implementasi ini serta membantu penulisan dan penyesuaian kode JavaScript yang diperlukan.

Selain itu, saya mengimplementasikan AJAX untuk mendukung interaksi pada Digital Closet agar beberapa proses dapat dilakukan tanpa perlu memuat ulang seluruh halaman. Dalam proses implementasi AJAX, AI digunakan untuk membantu saya menyusun kode JavaScript yang diperlukan.

AI juga digunakan sebagai alat bantu dalam menyelesaikan detail interface, seperti penyesuaian format tampilan nominal harga menggunakan pemisah ribuan. 

Sumber eksternal:
- https://youtu.be/xKOyDDuQSVY?si=NGuyf6DxNCOUbiRZ 
- https://youtu.be/MBaw_6cPmAw?si=fz7_QdNRE3GoHkss
- https://youtu.be/4pSPWkrd-1M?si=dMmcVCcspA90blbv
- https://youtu.be/opjyyXoqrxg?si=DwmeoCX6oHeldoGH


2. Modul 2: Mix & Match Outfit Builder

Dalam pengembangan modul Mix & Match, saya menggunakan AI (Claude dan ChatGPT) sebagai alat bantu selama proses pengerjaan, terutama dalam pengembangan JavaScript, CSS, dan beberapa penyesuaian backend Django.

Saya menentukan sendiri tampilan, alur penggunaan, serta fitur-fitur yang ingin dikembangkan, seperti Saved Outfits, Outfit Details, Edit, Update, Share to Community, Reset, dan Shuffle.

Selama proses coding, saya tetap berusaha mengerjakan dan memahami implementasinya terlebih dahulu. AI membantu dalam mengembangkan beberapa bagian kode serta menyesuaikan fitur dengan kebutuhan modul, misalnya memungkinkan pengguna memilih lebih dari satu aksesori dalam satu outfit, mengombinasikan dress dengan item pakaian lainnya, dan mengembangkan fungsi dari fitur-fitur yang telah dirancang. Selain itu, AI juga membantu memberikan saran dan mencari solusi ketika terdapat error atau fitur yang belum berjalan sesuai harapan.

Hasil dari proses tersebut kemudian saya pelajari, sesuaikan dengan kode yang sudah dibuat, dan uji kembali untuk memastikan setiap fitur berjalan sesuai harapan. Melalui proses ini, AI tidak hanya membantu dalam implementasi teknis, tetapi juga membantu saya memahami dan mengembangkan kode selama pengerjaan modul.

3. Modul 3: Weekly Outfit Planner & Weather Recommendation

Pada fitur Planner RE:STYLE, saya menggunakan AI sebagai asisten, bukan sebagai pengganti proses perancangan. Konsep fitur, aturan, dan desain antarmuka (modal pemilihan outfit, widget cuaca, dll.) saya tentukan dan rancang sendiri di Figma. Aturan seperti status "In the Wash" yang kembali "Ready" pada hari laundry, rekomendasi outfit berdasarkan cuaca, hingga penggunaan ulang komponen yang sudah ada (kartu outfit, tombol, toast) juga berasal dari keputusan saya.

AI membantu pada tahap implementasi, terutama di bagian yang masih sulit bagi saya, yaitu JavaScript seperti pengambilan lokasi, fetch data cuaca, dan beberapa pembaruan tampilan tanpa reload, serta beberapa logika di sisi Django seperti perhitungan status item dan pengambilan data forecast. Cara kerjanya adalah saya menyusun kebutuhan, referensi desain, dan konteks kode yang sudah ada menjadi prompt, lalu meminta AI membuat atau merevisi bagian tertentu. Hasilnya saya jalankan, uji, dan saya sesuaikan dengan model, view, URL, dan template di project.

AI juga saya pakai untuk memahami kode yang dihasilkan, misalnya alur request dan response, query ORM, serta validasi di view, sehingga saya dapat menjelaskan dan memodifikasinya sendiri untuk kedepannya. Untuk dasar konsep, saya merujuk ke dokumentasi Django, tutorial PBP, serta dokumentasi Open-Meteo dan Nominatim (untuk mengolah data OpenStreetMap).

Saya mengakui bahwa kontribusi AI pada kode JavaScript dan beberapa fitur tambahan Planner. Namun, kebutuhan, desain, dan keputusan akhir tetap saya yang tentukan, dan kode dari AI tidak saya terima begitu saja tanpa pemeriksaan.

4. Modul 4: Conscious Shopping Reminder & Autentikasi - Hasya Azzahra Rangkuti

Dalam pengembangan Modul 4 (Conscious Shopping Reminder & Autentikasi), saya menggunakan AI (Gemini) sebagai asisten dan alat bantu selama proses perancangan hingga implementasi fitur, terutama pada bagian integrasi JavaScript interaktif dan penyesuaian backend Django.

Konsep utama pengingat *Conscious Shopping*—yaitu mencegah pembelian impulsif dengan mendeteksi kemiripan barang (berdasarkan kategori dan warna) antara barang impian dengan item di Digital Closet pengguna—saya tentukan berdasarkan ide modul dan kebutuhan aplikasi RE:STYLE. AI membantu saya menerjemahkan logika tersebut ke dalam kode, mulai dari validasi real-time di backend Django hingga interaksi dinamis di frontend.

Peran AI sangat krusial dalam membangun alur interaksi kompleks, seperti pembuatan modal pop-up *Conscious Alert* yang dilengkapi maskot bunglon, penanganan *deep-linking* parameter URL (`cat` & `color`) dengan format *case-insensitive* ke halaman Digital Closet, serta pembuatan *chip* interaktif pada *modal view detail* Wishlist yang memungkinkan *redirect* langsung ke item terkait di closet. Selain itu, AI membantu penanganan form *AJAX*, kompresi foto sebelum diunggah, format harga dengan pemisah ribuan, hingga sinkronisasi data Wishlist yang ditambahkan langsung dari halaman Fashion Community.

Saya juga memanfaatkan AI dalam mengimplementasikan fitur autentikasi pengguna (registrasi akun, login, dan logout) serta penataan antarmuka modal (*add*, *edit*, dan *confirm delete*) agar konsisten dengan panduan desain aplikasi.

Seluruh kode yang dihasilkan AI tidak langsung saya gunakan secara mentah. Saya mengecek, melakukan pengujian langsung di lingkungan lokal dan server PWS, serta menyesuaikan logika fungsi pada *views*, *models*, *urls*, dan *template* agar terintegrasi sempurna dengan modul anggota tim lainnya.

Sumber eksternal:
- Dokumentasi Resmi Django (Authentication & Request/Response Lifecycle)
- Dokumentasi MDN Web Docs (Fetch API & URLSearchParams)
- Tutorial Web PBP (Pengelolaan Form & Autentikasi Django)

5. Modul 5: Fashion Community dan Modul 6: Admin Panel (Moderasi Konten) - Salsabilla Hasan

AI saya gunakan sebagai alat bantu selama pengembangan RE:STYLE, terutama pada fitur Community yang memiliki cukup banyak fitur tambahan dan alur yang cukup kompleks. Untuk Community, saya sendiri yang merancang tampilan dan desain antarmukanya melalui Figma, termasuk menentukan layout, komponen, serta alur interaksi yang ingin digunakan.

Untuk core fitur Community yang terdapat pada modul, saya mempelajari konsep dan alurnya melalui sumber eksternal seperti dokumentasi Django dan tutorial web PBP. Sementara itu, untuk beberapa fitur tambahan Community seperti search, notifications, saved posts, follow dan profil pengguna, mention, tag item Digital Closet, foto pada balasan, dan foto profil khusus Community, saya menggunakan bantuan AI dalam proses implementasinya. Karena fitur-fitur tersebut cukup kompleks, saya menggunakan AI untuk membantu menerjemahkan rancangan dan kebutuhan fitur yang sudah saya tentukan ke dalam kode.

Bantuan AI juga cukup banyak digunakan pada bagian JavaScript karena bagian tersebut masih cukup sulit bagi saya untuk implementasikan sendiri. Biasanya saya memberikan konteks mengenai fitur, desain, atau kode yang sudah ada, kemudian meminta AI membantu membuat atau menjelaskan bagian tertentu. Hasil dari AI kemudian saya cek dan sesuaikan kembali dengan struktur project yang saya miliki.

Selain Community, saya juga turut berkontribusi pada Modul 6: Admin Panel (Moderasi Konten). Pada bagian ini, saya ikut mengerjakan dan mengembangkan bagian dari admin panel yang digunakan untuk mendukung kebutuhan moderasi Fashion Community. Karena pengembangan Admin Panel juga memiliki kompleksitas tersendiri, saya menggunakan bantuan AI dalam proses implementasinya. Terutama untuk bagian yang belum saya kuasai, saya menggunakan AI untuk membantu menerjemahkan kebutuhan fitur ke dalam kode, kemudian melakukan pengecekan dan penyesuaian terhadap project yang sudah ada.

Saya menyadari bahwa pada beberapa bagian, terutama fitur tambahan Community dan Admin Panel, AI memiliki peran yang cukup besar dalam membantu proses implementasi. Saya tidak menganggap hasil dari AI selalu langsung benar. Kode yang diberikan tetap saya cek dan sesuaikan dengan model, URL, view, template, serta struktur project yang digunakan. Sementara itu, desain antarmuka dan kebutuhan fitur yang menjadi dasar implementasi saya tentukan sendiri melalui perancangan di Figma dan kebutuhan modul.

Dengan demikian, AI saya gunakan sebagai alat bantu dalam proses belajar dan implementasi, terutama untuk bagian yang masih sulit saya kerjakan secara mandiri. Saya tetap melakukan pengecekan dan penyesuaian terhadap hasil AI agar dapat digunakan sesuai dengan struktur dan kebutuhan RE:STYLE.

### Link Deployment PWS
https://pws.cs.ui.ac.id/web/project/aulia.nur51/restyle



### Link Figma
https://www.figma.com/files/team/1681266096856658809/folder/654466752?fuid=1569545861454915648

