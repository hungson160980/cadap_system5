import streamlit as st
import pandas as pd
import numpy as np
from docx import Document
import io
import re
from datetime import datetime

# Import có điều kiện - CHỈ dùng plotly.express
try:
    import plotly.express as px
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False

try:
    import google.generativeai as genai
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False

# Cấu hình trang
st.set_page_config(
    page_title="Hệ Thống Thẩm Định Phương Án Kinh Doanh",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS tùy chỉnh
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        padding: 1rem 0;
        background: linear-gradient(90deg, #e3f2fd 0%, #bbdefb 100%);
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    
    /* Tối ưu tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        overflow-x: auto;
        flex-wrap: nowrap;
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 45px;
        white-space: nowrap;
        padding: 0 16px;
        font-size: 0.95rem;
        background-color: #f0f2f6;
        border-radius: 8px 8px 0 0;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: #1f77b4;
        color: white !important;
    }
    
    /* Tối ưu content area */
    .main .block-container {
        max-width: 100%;
        padding-top: 1rem;
        padding-bottom: 3rem;
    }
    
    /* Scrollable content */
    section[data-testid="stVerticalBlock"] > div {
        overflow-y: auto;
        max-height: calc(100vh - 200px);
    }
    
    /* Chat container */
    .chat-container {
        max-height: 500px;
        overflow-y: auto;
        padding: 1rem;
        background: #f8f9fa;
        border-radius: 8px;
        margin-bottom: 1rem;
    }
    
    /* Responsive */
    @media (max-width: 768px) {
        .stTabs [data-baseweb="tab"] {
            font-size: 0.85rem;
            padding: 0 12px;
        }
    }
</style>
""", unsafe_allow_html=True)

# Khởi tạo session state
if 'data_extracted' not in st.session_state:
    st.session_state.data_extracted = False
if 'customer_info' not in st.session_state:
    st.session_state.customer_info = {}
if 'financial_info' not in st.session_state:
    st.session_state.financial_info = {}
if 'collateral_info' not in st.session_state:
    st.session_state.collateral_info = {}
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'uploaded_content' not in st.session_state:
    st.session_state.uploaded_content = ""

def format_number(num):
    try:
        return "{:,.0f}".format(float(num)).replace(",", ".")
    except:
        return str(num)

def parse_number(text):
    try:
        clean_text = str(text).replace(".", "").replace(",", ".")
        return float(clean_text)
    except:
        return 0

def extract_info_from_docx(file):
    doc = Document(file)
    full_text = '\n'.join([para.text for para in doc.paragraphs])
    st.session_state.uploaded_content = full_text
    
    customer_info = {}
    financial_info = {}
    collateral_info = {}
    
    name_match = re.search(r'Họ và tên:\s*([^\n\r-]+)', full_text)
    if name_match:
        customer_info['name'] = name_match.group(1).strip()
    
    cccd_match = re.search(r'(?:CMND/)?CCCD(?:/hộ chiếu)?:\s*(\d+)', full_text)
    if cccd_match:
        customer_info['cccd'] = cccd_match.group(1).strip()
    
    address_match = re.search(r'Nơi cư trú:\s*([^\n\r]+)', full_text)
    if address_match:
        customer_info['address'] = address_match.group(1).strip()
    
    phone_match = re.search(r'Số điện thoại:\s*(\d+)', full_text)
    if phone_match:
        customer_info['phone'] = phone_match.group(1).strip()
    
    email_match = re.search(r'Email:\s*([^\s\n\r]+)', full_text)
    if email_match:
        customer_info['email'] = email_match.group(1).strip()
    
    total_need_match = re.search(r'Tổng nhu cầu vốn:\s*([\d.,]+)\s*đồng', full_text)
    if total_need_match:
        financial_info['total_need'] = parse_number(total_need_match.group(1))
    
    equity_match = re.search(r'Vốn đối ứng[^:]*:\s*([\d.,]+)\s*đồng', full_text)
    if equity_match:
        financial_info['equity'] = parse_number(equity_match.group(1))
    
    loan_match = re.search(r'Vốn vay[^:]*số tiền:\s*([\d.,]+)\s*đồng', full_text)
    if loan_match:
        financial_info['loan_amount'] = parse_number(loan_match.group(1))
    
    interest_match = re.search(r'Lãi suất:\s*([\d.,]+)%', full_text)
    if interest_match:
        financial_info['interest_rate'] = float(interest_match.group(1).replace(',', '.'))
    
    term_match = re.search(r'Thời hạn vay:\s*(\d+)\s*tháng', full_text)
    if term_match:
        financial_info['loan_term'] = int(term_match.group(1))
    
    purpose_match = re.search(r'Mục đích vay:\s*([^\n\r]+)', full_text)
    if purpose_match:
        financial_info['purpose'] = purpose_match.group(1).strip()
    
    income_patterns = [
        r'Tổng thu nhập[^:]*:\s*([\d.,]+)\s*đồng',
        r'Thu nhập[^:]*:\s*([\d.,]+)\s*đồng/tháng'
    ]
    for pattern in income_patterns:
        income_match = re.search(pattern, full_text)
        if income_match:
            financial_info['monthly_income'] = parse_number(income_match.group(1))
            break
    
    expense_match = re.search(r'Tổng chi phí hàng tháng:\s*([\d.,]+)', full_text)
    if expense_match:
        financial_info['monthly_expense'] = parse_number(expense_match.group(1))
    
    collateral_type_match = re.search(r'Tài sản \d+:\s*([^\n\r.]+)', full_text)
    if collateral_type_match:
        collateral_info['type'] = collateral_type_match.group(1).strip()
    
    collateral_value_patterns = [
        r'Giá trị:\s*([\d.,]+)\s*đồng',
        r'Giá trị[^:]*:\s*([\d.,]+)\s*đồng'
    ]
    for pattern in collateral_value_patterns:
        collateral_value_match = re.search(pattern, full_text)
        if collateral_value_match:
            collateral_info['value'] = parse_number(collateral_value_match.group(1))
            break
    
    collateral_address_match = re.search(r'Địa chỉ:\s*([^\n\r]+?)(?:Diện tích|Giấy|Tỷ lệ|\n|$)', full_text)
    if collateral_address_match:
        collateral_info['address'] = collateral_address_match.group(1).strip()
    
    area_match = re.search(r'Diện tích đất:\s*([\d.,]+)\s*m', full_text)
    if area_match:
        collateral_info['area'] = parse_number(area_match.group(1))
    
    return customer_info, financial_info, collateral_info

def calculate_financial_metrics(financial_info):
    metrics = {}
    
    loan_amount = financial_info.get('loan_amount', 0)
    interest_rate = financial_info.get('interest_rate', 0) / 100 / 12
    loan_term = financial_info.get('loan_term', 0)
    monthly_income = financial_info.get('monthly_income', 0)
    monthly_expense = financial_info.get('monthly_expense', 0)
    
    if loan_amount > 0 and loan_term > 0:
        monthly_principal = loan_amount / loan_term
        repayment_schedule = []
        remaining_balance = loan_amount
        
        for month in range(1, loan_term + 1):
            interest_payment = remaining_balance * interest_rate
            principal_payment = monthly_principal
            total_payment = principal_payment + interest_payment
            remaining_balance -= principal_payment
            
            repayment_schedule.append({
                'Tháng': month,
                'Dư nợ đầu kỳ': remaining_balance + principal_payment,
                'Trả gốc': principal_payment,
                'Trả lãi': interest_payment,
                'Tổng trả': total_payment,
                'Dư nợ cuối kỳ': max(0, remaining_balance)
            })
        
        metrics['repayment_schedule'] = pd.DataFrame(repayment_schedule)
        metrics['monthly_principal'] = monthly_principal
        metrics['first_month_interest'] = loan_amount * interest_rate
        metrics['first_month_payment'] = monthly_principal + metrics['first_month_interest']
        metrics['total_interest'] = sum([row['Trả lãi'] for row in repayment_schedule])
        metrics['total_payment'] = loan_amount + metrics['total_interest']
        metrics['net_income'] = monthly_income - monthly_expense
        metrics['debt_service_ratio'] = (metrics['first_month_payment'] / monthly_income * 100) if monthly_income > 0 else 0
        metrics['surplus'] = metrics['net_income'] - metrics['first_month_payment']
        metrics['dscr'] = (metrics['net_income'] / metrics['first_month_payment']) if metrics['first_month_payment'] > 0 else 0
        
    return metrics

def configure_gemini(api_key):
    if not GENAI_AVAILABLE:
        return False
    try:
        genai.configure(api_key=api_key)
        return True
    except Exception as e:
        st.error(f"Lỗi cấu hình Gemini API: {str(e)}")
        return False

def get_available_model(api_key):
    """Tự động chọn model khả dụng"""
    try:
        configure_gemini(api_key)
        # Danh sách models theo thứ tự ưu tiên
        preferred_models = [
            'gemini-1.5-flash-latest',
            'gemini-1.5-flash',
            'gemini-1.5-pro-latest', 
            'gemini-1.5-pro',
            'gemini-pro',
            'gemini-1.0-pro'
        ]
        
        # Thử từng model
        for model_name in preferred_models:
            try:
                model = genai.GenerativeModel(model_name)
                # Test với prompt đơn giản
                test_response = model.generate_content("Hi")
                if test_response:
                    return model_name
            except:
                continue
        
        # Fallback
        return 'gemini-pro'
    except:
        return 'gemini-pro'

def analyze_with_gemini(api_key, data_source, data_content):
    if not GENAI_AVAILABLE:
        return "Thư viện Google Generative AI chưa được cài đặt."
    
    try:
        configure_gemini(api_key)
        
        # Tự động chọn model khả dụng
        model_name = 'gemini-pro'  # Default safe model
        model = genai.GenerativeModel(model_name)
        
        if data_source == "file":
            prompt = f"""
Bạn là chuyên gia phân tích tín dụng ngân hàng. Hãy phân tích chi tiết phương án vay vốn dưới đây:

{data_content}

Yêu cầu phân tích:
1. Đánh giá tổng quan về phương án
2. Phân tích điểm mạnh và điểm yếu
3. Đánh giá khả năng trả nợ
4. Phân tích rủi ro
5. Kết luận và đề xuất
"""
        else:
            prompt = f"""
Bạn là chuyên gia phân tích tín dụng ngân hàng. Hãy phân tích các chỉ tiêu tài chính sau:

{data_content}

Yêu cầu phân tích:
1. Đánh giá các chỉ tiêu tài chính quan trọng
2. So sánh với tiêu chuẩn ngân hàng
3. Phân tích khả năng trả nợ và dòng tiền
4. Đánh giá mức độ rủi ro
5. Kết luận và khuyến nghị
"""
        
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        error_msg = str(e)
        if "429" in error_msg or "quota" in error_msg.lower():
            return """⚠️ **Lỗi vượt giới hạn API**

API Key của bạn đã hết quota. Vui lòng:
1. Đợi 1 phút rồi thử lại (giới hạn 15 requests/phút)
2. Hoặc tạo API Key mới tại: https://aistudio.google.com/app/apikey
3. Hoặc nâng cấp tài khoản Google Cloud

**Lưu ý**: API miễn phí có giới hạn:
- 15 requests/phút
- 1,500 requests/ngày
- 1 triệu tokens/ngày"""
        return f"Lỗi phân tích: {error_msg}"

def export_to_excel(repayment_schedule):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df = repayment_schedule.copy()
        for col in ['Dư nợ đầu kỳ', 'Trả gốc', 'Trả lãi', 'Tổng trả', 'Dư nợ cuối kỳ']:
            df[col] = df[col].apply(lambda x: format_number(x))
        df.to_excel(writer, sheet_name='Kế hoạch trả nợ', index=False)
    return output.getvalue()

def export_appraisal_report(customer_info, financial_info, collateral_info, metrics, analysis_file, analysis_metrics):
    doc = Document()
    
    title = doc.add_heading('BÁO CÁO THẨM ĐỊNH PHƯƠNG ÁN VAY VỐN', 0)
    title.alignment = 1
    
    doc.add_heading('I. THÔNG TIN KHÁCH HÀNG', 1)
    doc.add_paragraph(f"Họ và tên: {customer_info.get('name', 'N/A')}")
    doc.add_paragraph(f"CCCD: {customer_info.get('cccd', 'N/A')}")
    doc.add_paragraph(f"Địa chỉ: {customer_info.get('address', 'N/A')}")
    doc.add_paragraph(f"Số điện thoại: {customer_info.get('phone', 'N/A')}")
    doc.add_paragraph(f"Email: {customer_info.get('email', 'N/A')}")
    
    doc.add_heading('II. THÔNG TIN TÀI CHÍNH', 1)
    doc.add_paragraph(f"Mục đích vay: {financial_info.get('purpose', 'N/A')}")
    doc.add_paragraph(f"Tổng nhu cầu vốn: {format_number(financial_info.get('total_need', 0))} đồng")
    doc.add_paragraph(f"Vốn đối ứng: {format_number(financial_info.get('equity', 0))} đồng")
    doc.add_paragraph(f"Số tiền vay: {format_number(financial_info.get('loan_amount', 0))} đồng")
    doc.add_paragraph(f"Lãi suất: {financial_info.get('interest_rate', 0)}%/năm")
    doc.add_paragraph(f"Thời hạn vay: {financial_info.get('loan_term', 0)} tháng")
    
    doc.add_heading('III. TÀI SẢN ĐẢM BẢO', 1)
    doc.add_paragraph(f"Loại tài sản: {collateral_info.get('type', 'N/A')}")
    doc.add_paragraph(f"Giá trị: {format_number(collateral_info.get('value', 0))} đồng")
    
    doc.add_heading('IV. CÁC CHỈ TIÊU TÀI CHÍNH', 1)
    doc.add_paragraph(f"DSCR: {metrics.get('dscr', 0):.2f}")
    doc.add_paragraph(f"Tỷ lệ trả nợ/thu nhập: {metrics.get('debt_service_ratio', 0):.2f}%")
    
    if analysis_file:
        doc.add_heading('V. PHÂN TÍCH TỪ FILE', 1)
        doc.add_paragraph(analysis_file)
    
    if analysis_metrics:
        doc.add_heading('VI. PHÂN TÍCH TỪ CHỈ SỐ', 1)
        doc.add_paragraph(analysis_metrics)
    
    output = io.BytesIO()
    doc.save(output)
    output.seek(0)
    return output.getvalue()

# SIDEBAR
with st.sidebar:
    st.markdown("### 🔑 Cấu Hình API")
    api_key = st.text_input("Nhập Gemini API Key:", type="password")
    
    if api_key and GENAI_AVAILABLE:
        if configure_gemini(api_key):
            st.success("✅ API Key hợp lệ!")
            st.caption("🤖 Model: gemini-pro")
    
    st.markdown("---")
    st.markdown("### 📤 Upload File")
    uploaded_file = st.file_uploader("Chọn file PASDV (.docx)", type=['docx'])
    
    if uploaded_file is not None:
        if st.button("🔍 Trích Xuất Dữ Liệu", use_container_width=True):
            with st.spinner("Đang xử lý..."):
                customer_info, financial_info, collateral_info = extract_info_from_docx(uploaded_file)
                st.session_state.customer_info = customer_info
                st.session_state.financial_info = financial_info
                st.session_state.collateral_info = collateral_info
                st.session_state.data_extracted = True
                st.success("✅ Trích xuất thành công!")
                st.rerun()

# HEADER
st.markdown('<div class="main-header">🏦 HỆ THỐNG THẨM ĐỊNH PHƯƠNG ÁN KINH DOANH</div>', unsafe_allow_html=True)

# MAIN CONTENT
if st.session_state.data_extracted:
    tabs = st.tabs([
        "👤 KH",
        "💰 Tài Chính", 
        "🏠 TSĐB",
        "📊 Chỉ Tiêu",
        "📈 Đồ Thị",
        "🤖 AI",
        "💬 Chat",
        "📥 Xuất"
    ])
    
    with tabs[0]:
        st.subheader("📋 Thông Tin Khách Hàng")
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Họ tên:", value=st.session_state.customer_info.get('name', ''))
            cccd = st.text_input("CCCD:", value=st.session_state.customer_info.get('cccd', ''))
            phone = st.text_input("Điện thoại:", value=st.session_state.customer_info.get('phone', ''))
        with col2:
            email = st.text_input("Email:", value=st.session_state.customer_info.get('email', ''))
            address = st.text_area("Địa chỉ:", value=st.session_state.customer_info.get('address', ''), height=100)
        
        if st.button("💾 Lưu", key="save_customer"):
            st.session_state.customer_info.update({'name': name, 'cccd': cccd, 'phone': phone, 'email': email, 'address': address})
            st.success("✅ Đã lưu!")
    
    with tabs[1]:
        st.subheader("💰 Thông Tin Tài Chính")
        col1, col2 = st.columns(2)
        with col1:
            purpose = st.text_area("Mục đích:", value=st.session_state.financial_info.get('purpose', ''), height=80)
            total_need = st.number_input("Tổng nhu cầu (đ):", value=float(st.session_state.financial_info.get('total_need', 0)), step=1000000.0)
            equity = st.number_input("Vốn đối ứng (đ):", value=float(st.session_state.financial_info.get('equity', 0)), step=1000000.0)
            loan_amount = st.number_input("Số vay (đ):", value=float(st.session_state.financial_info.get('loan_amount', 0)), step=1000000.0)
        with col2:
            interest_rate = st.number_input("Lãi suất (%/năm):", value=float(st.session_state.financial_info.get('interest_rate', 8.5)), step=0.1)
            loan_term = st.number_input("Thời hạn (tháng):", value=int(st.session_state.financial_info.get('loan_term', 60)), step=1)
            monthly_income = st.number_input("Thu nhập/tháng (đ):", value=float(st.session_state.financial_info.get('monthly_income', 0)), step=1000000.0)
            monthly_expense = st.number_input("Chi phí/tháng (đ):", value=float(st.session_state.financial_info.get('monthly_expense', 0)), step=1000000.0)
        
        if st.button("💾 Lưu", key="save_financial"):
            st.session_state.financial_info.update({
                'purpose': purpose, 'total_need': total_need, 'equity': equity,
                'loan_amount': loan_amount, 'interest_rate': interest_rate, 'loan_term': loan_term,
                'monthly_income': monthly_income, 'monthly_expense': monthly_expense
            })
            st.success("✅ Đã lưu!")
    
    with tabs[2]:
        st.subheader("🏠 Tài Sản Đảm Bảo")
        col1, col2 = st.columns(2)
        with col1:
            collateral_type = st.text_input("Loại TS:", value=st.session_state.collateral_info.get('type', ''))
            collateral_value = st.number_input("Giá trị (đ):", value=float(st.session_state.collateral_info.get('value', 0)), step=1000000.0)
            collateral_area = st.number_input("Diện tích (m²):", value=float(st.session_state.collateral_info.get('area', 0)), step=1.0)
        with col2:
            collateral_address = st.text_area("Địa chỉ TS:", value=st.session_state.collateral_info.get('address', ''), height=100)
            if collateral_value > 0 and st.session_state.financial_info.get('loan_amount', 0) > 0:
                ltv = (st.session_state.financial_info['loan_amount'] / collateral_value) * 100
                st.metric("LTV", f"{ltv:.2f}%")
        
        if st.button("💾 Lưu", key="save_collateral"):
            st.session_state.collateral_info.update({
                'type': collateral_type, 'value': collateral_value,
                'area': collateral_area, 'address': collateral_address
            })
            st.success("✅ Đã lưu!")
    
    with tabs[3]:
        st.subheader("📊 Các Chỉ Tiêu Tài Chính")
        metrics = calculate_financial_metrics(st.session_state.financial_info)
        
        if metrics:
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Gốc/tháng", f"{format_number(metrics.get('monthly_principal', 0))} đ")
            with col2:
                st.metric("Lãi tháng 1", f"{format_number(metrics.get('first_month_interest', 0))} đ")
            with col3:
                st.metric("Tổng tháng 1", f"{format_number(metrics.get('first_month_payment', 0))} đ")
            with col4:
                st.metric("DSCR", f"{metrics.get('dscr', 0):.2f}")
            
            st.markdown("### Kế Hoạch Trả Nợ")
            if 'repayment_schedule' in metrics:
                df = metrics['repayment_schedule'].copy()
                for col in ['Dư nợ đầu kỳ', 'Trả gốc', 'Trả lãi', 'Tổng trả', 'Dư nợ cuối kỳ']:
                    df[col] = df[col].apply(lambda x: format_number(x))
                st.dataframe(df, use_container_width=True, height=400)
                st.session_state.repayment_schedule = metrics['repayment_schedule']
                st.session_state.metrics = metrics
    
    with tabs[4]:
        st.subheader("📈 Biểu Đồ Phân Tích")
        
        if not PLOTLY_AVAILABLE:
            st.warning("⚠️ Plotly chưa cài đặt. Vui lòng cài: `pip install plotly`")
        elif 'metrics' not in st.session_state:
            st.info("💡 Vui lòng nhập đầy đủ thông tin tài chính ở tab Tài Chính để xem biểu đồ")
        else:
            metrics = st.session_state.metrics
            
            # Container để tránh bị tràn
            with st.container():
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("#### 🥧 Thanh Toán Tháng Đầu")
                    payment_data = pd.DataFrame({
                        'Loại': ['Gốc', 'Lãi'],
                        'Số tiền': [metrics.get('monthly_principal', 0), metrics.get('first_month_interest', 0)]
                    })
                    fig1 = px.pie(payment_data, values='Số tiền', names='Loại',
                                 color_discrete_sequence=['#1f77b4', '#ff7f0e'],
                                 height=350)
                    st.plotly_chart(fig1, use_container_width=True, key="chart1")
                    
                    st.markdown("---")
                    
                    st.markdown("#### 📊 Thu Chi Hàng Tháng")
                    income_expense = pd.DataFrame({
                        'Loại': ['Thu nhập', 'Chi phí', 'Trả nợ', 'Còn lại'],
                        'Số tiền': [
                            st.session_state.financial_info.get('monthly_income', 0),
                            st.session_state.financial_info.get('monthly_expense', 0),
                            metrics.get('first_month_payment', 0),
                            max(0, metrics.get('surplus', 0))
                        ]
                    })
                    fig2 = px.bar(income_expense, x='Loại', y='Số tiền',
                                 color='Loại',
                                 color_discrete_sequence=['#2ca02c', '#d62728', '#ff7f0e', '#1f77b4'],
                                 height=350)
                    fig2.update_layout(showlegend=False, xaxis_title="", yaxis_title="Số tiền (đ)")
                    st.plotly_chart(fig2, use_container_width=True, key="chart2")
                
                with col2:
                    if 'repayment_schedule' in metrics:
                        st.markdown("#### 📉 Diễn Biến Dư Nợ")
                        fig3 = px.line(metrics['repayment_schedule'], 
                                      x='Tháng', y='Dư nợ cuối kỳ',
                                      markers=True,
                                      height=350)
                        fig3.update_traces(line_color='#1f77b4', line_width=3)
                        fig3.update_layout(xaxis_title="Tháng", yaxis_title="Dư nợ (đ)", hovermode='x unified')
                        st.plotly_chart(fig3, use_container_width=True, key="chart3")
                        
                        st.markdown("---")
                        
                        st.markdown("#### 📊 Gốc & Lãi Theo Tháng")
                        fig4 = px.bar(metrics['repayment_schedule'], 
                                     x='Tháng', y=['Trả gốc', 'Trả lãi'],
                                     barmode='stack',
                                     color_discrete_sequence=['#1f77b4', '#ff7f0e'],
                                     height=350)
                        fig4.update_layout(xaxis_title="Tháng", yaxis_title="Số tiền (đ)", 
                                          hovermode='x unified', legend_title="")
                        st.plotly_chart(fig4, use_container_width=True, key="chart4")
    
    with tabs[5]:
        st.subheader("🤖 Phân Tích Bằng AI Gemini")
        
        if not api_key:
            st.warning("⚠️ Vui lòng nhập Gemini API Key ở sidebar bên trái!")
            st.info("💡 Lấy API Key miễn phí tại: https://aistudio.google.com/app/apikey")
        else:
            # Sử dụng expander để tiết kiệm không gian
            with st.expander("📄 Phân Tích Từ File Upload", expanded=False):
                if st.button("🔍 Phân Tích File", use_container_width=True, key="analyze_file_btn"):
                    if st.session_state.uploaded_content:
                        with st.spinner("🤖 AI đang phân tích file..."):
                            analysis = analyze_with_gemini(api_key, "file", st.session_state.uploaded_content)
                            st.session_state.analysis_file = analysis
                            st.success("✅ Phân tích hoàn tất!")
                
                if 'analysis_file' in st.session_state:
                    st.markdown("#### 📊 Kết Quả:")
                    st.info("**Nguồn:** Dữ liệu từ file .docx đã upload")
                    # Container với scroll
                    with st.container():
                        st.markdown(f"""
                        <div style='max-height: 400px; overflow-y: auto; padding: 1rem; 
                                    background: #f8f9fa; border-radius: 8px; border-left: 4px solid #1f77b4;'>
                            {st.session_state.analysis_file}
                        </div>
                        """, unsafe_allow_html=True)
            
            st.markdown("---")
            
            with st.expander("📊 Phân Tích Từ Các Chỉ Số Tài Chính", expanded=False):
                if st.button("🔍 Phân Tích Chỉ Số", use_container_width=True, key="analyze_metrics_btn"):
                    if 'metrics' in st.session_state:
                        data = f"""
THÔNG TIN KHÁCH HÀNG:
- Họ tên: {st.session_state.customer_info.get('name', 'N/A')}
- Thu nhập/tháng: {format_number(st.session_state.financial_info.get('monthly_income', 0))} đồng
- Chi phí/tháng: {format_number(st.session_state.financial_info.get('monthly_expense', 0))} đồng

THÔNG TIN VAY VỐN:
- Số tiền vay: {format_number(st.session_state.financial_info.get('loan_amount', 0))} đồng
- Lãi suất: {st.session_state.financial_info.get('interest_rate', 0)}%/năm
- Thời hạn: {st.session_state.financial_info.get('loan_term', 0)} tháng

CHỈ TIÊU TÀI CHÍNH:
- Trả nợ/tháng: {format_number(st.session_state.metrics.get('first_month_payment', 0))} đồng
- DSCR: {st.session_state.metrics.get('dscr', 0):.2f}
- Tỷ lệ trả nợ/thu nhập: {st.session_state.metrics.get('debt_service_ratio', 0):.2f}%
- Còn lại sau trả nợ: {format_number(st.session_state.metrics.get('surplus', 0))} đồng
"""
                        with st.spinner("🤖 AI đang phân tích chỉ số..."):
                            analysis = analyze_with_gemini(api_key, "metrics", data)
                            st.session_state.analysis_metrics = analysis
                            st.success("✅ Phân tích hoàn tất!")
                
                if 'analysis_metrics' in st.session_state:
                    st.markdown("#### 📊 Kết Quả:")
                    st.info("**Nguồn:** Các chỉ số đã nhập và tính toán")
                    with st.container():
                        st.markdown(f"""
                        <div style='max-height: 400px; overflow-y: auto; padding: 1rem; 
                                    background: #f8f9fa; border-radius: 8px; border-left: 4px solid #2ca02c;'>
                            {st.session_state.analysis_metrics}
                        </div>
                        """, unsafe_allow_html=True)
    
    with tabs[6]:
        st.subheader("💬 Chatbox AI Gemini")
        
        if not api_key or not GENAI_AVAILABLE:
            st.warning("⚠️ Vui lòng nhập Gemini API Key ở sidebar!")
            st.info("💡 Lấy API Key miễn phí tại: https://aistudio.google.com/app/apikey")
        else:
            # Chat history với scroll
            st.markdown("#### 💭 Lịch Sử Trò Chuyện:")
            
            chat_container = st.container()
            with chat_container:
                if len(st.session_state.chat_history) == 0:
                    st.info("👋 Bắt đầu trò chuyện với AI về phương án vay vốn!")
                else:
                    # Hiển thị chat với style đẹp
                    st.markdown("""
                    <div style='max-height: 450px; overflow-y: auto; padding: 1rem; 
                                background: #f8f9fa; border-radius: 8px; margin-bottom: 1rem;'>
                    """, unsafe_allow_html=True)
                    
                    for i, chat in enumerate(st.session_state.chat_history):
                        if chat['role'] == 'user':
                            st.markdown(f"""
                            <div style='background: #e3f2fd; padding: 0.8rem; border-radius: 8px; 
                                        margin-bottom: 0.5rem; border-left: 4px solid #1f77b4;'>
                                <strong>👤 Bạn:</strong><br>{chat['content']}
                            </div>
                            """, unsafe_allow_html=True)
                        else:
                            st.markdown(f"""
                            <div style='background: #f1f8e9; padding: 0.8rem; border-radius: 8px; 
                                        margin-bottom: 0.5rem; border-left: 4px solid #4caf50;'>
                                <strong>🤖 AI:</strong><br>{chat['content']}
                            </div>
                            """, unsafe_allow_html=True)
                    
                    st.markdown("</div>", unsafe_allow_html=True)
            
            st.markdown("---")
            
            # Input area
            st.markdown("#### ✍️ Nhập Câu Hỏi:")
            col1, col2, col3 = st.columns([6, 1, 1])
            
            with col1:
                user_input = st.text_input("Hỏi AI về phương án vay vốn, tài chính, rủi ro...", 
                                          key="chat_input", 
                                          placeholder="Ví dụ: Phương án này có rủi ro gì?")
            with col2:
                send_btn = st.button("📤 Gửi", use_container_width=True, type="primary")
            with col3:
                clear_btn = st.button("🗑️ Xóa", use_container_width=True)
            
            if send_btn and user_input:
                st.session_state.chat_history.append({'role': 'user', 'content': user_input})
                
                context = f"""
Bạn là chuyên gia tư vấn tài chính ngân hàng. Dưới đây là thông tin khách hàng:
- Tên: {st.session_state.customer_info.get('name', 'N/A')}
- Số tiền vay: {format_number(st.session_state.financial_info.get('loan_amount', 0))} đồng
- Lãi suất: {st.session_state.financial_info.get('interest_rate', 0)}%/năm
- Thu nhập/tháng: {format_number(st.session_state.financial_info.get('monthly_income', 0))} đồng

Hãy trả lời ngắn gọn, chuyên nghiệp và hữu ích.
"""
                
                with st.spinner("🤖 AI đang suy nghĩ..."):
                    try:
                        configure_gemini(api_key)
                        model = genai.GenerativeModel('gemini-pro')
                        prompt = f"{context}\n\nCâu hỏi: {user_input}"
                        response = model.generate_content(prompt)
                        ai_response = response.text
                        st.session_state.chat_history.append({'role': 'assistant', 'content': ai_response})
                    except Exception as e:
                        error_msg = str(e)
                        if "429" in error_msg or "quota" in error_msg.lower():
                            ai_response = "⚠️ Vượt giới hạn API! Vui lòng đợi 1 phút hoặc tạo API Key mới."
                        else:
                            ai_response = f"❌ Lỗi: {error_msg}"
                        st.session_state.chat_history.append({'role': 'assistant', 'content': ai_response})
                
                st.rerun()
            
            if clear_btn:
                st.session_state.chat_history = []
                st.success("✅ Đã xóa lịch sử chat!")
                st.rerun()
    
    with tabs[7]:
        st.subheader("📥 Xuất Dữ Liệu & Báo Cáo")
        
        # Sử dụng columns để layout đẹp hơn
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.markdown("### 🎯 Chọn Loại Xuất:")
            export_option = st.radio(
                "Chọn định dạng:",
                ["📊 Excel - Kế hoạch trả nợ", "📄 Word - Báo cáo thẩm định"],
                label_visibility="collapsed"
            )
        
        with col2:
            if export_option == "📊 Excel - Kế hoạch trả nợ":
                st.markdown("### 📊 Xuất Bảng Kế Hoạch Trả Nợ")
                
                if 'repayment_schedule' not in st.session_state:
                    st.warning("⚠️ Chưa có dữ liệu kế hoạch trả nợ!")
                    st.info("💡 Vui lòng nhập đầy đủ thông tin tài chính ở tab **Tài Chính** để tạo kế hoạch trả nợ.")
                else:
                    # Preview data
                    st.markdown("#### 👁️ Xem Trước:")
                    preview_df = st.session_state.repayment_schedule.head(10).copy()
                    for col in ['Dư nợ đầu kỳ', 'Trả gốc', 'Trả lãi', 'Tổng trả', 'Dư nợ cuối kỳ']:
                        preview_df[col] = preview_df[col].apply(lambda x: format_number(x))
                    
                    st.dataframe(preview_df, use_container_width=True, height=300)
                    
                    if len(st.session_state.repayment_schedule) > 10:
                        st.info(f"📌 Hiển thị 10/{len(st.session_state.repayment_schedule)} tháng. File đầy đủ sẽ có tất cả dữ liệu.")
                    
                    st.markdown("---")
                    
                    # Download button
                    excel_data = export_to_excel(st.session_state.repayment_schedule)
                    
                    col_a, col_b, col_c = st.columns([1, 2, 1])
                    with col_b:
                        st.download_button(
                            label="📥 Tải Xuống File Excel",
                            data=excel_data,
                            file_name=f"ke_hoach_tra_no_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            use_container_width=True,
                            type="primary"
                        )
                    
                    st.success("✅ File Excel chứa đầy đủ kế hoạch trả nợ theo từng tháng!")
            
            else:  # Báo cáo Word
                st.markdown("### 📄 Xuất Báo Cáo Thẩm Định")
                
                if 'metrics' not in st.session_state:
                    st.warning("⚠️ Chưa có dữ liệu để xuất báo cáo!")
                    st.info("💡 Vui lòng nhập đầy đủ thông tin ở các tab trước.")
                else:
                    # Thông tin báo cáo
                    st.markdown("#### 📋 Nội Dung Báo Cáo:")
                    
                    report_items = [
                        "✓ Thông tin khách hàng",
                        "✓ Thông tin tài chính và vay vốn",
                        "✓ Tài sản đảm bảo",
                        "✓ Các chỉ tiêu tài chính (DSCR, LTV, etc.)",
                    ]
                    
                    if 'analysis_file' in st.session_state:
                        report_items.append("✓ Phân tích AI từ file upload")
                    
                    if 'analysis_metrics' in st.session_state:
                        report_items.append("✓ Phân tích AI từ chỉ số tài chính")
                    
                    for item in report_items:
                        st.markdown(f"- {item}")
                    
                    st.markdown("---")
                    
                    # Download button
                    analysis_file = st.session_state.get('analysis_file', '')
                    analysis_metrics = st.session_state.get('analysis_metrics', '')
                    
                    word_data = export_appraisal_report(
                        st.session_state.customer_info,
                        st.session_state.financial_info,
                        st.session_state.collateral_info,
                        st.session_state.metrics,
                        analysis_file,
                        analysis_metrics
                    )
                    
                    col_a, col_b, col_c = st.columns([1, 2, 1])
                    with col_b:
                        st.download_button(
                            label="📥 Tải Xuống Báo Cáo Word",
                            data=word_data,
                            file_name=f"bao_cao_tham_dinh_{datetime.now().strftime('%Y%m%d_%H%M%S')}.docx",
                            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                            use_container_width=True,
                            type="primary"
                        )
                    
                    st.success("✅ Báo cáo Word đầy đủ thông tin thẩm định!")
                    
                    if not analysis_file and not analysis_metrics:
                        st.info("💡 **Mẹo:** Sử dụng tính năng **Phân Tích AI** để thêm phân tích chuyên sâu vào báo cáo!")

else:
    st.markdown("""
    <div style='text-align: center; padding: 3rem;'>
        <h2>👋 Chào Mừng</h2>
        <p style='font-size: 1.2rem;'>Upload file PASDV.docx ở sidebar!</p>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")
st.markdown("<div style='text-align: center;'><p>🏦 Hệ Thống Thẩm Định v1.0</p></div>", unsafe_allow_html=True)
