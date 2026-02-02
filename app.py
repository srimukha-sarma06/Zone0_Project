import streamlit as st
import cv2 as cv
import numpy as np
import time
import threading
import json
import psutil
from streamlit.runtime.scriptrunner import add_script_run_ctx
from services.get_dates import get_dates
from services.render_page import render_date_page
from services.threading_file import video_live 
import base64

def main():

    st.set_page_config(page_title="Industry Safety Dashboard", page_icon="🦺", layout="wide")

    if "latest_frame" not in st.session_state:
        st.session_state.latest_frame = None

    if "video_thread_started" not in st.session_state:
        st.session_state.video_thread_started = False

    if "machine_overlap" not in st.session_state:
        st.session_state.machine_overlap = None

    if "missing_ppe" not in st.session_state:
        st.session_state.missing_ppe = None

    if "fire_involved" not in st.session_state:
        st.session_state.fire_involved = False

    if "faint" not in st.session_state:
        st.session_state.faint = False

    if not st.session_state.video_thread_started:
        t = threading.Thread(target=video_live, args=(st.session_state,), daemon=True)
        add_script_run_ctx(t)
        t.start()
        st.session_state.video_thread_started = True


    st.sidebar.title("System Status")
    
    # Refresh metrics
    cpu_usage = psutil.cpu_percent(interval=None)
    ram = psutil.virtual_memory().percent
    
    # Create 3 columns now
    c1, c2, c3 = st.sidebar.columns(3)
    c1.metric("CPU", f"{cpu_usage}%")
    c2.metric("RAM", f"{ram}%")
    
    current_temp = getattr(st.session_state, 'current_temp', 0.0)
    c3.metric("Temp", f"{current_temp}°C")
    
    st.sidebar.divider()
    
    @st.cache_data(ttl=5)
    def cached_dates():
        return get_dates()

    st.sidebar.subheader("Accident Logs")
    dates = cached_dates()
    selected_date = st.sidebar.selectbox("Select Date", dates)

    tab1, tab2 = st.tabs(["Live Feed", "Accident History"])

    with tab1:
        st.header("Live Monitoring")
        
        if st.session_state.fire_involved:
            st.error(f"CRITICAL ALERT: FIRE DETECTED! EVACUATE!")
        elif st.session_state.machine_overlap:
            st.error(f"DANGER: ZONE BREACH ({st.session_state.machine_overlap})")
        elif st.session_state.missing_ppe:
            st.warning(f"PPE VIOLATION: {st.session_state.missing_ppe}")
        else:
            st.success("System Status: Secure")
        
        if st.session_state.faint:
            st.error(f"PERSON FAINTED: {st.session_state.faint}")

        # VIDEO FEED
        frame_slot = st.empty()
        if st.session_state.latest_frame is not None:
                display_frame = cv.resize(st.session_state.latest_frame, (640, 480))
                
                _, buffer = cv.imencode('.jpg', display_frame, [cv.IMWRITE_JPEG_QUALITY, 70])
                
                img_str = base64.b64encode(buffer).decode()
                
                frame_slot.markdown(
                    f'<img src="data:image/jpeg;base64,{img_str}" style="width:100%; border-radius:10px;">', 
                    unsafe_allow_html=True
                )
        else:
            frame_slot.warning("Initializing Camera Feed...")

    with tab2:
        if selected_date:
            render_date_page(selected_date)
        else:
            st.info("No logs available for selected date.")

    #time.sleep(0.01)
    st.rerun()

if __name__ == "__main__":
    main()
