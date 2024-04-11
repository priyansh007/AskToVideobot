import streamlit as st
from pathlib import Path
import videoToScript
import sourcecode
import os


def ask_LLM(scrumbot):
    chat_history = st.session_state.get("chat_history", [])
    with st.form(key='user_input_form'):
        user_query = st.text_input("Enter your query:")
        submit_button = st.form_submit_button(label='Ask LLM')

    # Button to trigger the ask_llm function
    if submit_button:
        with st.spinner("Analyzing..."):
            llm_response = scrumbot.llm_bot(isChatBot=True,query=user_query)
        chat_history.append({"user": user_query, "llm": llm_response})
        st.session_state.chat_history = chat_history
        st.text_area("Answer:",value=llm_response, height=500, max_chars=None)
        st.subheader("Chat History")
        for entry in chat_history:
            st.markdown(f"User: {entry['user']}")
            st.markdown(f"LLM: {entry['llm']}")
            st.text("-----------"*5)     


def show_main_dashboard():
    st.title("ScrumBot")   
    uploaded_file = st.file_uploader("Choose a video file or txt file", type=["mp4", "avi", "mov", "mkv", "txt", "mp3"])
    
    if uploaded_file is not None:
        
        file_extension = Path(uploaded_file.name).suffix.lower()[1:]
        if file_extension not in ["mp4", "avi", "mov", "mkv", "txt", "mp3"]:
            st.error("Unsupported file format. Please upload an MP4, AVI, MOV,MP3 or MKV file.")
        else:
            filename = uploaded_file.name
            txt_filename =  filename.replace(file_extension, "txt")
           
            summary_filename = txt_filename.replace(".txt", "_summary.txt")
            s3_bucket="speech-to-text-meetsummarizar" 
            endpoint_name='speech-to-text-meetsummarizar-endpoint'
            prev_filename = st.session_state.get("prev_file", None)
            sourcecode.remove_all_txt_files(set([txt_filename, summary_filename]))
            scrumbot = videoToScript.ScrumBot(s3_bucket,
                                            filename,
                                            txt_filename,
                                            summary_filename,
                                            endpoint_name,
                                            file_extension)
            options = ["Summarize", "Analyze"]
            default_option_index = 0 
            
            if filename != prev_filename:
                st.session_state.chat_history = []
            st.session_state.prev_file = filename
            
            
            option_selected = st.radio("Select an action", options, index=default_option_index)
            bytes = uploaded_file.read()
            if option_selected == "Summarize":
                if os.path.exists(summary_filename):
                    with open(summary_filename, "r") as content:
                        summary = content.read()
                    if file_extension != "txt" and file_extension != "mp3":
                        st.video(bytes)
                else:
                    
                    with open(filename, "wb") as file:
                        file.write(bytes)
                    if file_extension == "txt":
                        sourcecode.upload_to_s3(filename, filename)
                    else:
                        if file_extension != "mp3":
                            st.video(bytes)
                        with st.spinner("Transcribing..."):
                            scrumbot.videoToScript()
                    with st.spinner("Summarizing..."):
                        summary = scrumbot.llm_bot()
                st.subheader("Summary:")
                st.text_area("Details are from Claude LLM",value=summary, height=500, max_chars=None)
            else:
                ask_LLM(scrumbot)
                
        
show_main_dashboard()

