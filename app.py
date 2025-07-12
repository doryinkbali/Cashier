import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import datetime
import io
from reportlab.lib.pagesizes import A5
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm

# ===== KONFIGURASI GOOGLE API =====
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]
SERVICE_ACCOUNT_FILE = "/tmp/service_account.json"
with open(SERVICE_ACCOUNT_FILE, "w") as f:
    f.write(st.secrets["SERVICE_ACCOUNT"])

# ===== AUTHENTIKASI =====
creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
client = gspread.authorize(creds)
sheet = client.open("Data Kasir Studio").worksheet("Transaksi")

# ===== FUNGSI BUAT STRUK PDF DENGAN REPORTLAB =====
def buat_struk_pdf(nama, tanggal, item, payment, harga_format):
    try:
        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=A5)
        width, height = A5

        # Header besar
        c.setFont("Helvetica-Bold", 22)
        c.drawCentredString(width / 2, height - 2 * cm, "DORY INK BALI")

        # Garis horizontal
        c.setLineWidth(1)
        c.line(1 * cm, height - 2.3 * cm, width - 1 * cm, height - 2.3 * cm)

        # Alamat dan kontak
        c.setFont("Helvetica", 10)
        c.drawCentredString(width / 2, height - 3.2 * cm, "Jl. Poppies Lane II, Kuta, Bali")
        c.drawCentredString(width / 2, height - 3.7 * cm, "Whats app : 0811-3982-040")

        # Garis horizontal kedua
        c.line(1 * cm, height - 4.2 * cm, width - 1 * cm, height - 4.2 * cm)

        # Konten utama
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

        # Garis horizontal bawah
        c.line(1 * cm, start_y - 5 * line_height, width - 1 * cm, start_y - 5 * line_height)

        # Footer
        footer_text_1 = "Thank you for trusting us with your art"
        footer_text_2 = "Instagram: @doryinkbali"
        footer_text_3 = "Facebook : Dory Ink Bali"

        c.setFont("Helvetica-Oblique", 9)
        c.drawCentredString(width / 2, start_y - 6 * line_height, footer_text_1)
        c.drawCentredString(width / 2, start_y - 6.7 * line_height, footer_text_2)
        c.drawCentredString(width / 2, start_y - 7.4 * line_height, footer_text_3)

        c.showPage()
        c.save()

        buffer.seek(0)
        return buffer, f"Struk_{nama}_{tanggal.replace('/', '-')}.pdf"

    except Exception as e:
        st.error("❌ Gagal membuat struk PDF.")
        st.exception(e)
        return None, None

# ===== STREAMLIT UI =====
st.set_page_config(page_title="Kasir Tattoo", layout="centered")
st.markdown('<div class="title">📋 Kasir Tattoo - Dory Ink Bali</div>', unsafe_allow_html=True)

with st.form("kasir_form"):
    nama = st.text_input("👤 Nama Pelanggan")
    tanggal = st.date_input("📅 Tanggal", value=datetime.date.today())
    item = st.selectbox("🎨 Jenis Tattoo", ["Small Tattoo", "Medium Tattoo", "Big Tattoo"])
    payment = st.selectbox("💳 Metode Pembayaran", ["Cash", "Card", "Transfer"])
    harga = st.number_input("💰 Harga (Rp)", min_value=0, step=50000)
    artist_percent = st.selectbox("🎯 Artist Share (%)", options=[40, 45, 50, 55, 60, 65, 70])
    konfirmasi = st.checkbox("✅ Saya sudah mengecek dan ingin menyimpan")
    submitted = st.form_submit_button("💾 Simpan & Buat Struk")

if submitted:
    if not nama:
        st.warning("⚠️ Mohon isi nama pelanggan.")
    elif not konfirmasi:
        st.warning("⚠️ Centang dulu kotak konfirmasi sebelum menyimpan.")
    else:
        try:
            formatted_tanggal = tanggal.strftime("%d/%m/%Y")
            harga_format = f"Rp{harga:,.0f}".replace(",", ".")
            artist_price_value = harga * (artist_percent / 100)
            artist_price_format = f"Rp{artist_price_value:,.0f}".replace(",", ".")

            sheet.append_row([
                nama,
                formatted_tanggal,
                item,
                payment,
                harga_format,
                artist_price_format
            ])

            st.success("✅ Data berhasil disimpan ke Google Sheets!")

            pdf_data, pdf_nama = buat_struk_pdf(nama, formatted_tanggal, item, payment, harga_format)
            if pdf_data:
                st.download_button("📥 Unduh Struk PDF", pdf_data, file_name=pdf_nama, mime="application/pdf")

        except Exception as e:
            st.error("❌ Gagal menyimpan data atau membuat struk.")
            st.exception(e)
