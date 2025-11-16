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

def analyze_with_gemini(api_key, data_source, data_content):
    if not GENAI_AVAILABLE:
        return "Thư viện Google Generative AI chưa được cài đặt."
    
    try:
        configure_gemini(api_key)
        # Sử dụng model ổn định, không phải experimental
        model = genai.GenerativeModel('gemini-1.5-flash')
        
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
        "📋 Thông Tin KH",
        "💰 Thông Tin Tài Chính", 
        "🏠 Tài Sản ĐB",
        "📊 Chỉ Tiêu",
        "📈 Biểu Đồ",
        "🤖 Phân Tích AI",
        "💬 Chat AI",
        "📥 Xuất File"
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
        st.subheader("📈 Biểu Đồ")
        if not PLOTLY_AVAILABLE:
            st.warning("⚠️ Plotly chưa cài đặt")
        elif 'metrics' in st.session_state:
            metrics = st.session_state.metrics
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### Thanh toán tháng đầu")
                payment_data = pd.DataFrame({
                    'Loại': ['Gốc', 'Lãi'],
                    'Số tiền': [metrics.get('monthly_principal', 0), metrics.get('first_month_interest', 0)]
                })
                fig1 = px.pie(payment_data, values='Số tiền', names='Loại')
                st.plotly_chart(fig1, use_container_width=True)
            
            with col2:
                st.markdown("#### Dư nợ theo tháng")
                if 'repayment_schedule' in metrics:
                    fig2 = px.line(metrics['repayment_schedule'], x='Tháng', y='Dư nợ cuối kỳ', markers=True)
                    st.plotly_chart(fig2, use_container_width=True)
    
    with tabs[5]:
        st.subheader("🤖 Phân Tích AI")
        if not api_key:
            st.warning("⚠️ Nhập API Key!")
        else:
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("### 📄 Phân tích File")
                if st.button("🔍 Phân tích", key="analyze_file"):
                    if st.session_state.uploaded_content:
                        with st.spinner("Đang phân tích..."):
                            analysis = analyze_with_gemini(api_key, "file", st.session_state.uploaded_content)
                            st.session_state.analysis_file = analysis
                if 'analysis_file' in st.session_state:
                    st.write(st.session_state.analysis_file)
            
            with col2:
                st.markdown("### 📊 Phân tích Chỉ số")
                if st.button("🔍 Phân tích", key="analyze_metrics"):
                    if 'metrics' in st.session_state:
                        data = f"""
Thu nhập: {format_number(st.session_state.financial_info.get('monthly_income', 0))}
Chi phí: {format_number(st.session_state.financial_info.get('monthly_expense', 0))}
Vay: {format_number(st.session_state.financial_info.get('loan_amount', 0))}
DSCR: {st.session_state.metrics.get('dscr', 0):.2f}
"""
                        with st.spinner("Đang phân tích..."):
                            analysis = analyze_with_gemini(api_key, "metrics", data)
                            st.session_state.analysis_metrics = analysis
                if 'analysis_metrics' in st.session_state:
                    st.write(st.session_state.analysis_metrics)
    
    with tabs[6]:
        st.subheader("💬 Chat AI")
        if not api_key or not GENAI_AVAILABLE:
            st.warning("⚠️ Nhập API Key!")
        else:
            for chat in st.session_state.chat_history:
                if chat['role'] == 'user':
                    st.markdown(f"**👤:** {chat['content']}")
                else:
                    st.markdown(f"**🤖:** {chat['content']}")
            
            col1, col2 = st.columns([5, 1])
            with col1:
                user_input = st.text_input("Câu hỏi:", key="chat_input")
            with col2:
                if st.button("Gửi"):
                    if user_input:
                        st.session_state.chat_history.append({'role': 'user', 'content': user_input})
                        try:
                            configure_gemini(api_key)
                            model = genai.GenerativeModel('gemini-1.5-flash')
                            response = model.generate_content(user_input)
                            st.session_state.chat_history.append({'role': 'assistant', 'content': response.text})
                        except Exception as e:
                            error_msg = str(e)
                            if "429" in error_msg or "quota" in error_msg.lower():
                                ai_response = "⚠️ Vượt giới hạn API! Đợi 1 phút hoặc tạo API Key mới."
                            else:
                                ai_response = f"Lỗi: {error_msg}"
                            st.session_state.chat_history.append({'role': 'assistant', 'content': ai_response})
                        st.rerun()
            
            if st.button("🗑️ Xóa chat"):
                st.session_state.chat_history = []
                st.rerun()
    
    with tabs[7]:
        st.subheader("📥 Xuất File")
        export_option = st.selectbox("Chọn:", ["Excel - Kế hoạch trả nợ", "Word - Báo cáo"])
        
        if export_option == "Excel - Kế hoạch trả nợ":
            if 'repayment_schedule' in st.session_state:
                excel_data = export_to_excel(st.session_state.repayment_schedule)
                st.download_button("📥 Tải Excel", excel_data, f"ke_hoach_{datetime.now().strftime('%Y%m%d')}.xlsx",
                                 "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        else:
            if 'metrics' in st.session_state:
                word_data = export_appraisal_report(
                    st.session_state.customer_info, st.session_state.financial_info,
                    st.session_state.collateral_info, st.session_state.metrics,
                    st.session_state.get('analysis_file', ''), st.session_state.get('analysis_metrics', '')
                )
                st.download_button("📥 Tải Word", word_data, f"bao_cao_{datetime.now().strftime('%Y%m%d')}.docx",
                                 "application/vnd.openxmlformats-officedocument.wordprocessingml.document")

else:
    st.markdown("""
    <div style='text-align: center; padding: 3rem;'>
        <h2>👋 Chào Mừng</h2>
        <p style='font-size: 1.2rem;'>Upload file PASDV.docx ở sidebar!</p>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")
st.markdown("<div style='text-align: center;'><p>🏦 Hệ Thống Thẩm Định v1.0</p></div>", unsafe_allow_html=True)
