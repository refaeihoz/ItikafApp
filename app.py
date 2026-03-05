import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import json
from datetime import date
import streamlit.components.v1 as components

# إعداد صفحة البرنامج
st.set_page_config(page_title="حسابات الاعتكاف", page_icon="🕌", layout="wide", initial_sidebar_state="collapsed")

# ==========================================
# 🟢 نظام التحكم في المظهر (فاتح - داكن - تلقائي)
# ==========================================
if "appearance_mode" not in st.session_state:
    st.session_state.appearance_mode = "تلقائي"

with st.sidebar:
    st.title("إعدادات البرنامج")
    st.session_state.appearance_mode = st.selectbox("مظهر التطبيق", ["فاتح ☀️", "داكن 🌙", "تلقائي 🖥️"], index=["فاتح ☀️", "داكن 🌙", "تلقائي 🖥️"].index(st.session_state.appearance_mode))

is_dark_final = False
if st.session_state.appearance_mode == "داكن 🌙":
    is_dark_final = True
elif st.session_state.appearance_mode == "تلقائي 🖥️":
    components.html("<script>window.parent.postMessage({type: 'theme', theme: window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'}, '*');</script>", height=0)

bg_color = "#121212" if is_dark_final else "#F4F7F6"
text_color = "#E0E0E0" if is_dark_final else "#2C3E50"
card_bg = "#1E1E1E" if is_dark_final else "#ffffff"
border_col = "#333333" if is_dark_final else "#F0F0F0"
highlight = "#64B5F6" if is_dark_final else "#1E88E5"
danger = "#EF5350" if is_dark_final else "#D32F2F"

# ==========================================
# 🎨 كود CSS السحري للـ UI/UX
# ==========================================
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;800&display=swap');
    .stApp {{ font-family: 'Cairo', sans-serif !important; direction: rtl; background-color: {bg_color} !important; }}
    p, h1, h2, h3, h4, h5, h6, label, div[data-testid="stMarkdownContainer"] {{ color: {text_color} !important; text-align: right !important; }}
    input, .stSelectbox div[data-baseweb="select"] {{ color: {text_color} !important; -webkit-text-fill-color: {text_color} !important; background-color: {card_bg} !important; }}
    #MainMenu, footer, header {{visibility: hidden;}}
    .main-title {{ text-align: center !important; background: linear-gradient(45deg, #1E88E5, #004D40); -webkit-background-clip: text !important; -webkit-text-fill-color: transparent !important; font-weight: 800; padding-bottom: 20px; }}
    div[data-testid="metric-container"] {{ background: {card_bg} !important; border-right: 5px solid {highlight}; padding: 20px; border-radius: 16px; box-shadow: 0 10px 30px rgba(0, 0, 0, 0.04); }}
    div[data-testid="stMetricValue"] > div {{ color: {highlight} !important; font-weight: 800 !important; }}
    div[data-testid="stForm"] {{ background: {card_bg} !important; border-radius: 20px; border: none; box-shadow: 0 8px 25px rgba(0, 0, 0, 0.03); }}
    div[data-testid="stVerticalBlockBorderWrapper"] {{ background: {card_bg} !important; border-radius: 16px !important; border: 1px solid {border_col} !important; }}
    .stButton>button[kind="primary"] {{ background: linear-gradient(135deg, #1E88E5 0%, #1565C0 100%) !important; border: none !important; border-radius: 12px !important; padding: 10px 0 !important; box-shadow: 0 4px 15px rgba(30, 136, 229, 0.3) !important; }}
    .stButton>button[kind="primary"] p, .stButton>button[kind="primary"] div {{ color: white !important; font-weight: 700 !important; font-size: 1.1rem !important; }}
    .stButton>button[kind="secondary"] {{ background-color: {'#3B2020' if is_dark_final else '#FFEBEE'} !important; border: none !important; border-radius: 10px !important; }}
    .stButton>button[kind="secondary"] p {{ color: {danger} !important; }}
    button[data-baseweb="tab"] div {{ font-family: 'Cairo', sans-serif !important; font-size: 1.1rem !important; font-weight: 600 !important; color: {text_color} !important; }}
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 🔗 الاتصال بقاعدة بيانات Google Sheets
# ==========================================
scopes = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

try:
    try:
        # المحاولة الأولى: اللاب توب
        creds = Credentials.from_service_account_file("secrets.json", scopes=scopes)
    except FileNotFoundError:
        # المحاولة الثانية: الإنترنت
        creds_dict = json.loads(st.secrets["gcp_keys"])
        creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
        
    client = gspread.authorize(creds)
    sheet = client.open("itikaf_db")
    income_sheet = sheet.worksheet("income")
    expenses_sheet = sheet.worksheet("expenses")
except Exception as e:
    st.error(f"⚠️ خطأ في الاتصال بجوجل شيت! التفاصيل: {e}")
    st.stop()

# جلب البيانات من الشيت
incomes = income_sheet.get_all_records()
expenses = expenses_sheet.get_all_records()

# دالة مساعدة لجمع الأرقام وتفادي الأخطاء
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
            <div style="margin-bottom: 20px; direction: rtl; background: {card_bg}; padding: 15px; border-radius: 12px; border: 1px solid {border_col};">
                <div style="display: flex; justify-content: space-between; margin-bottom: 8px; font-size: 1.1rem;">
                    <span style="font-weight: 700; color: {text_color};">{category}</span>
                    <span style="color: {highlight}; font-weight: 800;">{amount:.2f} ₺</span>
                </div>
                <div style="background-color: {'#333' if is_dark_final else '#EDF2F7'}; border-radius: 10px; width: 100%; height: 10px; overflow: hidden;">
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
        i_amount = st.number_input("المبلغ", min_value=0.0, step=50.0, format="%.2f", value=None)
        i_notes = st.text_input("ملاحظات", placeholder="أي تفاصيل إضافية (اختياري)...")
        
        st.write("") 
        submitted_income = st.form_submit_button("💾 حـفـظ الإيــراد", type="primary", use_container_width=True)
        if submitted_income:
            if not i_name or i_name.strip() == "":
                st.error("⚠️ يرجى إدخال اسم المعتكف أو المتبرع أولاً!")
            elif i_amount is None or i_amount <= 0:
                st.error("⚠️ يرجى إدخال مبلغ صحيح أكبر من الصفر!")
            else:
                # الحفظ بدون ID (الترتيب: name, type, amount, notes, date)
                income_sheet.append_row([i_name, i_type, float(i_amount), i_notes, str(i_date)])
                st.success("🎉 تم الحفظ بنجاح!")
                st.rerun()
            
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### 📋 سجل الإيرادات")
    
    if incomes:
        # استخدام enumerate لحفظ رقم الصف الأصلي للحذف (الصف في الشيت = index + 2)
        for i, inc in reversed(list(enumerate(incomes))):
            inc_date = inc.get('date', '-')
            with st.container(border=True):
                col1, col2 = st.columns([5, 1])
                with col1:
                    st.markdown(f"<span style='font-size: 1.1rem; font-weight: 700; color: {text_color};'>👤 {inc.get('name','')}</span>", unsafe_allow_html=True)
                    st.markdown(f"<span style='color: #7F8C8D; font-size: 0.9em; font-weight: 600;'>{inc.get('type','')} • 📅 {inc_date}</span>", unsafe_allow_html=True)
                    st.markdown(f"<span style='color: {highlight}; font-size: 1.4em; font-weight: 800;'>{safe_float(inc.get('amount',0)):.2f} ₺</span>", unsafe_allow_html=True)
                    if inc.get('notes'):
                        st.caption(f"📝 {inc['notes']}")
                with col2:
                    st.write("")
                    st.write("")
                    # زرار الحذف بيعتمد على رقم الـ index
                    if st.button("🗑️", key=f"del_inc_{i}", help="حذف", type="secondary"):
                        income_sheet.delete_rows(i + 2)
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
        e_amount = st.number_input("المبلغ", min_value=0.0, step=50.0, format="%.2f", value=None)
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
                # الحفظ بدون ID (الترتيب: date, category, amount, buyer, notes)
                expenses_sheet.append_row([str(e_date), e_category, float(e_amount), e_buyer, e_notes])
                st.success("🎉 تم الحفظ بنجاح!")
                st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### 📋 سجل المصروفات")
    
    if expenses:
        for i, exp in reversed(list(enumerate(expenses))):
            with st.container(border=True):
                col1, col2 = st.columns([5, 1])
                with col1:
                    st.markdown(f"<span style='font-size: 1.1rem; font-weight: 700; color: {text_color};'>🏷️ {exp.get('category','')}</span>", unsafe_allow_html=True)
                    st.markdown(f"<span style='color: #7F8C8D; font-size: 0.9em; font-weight: 600;'>📅 {exp.get('date','')} • 👤 {exp.get('buyer','')}</span>", unsafe_allow_html=True)
                    st.markdown(f"<span style='color: {danger}; font-size: 1.4em; font-weight: 800;'>{safe_float(exp.get('amount',0)):.2f} ₺</span>", unsafe_allow_html=True)
                    if exp.get('notes'):
                        st.caption(f"📝 {exp['notes']}")
                with col2:
                    st.write("")
                    st.write("")
                    if st.button("🗑️", key=f"del_exp_{i}", help="حذف", type="secondary"):
                        expenses_sheet.delete_rows(i + 2)
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
