# 🛍️ E-Commerce Brasil – Dashboard Analisis Data

Dashboard interaktif berbasis **Streamlit** untuk menganalisis dataset E-Commerce Publik Brasil (Olist).

---

## 📁 Struktur Direktori

```
submission/
├── dashboard/
│   ├── dashboard.py        ← File utama Streamlit
│   └── data/
│       ├── main_data.csv                          ← Data utama hasil cleaning
│       ├── orders_dataset.csv
│       ├── order_items_dataset.csv
│       ├── order_payments_dataset.csv
│       ├── order_reviews_dataset.csv
│       ├── customers_dataset.csv
│       ├── products_dataset.csv
│       ├── sellers_dataset.csv
│       └── product_category_name_translation.csv
├── notebook.ipynb          ← Jupyter Notebook analisis lengkap
├── README.md               ← File ini
├── requirements.txt        ← Library yang dibutuhkan
└── url.txt                 ← (isi link deploy Streamlit Cloud jika ada)
```

---

## 🚀 Cara Menjalankan Dashboard (Local)

### 1. Clone / Extract project

Pastikan semua file sudah ada di folder `submission/`.

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Siapkan data

Letakkan semua file CSV dataset ke dalam folder `dashboard/data/`.  
Pastikan file `main_data.csv` sudah ada (dihasilkan dari notebook).  
Jika belum, jalankan notebook terlebih dahulu hingga selesai.

### 4. Jalankan Streamlit

```bash
cd dashboard
streamlit run dashboard.py
```

Dashboard akan terbuka di browser pada alamat: `http://localhost:8501`

---

## 📊 Pertanyaan Bisnis yang Dijawab

1. **Kategori produk apa yang menghasilkan total revenue tertinggi?**  
   → Menggunakan visualisasi horizontal bar chart dengan filter top N kategori.

2. **Bagaimana tren jumlah pesanan bulanan dari waktu ke waktu?**  
   → Menggunakan line chart dengan anotasi puncak pesanan.

3. *(Analisis Lanjutan)* **Bagaimana segmentasi pelanggan berdasarkan RFM?**  
   → Segmentasi Champions, Loyal, Potential Loyalists, At Risk, dan Lost.

---

## ⚙️ Fitur Dashboard

- Filter periode tanggal (sidebar)
- Filter kategori produk (multiselect)
- KPI Metrics: Revenue, Jumlah Order, Produk, Rata-rata per Order
- Visualisasi interaktif dengan slider dan tab
- Tabel data yang dapat di-scroll
- Analisis RFM dengan statistik per segmen

---

## 📦 Library Utama

| Library | Versi | Kegunaan |
|---------|-------|----------|
| pandas | 2.0.3 | Manipulasi data |
| numpy | 1.24.3 | Komputasi numerik |
| matplotlib | 3.7.2 | Visualisasi data |
| seaborn | 0.12.2 | Statistik visual |
| streamlit | 1.28.0 | Dashboard interaktif |
