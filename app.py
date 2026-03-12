import streamlit as st
import base64
import re
import io
from mistralai import Mistral
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH

# --- 1. دالة تنظيف النص وتنظيمه ---
def clean_and_format_text(ocr_pages):
    final_text = ""
    for i, page in enumerate(ocr_pages):
        text = page.markdown
        # إزالة المسافات الزائدة (أكثر من مسافتين)
        text = re.sub(r'\s{2,}', ' ', text)
        # إضافة فاصل صفحات واضح
        page_header = f"\n\n--- صفحة {i+1} ---\n\n"
        final_text += page_header + text
    return final_text

# --- 2. دالة إنشاء ملف الوورد ---
def create_word_file(text):
    doc = Document()
    # إعداد المستند ليدعم الكتابة من اليمين لليسار
    style = doc.styles['Normal']
    style.font.name = 'Arial'

    for line in text.split('\n'):
        p = doc.add_paragraph(line)
        p.alignment = WD_ALIGN_PARAGRAPH.RIGHT # محاذاة لليمين

    # حفظ الملف في ذاكرة مؤقتة (Buffer) لتحميله عبر المتصفح
    bio = io.BytesIO()
    doc.save(bio)
    return bio.getvalue()

# --- 3. واجهة المستخدم (Streamlit) ---
st.set_page_config(page_title="معالج الكتب الذكي", page_icon="📚")
st.title("معالج الكتب العربي الذكي 🤖📖")

with st.sidebar:
    st.header("الإعدادات")
# 1. جلب المفتاح بأمان من الخزنة
api_key = st.secrets["MISTRAL_API_KEY"]
client = Mistral(api_key=api_key)

# 2. إرسال الطلب ومعالجة النتيجة (الربط)
if uploaded_file is not None:
    with st.spinner("جاري قراءة النص وتحليله... ⏳"):
        # نقوم برفع الملف ومعالجته عبر API
        ocr_response = client.ocr(
            model="mistral-ocr-latest",
            document={"type": "file", "file": uploaded_file}
        )
        
        # 3. معالجة النص وعرضه
        full_text = clean_and_format_text(ocr_response.pages)
        st.text_area("النص المستخرج:", full_text, height=300)

        # 4. تحويل النص لملف Word وإظهار زر التحميل (التحسين)
        if full_text.strip():
            word_data = create_word_file(full_text)
            st.download_button(
                label="📥 تحميل النص كملف Word",
                data=word_data,
                file_name="mistral_ocr_result.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )

            st.success("تمت العملية بنجاح! 🎉")

            # عرض النص في التطبيق للمعاينة
            st.text_area("معاينة النص المستخرج:", full_text, height=300)

            # أزرار التحميل
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
      st.error(f"حدث خطأ: {e}")
     else:
    st.info("يرجى إدخال مفتاح API ورفع ملف للبدء.")
