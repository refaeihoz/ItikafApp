import streamlit as st
import sqlite3
from datetime import date
import streamlit.components.v1 as components
import gspread
from google.oauth2.service_account import Credentials

# إعداد صفحة البرنامج (يجب أن يكون أول سطر)
st.set_page_config(page_title="حسابات الاعتكاف", page_icon="🕌", layout="wide", initial_sidebar_state="collapsed")

# ==========================================
# 🌐 الاتصال بـ Google Sheets
# ==========================================
@st.cache_resource
def init_gsheets():
    try:
        # تحديد الصلاحيات المطلوبة
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        # جلب بيانات الاعتماد من Streamlit Secrets
        creds = Credentials.from_service_account_info(
            st.secrets["gcp_service_account"], scopes=scopes
        )
        client = gspread.authorize(creds)
        # فتح الشيت باستخدام الرابط
        sheet = client.open_by_url(st.secrets["sheet_url"])
        return sheet
    except Exception as e:
        st.warning(f"⚠️ تعذر الاتصال بجوجل شيت. تأكد من إعدادات الـ Secrets. الخطأ: {e}")
        return None

gsheet_doc = init_gsheets()

# ==========================================
# 🎨 كود CSS السحري للـ UI/UX الفخم 
# ==========================================
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;800&display=swap');
    .stApp {
        font-family: 'Cairo', sans-serif !important;
        direction: rtl;
        background-color: #F4F7F6 !important;
    }
    p, h1, h2, h3, h4, h5, h6, label, div[data-testid="stMarkdownContainer"] {
        color: #2C3E50 !important;
        text-align: right !important;
    }
    input, .stSelectbox div[data-baseweb="select"] {
        color: #ffffff !important;
        -webkit-text-fill-color: #ffffff !important; 
    }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .main-title {
        text-align: center !important;
        background: linear-gradient(45deg, #1E88E5, #004D40);
        -webkit-background-clip: text !important;
        -webkit-text-fill-color: transparent !important;
        font-weight: 800;
        padding-bottom: 20px;
    }
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
    div[data-testid="stForm"] {
        background: #ffffff !important;
        border-radius: 20px;
        padding: 30px 20px;
        border: none;
        box-shadow: 0 8px 25px rgba(0, 0, 0, 0.03);
    }
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
    .stButton>button[kind="secondary"] {
        background-color: #FFEBEE !important;
        border: none !important;
        border-radius: 10px !important;
    }
    .stButton>button[kind="secondary"] p {
        color: #D32F2F !important;
    }
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background: #ffffff !important;
        border-radius: 16px !important;
        border: 1px solid #F0F0F0 !important;
        box-shadow: 0 4px 10px rgba(0, 0, 0, 0.02) !important;
        padding: 5px;
        margin-bottom: 10px;
    }
    button[data-baseweb="tab"] div {
        font-family: 'Cairo', sans-serif !important;
        font-size: 1.1rem !important;
        font-weight: 600 !important;
        color: #2C3E50 !important;
    }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# إعداد قاعدة البيانات المحلية SQLite
# ==========================================
conn = sqlite3.connect('itikaf.db', check_same_thread=False)
c = conn.cursor()

c.execute('''CREATE TABLE IF NOT EXISTS income (id INTEGER PRIMARY KEY, name TEXT, type TEXT, amount REAL, notes TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS expenses (id INTEGER PRIMARY KEY, date TEXT, category TEXT, amount REAL, buyer TEXT, notes TEXT)''')

c.execute("PRAGMA table_info(income)")
columns = [column[1] for column in c.fetchall()]
if 'date' not in columns:
    c.execute("ALTER TABLE income ADD COLUMN date TEXT")
    today_str = date.today().strftime("%Y-%m-%d")
    c.execute("UPDATE income SET date = ?", (today_str,))
conn.commit()

c.execute("SELECT SUM(amount) FROM income")
total_income = c.fetchone()[0] or 0.0

c.execute("SELECT SUM(amount) FROM expenses")
total_expenses = c.fetchone()[0] or 0.0

balance = total_income - total_expenses
treasury = balance if balance > 0 else 0.0
debt = abs(balance) if balance < 0 else 0.0

# 🌟 عرض العنوان الفخم مع زر التحديث
col1, col2, col3 = st.columns([1, 4, 1])
with col2:
    st.markdown("<h1 class='main-title'>🕌 إدارة حسابات الاعتكاف</h1>", unsafe_allow_html=True)
with col3:
    st.write("") # لضبط المحاذاة العمودية
    if st.button("🔄 تحديث", type="secondary", use_container_width=True):
        st.cache_resource.clear()
        st.rerun()

st.write("") 

# === هذا هو السطر المفقود الذي تسبب في المشكلة ===
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
    
    c.execute("SELECT category, SUM(amount) FROM expenses GROUP BY category")
    chart_data = c.fetchall()
    
    if chart_data:
        max_amount = max([row[1] for row in chart_data])
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
                # 1. الحفظ في SQLite
                c.execute("INSERT INTO income (name, type, amount, notes, date) VALUES (?, ?, ?, ?, ?)", (i_name, i_type, i_amount, i_notes, i_date))
                conn.commit()
                
                # 2. الحفظ في Google Sheets
                if gsheet_doc:
                    try:
                        income_sheet = gsheet_doc.worksheet("Income")
                        # تحويل التاريخ إلى نص قبل إرساله
                        income_sheet.append_row([i_date.strftime("%Y-%m-%d"), i_name, i_type, float(i_amount), i_notes])
                    except Exception as e:
                        st.warning(f"تم الحفظ محلياً، ولكن حدث خطأ أثناء المزامنة مع جوجل شيت: {e}")
                
                st.success("🎉 تم الحفظ بنجاح!")
                st.rerun()
            
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### 📋 سجل الإيرادات")
    
    c.execute("SELECT * FROM income ORDER BY id DESC")
    incomes = c.fetchall()
    
    if incomes:
        for inc in incomes:
            inc_date = inc[5] if len(inc) > 5 and inc[5] else "-"
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
                    # === كود الحذف الجديد المربوط بجوجل شيت ===
                    if st.button("🗑️", key=f"del_inc_{inc[0]}", help="حذف", type="secondary"):
                        # 1. الحذف من جوجل شيت أولاً
                        if gsheet_doc:
                            try:
                                income_sheet = gsheet_doc.worksheet("Income")
                                records = income_sheet.get_all_values()
                                for i, row in enumerate(records):
                                    try:
                                        # مطابقة الاسم والمبلغ والتاريخ لضمان حذف الصف الصحيح
                                        if len(row) >= 4 and row[1] == str(inc[1]) and float(row[3]) == float(inc[3]) and row[0] == str(inc_date):
                                            income_sheet.delete_rows(i + 1)
                                            break # يحذف صف واحد فقط ويخرج
                                    except ValueError:
                                        continue # لتخطي صف العناوين (Headers)
                            except Exception as e:
                                st.warning(f"تعذر الحذف من الشيت: {e}")
                        
                        # 2. الحذف من القاعدة المحلية
                        c.execute("DELETE FROM income WHERE id=?", (inc[0],))
                        conn.commit()
                        st.rerun()
                    # ==========================================
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
                # 1. الحفظ في SQLite
                c.execute("INSERT INTO expenses (date, category, amount, buyer, notes) VALUES (?, ?, ?, ?, ?)", (e_date, e_category, e_amount, e_buyer, e_notes))
                conn.commit()
                
                # 2. الحفظ في Google Sheets
                if gsheet_doc:
                    try:
                        expense_sheet = gsheet_doc.worksheet("Expenses")
                        expense_sheet.append_row([e_date.strftime("%Y-%m-%d"), e_category, float(e_amount), e_buyer, e_notes])
                    except Exception as e:
                        st.warning(f"تم الحفظ محلياً، ولكن حدث خطأ أثناء المزامنة مع جوجل شيت: {e}")
                
                st.success("🎉 تم الحفظ بنجاح!")
                st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### 📋 سجل المصروفات")
    
    c.execute("SELECT * FROM expenses ORDER BY id DESC")
    expenses = c.fetchall()
    
    if expenses:
        for exp in expenses:
            with st.container(border=True):
                col1, col2 = st.columns([5, 1])
                with col1:
                    st.markdown(f"<span style='font-size: 1.1rem; font-weight: 700; color: #2C3E50;'>🏷️ {exp[2]}</span>", unsafe_allow_html=True)
                    st.markdown(f"<span style='color: #7F8C8D; font-size: 0.9em; font-weight: 600;'>📅 {exp[1]} • 👤 {exp[4]}</span>", unsafe_allow_html=True)
                    st.markdown(f"<span style='color: #E53935; font-size: 1.4em; font-weight: 800;'>{exp[3]:.2f} ₺</span>", unsafe_allow_html=True)
                    if exp[5]:
                        st.caption(f"📝 {exp[5]}")
                with col2:
                    st.write("")
                    st.write("")
                    # === كود الحذف الجديد المربوط بجوجل شيت ===
                    if st.button("🗑️", key=f"del_exp_{exp[0]}", help="حذف", type="secondary"):
                        # 1. الحذف من جوجل شيت أولاً
                        if gsheet_doc:
                            try:
                                expense_sheet = gsheet_doc.worksheet("Expenses")
                                records = expense_sheet.get_all_values()
                                for i, row in enumerate(records):
                                    try:
                                        # مطابقة البند والمبلغ والتاريخ
                                        if len(row) >= 3 and row[1] == str(exp[2]) and float(row[2]) == float(exp[3]) and row[0] == str(exp[1]):
                                            expense_sheet.delete_rows(i + 1)
                                            break
                                    except ValueError:
                                        continue
                            except Exception as e:
                                st.warning(f"تعذر الحذف من الشيت: {e}")

                        # 2. الحذف من القاعدة المحلية
                        c.execute("DELETE FROM expenses WHERE id=?", (exp[0],))
                        conn.commit()
                        st.rerun()
                    # ==========================================
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
