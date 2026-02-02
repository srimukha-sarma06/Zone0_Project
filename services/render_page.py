from PIL import Image
import streamlit as st
import os
import json

VALID_EXT = (".jpg", ".jpeg", ".png")

def render_date_page(date):
    st.title(f"Accidents on {date}")
    
    folder = os.path.join("accidents", date)
    
    if not os.path.exists(folder):
        st.error("Folder not found.")
        return

    images = sorted(
        [f for f in os.listdir(folder) if f.lower().endswith(VALID_EXT)],
        reverse=True
    )

    if not images:
        st.info("No accidents recorded for this date.")
        return

    for img in images:
        col1, col2 = st.columns([3, 1])
        
        # 1. Get the Image Path
        img_path = os.path.join(folder, img)
        
        # 2. Find the Companion JSON file
        json_filename = img.rsplit('.', 1)[0] + ".json"
        json_path = os.path.join(folder, json_filename)
        
        # Default values in case JSON is missing (legacy data)
        machine_name = "Unknown"
        fire = False
        
        # 3. Read the specific data for THIS accident
        if os.path.exists(json_path):
            try:
                with open(json_path, 'r') as f:
                    accident_summary = json.load(f)
                    machine_name = accident_summary.get('machine', 'Unknown')
                    fire = accident_summary.get('fire_involved', False)
                    
            except Exception:
                pass 
        
        with col1:
            st.subheader("Frame:")
            st.image(Image.open(img_path))

        with col2:
            st.subheader("Accident Summary")
            
            st.error(f"Machine: {machine_name}")
            st.error(f"Fire Involved: {fire}")
            
            time_str = img.rsplit('.', 1)[0].replace("-", ":")
            st.write(f"Time: {time_str}")
    
        st.divider()