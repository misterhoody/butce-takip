import streamlit as st
import pandas as pd
import os
from datetime import datetime
import matplotlib.pyplot as plt

# Sayfa Ayarları
st.set_page_config(page_title="Cebimdeki Ekonomi", page_icon="💰", layout="centered")

DOSYA_ADI = "butce_verileri.csv"

# --- Veri İşleme Fonksiyonları ---
def veri_yukle():
    if not os.path.exists(DOSYA_ADI):
        df = pd.DataFrame(columns=["Tarih", "Tür", "Kategori", "Açıklama", "Tutar"])
        df.to_csv(DOSYA_ADI, index=False)
        return df
    else:
        return pd.read_csv(DOSYA_ADI)

def veri_kaydet(df):
    df.to_csv(DOSYA_ADI, index=False)

# --- Ana Uygulama ---
st.title("💰 Bireysel Ekonomi Takipçisi")

# Sekmeler oluştur
tab1, tab2, tab3 = st.tabs(["➕ Ekle / Sil", "📊 Raporlar", "📋 Veri Listesi"])

# Verileri belleğe al
df = veri_yukle()

# --- TAB 1: VERİ GİRİŞİ ---
with tab1:
    st.header("Yeni İşlem Ekle")
    
    col1, col2 = st.columns(2)
    with col1:
        tur = st.selectbox("İşlem Türü", ["Gider", "Gelir"])
        tutar = st.number_input("Tutar (TL)", min_value=0.0, format="%.2f")
    
    with col2:
        kategoriler = ["Gıda & Market", "Barınma", "Ulaşım", "Faturalar", "Eğlence", "Sağlık", "Maaş", "Ek Gelir", "Yatırım", "Diğer"]
        kategori = st.selectbox("Kategori", kategoriler)
        aciklama = st.text_input("Açıklama")

    if st.button("Kaydet", use_container_width=True):
        if tutar > 0:
            yeni_veri = {
                "Tarih": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "Tür": tur,
                "Kategori": kategori,
                "Açıklama": aciklama,
                "Tutar": tutar
            }
            # Yeni veriyi ekle
            df = pd.concat([pd.DataFrame([yeni_veri]), df], ignore_index=True)
            veri_kaydet(df)
            st.success("İşlem başarıyla kaydedildi!")
            st.rerun() # Sayfayı yenile
        else:
            st.warning("Lütfen 0'dan büyük bir tutar girin.")

# --- TAB 2: ANALİZ VE GRAFİKLER ---
with tab2:
    st.header("Finansal Durum")
    
    if not df.empty:
        # Özet Kartları
        gelir_toplam = df[df["Tür"] == "Gelir"]["Tutar"].sum()
        gider_toplam = df[df["Tür"] == "Gider"]["Tutar"].sum()
        bakiye = gelir_toplam - gider_toplam

        col_a, col_b, col_c = st.columns(3)
        col_a.metric("Toplam Gelir", f"{gelir_toplam:,.2f} TL")
        col_b.metric("Toplam Gider", f"{gider_toplam:,.2f} TL")
        col_c.metric("Net Bakiye", f"{bakiye:,.2f} TL", delta_color="normal")

        st.divider()

        # Filtreleme
        aylar = df["Tarih"].str.slice(0, 7).unique() # YYYY-MM
        secilen_ay = st.selectbox("Dönem Seçiniz (Grafikler İçin)", ["Tümü"] + list(aylar))

        # Grafik Verisi Hazırlama
        df_grafik = df.copy()
        if secilen_ay != "Tümü":
            df_grafik = df_grafik[df_grafik["Tarih"].str.startswith(secilen_ay)]

        if not df_grafik.empty:
            # Pasta Grafiği (Sadece Giderler)
            giderler = df_grafik[df_grafik["Tür"] == "Gider"]
            if not giderler.empty:
                fig1, ax1 = plt.subplots()
                gider_kat = giderler.groupby("Kategori")["Tutar"].sum()
                ax1.pie(gider_kat, labels=gider_kat.index, autopct='%1.1f%%', startangle=90)
                ax1.set_title(f"Gider Dağılımı ({secilen_ay})")
                st.pyplot(fig1)
            else:
                st.info("Bu dönemde gider kaydı yok.")
        else:
            st.info("Seçilen dönemde veri yok.")

# --- TAB 3: LİSTE VE DÜZENLEME ---
with tab3:
    st.header("Tüm Kayıtlar")
    st.write("Tabloyu düzenlemek için üzerine çift tıklayabilirsin (CSV'ye kaydetmez, sadece görünüm). Silmek için yandaki kutucuğu seçip butona bas.")

    # Silme İşlemi için Checkbox'lı liste
    # Streamlit'te satır silmek biraz farklıdır, en basiti seçip silmektir.
    
    silinecek_indexler = []
    for index, row in df.iterrows():
        col_list1, col_list2 = st.columns([0.1, 0.9])
        with col_list1:
            if st.checkbox("", key=index):
                silinecek_indexler.append(index)
        with col_list2:
            st.text(f"{row['Tarih']} | {row['Tür']} | {row['Kategori']} | {row['Tutar']} TL | {row['Açıklama']}")
        st.divider()

    if silinecek_indexler:
        if st.button("Seçilileri Sil"):
            df = df.drop(silinecek_indexler)
            veri_kaydet(df)
            st.success("Seçilen kayıtlar silindi.")
            st.rerun()