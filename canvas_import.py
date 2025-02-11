#!/usr/bin/env python3
import os
import requests
import streamlit as st

# ---------------------------
# Configuration and Metadata
# ---------------------------
PUBLISHED = True
SYSTEM_PROMPT = "Convert raw content into properly formatted HTML excluding any DOCTYPE or extraneous header lines."

# ---------------------------------------
# Canvas API Functions
# ---------------------------------------

def get_headers():
    """Retrieve authentication headers for Canvas API requests."""
    return {
        "Authorization": f"Bearer {st.secrets['CANVAS_ACCESS_TOKEN']}",
        "Content-Type": "application/json"
    }

def get_existing_module(module_name, canvas_domain, course_id):
    """Check if a module with the given name exists in Canvas LMS."""
    url = f"https://{canvas_domain}/api/v1/courses/{course_id}/modules"
    response = requests.get(url, headers=get_headers())

    if response.status_code == 200:
        modules = response.json()
        for module in modules:
            if module["name"].strip().lower() == module_name.strip().lower():
                return module["id"]  # Return the existing module ID
    st.warning(f"Module '{module_name}' not found. A new module will be created.")
    return None  # Return None if module doesn't exist

def create_module(module_name, canvas_domain, course_id):
    """Create a new module in the Canvas course."""
    url = f"https://{canvas_domain}/api/v1/courses/{course_id}/modules"
    payload = {"module": {"name": module_name, "published": PUBLISHED}}
    response = requests.post(url, headers=get_headers(), json=payload)

    if response.status_code in [200, 201]:
        st.success(f"✅ Module '{module_name}' created successfully!")
        return response.json()["id"]
    
    st.error(f"❌ Failed to create module '{module_name}'. Error: {response.text}")
    return None

def create_wiki_page(page_title, page_body, canvas_domain, course_id):
    """Create a new wiki page in the Canvas course."""
    url = f"https://{canvas_domain}/api/v1/courses/{course_id}/pages"
    payload = {"wiki_page": {"title": page_title, "body": page_body, "published": PUBLISHED}}
    response = requests.post(url, headers=get_headers(), json=payload)

    if response.status_code in [200, 201]:
        st.success(f"✅ Page '{page_title}' created successfully!")
        return response.json()
    
    st.error(f"❌ Failed to create page '{page_title}'. Error: {response.text}")
    return None

def add_page_to_module(module_id, page_title, page_url, canvas_domain, course_id):
    """Add an existing wiki page to a module in Canvas."""
    url = f"https://{canvas_domain}/api/v1/courses/{course_id}/modules/{module_id}/items"
    payload = {"module_item": {"title": page_title, "type": "Page", "page_url": page_url, "published": PUBLISHED}}
    response = requests.post(url, headers=get_headers(), json=payload)

    if response.status_code in [200, 201]:
        st.success(f"✅ Page '{page_title}' added to module successfully!")
        return response.json()
    
    st.error(f"❌ Failed to add page to module. Error: {response.text}")
    return None

# ---------------------------------------
# OpenAI API Call
# ---------------------------------------
def get_ai_generated_html(prompt):
    """Calls OpenAI API to format extracted content into HTML."""
    openai_api_key = st.secrets["OPENAI_API_KEY"]  
    if not openai_api_key:
        st.error("❌ Missing OpenAI API Key. Please add it to your Streamlit secrets.")
        return None

    headers = {
        "Authorization": f"Bearer {openai_api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "gpt-4o",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.3
    }

    response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
    
    if response.status_code == 200:
        return response.json()["choices"][0]["message"]["content"].strip("`")  # Strip any ```
    
    st.error(f"❌ OpenAI API Error: {response.status_code} - {response.text}")
    return None

# ---------------------------------------
# Main Streamlit App
# ---------------------------------------
def main():
    st.set_page_config(page_title="Construct HTML Generator", layout="centered", initial_sidebar_state="expanded")
    
    st.title("Construct HTML Generator")
    st.markdown("""
    This tool allows you to convert text content into properly formatted HTML and upload it to Canvas LMS.
    """)

    st.header("Step 1: Provide Canvas Page Details")
    
    module_title = st.text_input("Enter the title of your module:")
    page_title = st.text_input("Enter the title of your page:")
    uploaded_files = st.file_uploader("Choose files", type=['docx', 'pdf'], accept_multiple_files=True)
    
    uploaded_text = ""
    if uploaded_files:
        uploaded_text = "\n".join([file.read().decode('utf-8') for file in uploaded_files])
        st.text_area("Extracted Text", uploaded_text, height=300)

    st.header("Step 2: Generate HTML")
    if st.button("Generate HTML"):
        if not module_title or not page_title or not uploaded_text:
            st.error("❌ Please provide all inputs (module title, page title, and upload at least one file).")
        else:
            prompt = f"Module: {module_title}\nPage Title: {page_title}\nContent: {uploaded_text}"
            ai_generated_html = get_ai_generated_html(prompt)

            if ai_generated_html:
                st.markdown("### AI-Generated HTML Output:")
                st.text_area("AI Response:", ai_generated_html, height=300)
                st.session_state.ai_generated_html = ai_generated_html
            else:
                st.error("❌ AI failed to generate HTML content.")

    st.header("Step 3: Push to Canvas")
    if "ai_generated_html" in st.session_state and st.session_state.ai_generated_html:
        if st.button("Push to Canvas"):
            canvas_domain = st.secrets["CANVAS_DOMAIN"]
            course_id = st.secrets["CANVAS_ID"]

            if not canvas_domain or not course_id:
                st.error("❌ Missing Canvas configuration settings.")
                return
            
            headers = get_headers()

            # 🔍 Check if the module exists before creating it
            existing_module_id = get_existing_module(module_title, canvas_domain, course_id)

            if existing_module_id:
                st.info(f"✅ Module '{module_title}' found in Canvas. Adding page to existing module.")
                module_id = existing_module_id
            else:
                module_id = create_module(module_title, canvas_domain, course_id)
                if not module_id:
                    return

            # 📝 Create the wiki page
            page_data = create_wiki_page(page_title, st.session_state.ai_generated_html, canvas_domain, course_id)
            if not page_data:
                return

            # 🔗 Add the wiki page to the module
            page_url = page_data.get("url") or page_title.lower().replace(" ", "-")
            add_page_to_module(module_id, page_title, page_url, canvas_domain, course_id)

            st.success(f"🎉 Successfully added '{page_title}' to module '{module_title}' in Canvas!")

if __name__ == "__main__":
    main()
