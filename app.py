import streamlit as st, os, time
from google import genai
from google.genai import types
from pypdf import PdfReader, PdfWriter, PdfMerger
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def setup_page():
    st.set_page_config(
        page_title="AI-Powered Chatbot",
        layout="centered"
    )

    st.header("AI-Powered Chatbot", anchor=False, divider="blue")

    st.sidebar.header("Options", divider='rainbow')

    hide_menu_style = """
            <style>
            #MainMenu {visibility: hidden;}
            </style>
            """
    st.markdown(hide_menu_style, unsafe_allow_html=True)


def get_choice():
    choice = st.sidebar.radio("Choose:", ["Chat with AI",
                                          "Chat with a PDF",
                                          "Chat with many PDFs",
                                          "Chat with an image",
                                          "Chat with audio",
                                          "Chat with video"], )
    return choice


def get_clear():
    clear_button = st.sidebar.button("Start new session", key="clear")
    return clear_button


def main():
    choice = get_choice()

    if choice == "Chat with AI":
        st.subheader("Chat with AI")
        clear = get_clear()
        if clear:
            if 'message' in st.session_state:
                del st.session_state['message']

        if 'message' not in st.session_state:
            st.session_state.message = " "

        if 'chat' not in st.session_state or clear: # Create a new chat object at the begining of session or after "Start New Session" button is clicked
            st.session_state.chat = client.chats.create(model=MODEL_ID, config=types.GenerateContentConfig(
                system_instruction="You are a helpful assistant. Your answers need to be positive and accurate.", ))

        prompt = st.chat_input("Enter your question here")
        if prompt:
            with st.chat_message("user"):
                st.write(prompt)

            st.session_state.message += prompt
            with st.chat_message(
                    "model", avatar="🟦",
            ):
                response = st.session_state.chat.send_message(st.session_state.message) # Now using the chat object from session state
                st.markdown(response.text)
                st.sidebar.markdown(str(response.usage_metadata))
            st.session_state.message += response.text

    elif choice == "Chat with a PDF":
        st.subheader("Chat with your PDF file")
        clear = get_clear()
        if clear:
            if 'message' in st.session_state:
                del st.session_state['message']

        if 'message' not in st.session_state:
            st.session_state.message = " "

        uploaded_files = st.file_uploader("Choose your pdf file", type=['pdf'], accept_multiple_files=False)
        if uploaded_files:
            try:
                with st.spinner("Uploading and processing PDF..."):
                    # Save uploaded file to temporary location
                    with open("temp.pdf", "wb") as f:
                        f.write(uploaded_files.read())

                    file_upload = client.upload_file(file="temp.pdf", mime_type="application/pdf") # Mime Type added for better compatibility


                if 'chat2' not in st.session_state or clear: # Check if chat object exists or if "clear" is pressed
                    st.session_state.chat2 = client.chats.create(model=MODEL_ID,
                        history=[
                            types.Content(
                                role="user",
                                parts=[

                                        types.Part.from_uri(
                                            file_uri=file_upload.uri,
                                            mime_type="application/pdf"), # Mime Type added here too for compatibility
                                        ]
                                ),
                            ]
                            )
                prompt2 = st.chat_input("Enter your question here")
                if prompt2:
                    with st.chat_message("user"):
                        st.write(prompt2)

                    st.session_state.message += prompt2
                    with st.chat_message(
                        "model", avatar="🟦",
                    ):
                        response2 = st.session_state.chat2.send_message(st.session_state.message)
                        st.markdown(response2.text)
                        st.sidebar.markdown(str(response2.usage_metadata))
                    st.session_state.message += response2.text
            except Exception as e:
                st.error(f"An error occurred processing the PDF: {e}")
            finally:
                if os.path.exists("temp.pdf"):
                    os.remove("temp.pdf")  # Clean up temporary file

    elif choice == "Chat with many PDFs":
        st.subheader("Chat with your PDF file")
        clear = get_clear()
        if clear:
            if 'message' in st.session_state:
                del st.session_state['message']

        if 'message' not in st.session_state:
            st.session_state.message = " "

        uploaded_files2 = st.file_uploader("Choose 1 or more files", type=['pdf'], accept_multiple_files=True)

        if uploaded_files2:
            try:
                with st.spinner("Merging PDFs..."):
                    merger = PdfMerger()
                    temp_files = []  # Keep track of temporary files

                    for file in uploaded_files2:
                        temp_file_path = f"temp_{file.name}"  # Unique temporary filename
                        with open(temp_file_path, "wb") as f:
                            f.write(file.read())
                        merger.append(temp_file_path)
                        temp_files.append(temp_file_path)

                    fullfile = "merged_all_files.pdf"
                    merger.write(fullfile)
                    merger.close()

                with st.spinner("Uploading merged PDF..."):
                    file_upload = client.upload_file(file=fullfile, mime_type="application/pdf")

                if 'chat2b' not in st.session_state or clear:
                    st.session_state.chat2b = client.chats.create(model=MODEL_ID,
                        history=[
                            types.Content(
                                role="user",
                                parts=[

                                        types.Part.from_uri(
                                            file_uri=file_upload.uri,
                                            mime_type="application/pdf"),
                                        ]
                                ),
                            ]
                            )

                prompt2b = st.chat_input("Enter your question here")
                if prompt2b:
                    with st.chat_message("user"):
                        st.write(prompt2b)

                    st.session_state.message += prompt2b
                    with st.chat_message(
                        "model", avatar="🟦",
                    ):
                        response2b = st.session_state.chat2b.send_message(st.session_state.message)
                        st.markdown(response2b.text)
                        st.sidebar.markdown(str(response2b.usage_metadata))
                    st.session_state.message += response2b.text
            except Exception as e:
                st.error(f"An error occurred: {e}")
            finally:
                # Clean up temporary files
                for temp_file in temp_files:
                    if os.path.exists(temp_file):
                        os.remove(temp_file)
                if os.path.exists(fullfile):
                    os.remove(fullfile)

    elif choice == "Chat with an image":
        st.subheader("Chat with an Image")
        clear = get_clear()
        if clear:
            if 'message' in st.session_state:
                del st.session_state['message']

        if 'message' not in st.session_state:
            st.session_state.message = " "

        uploaded_files2 = st.file_uploader("Choose your PNG or JPEG file", type=['png', 'jpg', 'jpeg'],
                                            accept_multiple_files=False)
        if uploaded_files2:
            try:
                with st.spinner("Uploading and processing image..."):
                    # Save uploaded file to temporary location
                    with open("temp_image", "wb") as f:
                        f.write(uploaded_files2.read())
                    mime_type = "image/png" if uploaded_files2.name.endswith(".png") else "image/jpeg" # Detect image type
                    file_upload = client.upload_file(file="temp_image", mime_type=mime_type)

                if 'chat3' not in st.session_state or clear:
                    st.session_state.chat3 = client.chats.create(model=MODEL_ID,
                        history=[
                            types.Content(
                                role="user",
                                parts=[

                                        types.Part.from_uri(
                                            file_uri=file_upload.uri,
                                            mime_type=mime_type),
                                        ]
                                ),
                            ]
                            )

                prompt3 = st.chat_input("Enter your question here")
                if prompt3:
                    with st.chat_message("user"):
                        st.write(prompt3)

                    st.session_state.message += prompt3
                    with st.chat_message(
                        "model", avatar="🟦",
                    ):
                        response3 = st.session_state.chat3.send_message(st.session_state.message)
                        st.markdown(response3.text)
                    st.session_state.message += response3.text
            except Exception as e:
                st.error(f"An error occurred: {e}")
            finally:
                 if os.path.exists("temp_image"):
                    os.remove("temp_image")

    elif choice == "Chat with audio":
        st.subheader("Chat with your audio file")
        clear = get_clear()
        if clear:
            if 'message' in st.session_state:
                del st.session_state['message']

        if 'message' not in st.session_state:
            st.session_state.message = " "

        uploaded_files3 = st.file_uploader("Choose your mp3 or wav file", type=['mp3', 'wav'],
                                            accept_multiple_files=False)
        if uploaded_files3:
            try:
                with st.spinner("Uploading and processing audio..."):
                    with open("temp_audio", "wb") as f:
                        f.write(uploaded_files3.read())

                    mime_type = "audio/mpeg" if uploaded_files3.name.endswith(".mp3") else "audio/wav" # Detect audio type
                    file_upload = client.upload_file(file="temp_audio", mime_type=mime_type)


                if 'chat4' not in st.session_state or clear:
                    st.session_state.chat4 = client.chats.create(model=MODEL_ID,
                        history=[
                            types.Content(
                                role="user",
                                parts=[

                                        types.Part.from_uri(
                                            file_uri=file_upload.uri,
                                            mime_type=mime_type),
                                        ]
                                ),
                            ]
                            )

                prompt5 = st.chat_input("Enter your question here")
                if prompt5:
                    with st.chat_message("user"):
                        st.write(prompt5)

                    st.session_state.message += prompt5
                    with st.chat_message(
                        "model", avatar="🟦",
                    ):
                        response4 = st.session_state.chat4.send_message(st.session_state.message)
                        st.markdown(response4.text)
                    st.session_state.message += response4.text
            except Exception as e:
                st.error(f"An error occurred: {e}")
            finally:
                if os.path.exists("temp_audio"):
                    os.remove("temp_audio")

    elif choice == "Chat with video":
        st.subheader("Chat with your video file")
        clear = get_clear()
        if clear:
            if 'message' in st.session_state:
                del st.session_state['message']

        if 'message' not in st.session_state:
            st.session_state.message = " "

        uploaded_files4 = st.file_uploader("Choose your mp4 or mov file", type=['mp4', 'mov'],
                                            accept_multiple_files=False)

        if uploaded_files4:
            try:
                with st.spinner("Uploading and processing video..."):
                    with open("temp_video", "wb") as f:
                        f.write(uploaded_files4.read())
                    mime_type = "video/mp4" if uploaded_files4.name.endswith(".mp4") else "video/quicktime"  # Assuming mov is quicktime

                    video_file = client.upload_file(file="temp_video", mime_type=mime_type)

                    while video_file.state == "PROCESSING":
                        time.sleep(10)
                        video_file = client.files.get(name=video_file.name)

                    if video_file.state == "FAILED":
                        raise ValueError(video_file.state)

                if 'chat5' not in st.session_state or clear:
                    st.session_state.chat5 = client.chats.create(model=MODEL_ID,
                        history=[
                            types.Content(
                                role="user",
                                parts=[

                                        types.Part.from_uri(
                                            file_uri=video_file.uri,
                                            mime_type=mime_type),
                                        ]
                                ),
                            ]
                            )

                prompt4 = st.chat_input("Enter your question here")
                if prompt4:
                    with st.chat_message("user"):
                        st.write(prompt4)

                    st.session_state.message += prompt4
                    with st.chat_message(
                        "model", avatar="🟦",
                    ):
                        response5 = st.session_state.chat5.send_message(st.session_state.message)
                        st.markdown(response5.text)
                    st.session_state.message += response5.text
            except Exception as e:
                st.error(f"An error occurred: {e}")
            finally:
                if os.path.exists("temp_video"):
                    os.remove("temp_video")


if __name__ == '__main__':
    setup_page()
    GOOGLE_API_KEY = os.environ.get('GOOGLE_API_KEY')
    if not GOOGLE_API_KEY:
        st.error("Please set the GOOGLE_API_KEY environment variable.")
    else:
        client = genai.Client(api_key=GOOGLE_API_KEY)
        MODEL_ID = "gemini-2.0-flash"
        main()
