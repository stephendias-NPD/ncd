import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import os # We need this to check if the local file exists

# --- Page Config ---
st.set_page_config(page_title="Neuropedia Clinical Directory", page_icon="✅", layout="wide")

# --- Constants ---
JSON_KEY_FILE = "ncnc-staff-directory-2cf1ef3956ba.json"
SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/1UO1RRjt4d1JX7oU43k0PF8AhhTT5pQDhf0VXe4CW1Ws/edit?usp=sharing"

# --- Helper Functions ---

@st.cache_resource
def connect_to_google_sheets():
    """
    Connects to Google Sheets using a local JSON file (for testing)
    or Streamlit Secrets (for Cloud deployment).
    """
    try:
        scopes = ['https://www.googleapis.com/auth/spreadsheets']
        
        # 1. (NEW) Try to load from local file FIRST (for your laptop)
        if os.path.exists(JSON_KEY_FILE):
            creds = Credentials.from_service_account_file(JSON_KEY_FILE, scopes=scopes)
            
        # 2. (NEW) Fallback to Streamlit Secrets (for Cloud deployment)
        elif "gcp_service_account" in st.secrets:
            # Load credentials from the dictionary in Streamlit Secrets
            creds = Credentials.from_service_account_info(
                st.secrets["gcp_service_account"], 
                scopes=scopes
            )
            
        # 3. If neither is found, stop
        else:
            st.error("GCP service account key not found.")
            st.error("Please add `gcp_service_account` to your Streamlit Secrets.")
            st.stop()
            
        client = gspread.authorize(creds)
        sheet = client.open_by_url(SPREADSHEET_URL).sheet1
        return sheet
        
    except Exception as e:
        st.error(f"Connection Error: {e}")
        return None

def load_data(sheet):
    """Loads data from the sheet into a Pandas DataFrame."""
    try:
        data = sheet.get_all_records()
        df = pd.DataFrame(data)
        return df.astype(str)
    except Exception as e:
        st.error(f"Data Load Error: {e}")
        return pd.DataFrame()

def apply_custom_css():
    """
    Applies custom CSS. 
    THEME: 75% Dark Gray Background.
    FIX: Uses 'box-shadow' to force visible 1px white borders.
    """
    st.markdown("""
        <style>
        /* 1. FORCE Main Background Color (75% Dark Gray) */
        .stApp {
            background-color: #404040 !important;
        }
        
        /* 2. TEXT COLORS */
        /* Headings = Neuropedia Green */
        h1, h2, h3, h4, strong {
            color: #008764 !important;
        }
        
        /* Body Text = White */
        p, label, .stMarkdown, li, span, div {
            color: #FFFFFF;
        }
        
        /* 3. THE EXPANDER FIX (Box Shadow Trick) */
        [data-testid="stExpander"] {
            box-shadow: 0 0 0 1px white !important; /* 1px White "Border" */
            border-radius: 5px !important;
            background-color: transparent !important;
            overflow: hidden;
            margin-bottom: 20px;
        }
        [data-testid="stExpander"] > summary {
            background-color: #f0f0f0 !important; /* Light Grey Header */
            color: #008764 !important; /* Green Text */
            border-bottom: 1px solid white !important;
        }
        [data-testid="stExpander"] > summary p,
        [data-testid="stExpander"] > summary span,
        [data-testid="stExpander"] > summary svg {
            color: #008764 !important;
            fill: #008764 !important;
        }
        [data-testid="stExpander"] > div {
            background-color: #505050 !important; /* Darker Grey Content */
            color: white !important;
        }
        
        /* 4. INPUT BORDERS (Using Box Shadow) */
        div[data-baseweb="input"], 
        div[data-baseweb="select"] > div, 
        div[data-baseweb="base-input"] {
            background-color: #FFFFFF !important;
            box-shadow: 0 0 0 1px white !important; /* 1px White Border */
            border: none !important;
            border-radius: 4px !important;
        }
        input, textarea, .stSelectbox div[data-baseweb="select"] div {
            color: #000000 !important;
            -webkit-text-fill-color: #000000 !important;
            caret-color: black !important;
        }
        
        /* 5. DROPDOWN MENUS */
        div[data-baseweb="popover"], div[data-baseweb="menu"] {
            background-color: #FFFFFF !important;
            box-shadow: 0 0 0 1px white !important;
            border-radius: 4px !important;
        }
        div[data-baseweb="popover"] * {
            color: #000000 !important;
        }
        div[data-baseweb="menu"] li:hover {
            background-color: #f0f0f0 !important;
        }
        div[data-baseweb="menu"] li[aria-selected="true"] {
            background-color: #e8f5e9 !important;
            font-weight: bold;
        }

        /* 6. Read-only 'Disabled' Input Boxes */
        div[data-testid="stTextInput"] div[disabled] {
             background-color: #e0e0e0 !important;
             box-shadow: 0 0 0 1px white !important;
        }
        div[data-testid="stTextInput"] div[disabled] input {
             color: #555555 !important;
             -webkit-text-fill-color: #555555 !important;
        }

        /* 7. Footer Styling */
        .footer {
            position: fixed;
            left: 0;
            bottom: 0;
            width: 100%;
            background-color: #008764;
            color: white !important;
            text-align: center;
            padding: 10px;
            font-size: 14px;
            border-top: 1px solid white !important;
            z-index: 100;
        }
        .block-container {
            padding-bottom: 5rem;
        }
        
        /* 8. Focus States */
        div[data-baseweb="input"]:focus-within, 
        div[data-baseweb="select"] > div:focus-within {
            box-shadow: 0 0 0 2px white !important;
        }
        </style>
    """, unsafe_allow_html=True)

# --- Main App Layout ---
def main():
    apply_custom_css()
    
    st.title("Neuropedia Clinical Directory")

    # 1. Load Data
    sheet = connect_to_google_sheets()
    if not sheet: 
        st.stop()
    
    df = load_data(sheet)
    if df.empty: 
        st.warning("No data found.")
        st.stop()

    # ==========================================
    # SECTION 1: TOP FILTERS
    # ==========================================
    with st.expander("🔍 Search & Filters", expanded=True):
        c1, c2, c3 = st.columns([1, 2, 2])
        with c1:
            loc_options = ["NPD", "NPS", "CDC"]
            selected_locs = st.multiselect("Location", loc_options, placeholder="Select Location...")
        with c2:
            search_role = st.text_input("Role", placeholder="Search by role...")
        with c3:
            search_name = st.text_input("Name", placeholder="Search by name...")

        c4, c5, c6, c7 = st.columns(4)
        with c4:
            age_options = ["All"] + sorted(list(df["Age Group Seen"].unique())) if "Age Group Seen" in df.columns else ["All"]
            search_age = st.selectbox("Age Group", age_options)
        with c5:
            search_days = st.text_input("Days Available", placeholder="Search days...")
        with c6:
            search_specialty = st.text_input("Specialty Areas", placeholder="Search specialty...")
        with c7:
            search_lang = st.text_input("Languages", placeholder="Search languages...")

    # ==========================================
    # SECTION 2: SECURITY & FILTER LOGIC
    # ==========================================
    
    filters_applied = any([
        len(selected_locs) > 0,
        len(search_role.strip()) > 0,
        len(search_name.strip()) > 0,
        search_age != "All",
        len(search_days.strip()) > 0,
        len(search_specialty.strip()) > 0,
        len(search_lang.strip()) > 0
    ])

    if not filters_applied:
        st.info("👋 Please select a location or enter search criteria above to view the staff list.")
        st.stop() 

    # Apply filters
    filtered_df = df.copy()

    if selected_locs:
        pattern = '|'.join(selected_locs)
        filtered_df = filtered_df[filtered_df["Location"].str.contains(pattern, case=False, na=False)]
    if search_role:
        filtered_df = filtered_df[filtered_df["Role"].str.contains(search_role, case=False, na=False)]
    if search_name:
        filtered_df = filtered_df[filtered_df["Clinicians Name"].str.contains(search_name, case=False, na=False)]
    if search_age and search_age != "All":
        filtered_df = filtered_df[filtered_df["Age Group Seen"] == search_age]
    if search_days:
        filtered_df = filtered_df[filtered_df["Days Available"].str.contains(search_days, case=False, na=False)]
    if search_specialty:
        filtered_df = filtered_df[filtered_df["Specialty Areas"].str.contains(search_specialty, case=False, na=False)]
    if search_lang:
        filtered_df = filtered_df[filtered_df["Languages Spoken"].str.contains(search_lang, case=False, na=False)]

    if filtered_df.empty:
        st.warning("No matching staff found.")
        st.stop()

    # ==========================================
    # SECTION 3: DATA TABLE (Secure View)
    # ==========================================
    st.markdown("### Staff List")
    
    sensitive_cols = ["Photo", "Contact Number", "Contact (Extn)"]
    display_df = filtered_df.drop(columns=sensitive_cols, errors='ignore')
    
    event = st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
        selection_mode="single-row",
        on_select="rerun",
        height=300 
    )

    # ==========================================
    # SECTION 4: DETAILS PANEL
    # ==========================================
    st.markdown("---") 
    st.subheader("Clinician Details")

    if event.selection and event.selection.rows:
        selected_index = event.selection.rows[0]
        row = filtered_df.iloc[selected_index]

        d_col1, d_col2, d_col3 = st.columns([1, 2, 2])

        with d_col1:
            st.markdown("**Photo**")
            photo_url = row.get("Photo", "")
            if photo_url and str(photo_url).startswith("http"):
                st.image(photo_url, use_container_width=True)
            else:
                st.warning("No Photo")

        with d_col2:
            st.text_input("Name", value=row.get("Clinicians Name", ""), disabled=True)
            st.text_input("Role", value=row.get("Role", ""), disabled=True)
            st.text_input("Location", value=row.get("Location", ""), disabled=True)
            st.text_input("Email", value=row.get("Email Address", ""), disabled=True)

        with d_col3:
            st.text_input("Days Available", value=row.get("Days Available", ""), disabled=True)
            st.text_input("Age Group", value=row.get("Age Group Seen", ""), disabled=True)
            st.text_input("Languages", value=row.get("Languages Spoken", ""), disabled=True)
            
        st.text_area("Specialty Areas", value=row.get("Specialty Areas", ""), height=100, disabled=True)
    else:
        st.info("👆 Select a clinician from the table above to view their details below.")

    # ==========================================
    # SECTION 5: FOOTER
    # ==========================================
    st.markdown("""
        <div class="footer">
            <p>Stephen/Khizar © 2025 - Neuropedia | Clinical Directory v2.14</p>
        </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
