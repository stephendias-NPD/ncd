import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import os

# --- Page Config ---
st.set_page_config(page_title="Neuropedia Clinical Directory", page_icon="NCD.ico", layout="wide")

# --- Constants ---
JSON_KEY_FILE = "ncnc-staff-directory-2cf1ef3956ba.json"
SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/1UO1RRjt4d1JX7oU43k0PF8AhhTT5pQDhf0VXe4CW1Ws/edit?usp=sharing"

# --- Helper Functions ---

@st.cache_resource
def connect_to_google_sheets():
    """
    Connects to Google Sheets.
    Cached as a resource so we don't re-authenticate on every rerun.
    """
    try:
        scopes = ['https://www.googleapis.com/auth/spreadsheets']
        
        if os.path.exists(JSON_KEY_FILE):
            creds = Credentials.from_service_account_file(JSON_KEY_FILE, scopes=scopes)
        elif "gcp_service_account" in st.secrets:
            creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scopes)
        else:
            st.error("GCP service account key not found.")
            st.stop()
            
        client = gspread.authorize(creds)
        return client
    except Exception as e:
        st.error(f"Connection Error: {e}")
        return None

@st.cache_data(ttl=600)
def load_data(_client, sheet_url):
    """
    Loads data from the sheet into a Pandas DataFrame.
    Cached for 600 seconds (10 mins) to prevent hitting Google API limits.
    """
    try:
        sheet = _client.open_by_url(sheet_url).sheet1
        data = sheet.get_all_records()
        df = pd.DataFrame(data)
        
        # Clean data: Fill NaN with empty strings BEFORE converting to string
        df = df.fillna("")
        return df.astype(str)
    except Exception as e:
        st.error(f"Data Load Error: {e}")
        return pd.DataFrame()

def apply_custom_css():
    st.markdown("""
        <style>
        /* 1. Main Background Color (Soft Gray) */
        .stApp { background-color: #f5f7fa !important; }
        
        /* 2. TEXT COLORS */
        h1, h2, h3, h4, strong { color: #008764 !important; }
        /* Body Text - The 'div' fix is handled naturally by removing 'div' from the list */
        p, label, .stMarkdown, li, span { color: #333333; }
        
        /* 3. Expander Styling */
        [data-testid="stExpander"] {
            border: 1px solid #008764 !important;
            border-radius: 5px !important;
            background-color: transparent !important;
            margin-bottom: 20px;
        }
        [data-testid="stExpander"] > summary {
            background-color: #e8f5e9 !important;
            color: #008764 !important;
            border-bottom: 1px solid #008764 !important;
        }
        [data-testid="stExpander"] > summary p,
        [data-testid="stExpander"] > summary span,
        [data-testid="stExpander"] > summary svg {
            color: #008764 !important;
            fill: #008764 !important;
        }
        [data-testid="stExpander"] > div {
            background-color: #FFFFFF !important;
            color: #333333 !important;
        }
        
        /* 4. Inputs */
        div[data-baseweb="input"], div[data-baseweb="select"] > div, div[data-baseweb="base-input"] {
            background-color: #FFFFFF !important;
            border: 1px solid #cccccc !important;
            border-radius: 4px !important;
        }
        input, textarea, .stSelectbox div[data-baseweb="select"] div {
            color: #000000 !important;
            -webkit-text-fill-color: #000000 !important;
            caret-color: black !important;
        }

        /* 5. Footer */
        .footer {
            position: fixed; left: 0; bottom: 0; width: 100%;
            background-color: #008764; color: white !important;
            text-align: center; padding: 10px; font-size: 14px;
            border-top: 1px solid #008764 !important; z-index: 100;
        }
        .footer p { color: white !important; margin: 0; }
        .block-container { padding-bottom: 5rem; }
        
        /* 9. Dataframe & Tags Fixes */
        [data-testid="stMultiSelect"] [data-baseweb="tag"] { background-color: #008764 !important; }
        .ag-row { cursor: pointer !important; }
        .ag-row-selected { background-color: #e8f5e9 !important; }
        .ag-row-selected .ag-cell, .ag-row-selected .ag-cell p { color: #333333 !important; }
        .ag-row-hover { background-color: #f0f0f0 !important; }
        .ag-row-hover .ag-cell, .ag-row-hover .ag-cell p { background-color: #f0f0f0 !important; color: #333333 !important; }
        
        /* 10. Dynamic Specialty Box */
        .specialty-box {
            background-color: #FFFFFF !important;
            border: 1px solid #cccccc !important;
            border-radius: 4px;
            padding: 10px;
            min-height: 45px;
            width: 100%;
            color: #333333 !important;
        }
        .specialty-box p { color: #333333 !important; }
        </style>
    """, unsafe_allow_html=True)

# --- Main App Layout ---
def main():
    apply_custom_css()
    
    # Always render footer
    st.markdown("""
        <div class="footer">
            <p>Stephen/Khizar © 2025 - Neuropedia | Clinical Directory v2.4</p>
        </div>
    """, unsafe_allow_html=True)

    st.title("Neuropedia Clinical Directory")

    # 1. Initialize Connection (Cached Resource)
    client = connect_to_google_sheets()
    if not client: 
        st.stop()
    
    # 2. Load Data (Cached Data)
    df = load_data(client, SPREADSHEET_URL)
    if df.empty: 
        st.warning("No data found or connection failed.")
        st.stop()

    # ==========================================
    # SECTION 1: SEARCH & FILTERS
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
            # Get unique values safely, filtering out empty ones
            valid_ages = [x for x in sorted(df["Age Group Seen"].unique()) if x]
            age_options = ["All"] + valid_ages
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
    # SECTION 3: DATA TABLE
    # ==========================================
    st.markdown("### Staff List")
    
    sensitive_cols = ["Photo", "Contact Number", "Contact (Extn)"]
    display_df = filtered_df.drop(columns=sensitive_cols, errors='ignore')
    
    # Configure columns for better display
    column_config = {
        "Clinicians Name": st.column_config.TextColumn("Name", width="medium"),
        "Role": st.column_config.TextColumn("Role", width="medium"),
        "Location": st.column_config.TextColumn("Loc", width="small"),
        "Email Address": st.column_config.TextColumn("Email", width="medium"),
        "Days Available": st.column_config.TextColumn("Days", width="medium"),
    }

    event = st.dataframe(
        display_df,
        width='stretch', # FIX 1: Replaced use_container_width=True with width='stretch'
        hide_index=True,
        selection_mode="single-row",
        on_select="rerun",
        column_config=column_config,
        height=300
    )

    # ==========================================
    # SECTION 4: DETAILS PANEL
    # ==========================================
    st.markdown("---") 
    st.subheader("Clinician Details")

    if event.selection and event.selection.rows:
        selected_index = event.selection.rows[0]
        # Fetch row from filtered_df to get hidden columns (Photo, etc.)
        row = filtered_df.iloc[selected_index]

        d_col1, d_col2, d_col3 = st.columns([1, 2, 2])

        with d_col1:
            st.markdown("**Photo**")
            photo_url = row.get("Photo", "")
            if photo_url and str(photo_url).strip().lower().startswith("http"):
                # FIX 2: Removed use_container_width=True to use standard st.image sizing
                st.image(photo_url) 
            else:
                # Placeholder if no photo
                st.markdown(
                    f'<div style="background:#eee;height:150px;display:flex;align-items:center;justify-content:center;border-radius:5px;color:#555;">No Photo</div>', 
                    unsafe_allow_html=True
                )

        with d_col2:
            st.text_input("Name", value=row.get("Clinicians Name", ""), disabled=True)
            st.text_input("Role", value=row.get("Role", ""), disabled=True)
            st.text_input("Location", value=row.get("Location", ""), disabled=True)
            st.text_input("Email", value=row.get("Email Address", ""), disabled=True)

        with d_col3:
            st.text_input("Days Available", value=row.get("Days Available", ""), disabled=True)
            st.text_input("Age Group", value=row.get("Age Group Seen", ""), disabled=True)
            st.text_input("Languages", value=row.get("Languages Spoken", ""), disabled=True)
            
        st.markdown("**Specialty Areas**")
        specialty_text = row.get("Specialty Areas", "N/A")
        # Simple clean up
        specialty_text_html = specialty_text.replace("\n", "<br>")
        st.markdown(f'<div class="specialty-box">{specialty_text_html}</div>', unsafe_allow_html=True)
        
    else:
        st.info("👆 Select a clinician from the table above to view their details below.")

if __name__ == "__main__":
    main()