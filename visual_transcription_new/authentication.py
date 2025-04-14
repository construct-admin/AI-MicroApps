"""
Authentication functions for Visual Transcription app
"""
import streamlit as st

def check_password():
    """Returns True if the password is correct, False otherwise."""
    try:
        # If already authenticated, return True
        if "authenticated" in st.session_state and st.session_state.authenticated:
            return True
        
        # If not set yet, initialize it to False
        if "authenticated" not in st.session_state:
            st.session_state.authenticated = False
        
        # Create login form
        st.title("VT Generator - Authentication Required")
        st.markdown("### Please enter your password to continue")
        st.markdown("This application requires authentication to access its functionality.")
        
        # Create columns for centered form
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            try:
                password = st.text_input("Password:", type="password", key="password_input")
                login_button = st.button("Login", key="login_button", type="primary")
                
                # Verify password
                if login_button or password:
                    if password == "pRoV3rsity!!@2024":
                        st.session_state.authenticated = True
                        st.success("Authentication successful! Loading application...")
                        st.experimental_rerun()
                        return True
                    else:
                        st.error("Incorrect password. Please try again.")
                        return False
            except Exception as input_error:
                st.error(f"Authentication input error: {input_error}")
                return False
        
        # Display application title only
        st.markdown("### VT Generator - Visual Transcription Service")
        
        return False
    except Exception as auth_error:
        st.error(f"Authentication error: {auth_error}")
        # In case of error, ensure we don't let through
        return False 