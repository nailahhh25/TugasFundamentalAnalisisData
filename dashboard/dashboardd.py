import os
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns
import warnings
warnings.filterwarnings('ignore')

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_DATA_DIR = os.path.join(BASE_DIR, "data")
DATA_DIR = DEFAULT_DATA_DIR

if not os.path.isdir(DATA_DIR):
    project_root = os.path.dirname(BASE_DIR)
    for candidate in os.listdir(project_root):
        candidate_path = os.path.join(project_root, candidate)
        if not os.path.isdir(candidate_path):
            continue

        if "main_data.csv" in os.listdir(candidate_path):
            DATA_DIR = candidate_path
            break

        candidate_data_dir = os.path.join(candidate_path, "data")
        if os.path.isdir(candidate_data_dir) and "main_data.csv" in os.listdir(candidate_data_dir):
            DATA_DIR = candidate_data_dir
            break

if not os.path.isdir(DATA_DIR):
    raise FileNotFoundError(f"Could not locate the data directory. Checked: {DATA_DIR}")

# ── Page Config ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="E-Commerce Brasil Dashboard",
    page_icon="🛍️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Custom CSS ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .main { background-color: #f8f9fa; }
    .metric-card {
        background: white;
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        border-left: 4px solid #1D3557;
    }
    .section-title {
        font-size: 22px;
        font-weight: 700;
        color: #1D3557;
        margin-bottom: 4px;
    }
    .section-sub {
        font-size: 13px;
        color: #6c757d;
        margin-bottom: 16px;
    }
    h1 { color: #1D3557 !important; }
</style>
""", unsafe_allow_html=True)

# ── Load Data ────────────────────────────────────────────────────────────────
@st.cache_data
def load_data():
    main_df = pd.read_csv(
        os.path.join(DATA_DIR, "main_data.csv"),
        parse_dates=["order_purchase_timestamp", "order_month"]
    )
    return main_df

@st.cache_data
def load_rfm():
    orders_df    = pd.read_csv(
        os.path.join(DATA_DIR, "orders_dataset.csv"),
        parse_dates=["order_purchase_timestamp"]
    )
    payments_df  = pd.read_csv(os.path.join(DATA_DIR, "order_payments_dataset.csv"))
    customers_df = pd.read_csv(os.path.join(DATA_DIR, "customers_dataset.csv"))

    orders_delivered = orders_df[orders_df["order_status"] == "delivered"].copy()

    rfm_base = orders_delivered.merge(
        payments_df.groupby("order_id")["payment_value"].sum().reset_index(),
        on="order_id", how="left"
    ).merge(
        customers_df[["customer_id", "customer_unique_id"]],
        on="customer_id", how="left"
    )

    reference_date = rfm_base["order_purchase_timestamp"].max() + pd.Timedelta(days=1)
    rfm_df = rfm_base.groupby("customer_unique_id").agg(
        recency=("order_purchase_timestamp", lambda x: (reference_date - x.max()).days),
        frequency=("order_id", "count"),
        monetary=("payment_value", "sum")
    ).reset_index()

    rfm_df["R_score"] = pd.qcut(rfm_df["recency"],   q=4, labels=[4,3,2,1]).astype(int)
    rfm_df["F_score"] = pd.qcut(rfm_df["frequency"].rank(method="first"), q=4, labels=[1,2,3,4]).astype(int)
    rfm_df["M_score"] = pd.qcut(rfm_df["monetary"],  q=4, labels=[1,2,3,4]).astype(int)
    rfm_df["RFM_score"] = rfm_df["R_score"] + rfm_df["F_score"] + rfm_df["M_score"]

    def segment(s):
        if s >= 10: return "Champions"
        elif s >= 8: return "Loyal Customers"
        elif s >= 6: return "Potential Loyalists"
        elif s >= 4: return "At Risk"
        else: return "Lost"

    rfm_df["segment"] = rfm_df["RFM_score"].apply(segment)
    return rfm_df


main_df = load_data()

# ── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🛍️ E-Commerce Dashboard")
    st.markdown("**Dataset:** Brazilian E-Commerce Public Dataset (Olist)")
    st.divider()

    # Date filter
    st.markdown("### 📅 Filter Periode")
    min_date = main_df["order_month"].min()
    max_date = main_df["order_month"].max()

    start_date = st.date_input("Dari tanggal", value=min_date, min_value=min_date, max_value=max_date)
    end_date   = st.date_input("Sampai tanggal", value=max_date, min_value=min_date, max_value=max_date)

    # Category filter
    st.markdown("### 🏷️ Filter Kategori")
    all_categories = sorted(main_df["product_category_name_english"].dropna().unique().tolist())
    selected_cats = st.multiselect(
        "Pilih kategori (kosong = semua)",
        options=all_categories,
        default=[]
    )

    st.divider()
    st.markdown("**Dibuat oleh:** [Nama Anda]")
    st.markdown("**Dicoding ID:** [Username]")

# ── Filter Data ───────────────────────────────────────────────────────────────
filtered_df = main_df[
    (main_df["order_month"] >= pd.Timestamp(start_date)) &
    (main_df["order_month"] <= pd.Timestamp(end_date))
].copy()

if selected_cats:
    filtered_df = filtered_df[filtered_df["product_category_name_english"].isin(selected_cats)]

# ── Header ────────────────────────────────────────────────────────────────────
st.title("🛍️ E-Commerce Brasil – Dashboard Analisis")
st.markdown(f"Menampilkan data: **{pd.Timestamp(start_date).strftime('%b %Y')}** hingga **{pd.Timestamp(end_date).strftime('%b %Y')}**")
st.divider()

# ── KPI Metrics ───────────────────────────────────────────────────────────────
col1, col2, col3, col4 = st.columns(4)

total_revenue  = filtered_df["total_revenue"].sum()
total_orders   = filtered_df["order_id"].nunique()
total_products = filtered_df["product_id"].nunique()
avg_order_val  = filtered_df.groupby("order_id")["total_revenue"].sum().mean()

col1.metric("💰 Total Revenue",     f"R$ {total_revenue:,.0f}")
col2.metric("📦 Total Pesanan",     f"{total_orders:,}")
col3.metric("🏷️ Produk Terjual",   f"{total_products:,}")
col4.metric("🧾 Rata-rata / Order", f"R$ {avg_order_val:,.2f}")

st.divider()

# ── Pertanyaan 1: Revenue per Kategori ───────────────────────────────────────
st.markdown('<p class="section-title">📊 Pertanyaan 1: Kategori Produk dengan Revenue Tertinggi</p>', unsafe_allow_html=True)
st.markdown('<p class="section-sub">Top kategori berdasarkan total revenue (harga produk + ongkos kirim)</p>', unsafe_allow_html=True)

col_left, col_right = st.columns([3, 1])

with col_left:
    top_n = st.slider("Tampilkan top N kategori", 5, 20, 10, key="topn")

    revenue_by_cat = (
        filtered_df.groupby("product_category_name_english")["total_revenue"]
        .sum().sort_values(ascending=False).head(top_n).reset_index()
    )
    revenue_by_cat.columns = ["Kategori", "Total Revenue"]

    colors = ["#E63946" if i == 0 else "#A8DADC" for i in range(len(revenue_by_cat))]

    fig1, ax1 = plt.subplots(figsize=(12, 6))
    bars = ax1.barh(
        revenue_by_cat["Kategori"][::-1],
        revenue_by_cat["Total Revenue"][::-1] / 1_000_000,
        color=colors[::-1], edgecolor="white", linewidth=0.5
    )
    for bar in bars:
        w = bar.get_width()
        ax1.text(w + 0.01, bar.get_y() + bar.get_height() / 2,
                 f"R$ {w:.2f}M", va="center", ha="left", fontsize=9)

    ax1.set_xlabel("Total Revenue (Juta R$)", fontsize=11)
    ax1.set_title(f"Top {top_n} Kategori Produk – Total Revenue", fontsize=13, fontweight="bold")
    ax1.set_xlim(0, revenue_by_cat["Total Revenue"].max() / 1_000_000 * 1.2)
    ax1.spines[["top", "right"]].set_visible(False)
    plt.tight_layout()
    st.pyplot(fig1)

with col_right:
    st.markdown("#### 📋 Tabel Data")
    revenue_by_cat["Total Revenue"] = revenue_by_cat["Total Revenue"].apply(lambda x: f"R$ {x:,.0f}")
    st.dataframe(revenue_by_cat, width="stretch", hide_index=True)

st.info("""
**💡 Insight:** Kategori **health_beauty** mendominasi total revenue, diikuti **watches_gifts** dan **bed_bath_table**.
Ketiga kategori ini berkaitan dengan gaya hidup dan kebutuhan rumah tangga — menunjukkan preferensi belanja konsumen Brasil.
""")

st.divider()

# ── Pertanyaan 2: Tren Pesanan Bulanan ───────────────────────────────────────
st.markdown('<p class="section-title">📈 Pertanyaan 2: Tren Jumlah Pesanan Bulanan</p>', unsafe_allow_html=True)
st.markdown('<p class="section-sub">Jumlah order unik per bulan sepanjang periode yang dipilih</p>', unsafe_allow_html=True)

monthly_orders = (
    filtered_df.groupby("order_month")["order_id"].nunique().reset_index()
)
monthly_orders.columns = ["Bulan", "Jumlah Order"]
monthly_orders = monthly_orders.sort_values("Bulan")

monthly_rev = (
    filtered_df.groupby("order_month")["total_revenue"].sum().reset_index()
)
monthly_rev.columns = ["Bulan", "Revenue"]
monthly_summary = monthly_orders.merge(monthly_rev, on="Bulan")

tab1, tab2 = st.tabs(["📉 Grafik Tren", "📋 Tabel Bulanan"])

with tab1:
    fig2, ax2 = plt.subplots(figsize=(14, 5))
    ax2.plot(monthly_summary["Bulan"], monthly_summary["Jumlah Order"],
             color="#1D3557", linewidth=2.5, marker="o", markersize=6, label="Jumlah Order")
    ax2.fill_between(monthly_summary["Bulan"], monthly_summary["Jumlah Order"],
                     alpha=0.12, color="#1D3557")

    if not monthly_summary.empty:
        peak_idx = monthly_summary["Jumlah Order"].idxmax()
        peak_row = monthly_summary.loc[peak_idx]
        ax2.annotate(
            f"Puncak: {peak_row['Jumlah Order']:,}",
            xy=(peak_row["Bulan"], peak_row["Jumlah Order"]),
            xytext=(peak_row["Bulan"], peak_row["Jumlah Order"] + 200),
            ha="center", fontsize=10, color="#E63946",
            arrowprops=dict(arrowstyle="->", color="#E63946"),
            bbox=dict(boxstyle="round,pad=0.3", facecolor="#FFF0F0", edgecolor="#E63946")
        )
        avg = monthly_summary["Jumlah Order"].mean()
        ax2.axhline(avg, color="gray", linestyle="--", linewidth=1.2, alpha=0.7)
        ax2.text(monthly_summary["Bulan"].iloc[-1], avg + 50,
                 f"Rata-rata: {avg:.0f}", fontsize=9, color="gray")

    ax2.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
    plt.xticks(rotation=45)
    ax2.set_xlabel("Bulan", fontsize=11)
    ax2.set_ylabel("Jumlah Order", fontsize=11)
    ax2.set_title("Tren Jumlah Pesanan Bulanan", fontsize=13, fontweight="bold")
    ax2.spines[["top", "right"]].set_visible(False)
    plt.tight_layout()
    st.pyplot(fig2)

with tab2:
    display_monthly = monthly_summary.copy()
    display_monthly["Bulan"] = display_monthly["Bulan"].dt.strftime("%B %Y")
    display_monthly["Revenue"] = display_monthly["Revenue"].apply(lambda x: f"R$ {x:,.0f}")
    st.dataframe(display_monthly, width="stretch", hide_index=True)

st.info("""
**💡 Insight:** Tren pesanan menunjukkan **pertumbuhan konsisten** dari 2017 ke 2018.
Puncak terjadi pada **November 2017** bertepatan dengan **Black Friday** di Brasil,
membuktikan efektivitas event promosi musiman dalam mendorong volume transaksi.
""")

st.divider()

# ── Analisis Lanjutan: RFM ────────────────────────────────────────────────────
st.markdown('<p class="section-title">🔍 Analisis Lanjutan: Segmentasi Pelanggan (RFM)</p>', unsafe_allow_html=True)
st.markdown('<p class="section-sub">Segmentasi pelanggan berdasarkan Recency, Frequency, dan Monetary</p>', unsafe_allow_html=True)

with st.spinner("Menghitung RFM..."):
    rfm_df = load_rfm()

segment_colors = {
    "Champions":           "#E63946",
    "Loyal Customers":     "#457B9D",
    "Potential Loyalists": "#A8DADC",
    "At Risk":             "#F4A261",
    "Lost":                "#6c757d"
}
order_seg = ["Champions", "Loyal Customers", "Potential Loyalists", "At Risk", "Lost"]

seg_count = rfm_df["segment"].value_counts().reindex(order_seg).reset_index()
seg_count.columns = ["Segmen", "Jumlah"]

col_a, col_b = st.columns([2, 1])

with col_a:
    fig3, ax3 = plt.subplots(figsize=(10, 5))
    bar_colors = [segment_colors[s] for s in seg_count["Segmen"]]
    bars3 = ax3.bar(seg_count["Segmen"], seg_count["Jumlah"], color=bar_colors,
                    edgecolor="white", linewidth=0.7)
    for b in bars3:
        h = b.get_height()
        ax3.text(b.get_x() + b.get_width() / 2, h + 200, f"{h:,}",
                 ha="center", fontsize=10)
    ax3.set_title("Distribusi Segmen Pelanggan (RFM Analysis)", fontsize=13, fontweight="bold")
    ax3.set_xlabel("Segmen", fontsize=11)
    ax3.set_ylabel("Jumlah Pelanggan", fontsize=11)
    ax3.spines[["top", "right"]].set_visible(False)
    plt.tight_layout()
    st.pyplot(fig3)

with col_b:
    st.markdown("#### 📊 Statistik per Segmen")
    rfm_stats = rfm_df.groupby("segment").agg(
        Pelanggan=("customer_unique_id", "count"),
        Avg_Recency=("recency", "mean"),
        Avg_Frequency=("frequency", "mean"),
        Avg_Monetary=("monetary", "mean")
    ).round(1).reindex(order_seg)
    rfm_stats["Avg_Monetary"] = rfm_stats["Avg_Monetary"].apply(lambda x: f"R$ {x:,.0f}")
    st.dataframe(rfm_stats, width="stretch")

    st.markdown("""
    **Keterangan Segmen:**
    - 🔴 **Champions** – Beli baru, sering, banyak
    - 🔵 **Loyal** – Sering beli, spending tinggi
    - 🩵 **Potential** – Baru, belum terlalu sering
    - 🟠 **At Risk** – Dulu aktif, kini jarang
    - ⚫ **Lost** – Sudah lama tidak bertransaksi
    """)

st.info("""
**💡 Insight RFM:** Mayoritas pelanggan berada di segmen **At Risk** dan **Potential Loyalists**.
Strategi yang direkomendasikan: program loyalitas untuk mengkonversi *Potential* → *Loyal*, 
dan kampanye win-back untuk segmen *At Risk* dan *Lost*.
""")

st.divider()

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("""
<div style='text-align:center; color:#6c757d; font-size:13px; padding:10px'>
    📊 E-Commerce Brasil Dashboard · Data Source: Olist Brazilian E-Commerce Public Dataset ·
    Dibuat dengan Streamlit & Matplotlib
</div>
""", unsafe_allow_html=True)
