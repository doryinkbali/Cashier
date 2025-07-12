import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import datetime
import io
from reportlab.lib.pagesizes import A5
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
import re

# ===== KONFIGURASI GOOGLE API =====
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

# ===== LOAD SERVICE ACCOUNT DARI STREAMLIT SECRETS =====
try:
    creds = Credentials.from_service_account_info(
        st.secrets["SERVICE_ACCOUNT"], scopes=SCOPES
    )
    client = gspread.authorize(creds)
    sheet = client.open("Data Kasir Studio").worksheet("Transaksi")
except KeyError as e:
    st.error("❌ Gagal mengakses kredensial: Kunci 'SERVICE_ACCOUNT' tidak ditemukan di secrets.toml. Pastikan secrets.toml dikonfigurasi dengan benar.")
    st.exception(e)
    st.stop()
except Exception as e:
    st.error("❌ Gagal mengautentikasi dengan Google Sheets. Periksa kredensial atau izin spreadsheet.")
    st.exception(e)
    st.stop()

# ===== FUNGSI BUAT STRUK PDF DENGAN REPORTLAB =====
def buat_struk_pdf(nama, tanggal, item, payment, harga_format):
    try:
        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=A5)
        width, height = A5

        # Header
        c.setFont("Helvetica-Bold", 22)
        c.drawCentredString(width / 2, height - 2 * cm, "DORY INK BALI")
        c.setLineWidth(1)
        c.line(1 * cm, height - 2.3 * cm, width - 1 * cm, height - 2.3 * cm)
        c.setFont("Helvetica", 10)
        c.drawCentredString(width / 2, height - 3.2 * cm, "Jl. Poppies Lane II, Kuta, Bali")
        c.drawCentredString(width / 2, height - 3.7 * cm, "WhatsApp: 0811-3982-040")
        c.line(1 * cm, height - 4.2 * cm, width - 1 * cm, height - 4.2 * cm)

        # Konten Struk
        c.setFont("Helvetica", 12)
        start_y = height - 5.5 * cm
        line_height = 1.2 * cm

        c.drawString(2 * cm, start_y, "Date")
        c.drawRightString(width - 2 * cm, start_y, tanggal)

        c.drawString(2 * cm, start_y - line_height, "Client Name")
        c.drawRightString(width - 2 * cm, start_y - line_height, nama)

        c.drawString(2 * cm, start_y - 2 * line_height, "Tattoo Type")
        c.drawRightString(width - 2 * cm, start_y - 2 * line_height, item)

        c.drawString(2 * cm, start_y - 3 * line_height, "Payment")
        c.drawRightString(width - 2 * cm, start_y - 3 * line_height, payment)

        c.drawString(2 * cm, start_y - 4 * line_height, "Tattoo Price")
        c.drawRightString(width - 2 * cm, start_y - 4 * line_height, harga_format)

        c.line(1 * cm, start_y - 5 * line_height, width - 1 * cm, start_y - 5 * line_height)

        # Footer
        c.setFont("Helvetica-Oblique", 9)
        c.drawCentredString(width / 2, start_y - 6 * line_height, "Thank you for trusting us with your art")
        c.drawCentredString(width / 2, start_y - 6.7 * line_height, "Instagram: @doryinkbali")
        c.drawCentredString(width / 2, start_y - 7.4 * line_height, "Facebook: Dory Ink Bali")

        c.showPage()
        c.save()
        buffer.seek(0)

        # Membuat nama file yang aman
        safe_nama = re.sub(r'[^\w\s-]', '', nama).replace(' ', '_')
        pdf_nama = f"Struk_{safe_nama}_{tanggal.replace('/', '-')}.pdf"
        return buffer, pdf_nama

    except Exception as e:
        st.error("❌ Gagal membuat struk PDF.")
        st.exception(e)
        return None, None

# ===== STREAMLIT UI =====
st.set_page_config(page_title="Kasir Tattoo", layout="centered")

# CSS untuk styling
st.markdown("""
    <style>
    .title {
        font-size: 2.5em;
        font-weight: bold;
        text-align: center;
        color: #2E2E2E;
        margin-bottom: 1em;
    }
    .stButton>button {
        background-color: #4CAF50;
        color: white;
        border-radius: 5px;
    }
    .stButton>button:hover {
        background-color: #45a049;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown('<div class="title">📋 Kasir Tattoo - Dory Ink Bali</div>', unsafe_allow_html=True)

with st.form("kasir_form"):
    nama = st.text_input("👤 Nama Pelanggan", placeholder="Masukkan nama pelanggan")
    tanggal = st.date_input("📅 Tanggal", value=datetime.date.today(), max_value=datetime.date.today())
    item = st.selectbox("🎨 Jenis Tattoo", ["Small Tattoo", "Medium Tattoo", "Big Tattoo"])
    payment = st.selectbox("💳 Metode Pembayaran", ["Cash", "Card", "Transfer"])
    harga = st.number_input("💰 Harga (Rp)", min_value=10000, step=50000, value=100000)
    artist_percent = st.selectbox("🎯 Artist Share (%)", options=[40, 45, 50, 55, 60, 65, 70])
    konfirmasi = st.checkbox("✅ Saya sudah mengecek dan ingin menyimpan")
    submitted = st.form_submit_button("💾 Simpan & Buat Struk")

if submitted:
    if not nama.strip():
        st.warning("⚠️ Mohon isi nama pelanggan.")
    elif not konfirmasi:
        st.warning("⚠️ Centang kotak konfirmasi sebelum menyimpan.")
    elif harga <= 0:
        st.warning("⚠️ Harga harus lebih besar dari 0.")
    else:
        try:
            formatted_tanggal = tanggal.strftime("%d/%m/%Y")
            harga_format = f"Rp{harga:,.0f}".replace(",", ".")
            artist_price_value = harga * (artist_percent / 100)
            artist_price_format = f"Rp{artist_price_value:,.0f}".replace(",", ".")

            # Simpan ke Google Sheets
            sheet.append_row([
                nama.strip(),
                formatted_tanggal,
                item,
                payment,
                harga_format,
                artist_price_format
            ])

            st.success("✅ Data berhasil disimpan ke Google Sheets!")

            # Buat dan unduh struk PDF
            pdf_data, pdf_nama = buat_struk_pdf(nama.strip(), formatted_tanggal, item, payment, harga_format)
            if pdf_data:
                st.download_button(
                    label="📥 Unduh Struk PDF",
                    data=pdf_data,
                    file_name=pdf_nama,
                    mime="application/pdf"
                )

        except gspread.exceptions.APIError as e:
            st.error("❌ Gagal menyimpan data ke Google Sheets. Periksa izin atau koneksi.")
            st.exception(e)
        except Exception as e:
            st.error("❌ Terjadi kesalahan.")
            st.exception(e)
