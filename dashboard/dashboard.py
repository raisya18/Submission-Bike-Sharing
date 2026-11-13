import os

import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import numpy as np
import pandas as pd
import seaborn as sns
import streamlit as st

# ---------------------------------------------------------------- konfigurasi
st.set_page_config(page_title="Bike Sharing Dashboard", page_icon="🚲", layout="wide")
sns.set_theme(style="whitegrid", font_scale=1.0)
plt.rcParams["axes.spines.top"] = False
plt.rcParams["axes.spines.right"] = False
BLUE, ORANGE, GREY, RED, LIGHT = "#1f4e79", "#e08e0b", "#b8b8b8", "#c0392b", "#7aa6d1"

BASE = os.path.dirname(os.path.abspath(__file__))
URUTAN_CUACA = ["Cerah", "Berkabut/Berawan", "Hujan/Salju Ringan"]
URUTAN_MUSIM = ["Winter", "Spring", "Summer", "Fall"]
URUTAN_BULAN = ["Jan", "Feb", "Mar", "Apr", "Mei", "Jun", "Jul", "Agu", "Sep", "Okt", "Nov", "Des"]


@st.cache_data
def load_data():
    day = pd.read_csv(os.path.join(BASE, "main_data.csv"), parse_dates=["dteday"])
    hour = pd.read_csv(os.path.join(BASE, "hour_data.csv"), parse_dates=["dteday"])
    return day, hour


day_all, hour_all = load_data()

# -------------------------------------------------------------------- sidebar
with st.sidebar:
    st.title("🚲 Bike Sharing")
    st.caption("Washington D.C., 2011–2012")
    rentang = st.date_input(
        "Rentang tanggal",
        value=(day_all["dteday"].min().date(), day_all["dteday"].max().date()),
        min_value=day_all["dteday"].min().date(),
        max_value=day_all["dteday"].max().date(),
    )
    musim = st.multiselect("Musim", URUTAN_MUSIM, default=URUTAN_MUSIM)
    st.markdown("---")
    st.caption(
        "Filter berlaku untuk semua grafik. Sumber data: Bike Sharing Dataset "
        "(Fanaee-T & Gama, 2013), sudah dibersihkan pada notebook analisis."
    )

if isinstance(rentang, tuple) and len(rentang) == 2:
    awal, akhir = pd.Timestamp(rentang[0]), pd.Timestamp(rentang[1])
else:
    st.info("Pilih tanggal awal dan akhir pada sidebar.")
    st.stop()

day = day_all[day_all["dteday"].between(awal, akhir) & day_all["season_name"].isin(musim)].copy()
hour = hour_all[hour_all["dteday"].between(awal, akhir) & hour_all["season_name"].isin(musim)].copy()

st.title("Dashboard Analisis Bike Sharing")
st.markdown("Ringkasan pola penyewaan sepeda untuk mendukung keputusan operasional dan pemasaran.")

if day.empty:
    st.warning("Tidak ada data pada filter yang dipilih. Ubah rentang tanggal atau musim.")
    st.stop()

# ------------------------------------------------------------------------ KPI
pola_kpi = hour.groupby("hr")["total"].mean()
k1, k2, k3, k4 = st.columns(4)
k1.metric("Total penyewaan", f"{day['total'].sum():,.0f}")
k2.metric("Rata-rata per hari", f"{day['total'].mean():,.0f}")
k3.metric("Porsi pengguna registered", f"{day['registered'].sum() / day['total'].sum() * 100:.1f}%")
k4.metric("Jam tersibuk (rata-rata)", f"{int(pola_kpi.idxmax()):02d}.00")

tab1, tab2, tab3, tab4 = st.tabs(
    ["⏰ Pola Jam", "🌦️ Cuaca & Musim", "📈 Pertumbuhan 2012 vs 2011", "🧩 Segmentasi (Analisis Lanjutan)"]
)

# ------------------------------------------------------------ tab 1: pola jam
with tab1:
    st.markdown("**Pertanyaan 1:** Pada jam berapa rata-rata penyewaan sepeda per jam mencapai puncak pada hari kerja dibandingkan akhir pekan/hari libur sepanjang 2011–2012, dan berapa selisih rata-rata penyewaan pada jam puncak tersebut, agar tim operasional dapat menjadwalkan redistribusi dan perawatan sepeda di luar jam puncak?")
    pola = hour.groupby(["day_type", "hr"])["total"].mean().unstack(0)
    fig, ax = plt.subplots(figsize=(11, 4.8))
    ax.axvspan(7, 9, color=BLUE, alpha=0.07)
    ax.axvspan(16, 19, color=BLUE, alpha=0.07)
    for kolom, warna in [("Hari Kerja", BLUE), ("Akhir Pekan/Libur", ORANGE)]:
        if kolom in pola.columns:
            ax.plot(pola.index, pola[kolom], color=warna, lw=2.6, marker="o", ms=4, label=kolom)
            jam = pola[kolom].idxmax()
            ax.annotate(f"Puncak {int(jam):02d}.00\n{pola.loc[jam, kolom]:.0f}/jam", (jam, pola.loc[jam, kolom]),
                        (jam - 1.4, pola.loc[jam, kolom] + pola.max().max() * 0.10), color=warna,
                        fontweight="bold", fontsize=9.5, ha="center",
                        arrowprops=dict(arrowstyle="-", color=warna))
    ax.set_xticks(range(24))
    ax.set_xticklabels([f"{h:02d}" for h in range(24)])
    ax.set_xlabel("Jam dalam sehari")
    ax.set_ylabel("Rata-rata penyewaan per jam")
    ax.set_ylim(0, pola.max().max() * 1.3)
    ax.legend(frameon=False, loc="upper left")
    st.pyplot(fig)
    plt.close(fig)

    if {"Hari Kerja", "Akhir Pekan/Libur"} <= set(pola.columns):
        wk, we = pola["Hari Kerja"], pola["Akhir Pekan/Libur"]
        st.info(
            f"**Insight:** puncak hari kerja pukul **{int(wk.idxmax()):02d}.00** ({wk.max():.0f}/jam) dan puncak akhir "
            f"pekan pukul **{int(we.idxmax()):02d}.00** ({we.max():.0f}/jam). Puncak hari kerja "
            f"**{(wk.max() / we.max() - 1) * 100:.0f}% lebih tinggi** dari puncak akhir pekan. "
            f"**Aksi:** pastikan sepeda tersedia dan petugas redistribusi siap sebelum 07.00 dan 16.00 pada hari kerja; jadwalkan perawatan di luar jam puncak."
        )

# --------------------------------------------------------- tab 2: cuaca musim
with tab2:
    st.markdown("**Pertanyaan 2:** Berapa persen perbedaan rata-rata penyewaan harian pada kondisi cuaca berkabut/berawan dan hujan/salju ringan dibandingkan cuaca cerah, serta musim apa yang memiliki rata-rata penyewaan harian tertinggi dan terendah sepanjang 2011–2012, agar tim pemasaran dapat menentukan waktu promosi dan kebijakan ukuran armada?")
    cuaca = (day.groupby("weather")["total"].agg(rata="mean", n="count")
             .reindex([c for c in URUTAN_CUACA if c in day["weather"].unique()]))
    mus = (day.groupby("season_name")["total"].agg(rata="mean", n="count")
           .reindex([m for m in URUTAN_MUSIM if m in day["season_name"].unique()]))
    c1, c2 = st.columns(2)
    with c1:
        fig, ax = plt.subplots(figsize=(6, 4.6))
        warna = [BLUE, LIGHT, RED][: len(cuaca)]
        bars = ax.bar(cuaca.index, cuaca["rata"], color=warna, width=0.6)
        for bar, (nama, b) in zip(bars, cuaca.iterrows()):
            lbl = f"{b['rata']:,.0f}"
            if "Cerah" in cuaca.index and nama != "Cerah":
                lbl += f"\n({(b['rata'] / cuaca.loc['Cerah', 'rata'] - 1) * 100:+.1f}%)"
            ax.text(bar.get_x() + bar.get_width() / 2, b["rata"] + cuaca["rata"].max() * 0.015, lbl,
                    ha="center", fontweight="bold", fontsize=9.5)
        ax.set_xticks(range(len(cuaca)))
        ax.set_xticklabels([f"{n}\n(n = {int(r['n'])} hari)" for n, r in cuaca.iterrows()], fontsize=9)
        ax.set_ylim(0, cuaca["rata"].max() * 1.22)
        ax.set_ylabel("Rata-rata penyewaan harian")
        ax.set_title("Berdasarkan cuaca", loc="left", fontweight="bold")
        st.pyplot(fig)
        plt.close(fig)
    with c2:
        fig, ax = plt.subplots(figsize=(6, 4.6))
        urut = mus["rata"]
        warna = [RED if v == urut.min() else BLUE if v == urut.max() else LIGHT for v in urut]
        bars = ax.bar(mus.index, mus["rata"], color=warna, width=0.6)
        for bar, v in zip(bars, mus["rata"]):
            ax.text(bar.get_x() + bar.get_width() / 2, v + mus["rata"].max() * 0.015, f"{v:,.0f}",
                    ha="center", fontweight="bold", fontsize=9.5)
        ax.set_ylim(0, mus["rata"].max() * 1.18)
        ax.set_ylabel("")
        ax.set_title("Berdasarkan musim", loc="left", fontweight="bold")
        st.pyplot(fig)
        plt.close(fig)

    if "Cerah" in cuaca.index and len(cuaca) > 1:
        teks = " | ".join(f"**{n}**: {(r['rata'] / cuaca.loc['Cerah', 'rata'] - 1) * 100:+.1f}% vs cerah"
                          for n, r in cuaca.iterrows() if n != "Cerah")
        st.info(f"**Insight:** {teks}. Musim tertinggi **{mus['rata'].idxmax()}** ({mus['rata'].max():,.0f}/hari), "
                f"terendah **{mus['rata'].idxmin()}** ({mus['rata'].min():,.0f}/hari). "
                "Perbandingan ini deskriptif, bukan sebab-akibat. **Aksi:** uji coba promo pada musim rendah/hari berkabut dan siapkan armada penuh di musim puncak.")

# --------------------------------------------------------- tab 3: pertumbuhan
with tab3:
    st.markdown("**Pertanyaan 3:** Berapa persentase pertumbuhan total penyewaan tahun 2012 dibandingkan 2011 (secara keseluruhan, per bulan, serta per segmen pengguna casual vs registered), agar manajemen dapat menentukan segmen yang harus diprioritaskan pada strategi akuisisi dan retensi?")
    bln = day.pivot_table(index="month", columns="year", values="total", aggfunc="sum")
    if {2011, 2012} <= set(bln.columns):
        bln = bln.dropna(subset=[2011, 2012])
    if {2011, 2012} <= set(bln.columns) and not bln.empty:
        bln["growth"] = (bln[2012] / bln[2011] - 1) * 100
        bln["nama"] = [URUTAN_BULAN[m - 1] for m in bln.index]
        thn = day[day["month"].isin(bln.index)].groupby("year")[["casual", "registered", "total"]].sum()
        g = (thn.loc[2012] / thn.loc[2011] - 1) * 100

        c1, c2 = st.columns([1.6, 1])
        with c1:
            fig, ax = plt.subplots(figsize=(8, 4.6))
            ax.plot(bln["nama"], bln[2011], color=GREY, lw=2.6, marker="o", label="2011")
            ax.plot(bln["nama"], bln[2012], color=BLUE, lw=2.6, marker="o", label="2012")
            ax.fill_between(bln["nama"], bln[2011], bln[2012], color=BLUE, alpha=0.08)
            ax.yaxis.set_major_formatter(mtick.FuncFormatter(lambda x, _: f"{x / 1000:.0f}rb"))
            ax.set_ylim(0, bln[[2011, 2012]].max().max() * 1.15)
            ax.set_ylabel("Total penyewaan per bulan")
            ax.set_title(f"Total penyewaan naik {g['total']:.1f}% pada 2012", loc="left", fontweight="bold")
            ax.legend(frameon=False, loc="upper left")
            st.pyplot(fig)
            plt.close(fig)
        with c2:
            fig, ax = plt.subplots(figsize=(4.6, 4.6))
            bars = ax.bar(["Casual", "Registered"], [g["casual"], g["registered"]], color=[ORANGE, BLUE], width=0.5)
            for bar, v in zip(bars, [g["casual"], g["registered"]]):
                ax.text(bar.get_x() + bar.get_width() / 2, v + 1, f"{v:+.1f}%", ha="center", fontweight="bold")
            ax.yaxis.set_major_formatter(mtick.PercentFormatter())
            ax.set_ylim(0, max(g["casual"], g["registered"]) * 1.2)
            ax.set_title("Pertumbuhan per segmen", loc="left", fontweight="bold")
            st.pyplot(fig)
            plt.close(fig)

        top, low = bln["growth"].idxmax(), bln["growth"].idxmin()
        st.info(f"**Insight:** pertumbuhan total **{g['total']:+.1f}%**; registered **{g['registered']:+.1f}%**, casual "
                f"**{g['casual']:+.1f}%**. Pertumbuhan bulanan tertinggi **{bln.loc[top, 'nama']} ({bln.loc[top, 'growth']:+.0f}%)**, "
                f"terendah **{bln.loc[low, 'nama']} ({bln.loc[low, 'growth']:+.0f}%)**. "
                "**Aksi:** pertahankan pengguna registered dan tawarkan paket langganan kepada pengguna casual.")
    else:
        st.warning("Perbandingan 2012 vs 2011 membutuhkan rentang tanggal yang mencakup bulan yang sama di kedua tahun.")

# ------------------------------------------------------ tab 4: analisis lanjut
with tab4:
    st.markdown("**Analisis lanjutan (tanpa machine learning):** binning suhu dan klaster tingkat permintaan harian.")
    day["kelompok_suhu"] = pd.cut(day["temp_c"], bins=[-np.inf, 10, 20, 28, np.inf], right=False,
                                  labels=["Dingin (<10°C)", "Sejuk (10-20°C)", "Hangat (20-28°C)", "Panas (≥28°C)"])
    day["klaster"] = pd.cut(day["total"], bins=[0, 3000, 5000, 7000, np.inf], right=False,
                            labels=["Rendah", "Sedang", "Tinggi", "Sangat Tinggi"])
    suhu = day.groupby("kelompok_suhu", observed=False)["total"].agg(rata="mean", n="count").dropna()
    kl = (pd.crosstab(day["season_name"], day["klaster"], normalize="index") * 100)
    kl = kl.reindex([m for m in URUTAN_MUSIM if m in kl.index])

    c1, c2 = st.columns([1, 1.2])
    with c1:
        fig, ax = plt.subplots(figsize=(6, 4.6))
        bars = ax.bar(suhu.index.astype(str), suhu["rata"], color=[RED, LIGHT, BLUE, BLUE][: len(suhu)], width=0.6)
        for bar, (nama, b) in zip(bars, suhu.iterrows()):
            ax.text(bar.get_x() + bar.get_width() / 2, b["rata"] + suhu["rata"].max() * 0.015,
                    f"{b['rata']:,.0f}\n(n = {int(b['n'])})", ha="center", fontsize=9, fontweight="bold")
        ax.set_ylim(0, suhu["rata"].max() * 1.25)
        ax.set_ylabel("Rata-rata penyewaan harian")
        ax.set_title("Penyewaan menurut kelompok suhu", loc="left", fontweight="bold")
        ax.tick_params(axis="x", labelsize=8)
        st.pyplot(fig)
        plt.close(fig)
    with c2:
        fig, ax = plt.subplots(figsize=(7, 4.6))
        kl.plot(kind="barh", stacked=True, ax=ax, width=0.6,
                color=[{"Rendah": RED, "Sedang": GREY, "Tinggi": LIGHT, "Sangat Tinggi": BLUE}[c] for c in kl.columns])
        for i, (_, baris) in enumerate(kl.iterrows()):
            kiri = 0
            for v in baris:
                if v >= 8:
                    ax.text(kiri + v / 2, i, f"{v:.0f}%", ha="center", va="center", color="white",
                            fontweight="bold", fontsize=9)
                kiri += v
        ax.invert_yaxis()
        ax.xaxis.set_major_formatter(mtick.PercentFormatter())
        ax.set_xlabel("Proporsi hari")
        ax.set_ylabel("")
        ax.set_title("Klaster tingkat permintaan per musim", loc="left", fontweight="bold")
        ax.legend(title="Klaster", frameon=False, ncol=4, loc="upper center", bbox_to_anchor=(0.5, -0.18), fontsize=8.5)
        st.pyplot(fig)
        plt.close(fig)
    st.caption("Klaster: Rendah (<3.000), Sedang (3.000–4.999), Tinggi (5.000–6.999), Sangat Tinggi (≥7.000 penyewaan/hari).")

with st.expander("Lihat data harian (terfilter)"):
    st.dataframe(day.drop(columns=["kelompok_suhu", "klaster"], errors="ignore"))
