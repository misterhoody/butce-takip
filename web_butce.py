import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import matplotlib.pyplot as plt

# Sayfa Ayarları
st.set_page_config(page_title="Cebimdeki Ekonomi (Bulut)", page_icon="☁️", layout="centered")

# --- Google Sheets Bağlantısı ---
def get_data():
    # Streamlit Secrets'tan anahtarı al
    secrets = st.secrets["gcp_service_account"]
    
    # Bağlantı kapsamı
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    
    # Kimlik doğrulama
    credentials = Credentials.from_service_account_info(secrets, scopes=scopes)
    gc = gspread.authorize(credentials)
    
    # Dosyayı aç (Google Sheet adının "ButceVerileri" olduğundan emin ol)
    try:
        sh = gc.open("ButceVerileri")
        worksheet = sh.sheet1
        return worksheet
    except Exception as e:
        st.error(f"Google Sheet bulunamadı! Lütfen dosya adının 'ButceVerileri' olduğundan ve servis hesabıyla paylaşıldığından emin olun. Hata: {e}")
        return None

def veri_yukle(worksheet):
    if worksheet:
        data = worksheet.get_all_records()
        df = pd.DataFrame(data)
        # Tutar sütunu bazen metin gelebilir, sayıya çevirelim
        if not df.empty:
            # Virgülleri noktaya çevirip float yap
            if df["Tutar"].dtype == "object":
                 df["Tutar"] = df["Tutar"].astype(str).str.replace(",", ".").astype(float)
        return df
    return pd.DataFrame()

def veri_ekle(worksheet, veri_listesi):
    if worksheet:
        # Veriyi en sona ekle
        worksheet.append_row(veri_listesi)

# --- Ana Uygulama ---
st.title("☁️ Bulut Tabanlı Ekonomi Takip")

# Bağlantıyı Kur
sheet = get_data()
if sheet:
    df = veri_yukle(sheet)
else:
    st.stop()

tab1, tab2 = st.tabs(["➕ Ekle", "📊 Raporlar"])

# --- TAB 1: VERİ GİRİŞİ ---
with tab1:
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
            tarih = datetime.now().strftime("%Y-%m-%d %H:%M")
            # Google Sheets'e gönderilecek liste
            yeni_kayit = [tarih, tur, kategori, aciklama, tutar]
            
            try:
                veri_ekle(sheet, yeni_kayit)
                st.success("Kayıt Google E-Tablo'ya işlendi!")
                # Önbelleği temizle ki tablo güncellensin
                st.cache_data.clear()
                st.rerun()
            except Exception as e:
                st.error(f"Kayıt hatası: {e}")
        else:
            st.warning("Tutar giriniz.")

    st.divider()
    st.subheader("Son 5 İşlem")
    if not df.empty:
        st.dataframe(df.tail(5))

# --- TAB 2: ANALİZ ---
with tab2:
    if not df.empty:
        gelir = df[df["Tür"] == "Gelir"]["Tutar"].sum()
        gider = df[df["Tür"] == "Gider"]["Tutar"].sum()
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Gelir", f"{gelir:,.2f}")
        col2.metric("Gider", f"{gider:,.2f}")
        col3.metric("Kalan", f"{gelir - gider:,.2f}")
        
        st.divider()
        
        # Grafik
        gider_df = df[df["Tür"] == "Gider"]
        if not gider_df.empty:
            fig, ax = plt.subplots()
            gider_grup = gider_df.groupby("Kategori")["Tutar"].sum()
            ax.pie(gider_grup, labels=gider_grup.index, autopct='%1.1f%%')
            st.pyplot(fig)
    else:
        st.info("Henüz veri yok.")
