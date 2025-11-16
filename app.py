import streamlit as st
import pandas as pd
import numpy as np
from docx import Document
import io
import re
from datetime import datetime
import requests
import json

# Import có điều kiện
try:
    import plotly.express as px
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False

# Cấu hình trang
st.set_page_config(
    page_title="Hệ Thống Thẩm Định Phương Án Kinh Doanh",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS
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
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        overflow-x: auto;
    }
    .stTabs [data-baseweb="tab"] {
        height: 45px;
        padding: 0 16px;
        font-size: 0.95rem;
        background-color: #f0f2f6;
        border-radius: 8px 8px 0 0;
    }
    .stTabs [aria-selected="true"] {
        background-color: #1f77b4;
        color: white !important;
    }
</style>
""", unsafe_allow_html=True)

# Session state
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

# GEMINI API qua REST - Không dùng SDK
def call_gemini_api(api_key, prompt):
    """Gọi Gemini API trực tiếp qua REST"""
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={api_key}"
        
        headers = {
            'Content-Type': 'application/json'
        }
        
        data = {
            "contents": [{
                "parts": [{
                    "text": prompt
                }]
            }]
        }
        
        response = requests.post(url, headers=headers, json=data, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            if 'candidates' in result and len(result['candidates']) > 0:
                text = result['candidates'][0]['content']['parts'][0]['text']
                return True, text
            else:
                return False, "Không nhận được phản hồi từ AI"
        elif response.status_code == 429:
            return False, "⚠️ Vượt giới hạn API! Vui lòng đợi 1 phút hoặc tạo API Key mới."
        elif response.status_code == 400:
            return False, f"❌ API Key không hợp lệ hoặc hết hạn. Vui lòng tạo key mới tại: https://aistudio.google.com/app/apikey"
        else:
            return False, f"Lỗi API {response.status_code}: {response.text}"
            
    except requests.exceptions.Timeout:
        return False, "⏱️ Timeout - Vui lòng thử lại"
    except Exception as e:
        return False, f"Lỗi: {str(e)}"

def test_gemini_key(api_key):
    """Test API key with better error handling"""
    try:
        # Kiểm tra format cơ bản
        if not api_key or len(api_key) < 30:
            return False, "API Key quá ngắn"
        
        if not api_key.startswith('AIzaSy'):
            return False, "API Key phải bắt đầu bằng 'AIzaSy'"
        
        # Test với API
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={api_key}"
        
        headers = {'Content-Type': 'application/json'}
        data = {"contents": [{"parts": [{"text": "Hi"}]}]}
        
        response = requests.post(url, headers=headers, json=data, timeout=10)
        
        if response.status_code == 200:
            return True, "OK"
        elif response.status_code == 400:
            return False, "API Key không hợp lệ hoặc sai format"
        elif response.status_code == 403:
            return False, "API Key không có quyền truy cập"
        else:
            return False, f"Lỗi {response.status_code}"
            
    except requests.exceptions.Timeout:
        return False, "Timeout - Kiểm tra kết nối internet"
    except Exception as e:
        return False, f"Lỗi: {str(e)}"

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

def analyze_with_gemini(api_key, data_source, data_content):
    if data_source == "file":
        prompt = f"""Bạn là chuyên gia phân tích tín dụng ngân hàng. Hãy phân tích chi tiết phương án vay vốn:

{data_content}

Yêu cầu:
1. Đánh giá tổng quan
2. Điểm mạnh và điểm yếu
3. Khả năng trả nợ
4. Rủi ro
5. Kết luận

Trả lời ngắn gọn, chuyên sâu."""
    else:
        prompt = f"""Bạn là chuyên gia phân tích tín dụng. Phân tích các chỉ tiêu:

{data_content}

Yêu cầu:
1. Đánh giá chỉ tiêu
2. So sánh tiêu chuẩn
3. Khả năng trả nợ
4. Rủi ro
5. Khuyến nghị

Trả lời ngắn gọn, chuyên sâu."""
    
    success, response = call_gemini_api(api_key, prompt)
    return response

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
    
    doc.add_heading('II. THÔNG TIN TÀI CHÍNH', 1)
    doc.add_paragraph(f"Số tiền vay: {format_number(financial_info.get('loan_amount', 0))} đồng")
    doc.add_paragraph(f"Lãi suất: {financial_info.get('interest_rate', 0)}%/năm")
    doc.add_paragraph(f"Thời hạn: {financial_info.get('loan_term', 0)} tháng")
    
    doc.add_heading('III. CHỈ TIÊU TÀI CHÍNH', 1)
    doc.add_paragraph(f"DSCR: {metrics.get('dscr', 0):.2f}")
    doc.add_paragraph(f"Tỷ lệ trả nợ/thu nhập: {metrics.get('debt_service_ratio', 0):.2f}%")
    
    if analysis_file:
        doc.add_heading('IV. PHÂN TÍCH TỪ FILE', 1)
        doc.add_paragraph(analysis_file)
    
    if analysis_metrics:
        doc.add_heading('V. PHÂN TÍCH TỪ CHỈ SỐ', 1)
        doc.add_paragraph(analysis_metrics)
    
    output = io.BytesIO()
    doc.save(output)
    output.seek(0)
    return output.getvalue()

# SIDEBAR
with st.sidebar:
    st.markdown("### 🔑 API Configuration")
    api_key = st.text_input("Gemini API Key:", type="password", 
                            help="Get free key: https://aistudio.google.com/app/apikey")
    
    if api_key:
        # Kiểm tra độ dài trước
        if len(api_key.strip()) < 30:
            st.error("❌ API Key quá ngắn! Key phải ~39 ký tự")
            st.info("💡 Format: AIzaSy + 32 ký tự")
        elif not api_key.strip().startswith('AIzaSy'):
            st.error("❌ API Key phải bắt đầu bằng 'AIzaSy'")
            st.info("💡 Copy lại key từ Google AI Studio")
        else:
            with st.spinner("Testing API..."):
                success, message = test_gemini_key(api_key.strip())
                if success:
                    st.success("✅ API Key OK!")
                    st.caption("🤖 Using: gemini-pro (REST API)")
                else:
                    st.error(f"❌ {message}")
                    with st.expander("🔧 Hướng dẫn fix"):
                        st.markdown("""
                        **Các bước kiểm tra:**
                        
                        1. **Tạo API Key mới:**
                           - Vào: https://aistudio.google.com/app/apikey
                           - Click "Create API key"
                           - Chọn "Create API key in new project"
                           - Copy key mới
                        
                        2. **Copy đúng cách:**
                           - Click nút "Copy" (không tự gõ)
                           - Paste trực tiếp (không thêm/bớt gì)
                           - Không có khoảng trắng
                        
                        3. **Kiểm tra:**
                           - Key bắt đầu: AIzaSy
                           - Độ dài: ~39 ký tự
                           - Chỉ chữ + số
                        
                        4. **Nếu vẫn lỗi:**
                           - Xóa key cũ trên Google AI Studio
                           - Tạo key hoàn toàn mới
                           - Thử lại
                        """)
    
    st.markdown("---")
    st.markdown("### 📤 Upload File")
    uploaded_file = st.file_uploader("PASDV (.docx)", type=['docx'])
    
    if uploaded_file:
        if st.button("🔍 Extract", use_container_width=True):
            with st.spinner("Processing..."):
                customer_info, financial_info, collateral_info = extract_info_from_docx(uploaded_file)
                st.session_state.customer_info = customer_info
                st.session_state.financial_info = financial_info
                st.session_state.collateral_info = collateral_info
                st.session_state.data_extracted = True
                st.success("✅ Done!")
                st.rerun()

# HEADER
st.markdown('<div class="main-header">🏦 HỆ THỐNG THẨM ĐỊNH</div>', unsafe_allow_html=True)

# MAIN
if st.session_state.data_extracted:
    tabs = st.tabs(["👤 KH", "💰 Tài Chính", "🏠 TSĐB", "📊 Chỉ Tiêu", "📈 Đồ Thị", "🤖 AI", "💬 Chat", "📥 Xuất"])
    
    with tabs[0]:
        st.subheader("👤 Thông Tin Khách Hàng")
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Họ tên:", value=st.session_state.customer_info.get('name', ''))
            cccd = st.text_input("CCCD:", value=st.session_state.customer_info.get('cccd', ''))
        with col2:
            phone = st.text_input("ĐT:", value=st.session_state.customer_info.get('phone', ''))
            email = st.text_input("Email:", value=st.session_state.customer_info.get('email', ''))
        
        if st.button("💾 Lưu", key="save1"):
            st.session_state.customer_info.update({'name': name, 'cccd': cccd, 'phone': phone, 'email': email})
            st.success("✅ Saved!")
    
    with tabs[1]:
        st.subheader("💰 Thông Tin Tài Chính")
        col1, col2 = st.columns(2)
        with col1:
            loan_amount = st.number_input("Số vay (đ):", value=float(st.session_state.financial_info.get('loan_amount', 0)), step=1000000.0)
            interest_rate = st.number_input("Lãi suất (%/năm):", value=float(st.session_state.financial_info.get('interest_rate', 8.5)), step=0.1)
            loan_term = st.number_input("Thời hạn (tháng):", value=int(st.session_state.financial_info.get('loan_term', 60)), step=1)
        with col2:
            monthly_income = st.number_input("Thu nhập/tháng (đ):", value=float(st.session_state.financial_info.get('monthly_income', 0)), step=1000000.0)
            monthly_expense = st.number_input("Chi phí/tháng (đ):", value=float(st.session_state.financial_info.get('monthly_expense', 0)), step=1000000.0)
        
        if st.button("💾 Lưu", key="save2"):
            st.session_state.financial_info.update({
                'loan_amount': loan_amount, 'interest_rate': interest_rate, 
                'loan_term': loan_term, 'monthly_income': monthly_income, 
                'monthly_expense': monthly_expense
            })
            st.success("✅ Saved!")
    
    with tabs[2]:
        st.subheader("🏠 Tài Sản Đảm Bảo")
        col1, col2 = st.columns(2)
        with col1:
            collateral_value = st.number_input("Giá trị (đ):", value=float(st.session_state.collateral_info.get('value', 0)), step=1000000.0)
        with col2:
            if collateral_value > 0 and st.session_state.financial_info.get('loan_amount', 0) > 0:
                ltv = (st.session_state.financial_info['loan_amount'] / collateral_value) * 100
                st.metric("LTV", f"{ltv:.2f}%")
        
        if st.button("💾 Lưu", key="save3"):
            st.session_state.collateral_info['value'] = collateral_value
            st.success("✅ Saved!")
    
    with tabs[3]:
        st.subheader("📊 Chỉ Tiêu Tài Chính")
        metrics = calculate_financial_metrics(st.session_state.financial_info)
        
        if metrics:
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Gốc/tháng", f"{format_number(metrics.get('monthly_principal', 0))}")
            with col2:
                st.metric("Lãi T1", f"{format_number(metrics.get('first_month_interest', 0))}")
            with col3:
                st.metric("Tổng T1", f"{format_number(metrics.get('first_month_payment', 0))}")
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
        st.subheader("📈 Biểu Đồ")
        if not PLOTLY_AVAILABLE:
            st.warning("⚠️ Plotly not installed")
        elif 'metrics' in st.session_state:
            metrics = st.session_state.metrics
            col1, col2 = st.columns(2)
            
            with col1:
                payment_data = pd.DataFrame({
                    'Loại': ['Gốc', 'Lãi'],
                    'Số tiền': [metrics.get('monthly_principal', 0), metrics.get('first_month_interest', 0)]
                })
                fig = px.pie(payment_data, values='Số tiền', names='Loại', title="Thanh toán T1")
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                if 'repayment_schedule' in metrics:
                    fig = px.line(metrics['repayment_schedule'], x='Tháng', y='Dư nợ cuối kỳ', 
                                 title="Dư nợ", markers=True)
                    st.plotly_chart(fig, use_container_width=True)
    
    with tabs[5]:
        st.subheader("🤖 AI Analysis")
        if not api_key:
            st.warning("⚠️ Enter API Key!")
        else:
            with st.expander("📄 From File"):
                if st.button("Analyze", key="af"):
                    if st.session_state.uploaded_content:
                        with st.spinner("Analyzing..."):
                            result = analyze_with_gemini(api_key, "file", st.session_state.uploaded_content)
                            st.session_state.analysis_file = result
                
                if 'analysis_file' in st.session_state:
                    st.write(st.session_state.analysis_file)
            
            with st.expander("📊 From Metrics"):
                if st.button("Analyze", key="am"):
                    if 'metrics' in st.session_state:
                        data = f"Vay: {format_number(st.session_state.financial_info.get('loan_amount', 0))}\nDSCR: {st.session_state.metrics.get('dscr', 0):.2f}"
                        with st.spinner("Analyzing..."):
                            result = analyze_with_gemini(api_key, "metrics", data)
                            st.session_state.analysis_metrics = result
                
                if 'analysis_metrics' in st.session_state:
                    st.write(st.session_state.analysis_metrics)
    
    with tabs[6]:
        st.subheader("💬 Chat")
        if not api_key:
            st.warning("⚠️ Enter API Key!")
        else:
            for chat in st.session_state.chat_history:
                role = "👤" if chat['role'] == 'user' else "🤖"
                st.markdown(f"**{role}:** {chat['content']}")
            
            col1, col2 = st.columns([5, 1])
            with col1:
                user_input = st.text_input("Question:", key="ci")
            with col2:
                if st.button("Send"):
                    if user_input:
                        st.session_state.chat_history.append({'role': 'user', 'content': user_input})
                        with st.spinner("..."):
                            success, response = call_gemini_api(api_key, user_input)
                            st.session_state.chat_history.append({'role': 'assistant', 'content': response})
                        st.rerun()
            
            if st.button("Clear"):
                st.session_state.chat_history = []
                st.rerun()
    
    with tabs[7]:
        st.subheader("📥 Export")
        opt = st.radio("Type:", ["Excel", "Word"])
        
        if opt == "Excel":
            if 'repayment_schedule' in st.session_state:
                data = export_to_excel(st.session_state.repayment_schedule)
                st.download_button("📥 Download", data, f"plan_{datetime.now().strftime('%Y%m%d')}.xlsx",
                                 "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        else:
            if 'metrics' in st.session_state:
                data = export_appraisal_report(
                    st.session_state.customer_info, st.session_state.financial_info,
                    st.session_state.collateral_info, st.session_state.metrics,
                    st.session_state.get('analysis_file', ''), st.session_state.get('analysis_metrics', '')
                )
                st.download_button("📥 Download", data, f"report_{datetime.now().strftime('%Y%m%d')}.docx",
                                 "application/vnd.openxmlformats-officedocument.wordprocessingml.document")

else:
    st.markdown("""
    <div style='text-align: center; padding: 3rem;'>
        <h2>👋 Welcome</h2>
        <p>Upload PASDV.docx in sidebar to start!</p>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")
st.markdown("<div style='text-align: center;'><p>🏦 v3.0 - REST API</p></div>", unsafe_allow_html=True)
