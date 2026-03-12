import streamlit as st
import base64
import re
import io
from mistralai import Mistral
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Pt

# --- 1. دالة تنظيف النص وتنظيمه ---
def clean_and_format_text(ocr_pages):
    final_text = ""

    for i, page in enumerate(ocr_pages):
        text = page.markdown

        # توحيد الأسطر والمسافات دون مبالغة
        text = text.replace('\r\n', '\n').replace('\r', '\n')
        text = re.sub(r'[ \t]+', ' ', text)
        text = re.sub(r'\n{3,}', '\n\n', text).strip()

        # إضافة فاصل صفحات واضح
        page_header = f"\n\n--- صفحة {i+1} ---\n\n"
        final_text += page_header + text

    return final_text.strip()

# --- 2. دالة إنشاء ملف الوورد ---
def create_word_file(text):
    doc = Document()

    # النمط الأساسي
    style = doc.styles['Normal']
    style.font.name = 'Arial'
    style.font.size = Pt(14)

    lines = text.split('\n')

    for line in lines:
        stripped = line.strip()

        if not stripped:
            doc.add_paragraph("")
            continue

        # عنوان الصفحة
        if re.match(r'^--- صفحة \d+ ---$', stripped):
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.space_after = Pt(6)
            run = p.add_run(stripped)
            run.bold = True
            run.font.size = Pt(14)
            continue

        # عنوان رئيسي أو فرعي محتمل
        is_heading = (
            len(stripped) <= 50 and
            not stripped.endswith('،') and
            not stripped.endswith('.') and
            not stripped.endswith(':') and
            not re.match(r'^\d+\s*$', stripped)
        ) or re.match(r'^(الفصل|الباب|المبحث|المطلب|المسألة|الدرس|المحاضرة|عنوان)', stripped)

        if is_heading:
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
            p.paragraph_format.space_after = Pt(3)
            run = p.add_run(stripped)
            run.bold = True
            run.font.size = Pt(15)
            continue

        # فقرة عادية بتنسيق خفيف
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        p.paragraph_format.space_after = Pt(2)
        p.paragraph_format.line_spacing = 1.15
        run = p.add_run(stripped)
        run.font.size = Pt(14)

    bio = io.BytesIO()
    doc.save(bio)
    return bio.getvalue()

# --- 3. واجهة المستخدم (Streamlit) ---
st.set_page_config(page_title="معالج الكتب الذكي", page_icon="📚")
st.title("معالج الكتب العربي الذكي 🤖📖")

with st.sidebar:
    st.header("الإعدادات")
    # إحضار المفتاح من الخزنة السرية
api_key = st.secrets["MISTRAL_API_KEY"]

# تعريف العميل باستخدام المفتاح
client = Mistral(api_key=api_key)

uploaded_file = st.file_uploader("اختر ملف PDF", type=["pdf"])

if uploaded_file and api_key:
    if st.button("ابدأ عملية الاستخراج والتنسيق ✨"):
        try:
            client = Mistral(api_key=api_key)

            with st.status("جاري معالجة الكتاب..."):
                # تحويل الملف إلى Base64
                file_bytes = uploaded_file.read()
                encoded_pdf = base64.b64encode(file_bytes).decode("utf-8")

                # طلب الاستخراج من Mistral
                st.write("🔄 يتم الآن قراءة النص بالذكاء الاصطناعي...")
                ocr_response = client.ocr.process(
                    model="mistral-ocr-latest",
                    document={
                        "type": "document_url",
                        "document_url": f"data:application/pdf;base64,{encoded_pdf}"
                    }
                )

                # تنظيف وتنسيق النص
                st.write("🧹 جاري تنظيف وتنسيق النص العربي...")
                full_text = clean_and_format_text(ocr_response.pages)

                # إنشاء ملف الوورد
                word_data = create_word_file(full_text)

                # عرض النص المستخرج
                st.text_area("النص المستخرج:", full_text, height=300)

                # زر التحميل الأول
                if full_text.strip():
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
