import streamlit as st
import pandas as pd
import io
from luxury_correction import correct_luxury_title
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta

import streamlit as st

# --- Page Configuration ---
st.set_page_config(page_title="Luxury Title Retitler", layout="wide")

# --- User Credentials ---
USER_CREDENTIALS = {
    "admin": "luxury123"
}

# --- Initialize authentication ---
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

# --- CSS for big input text, placeholders, and custom button ---
st.markdown("""
<style>
/* Properly sized input boxes for large text with wider blue box */
input, [type="password"] {
    font-size: 20px !important;       /* size of typed text */
    height: 120px !important;         /* enough height for large font */
    width: 100% !important;           /* full width for blue box */
    max-width: 1200px !important;     /* prevent excessive stretching */
    padding: 10px 20px !important;    
    border-radius: 1px !important;
    border: 1px solid #2E86C1 !important;  /* thicker blue border */
    line-height: 1.1 !important;
    font-weight: bold !important;
    color: #2E86C1 !important;
    box-sizing: border-box;
    background-color: #D6EAF8 !important; /* light blue shading inside input */
}

/* Placeholder text size */
input::placeholder, [type="password"]::placeholder {
    font-size: 30px !important;
    color: #95A5A6 !important;
}

/* Remove default Streamlit labels */
div[data-baseweb="form-control"] label {
    display: none !important;
}

/* Custom login button with wider blue box */
div.stButton > button {
    width: 100% !important;            /* full width for button */
    max-width: 1200px !important;      
    height: 120px;
    font-size: 60px;
    font-weight: bold;
    color: white;
    background: linear-gradient(90deg, #2E86C1, #5DADE2);
    border: none;
    border-radius: 25px;
    box-shadow: 0px 5px 20px rgba(46, 134, 193, 0.7); /* stronger blue shadow */
    cursor: pointer;
    transition: 0.3s;
}
div.stButton > button:hover {
    opacity: 0.9;
}

/* Center content */
.css-1d391kg {
    justify-content: center !important;
    align-items: center !important;
    width: 100% !important;            /* ensure the container spans full width */
}
</style>
""", unsafe_allow_html=True)






# --- Login function ---
def login():
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("""
        <h1 style='text-align:center; font-size:100px; color:#2E86C1;'>🔒 Luxury Title Retitler</h1>
        <h3 style='text-align:center; font-size:50px; color:#34495E;'>Please login to continue</h3>
        """, unsafe_allow_html=True)

        st.markdown("<div style='margin-top:50px;'></div>", unsafe_allow_html=True)

        # Username input
        st.markdown("<p style='font-size:60px; font-weight:bold; color:#2E86C1;'>Username</p>", unsafe_allow_html=True)
        username = st.text_input("", placeholder="Type your username here", key="login_user")

        st.markdown("<div style='margin-top:30px;'></div>", unsafe_allow_html=True)

        # Password input
        st.markdown("<p style='font-size:60px; font-weight:bold; color:#2E86C1;'>Password</p>", unsafe_allow_html=True)
        password = st.text_input("", placeholder="Type your password here", type="password", key="login_pass")

        st.markdown("<div style='margin-top:50px;'></div>", unsafe_allow_html=True)

        # Working luxury login button
        login_button = st.button("LOGIN")

        # Handle login
        if login_button:
            if username in USER_CREDENTIALS and USER_CREDENTIALS[username] == password:
                st.session_state.authenticated = True
                st.success("✅ Login successful!")
            else:
                st.error("❌ Invalid username or password. Please try again.")

# --- Logout function ---
def logout():
    st.session_state.authenticated = False

# --- Main ---
if not st.session_state.authenticated:
    login()
    st.stop()
else:
    st.sidebar.success(f"✅ Logged in as: admin")
    if st.sidebar.button("🚪 Logout"):
        logout()

    # --- Main content after login ---
    st.title("Welcome to Luxury Title Retitler")
    st.write("You are now authenticated. Here you can add your app functionality.")



st.set_page_config(page_title="Luxury Title Retitler", layout="wide")

# --- Title and instructions with big font ---
st.markdown("<h1 style='font-size:100px; text-align:center;'>Luxury Product Title Retitler</h1>", unsafe_allow_html=True)
st.markdown("<h3 style='font-size:50px; text-align:center;'>Upload an Excel file with columns: NAME, Updated Title, CATEGORY</h3>", unsafe_allow_html=True)
st.write("")

# --- Big label above uploader ---
st.markdown("<h2 style='font-size:50px; color:#2E86C1;'>📂 Upload Your Excel File Here</h2>", unsafe_allow_html=True)
st.markdown("<p style='font-size:40px; color:#34495E;'>Drag and drop your Excel file here or click to browse. Supported type: .xlsx</p>", unsafe_allow_html=True)

# --- Normal-sized uploader box ---
# --- Custom CSS for uploader size ---
st.markdown(
    """
    <style>
    /* Target the file uploader container */
    div.stFileUploader {
        width: 100px;       /* Small width */
        height: 50px;      /* Tall height */
        border: 50px dashed #2E86C1;
        border-radius: 5px;
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 500px;
    }
    /* Make the "Browse files" button bigger */
    div.stFileUploader button {
        font-size: 100px;
        padding: 100px 100px;
    }
    </style>
    """, unsafe_allow_html=True
)

# --- Normal uploader (CSS will style it) ---
uploaded_file = st.file_uploader(
    label="",
    type=["xlsx"],
    label_visibility="collapsed",
    key="file_uploader"
)

if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file)

        # ✅ Normalize column names (case-insensitive, remove extra spaces)
        df.columns = df.columns.str.strip().str.lower()

        # ✅ Define required columns in lowercase
        required_columns = ["name", "updated title", "category"]

        # ✅ Check for missing columns
        for col in required_columns:
            if col not in df.columns:
                st.error(f"❌ Missing required column: {col}")
                st.stop()

        # ✅ Rename back to expected format so rest of code still works
        df.rename(columns={
            "name": "NAME",
            "updated title": "Updated Title",
            "category": "CATEGORY"
        }, inplace=True)

        

        total_rows = len(df)
        rows_to_process = df["Updated Title"].isna().sum()
        rows_processed = total_rows - rows_to_process

        # --- File Summary in large text ---
        st.markdown("<h2 style='font-size:80px;'>📊 File Summary</h2>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1, 1, 1])
        col1.metric("Total Rows", total_rows)
        col2.metric("Rows to Process", rows_to_process)
        col3.metric("Rows Already Processed", rows_processed)

        if rows_to_process > 0:
            st.markdown("<h3 style='font-size:80px;'>⏳ Processing Titles</h3>", unsafe_allow_html=True)
            
            progress_bar = st.progress(0)
            progress_text = st.empty()
            start_time = datetime.now()
            
            # Estimate function for remaining time
            def estimate_remaining(start, completed, total):
                elapsed = datetime.now() - start
                if completed == 0:
                    return "Estimating..."
                remaining = (elapsed / completed) * (total - completed)
                return str(timedelta(seconds=int(remaining.total_seconds())))

            def process_row(idx, name):
                try:
                    result = correct_luxury_title(name)
                    return idx, result.get("corrected_title", "")
                except Exception as e:
                    return idx, f"Error: {str(e)}"

            to_process = [(idx, row["NAME"]) for idx, row in df.iterrows() if pd.isna(row["Updated Title"])]

            with ThreadPoolExecutor(max_workers=50) as executor:
                futures = [executor.submit(process_row, idx, name) for idx, name in to_process]
                for i, future in enumerate(as_completed(futures)):
                    idx, updated_title = future.result()
                    df.at[idx, "Updated Title"] = updated_title
                    # Update progress bar with percentage
                    progress_bar.progress((i + 1) / len(to_process))
                    progress_text.markdown(
                        f"<h3 style='font-size:80px;'>Progress: {i + 1}/{len(to_process)} "
                        f"({int((i + 1)/len(to_process)*100)}%) | "
                        f"Estimated time left: {estimate_remaining(start_time, i + 1, len(to_process))}</h3>",
                        unsafe_allow_html=True
                    )

            finished_time = datetime.now()
            st.success(f"✅ Processing complete! Finished at {finished_time.strftime('%H:%M:%S')}")

            # Updated Summary
            rows_to_process = df["Updated Title"].isna().sum()
            rows_processed = total_rows - rows_to_process
            st.markdown("<h2 style='font-size:80px;'>✅ Updated Summary</h2>", unsafe_allow_html=True)

            st.markdown(
                f"""
                <div style='display: flex; justify-content: space-around; text-align: center; margin-top: 30px;'>

                    <div style='flex: 1;'>
                        <div style='font-size:800px; font-weight:bold; color:#2E86C1;'>{total_rows}</div>
                        <div style='font-size:600px; color:#34495E;'>Total Rows</div>
                    </div>

                    <div style='flex: 1;'>
                        <div style='font-size:800px; font-weight:bold; color:#C0392B;'>{rows_to_process}</div>
                        <div style='font-size:600px; color:#34495E;'>Rows to Process</div>
                    </div>

                    <div style='flex: 1;'>
                        <div style='font-size:800px; font-weight:bold; color:#27AE60;'>{rows_processed}</div>
                        <div style='font-size:600px; color:#34495E;'>Rows Already Processed</div>
                    </div>

                </div>
                """,
                unsafe_allow_html=True
            )

        else:
            st.info("All rows are already processed.")

        # --- Large dataframe display ---
        st.markdown("<h2 style='font-size:80px;'>📝 Updated Table</h2>", unsafe_allow_html=True)
        st.dataframe(df, width=6000, height=10000)

        # --- Download button ---
        output = io.BytesIO()
        df.to_excel(output, index=False)
        output.seek(0)

        st.download_button(
            label="📥 Download Updated Excel",
            data=output,
            file_name="updated_titles.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )

    except Exception as e:
        st.error(f"❌ Error processing file: {str(e)}")
