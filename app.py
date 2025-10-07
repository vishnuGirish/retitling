import streamlit as st
import pandas as pd
import io
from luxury_correction import correct_luxury_title
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
from difflib import SequenceMatcher

# --- Page Configuration ---
st.set_page_config(
    page_title="Luxury Title Retitler",
    page_icon="💎",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- User Credentials ---
USER_CREDENTIALS = {
    "admin": "luxury123"
}

# --- Initialize authentication and session state ---
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "processing_complete" not in st.session_state:
    st.session_state.processing_complete = False
if "processed_df" not in st.session_state:
    st.session_state.processed_df = None

# --- Modern CSS Styling ---
st.markdown("""
<style>
    /* Import Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@600;700&family=Inter:wght@400;500;600&display=swap');
    
    /* Global Styles */
    .main {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        padding: 2rem;
    }
    
    /* Custom Card Style */
    .custom-card {
        background: white;
        border-radius: 20px;
        padding: 2.5rem;
        box-shadow: 0 10px 40px rgba(0,0,0,0.1);
        margin: 1.5rem 0;
        border: 1px solid rgba(0,0,0,0.05);
    }
    
    /* Title Styles */
    .luxury-title {
        font-family: 'Playfair Display', serif;
        font-size: 3.5rem;
        font-weight: 700;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 1rem;
    }
    
    .subtitle {
        font-family: 'Inter', sans-serif;
        font-size: 1.2rem;
        color: #6b7280;
        text-align: center;
        margin-bottom: 2rem;
    }
    
    /* Input Field Styling */
    .stTextInput > div > div > input {
        font-size: 1.1rem;
        padding: 0.8rem 1rem;
        border-radius: 12px;
        border: 2px solid #e5e7eb;
        transition: all 0.3s ease;
        font-family: 'Inter', sans-serif;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #667eea;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
    }
    
    /* Button Styling */
    .stButton > button {
        width: 100%;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        font-size: 1.1rem;
        font-weight: 600;
        padding: 0.8rem 2rem;
        border-radius: 12px;
        border: none;
        transition: all 0.3s ease;
        font-family: 'Inter', sans-serif;
        margin-top: 1rem;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 25px rgba(102, 126, 234, 0.3);
    }
    
    /* Download Button - Extra Prominent */
    .stDownloadButton > button {
        background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%) !important;
        color: white !important;
        font-size: 1.3rem !important;
        font-weight: 700 !important;
        padding: 1.2rem 2.5rem !important;
        border-radius: 16px !important;
        border: none !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 10px 30px rgba(245, 158, 11, 0.4) !important;
    }
    
    .stDownloadButton > button:hover {
        transform: translateY(-3px) !important;
        box-shadow: 0 15px 40px rgba(245, 158, 11, 0.5) !important;
    }
    
    /* File Uploader */
    .stFileUploader {
        background: white;
        border: 2px dashed #667eea;
        border-radius: 16px;
        padding: 2rem;
        text-align: center;
        transition: all 0.3s ease;
    }
    
    .stFileUploader:hover {
        border-color: #764ba2;
        background: #f9fafb;
    }
    
    /* Metrics */
    .stMetric {
        background: linear-gradient(135deg, #f3f4f6 0%, #e5e7eb 100%);
        padding: 1.5rem;
        border-radius: 12px;
        text-align: center;
    }
    
    .stMetric label {
        font-size: 0.9rem !important;
        color: #6b7280 !important;
        font-weight: 500 !important;
    }
    
    .stMetric div {
        font-size: 2rem !important;
        font-weight: 700 !important;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    
    /* Progress Bar */
    .stProgress > div > div > div {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        border-radius: 10px;
    }
    
    /* Success/Error Messages */
    .stSuccess, .stError, .stInfo {
        border-radius: 12px;
        padding: 1rem;
        font-family: 'Inter', sans-serif;
    }
    
    /* Dataframe */
    .stDataFrame {
        border-radius: 12px;
        overflow: hidden;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    
    /* Sidebar */
    .css-1d391kg {
        background: white;
    }
    
    /* Hide Streamlit Branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Section Headers */
    .section-header {
        font-family: 'Playfair Display', serif;
        font-size: 2rem;
        font-weight: 600;
        color: #1f2937;
        margin: 2rem 0 1rem 0;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    
    /* Login Container */
    .login-container {
        max-width: 500px;
        margin: 5rem auto;
    }
    
    /* Label styling */
    .input-label {
        font-family: 'Inter', sans-serif;
        font-size: 0.95rem;
        font-weight: 600;
        color: #374151;
        margin-bottom: 0.5rem;
        display: block;
    }
    
    /* Download Section Highlight */
    .download-highlight {
        background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
        border-radius: 20px;
        padding: 2rem;
        margin: 2rem 0;
        border: 2px solid #f59e0b;
        box-shadow: 0 10px 30px rgba(245, 158, 11, 0.2);
    }
    
    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 2rem;
    }
    
    .stTabs [data-baseweb="tab"] {
        font-size: 1.1rem;
        font-weight: 600;
        font-family: 'Inter', sans-serif;
    }
</style>
""", unsafe_allow_html=True)

# --- Helper function for flexible column detection ---
def find_column(df, possible_names):
    """
    Find a column in the dataframe using flexible matching.
    Checks for exact match (case-insensitive) or partial match.
    """
    df_columns_lower = {col.lower(): col for col in df.columns}
    
    for name in possible_names:
        name_lower = name.lower()
        
        # Exact match (case-insensitive)
        if name_lower in df_columns_lower:
            return df_columns_lower[name_lower]
        
        # Partial match
        for col_lower, col_original in df_columns_lower.items():
            if name_lower in col_lower or col_lower in name_lower:
                return col_original
    
    return None

# --- Calculate similarity between two strings ---
def calculate_similarity(str1, str2):
    """Calculate similarity ratio between two strings (0-100%)"""
    if pd.isna(str1) or pd.isna(str2):
        return 0
    return SequenceMatcher(None, str(str1).lower(), str(str2).lower()).ratio() * 100

# --- Login function ---
def login():
    st.markdown('<h1 class="luxury-title">💎 Luxury Title Retitler</h1>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">AI-Powered Luxury Product Title Generation</p>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown('<p class="input-label">Username</p>', unsafe_allow_html=True)
        username = st.text_input("Username", placeholder="Enter your username", key="login_user", label_visibility="collapsed")
        
        st.markdown('<p class="input-label">Password</p>', unsafe_allow_html=True)
        password = st.text_input("Password", placeholder="Enter your password", type="password", key="login_pass", label_visibility="collapsed")
        
        login_button = st.button("🔐 LOGIN", use_container_width=True)
        
        if login_button:
            if username in USER_CREDENTIALS and USER_CREDENTIALS[username] == password:
                st.session_state.authenticated = True
                st.success("✅ Login successful! Redirecting...")
                st.rerun()
            else:
                st.error("❌ Invalid credentials. Please try again.")

# --- Logout function ---
def logout():
    st.session_state.authenticated = False
    st.session_state.processing_complete = False
    st.session_state.processed_df = None
    st.rerun()

# --- Main App ---
if not st.session_state.authenticated:
    login()
    st.stop()

# Authenticated content
st.sidebar.success(f"✅ **Logged in as:** admin")
if st.sidebar.button("🚪 Logout", use_container_width=True):
    logout()

# Main Header
st.markdown('<h1 class="luxury-title">💎 Luxury Product Title Retitler</h1>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">Transform your product titles with AI-powered precision using Google Gemini</p>', unsafe_allow_html=True)

# Create tabs for Title Generator and Accuracy Test
tab1, tab2 = st.tabs(["🎨 Title Generator", "📊 Accuracy Test"])

# ============= TAB 1: TITLE GENERATOR =============
with tab1:
    # Instructions Card
    st.markdown("### 📋 Instructions")
    st.markdown("""
    1. **Upload** an Excel file (.xlsx) with columns containing product data:
       - Product name (e.g., NAME, Product Name, Title)
       - Updated title column (e.g., Updated Title, New Title, Corrected Title)
       - Category (e.g., CATEGORY, Category, Product Category)
    2. **Process** titles automatically using Gemini AI
    3. **Download** your updated file with generated titles
    
    *Note: Column names are detected flexibly - exact matches not required!*
    """)

    # File Upload Section
    st.markdown('<h2 class="section-header">📂 Upload Your Excel File</h2>', unsafe_allow_html=True)

    uploaded_file = st.file_uploader(
        "Choose an Excel file",
        type=["xlsx"],
        help="Upload an Excel file containing your product data",
        key="title_gen_upload"
    )

    if uploaded_file:
        try:
            df = pd.read_excel(uploaded_file)
            
            # Flexible column detection
            name_col = find_column(df, ["NAME", "Product Name", "Title", "Product", "Item Name", "Item"])
            title_col = find_column(df, ["Updated Title", "New Title", "Corrected Title", "Title Output", "Generated Title"])
            category_col = find_column(df, ["CATEGORY", "Category", "Product Category", "Type", "Product Type"])
            
            # Validate required columns
            missing = []
            if not name_col:
                missing.append("Product Name column (e.g., NAME, Product Name)")
            if not title_col:
                missing.append("Updated Title column (e.g., Updated Title, New Title)")
            if not category_col:
                missing.append("Category column (e.g., CATEGORY, Category)")
            
            if missing:
                st.error(f"❌ Could not find required columns:\n" + "\n".join(f"- {m}" for m in missing))
                st.info(f"📊 Available columns in your file: {', '.join(df.columns.tolist())}")
                st.stop()
            
            # Show detected columns
            st.success(f"✅ Columns detected: **{name_col}** → **{title_col}** (Category: **{category_col}**)")

            total_rows = len(df)
            rows_to_process = df[title_col].isna().sum()
            rows_processed = total_rows - rows_to_process
            
            # File Summary
            st.markdown('<h2 class="section-header">📊 File Summary</h2>', unsafe_allow_html=True)
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("📝 Total Rows", f"{total_rows:,}")
            with col2:
                st.metric("⏳ To Process", f"{rows_to_process:,}", delta=None)
            with col3:
                st.metric("✅ Processed", f"{rows_processed:,}", delta=None)
            
            # Processing Section
            if rows_to_process > 0:
                st.markdown("### ⚡ Processing Titles")
                
                if st.button("🚀 Start Processing", type="primary", use_container_width=True):
                    progress_bar = st.progress(0.0)
                    status_text = st.empty()
                    start_time = datetime.now()
                    
                    def estimate_remaining(start, completed, total):
                        if completed == 0:
                            return "Calculating..."
                        elapsed = datetime.now() - start
                        remaining = (elapsed / completed) * (total - completed)
                        return str(timedelta(seconds=int(remaining.total_seconds())))
                    
                    def process_row(idx, name):
                        try:
                            result = correct_luxury_title(name)
                            # Expecting dict with "corrected_title" or just a string; handle both
                            if isinstance(result, dict):
                                return idx, result.get("corrected_title", "") 
                            else:
                                return idx, str(result)
                        except Exception as e:
                            return idx, f"Error: {str(e)}"
                    
                    to_process = [(idx, row[name_col]) for idx, row in df.iterrows() if pd.isna(row[title_col])]
                    
                    with ThreadPoolExecutor(max_workers=50) as executor:
                        futures = [executor.submit(process_row, idx, name) for idx, name in to_process]
                        
                        for i, future in enumerate(as_completed(futures)):
                            idx, updated_title = future.result()
                            df.at[idx, title_col] = updated_title
                            
                            progress = (i + 1) / len(to_process)
                            # progress_bar accepts 0.0-1.0 floats
                            progress_bar.progress(progress)
                            
                            status_text.markdown(f"""
                            **Progress:** {i + 1:,} / {len(to_process):,} ({int(progress * 100)}%)  
                            **Time Remaining:** {estimate_remaining(start_time, i + 1, len(to_process))}
                            """)
                    
                    elapsed = datetime.now() - start_time
                    st.success(f"✅ Processing complete in {str(timedelta(seconds=int(elapsed.total_seconds())))}")
                    
                    # Store processed dataframe in session state
                    st.session_state.processed_df = df
                    st.session_state.processing_complete = True
                    st.rerun()
            else:
                st.info("ℹ️ All rows are already processed!")
                st.session_state.processed_df = df
                st.session_state.processing_complete = True
            
            # Download Section - Only show after processing
            if st.session_state.processing_complete and st.session_state.processed_df is not None:
                st.markdown("---")
                st.markdown("### 📥 **DOWNLOAD YOUR RESULTS**")
                
                output = io.BytesIO()
                st.session_state.processed_df.to_excel(output, index=False)
                output.seek(0)
                
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                
                st.download_button(
                    label="⬇️ DOWNLOAD UPDATED EXCEL FILE",
                    data=output,
                    file_name=f"luxury_titles_{timestamp}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
            
            # Preview Table - Limited to 20 rows
            st.markdown('<h2 class="section-header">📋 Data Preview</h2>', unsafe_allow_html=True)
            
            preview_df = st.session_state.processed_df if st.session_state.processed_df is not None else df
            preview_rows = 20
            if len(preview_df) > preview_rows:
                st.info(f"Showing first {preview_rows} rows of {len(preview_df):,} total rows")
                st.dataframe(preview_df.head(preview_rows), use_container_width=True, height=400)
            else:
                st.dataframe(preview_df, use_container_width=True, height=400)
        
        except Exception as e:
            st.error(f"❌ Error processing file: {str(e)}")
            st.exception(e)

# ============= TAB 2: ACCURACY TEST =============
with tab2:
    st.markdown("### 📊 Accuracy Testing")
    st.markdown("""
    Upload two separate Excel files to compare AI-generated titles against ground truth (GT) titles.
    
    **Both files should have:**
    - `Updated Title` column (or similar naming like "New Title", "Title", etc.)
    - (Optional) Category column for breakdown analysis
    
    Files will be compared row-by-row (row 1 vs row 1, row 2 vs row 2, etc.)
    """)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 🤖 AI-Generated Titles File")
        ai_file = st.file_uploader(
            "Upload Excel with AI titles",
            type=["xlsx"],
            help="File containing AI-generated titles in 'Updated Title' column",
            key="ai_upload"
        )
    
    with col2:
        st.markdown("#### ✅ Ground Truth (GT) File")
        gt_file = st.file_uploader(
            "Upload Excel with GT titles",
            type=["xlsx"],
            help="File containing ground truth titles in 'Updated Title' column",
            key="gt_upload"
        )
    
    if ai_file and gt_file:
        try:
            ai_df = pd.read_excel(ai_file)
            gt_df = pd.read_excel(gt_file)
            
            # Detect title columns
            ai_title_col = find_column(ai_df, ["Updated Title", "New Title", "Title", "AI Title", "Generated Title"])
            gt_title_col = find_column(gt_df, ["Updated Title", "New Title", "Title", "GT Title", "Ground Truth"])
            
            # Validate
            if not ai_title_col:
                st.error(f"❌ Could not find title column in AI file. Available: {', '.join(ai_df.columns.tolist())}")
                st.stop()
            if not gt_title_col:
                st.error(f"❌ Could not find title column in GT file. Available: {', '.join(gt_df.columns.tolist())}")
                st.stop()
            
            # Check row counts
            if len(ai_df) != len(gt_df):
                st.warning(f"⚠️ Row count mismatch! AI file: {len(ai_df)} rows, GT file: {len(gt_df)} rows. Using minimum: {min(len(ai_df), len(gt_df))}")
            
            min_rows = min(len(ai_df), len(gt_df))
            
            # Detect category column
            cat_col = find_column(ai_df, ["CATEGORY", "Category", "Product Category", "Type"])
            if not cat_col:
                cat_col = find_column(gt_df, ["CATEGORY", "Category", "Product Category", "Type"])
            
            st.success(f"✅ Comparing **{ai_title_col}** (AI) vs **{gt_title_col}** (GT)" + (f" | Category: **{cat_col}**" if cat_col else ""))
            
            # Create comparison dataframe
            comparison_data = {
                'AI Title': ai_df[ai_title_col].head(min_rows).reset_index(drop=True),
                'GT Title': gt_df[gt_title_col].head(min_rows).reset_index(drop=True)
            }
            
            if cat_col:
                if cat_col in ai_df.columns:
                    comparison_data['Category'] = ai_df[cat_col].head(min_rows).reset_index(drop=True)
                elif cat_col in gt_df.columns:
                    comparison_data['Category'] = gt_df[cat_col].head(min_rows).reset_index(drop=True)
            
            acc_df = pd.DataFrame(comparison_data)
            
            # Calculate accuracy metrics
            acc_df['Exact Match'] = acc_df.apply(lambda row: str(row['AI Title']).lower().strip() == str(row['GT Title']).lower().strip(), axis=1)
            acc_df['Similarity %'] = acc_df.apply(lambda row: calculate_similarity(row['AI Title'], row['GT Title']), axis=1)
            
            total_rows = len(acc_df)
            exact_matches = int(acc_df['Exact Match'].sum())
            exact_accuracy = (exact_matches / total_rows * 100) if total_rows > 0 else 0
            avg_similarity = acc_df['Similarity %'].mean() if total_rows > 0 else 0
            
            # Display metrics
            st.markdown('<h2 class="section-header">📈 Accuracy Metrics</h2>', unsafe_allow_html=True)
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("📝 Total Rows", f"{total_rows:,}")
            with col2:
                st.metric("✅ Exact Matches", f"{exact_matches:,}")
            with col3:
                st.metric("🎯 Exact Accuracy", f"{exact_accuracy:.1f}%")
            with col4:
                st.metric("📊 Avg Similarity", f"{avg_similarity:.1f}%")
            
            # Category breakdown if available
            if cat_col and 'Category' in acc_df.columns:
                st.markdown('<h2 class="section-header">📂 Category Breakdown</h2>', unsafe_allow_html=True)
                
                category_stats = acc_df.groupby('Category').agg({
                    'Exact Match': ['count', 'sum'],
                    'Similarity %': 'mean'
                }).round(2)
                
                category_stats.columns = ['Total', 'Exact Matches', 'Avg Similarity %']
                category_stats['Accuracy %'] = (category_stats['Exact Matches'] / category_stats['Total'] * 100).round(1)
                
                st.dataframe(category_stats, use_container_width=True)
            
            # Mismatches table
            st.markdown('<h2 class="section-header">❌ Mismatches (Non-Exact)</h2>', unsafe_allow_html=True)
            
            mismatches = acc_df[~acc_df['Exact Match']]
            if len(mismatches) > 0:
                st.info(f"Found {len(mismatches):,} mismatches")
                
                display_cols = ['AI Title', 'GT Title', 'Similarity %']
                if 'Category' in acc_df.columns:
                    display_cols.insert(0, 'Category')
                
                preview_limit = 50
                if len(mismatches) > preview_limit:
                    st.warning(f"Showing first {preview_limit} of {len(mismatches):,} mismatches")
                    st.dataframe(mismatches[display_cols].head(preview_limit), use_container_width=True, height=400)
                else:
                    st.dataframe(mismatches[display_cols], use_container_width=True, height=400)
            else:
                st.success("🎉 No mismatches found! All titles match exactly!")
            
            # Download comparison results
            st.markdown('<h2 class="section-header">💾 Download Comparison</h2>', unsafe_allow_html=True)
            
            output = io.BytesIO()
            acc_df.to_excel(output, index=False)
            output.seek(0)
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            st.download_button(
                label="📥 Download Accuracy Comparison Results",
                data=output,
                file_name=f"accuracy_comparison_{timestamp}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
        
        except Exception as e:
            st.error(f"❌ Error processing accuracy file: {str(e)}")
            st.exception(e)

# Footer
st.markdown("---")
st.markdown(
    '<p style="text-align: center; color: #9ca3af; font-size: 0.9rem;">Powered by Google Gemini AI • Built with Streamlit</p>',
    unsafe_allow_html=True
)
