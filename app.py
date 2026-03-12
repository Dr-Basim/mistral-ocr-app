import streamlit as st
import base64
import re
import io
from mistralai import Mistral
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
import streamlit as st
import base64
import re
import io
import importlib.metadata  # المكتبة الحديثة للكشف عن النسخ
from mistralai import Mistral
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH

# --- اختبار نسخة المكتبة ---
try:
    current_version = importlib.metadata.version("mistralai")
    st.info(f"📦 نسخة المكتبة المكتشفة الآن: {current_version}")
except Exception:
    st.warning("⚠️ لم يتم العثور على مكتبة mistralai في هذه البيئة.")

# ... باقي الكود (دالة تنظيف النص، إلخ)

# --- 1. دالة تنظيف النص وتنظيمه ---
def clean_and_format_text(ocr_pages):
    final_text = ""
    for i, page in enumerate(ocr_pages):
        # استخراج النص من خاصية markdown المتوفرة في استجابة ميسترال
        text = page.markdown
        # إزالة المسافات الزائدة (أكثر من مسافتين)
        text = re.sub(r'\s{2,}', ' ', text)
        # إضافة فاصل صفحات واضح لترتيب المستند
        page_header = f"\n\n--- صفحة {i+1} ---\n\n"
        final_text += page_header + text
    return final_text

# --- 2. دالة إنشاء ملف الوورد ---
def create_word_file(text):
    doc = Document()
    # إعداد النمط الافتراضي ليدعم اللغة العربية
    style = doc.styles['Normal']
    style.font.name = 'Arial'

    for line in text.split('\n'):
        if line.strip(): # تجنب إضافة أسطر فارغة بلا داعي
            p = doc.add_paragraph(line)
            p.alignment = WD_ALIGN_PARAGRAPH.RIGHT  # محاذاة النص لليمين
    
    # حفظ الملف في ذاكرة مؤقتة (Buffer)
    bio = io.BytesIO()
    doc.save(bio)
    return bio.getvalue()

# --- 3. واجهة المستخدم (Streamlit) ---
st.set_page_config(page_title="معالج الكتب الذكي", page_icon="📚")
st.title("معالج الكتب العربي الذكي 🤖📖")

# جلب المفتاح من الخزنة السرية (Secrets) الخاصة بـ Streamlit
try:
    api_key = st.secrets["MISTRAL_API_KEY"]
except Exception:
    api_key = None
    st.error("لم يتم العثور على مفتاح MISTRAL_API_KEY في الإعدادات.")

# تعريف العميل (Client)
if api_key:
    client = Mistral(api_key=api_key)

uploaded_file = st.file_uploader("اختر ملف PDF", type=["pdf"])

if uploaded_file and api_key:
    if st.button("ابدأ عملية الاستخراج والتنسيق ✨"):
        try:
            with st.status("جاري معالجة الكتاب..."):
                # تحويل الملف المرفوع إلى Base64 ليتم إرساله عبر الرابط الافتراضي (Data URL)
                file_bytes = uploaded_file.read()
                encoded_pdf = base64.b64encode(file_bytes).decode("utf-8")

                st.write("🔄 يتم الآن قراءة النص بالذكاء الاصطناعي عبر Mistral OCR...")
                st.write("الأدوات المتاحة داخل العميل حالياً:", dir(client))

                # الاستدعاء الصحيح للنسخة 1.5.0 وما فوق
                ocr_response = client.ocr.process(
                 model="mistral-ocr-latest",
                  document={
                  "type": "document_url",
                  "document_url": f"data:application/pdf;base64,{encoded_pdf}"
                  }
                   )

                st.write("🧹 جاري تنظيف وتنسيق النص العربي المستخرج...")
                full_text = clean_and_format_text(ocr_response.pages)
                
                # تحويل النص النهائي إلى بيانات ملف Word
                word_data = create_word_file(full_text)

            # --- عرض النتائج وأزرار التحميل ---
            st.success("تمت المعالجة بنجاح! 🎉")
            
            # معاينة النص في منطقة نصية قابلة للنسخ
            st.text_area("معاينة النص المستخرج:", full_text, height=400)

            # توزيع أزرار التحميل في أعمدة لتنظيم الواجهة
            col1, col2 = st.columns(2)
            with col1:
                st.download_button(
                    label="تحميل كملف Word 📄",
                    data=word_data,
                    file_name="extracted_book.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                )
            with col2:
                st.download_button(
                    label="تحميل كملف نصي Text 📝",
                    data=full_text,
                    file_name="extracted_book.txt",
                    mime="text/plain"
                )

        except Exception as e:
            st.error(f"حدث خطأ أثناء الاتصال بالخادم: {e}")
            st.info("تأكد من تحديث مكتبة mistralai في ملف requirements.txt إلى الإصدار 1.4.0 أو أحدث.")
else:
    if not api_key:
        st.warning("يرجى التأكد من إضافة مفتاح API في خزنة الأسرار.")
    else:
        st.info("يرجى رفع ملف PDF للبدء في الاستخراج.")
