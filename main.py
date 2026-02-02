import streamlit as st
import google_auth_oauthlib.flow
from googleapiclient.discovery import build
import json
import os

# Page config
st.set_page_config(page_title="Streamlit Google Auth", layout="centered")

st.title("Google Authentication with Streamlit")

# Load secrets
# Streamlit secrets are accessible via st.secrets
# We expect [web] section in .streamlit/secrets.toml
try:
    if "web" in st.secrets:
        client_config = dict(st.secrets["web"])
    else:
        # Fallback to loading from file if st.secrets doesn't have the section 
        # (though st.secrets should have it if .streamlit/secrets.toml exists)
        if os.path.exists("client_secret.json"):
            with open("client_secret.json", "r") as f:
                client_config = json.load(f)["web"]
        else:
            st.error("Configuration missing. Please set up .streamlit/secrets.toml or client_secret.json")
            st.stop()
except Exception as e:
    # Try one more fallback: check if client_secret.json exists in root
    if os.path.exists("client_secret.json"):
        with open("client_secret.json", "r") as f:
            client_config = json.load(f)["web"]
    else:
        st.error(f"Error loading configuration: {e}")
        st.stop()

# Constants
SCOPES = [
    'https://www.googleapis.com/auth/userinfo.email', 
    'https://www.googleapis.com/auth/userinfo.profile', 
    'openid'
]

# Helper to create flow
def create_flow():
    # Convert Streamlit secrets to standard dict for Flow
    # Ensure redirect_uris is a list
    if "redirect_uris" in client_config and isinstance(client_config["redirect_uris"], str):
        client_config["redirect_uris"] = [client_config["redirect_uris"]]
        
    flow = google_auth_oauthlib.flow.Flow.from_client_config(
        {"web": client_config},
        scopes=SCOPES,
        redirect_uri=client_config["redirect_uris"][0]
    )
    return flow

# Initialize session state
if "credentials" not in st.session_state:
    st.session_state.credentials = None

# Main Logic
if st.session_state.credentials:
    st.success("Successfully Logged in!")
    
    # Show user info
    try:
        service = build('oauth2', 'v2', credentials=st.session_state.credentials)
        user_info = service.userinfo().get().execute()
        
        col1, col2 = st.columns([1, 3])
        with col1:
            st.image(user_info.get('picture'), width=100)
        with col2:
            st.write(f"**Name:** {user_info.get('name')}")
            st.write(f"**Email:** {user_info.get('email')}")
        
        with st.expander("View Raw User Info"):
            st.json(user_info)
            
        if st.button("Logout"):
            st.session_state.credentials = None
            st.query_params.clear()
            st.rerun()
            
    except Exception as e:
        st.error(f"Error fetching user info: {e}")
        st.session_state.credentials = None
        st.rerun()

else:
    # Check for auth code in query params
    code = st.query_params.get("code")
    
    if code:
        with st.spinner("Authenticating..."):
            try:
                flow = create_flow()
                flow.fetch_token(code=code)
                credentials = flow.credentials
                st.session_state.credentials = credentials
                
                # Clear query params to clean URL
                st.query_params.clear()
                st.rerun()
            except Exception as e:
                st.error(f"Authentication failed: {e}")
                st.info("Please try logging in again.")
                if st.button("Retry"):
                    st.query_params.clear()
                    st.rerun()
    else:
        # Show login button
        st.write("Please log in to continue.")
        
        try:
            flow = create_flow()
            auth_url, _ = flow.authorization_url(prompt='consent')
            st.link_button("Login with Google", auth_url, type="primary")
            
            st.info(f"Note: This app is configured to redirect to: `{client_config['redirect_uris'][0]}`")
            st.warning("If you are running this locally (on Replit), the redirect will fail because it points to Streamlit Cloud. This is expected as per your configuration.")
        except Exception as e:
            st.error(f"Error creating auth flow: {e}")
