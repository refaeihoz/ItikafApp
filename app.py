import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import json
from datetime import date
import streamlit.components.v1 as components

# إعداد صفحة البرنامج (يجب أن يكون أول سطر)
st.set_page_config(page_title="حسابات الاعتكاف", page_icon="🕌", layout="wide", initial_sidebar_state="collapsed")

# ==========================================
# 🎨 كود CSS السحري للـ UI/UX الفخم (كما هو من كودك)
# ==========================================
st.markdown("""
    <style>
    /* استيراد خط "القاهرة" الفخم من جوجل */
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;800&display=swap');

    /* تطبيق الخط والاتجاه على كل البرنامج وفرض لون الخلفية */
    .stApp {
        font-family: 'Cairo', sans-serif !important;
        direction: rtl;
        background-color: #F4F7F6 !important;
    }
    
    /* 🚨 حل مشكلة الوضع الليلي: إجبار كل النصوص على اللون الغامق */
    p, h1, h2, h3, h4, h5, h6, label, div[data-testid="stMarkdownContainer"] {
        color: #2C3E50 !important;
        text-align: right !important;
    }

    /* إجبار مربعات الإدخال إن الكلام جواها يكون غامق ومقروء */
    input, .stSelectbox div[data-baseweb="select"] {
        color: #2C3E50 !important;
        -webkit-text-fill-color: #2C3E50 !important; 
    }

    /* إخفاء القائمة العلوية وعلامة Streamlit المائية */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* 🌟 تصميم العنوان الرئيسي */
    .main-title {
        text-align: center !important;
        background: linear-gradient(45deg, #1E88E5, #004D40);
        -webkit-background-clip: text !important;
        -webkit-text-fill-color: transparent !important;
        font-weight: 800;
        padding-bottom: 20px;
    }

    /* 🌟 تصميم كروت الإجماليات (Metrics) */
    div[data-testid="metric-container"] {
        background: #ffffff !important;
        border-right: 5px solid #1E88E5;
        padding: 20px;
        border-radius: 16px;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.04);
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }
    div[data-testid="metric-container"]:hover {
        transform: translateY(-5px);
        box-shadow: 0 15px 35px rgba(0, 0, 0, 0.08);
    }
    div[data-testid="stMetricValue"], div[data-testid="stMetricValue"] > div {
        font-size: 2.5rem !important;
        color: #1E88E5 !important; 
        font-weight: 800 !important;
    }
    div[data-testid="stMetricLabel"], div[data-testid="stMetricLabel"] > div {
        font-size: 1.1rem !important;
        color: #7F8C8D !important;
        font-weight: 600 !important;
    }

    /* 🌟 تصميم نماذج الإدخال (Forms) */
    div[data-testid="stForm"] {
        background: #ffffff !important;
        border-radius: 20px;
        padding: 30px 20px;
        border: none;
        box-shadow: 0 8px 25px rgba(0, 0, 0, 0.03);
    }

    /* 🌟 تصميم الأزرار الأساسية (زر الحفظ) */
    .stButton>button[kind="primary"] {
        background: linear-gradient(135deg, #1E88E5 0%, #1565C0 100%) !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 10px 0 !important;
        box-shadow: 0 4px 15px rgba(30, 136, 229, 0.3) !important;
    }
    .stButton>button[kind="primary"] p, .stButton>button[kind="primary"] div {
        color: white !important;
        font-weight: 700 !important;
        font-size: 1.1rem !important;
    }

    /* 🌟 تصميم الأزرار الثانوية (زر الحذف) */
    .stButton>button[kind="secondary"] {
        background-color: #FFEBEE !important;
        border: none !important;
        border-radius: 10px !important;
    }
    .stButton>button[kind="secondary"] p {
        color: #D32F2F !important;
    }

    /* 🌟 تصميم كروت السجل (الجدول المخصص) */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background: #ffffff !important;
        border-radius: 16px !important;
        border: 1px solid #F0F0F0 !important;
        box-shadow: 0 4px 10px rgba(0, 0, 0, 0.02) !important;
        padding: 5px;
        margin-bottom: 10px;
    }
    
    /* تصميم التابات (Tabs) */
    button[data-baseweb="tab"] div {
        font-family: 'Cairo', sans-serif !important;
        font-size: 1.1rem !important;
        font-weight: 600 !important;
        color: #2C3E50 !important;
    }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 🔗 الاتصال الذكي بقاعدة بيانات Google Sheets (كاش لحل مشكلة الـ Quota)
# ==========================================
@st.cache_resource
def init_connection():
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    try:
        # المحاولة الأولى: من اللاب توب
        creds = Credentials.from_service_account_file("secrets.json", scopes=scopes)
    except FileNotFoundError:
        # المحاولة الثانية: من الإنترنت (Streamlit Secrets)
        creds_dict = json.loads(st.secrets["gcp_keys"])
        creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
        
    client = gspread.authorize(creds)
    sheet = client.open("itikaf_db")
    return sheet.worksheet("income"), sheet.worksheet("expenses")

try:
    income_sheet, expenses_sheet = init_connection()
except Exception as e:
    st.error(f"⚠️ خطأ في الاتصال بجوجل شيت! التفاصيل: {e}")
    st.stop()

# 🟢 استخدام الكاش لتخزين البيانات وعدم إرهاق سيرفر جوجل
@st.cache_data(ttl=60) # تحديث تلقائي كل 60 ثانية
def get_data():
    return income_sheet.get_all_records(), expenses_sheet.get_all_records()

incomes, expenses = get_data()

# دالة آمنة لتحويل النصوص لأرقام
def safe_float(val):
    try:
        return float(str(val).replace(',', ''))
    except:
        return 0.0

# حساب الإجماليات
total_income = sum(safe_float(row.get('amount', 0)) for row in incomes)
total_expenses = sum(safe_float(row.get('amount', 0)) for row in expenses)

balance = total_income - total_expenses
treasury = balance if balance > 0 else 0.0
debt = abs(balance) if balance < 0 else 0.0

# 🌟 عرض العنوان الفخم
st.markdown("<h1 class='main-title'>🕌 إدارة حسابات الاعتكاف</h1>", unsafe_allow_html=True)
st.write("") 

tab1, tab2, tab3 = st.tabs(["📊 الخلاصة والتقارير", "💵 الإيرادات", "🛒 المصروفات"])

# ==========================================
# صفحة الملخص
# ==========================================
with tab1:
    st.write("")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("💰 الرصيد المتاح (الخزنة)", f"{treasury:.2f} ₺")
    with col2:
        st.metric("⚠️ الدين (عجز الميزانية)", f"{debt:.2f} ₺")
        
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### 📊 تحليل المصروفات")
    
    # تجميع بيانات المصروفات للرسم البياني
    cat_totals = {}
    for exp in expenses:
        cat = exp.get('category', 'غير محدد')
        amt = safe_float(exp.get('amount', 0))
        cat_totals[cat] = cat_totals.get(cat, 0) + amt
        
    chart_data = [(cat, amt) for cat, amt in cat_totals.items() if amt > 0]
    
    if chart_data:
        max_amount = max([amt for cat, amt in chart_data])
        for category, amount in chart_data:
            percentage = (amount / max_amount) * 100 if max_amount > 0 else 0
            st.markdown(f"""
            <div style="margin-bottom: 20px; direction: rtl; background: #fff; padding: 15px; border-radius: 12px; box-shadow: 0 4px 10px rgba(0,0,0,0.02); border: 1px solid #eee;">
                <div style="display: flex; justify-content: space-between; margin-bottom: 8px; font-size: 1.1rem;">
                    <span style="font-weight: 700; color: #34495E;">{category}</span>
                    <span style="color: #1E88E5; font-weight: 800;">{amount:.2f} ₺</span>
                </div>
                <div style="background-color: #EDF2F7; border-radius: 10px; width: 100%; height: 10px; overflow: hidden;">
                    <div style="background: linear-gradient(90deg, #1E88E5, #42A5F5); width: {percentage}%; height: 100%; border-radius: 10px; transition: width 0.8s ease-in-out;"></div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("لم يتم تسجيل أي مصروفات بعد لعرض الرسم البياني.")

# ==========================================
# صفحة الإيرادات
# ==========================================
with tab2:
    st.write("")
    st.metric("📈 إجمالي الإيرادات", f"{total_income:.2f} ₺")
    st.markdown("<br>", unsafe_allow_html=True)
    
    with st.form("income_form", clear_on_submit=True): 
        st.markdown("### ➕ تسجيل إيراد جديد")
        
        i_date = st.date_input("التاريخ", date.today())
        i_name = st.text_input("اسم المعتكف / المتبرع", placeholder="اكتب الاسم هنا...")
        i_type = st.selectbox("نوع الدفع", ["اشتراك اعتكاف", "تبرع عام", "كفالة معتكف"])
        i_amount = st.number_input("المبلغ", min_value=0.0, step=50.0, format="%.2f", value=None, placeholder="اكتب المبلغ...")
        i_notes = st.text_input("ملاحظات", placeholder="أي تفاصيل إضافية (اختياري)...")
        
        st.write("") 
        submitted_income = st.form_submit_button("💾 حـفـظ الإيــراد", type="primary", use_container_width=True)
        if submitted_income:
            if not i_name or i_name.strip() == "":
                st.error("⚠️ يرجى إدخال اسم المعتكف أو المتبرع أولاً!")
            elif i_amount is None or i_amount <= 0:
                st.error("⚠️ يرجى إدخال مبلغ صحيح أكبر من الصفر!")
            else:
                # الحفظ في جوجل شيت
                income_sheet.append_row([i_name, i_type, float(i_amount), i_notes, str(i_date)])
                get_data.clear() # 🟢 مسح الكاش عشان البرنامج يقرأ الداتا الجديدة فوراً
                st.success("🎉 تم الحفظ بنجاح!")
                st.rerun()
            
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### 📋 سجل الإيرادات")
    
    if incomes:
        # استخدام enumerate لحفظ رقم الصف الحقيقي للحذف (الصف في الشيت = index + 2)
        for i, inc in reversed(list(enumerate(incomes))):
            inc_date = inc.get('date', '-')
            with st.container(border=True):
                col1, col2 = st.columns([5, 1])
                with col1:
                  st.markdown(f"<span style='font-size: 1.1rem; font-weight: 700; color: #2C3E50;'>👤 {inc[1]}</span>", unsafe_allow_html=True)
                    st.markdown(f"<span style='color: #7F8C8D; font-size: 0.9em; font-weight: 600;'>{inc[2]} • 📅 {inc_date}</span>", unsafe_allow_html=True)
                    st.markdown(f"<span style='color: #1E88E5; font-size: 1.4em; font-weight: 800;'>{inc[3]:.2f} ₺</span>", unsafe_allow_html=True)
                    if inc[4]:
                        st.caption(f"📝 {inc[4]}")
                with col2:
                    st.write("")
                    st.write("")
                    if st.button("🗑️", key=f"del_inc_{i}", help="حذف", type="secondary"):
                        # الحذف برقم الصف
                        income_sheet.delete_rows(i + 2)
                        get_data.clear() # 🟢 مسح الكاش
                        st.rerun()
    else:
        st.info("لا توجد إيرادات مسجلة حتى الآن.")

# ==========================================
# صفحة المصروفات
# ==========================================
with tab3:
    st.write("")
    st.metric("📉 إجمالي المصروفات", f"{total_expenses:.2f} ₺")
    st.markdown("<br>", unsafe_allow_html=True)
    
    with st.form("expense_form", clear_on_submit=True):
        st.markdown("### ➖ تسجيل مصروف جديد")
        
        e_date = st.date_input("التاريخ", date.today())
        e_category = st.selectbox("بند الصرف", ["سحور", "إفطار", "مشروبات وضيافة", "أدوات نظافة", "طوارئ ونثريات"])
        e_amount = st.number_input("المبلغ", min_value=0.0, step=50.0, format="%.2f", value=None, placeholder="اكتب المبلغ...")
        e_buyer = st.text_input("المسؤول عن الشراء", placeholder="مين اللي اشترى؟")
        e_notes = st.text_input("ملاحظات وتفاصيل", placeholder="مثال: عيش وفول من مطعم كذا...")
        
        st.write("")
        submitted_expense = st.form_submit_button("💾 حـفـظ المصـروف", type="primary", use_container_width=True)
        if submitted_expense:
            if e_amount is None or e_amount <= 0:
                st.error("⚠️ يرجى إدخال مبلغ صحيح أكبر من الصفر!")
            elif not e_buyer or e_buyer.strip() == "":
                st.error("⚠️ يرجى إدخال اسم المسؤول عن الشراء!")
            else:
                # الحفظ في جوجل شيت
                expenses_sheet.append_row([str(e_date), e_category, float(e_amount), e_buyer, e_notes])
                get_data.clear() # 🟢 مسح الكاش
                st.success("🎉 تم الحفظ بنجاح!")
                st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### 📋 سجل المصروفات")
    
    if expenses:
        for i, exp in reversed(list(enumerate(expenses))):
            with st.container(border=True):
                col1, col2 = st.columns([5, 1])
                with col1:
                    st.markdown(f"<span style='font-size: 1.1rem; font-weight: 700; color: #2C3E50;'>🏷️ {exp.get('category','')}</span>", unsafe_allow_html=True)
                    st.markdown(f"<span style='color: #7F8C8D; font-size: 0.9em; font-weight: 600;'>📅 {exp.get('date','')} • 👤 {exp.get('buyer','')}</span>", unsafe_allow_html=True)
                    st.markdown(f"<span style='color: #E53935; font-size: 1.4em; font-weight: 800;'>{safe_float(exp.get('amount',0)):.2f} ₺</span>", unsafe_allow_html=True)
                    if exp.get('notes'):
                        st.caption(f"📝 {exp['notes']}")
                with col2:
                    st.write("")
                    st.write("")
                    if st.button("🗑️", key=f"del_exp_{i}", help="حذف", type="secondary"):
                        expenses_sheet.delete_rows(i + 2)
                        get_data.clear() # 🟢 مسح الكاش
                        st.rerun()
    else:
        st.info("لا توجد مصروفات مسجلة حتى الآن.")

# ==========================================
# 🟢 كود جافا سكريبت لمنع زر الـ Enter
# ==========================================
components.html(
    """
    <script>
    const doc = window.parent.document;
    doc.addEventListener('keydown', function(event) {
        if (event.key === 'Enter') {
            const activeElement = doc.activeElement;
            if (activeElement.tagName === 'INPUT') {
                event.preventDefault(); 
                const inputs = Array.from(doc.querySelectorAll('input:not([type="hidden"])'));
                const index = inputs.indexOf(activeElement);
                if (index > -1 && index < inputs.length - 1) {
                    inputs[index + 1].focus();
                }
            }
        }
    }, true);
    </script>
    """,
    height=0,
    width=0,
)
