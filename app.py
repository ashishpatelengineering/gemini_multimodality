import os
import time
import tempfile
import streamlit as st
import google.generativeai as genai
from pypdf import PdfReader
import fitz
import PIL.Image
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def setup_page():
    """Set up the Streamlit page with a header and custom styles."""
    st.header("AI-Powered File & Media Interaction", anchor=False, divider="blue")

    # # Hide the Streamlit menu
    # hide_menu_style = """
    #     <style>
    #     #MainMenu {visibility: hidden;}
    #     </style>
    #     """
    # st.markdown(hide_menu_style, unsafe_allow_html=True)

def get_media_type():
    """Display a sidebar radio button to select the type of media."""
    st.sidebar.header("Select Type of Media", divider='orange')
    media_type = st.sidebar.radio(
        "Choose one:",
        ("PDF", "Image", "Video (mp4)", "Audio (mp3)")
    )
    return media_type


def get_llm_settings():
    """Display sidebar options for configuring the LLM."""
    st.sidebar.header("LLM Configuration", divider='rainbow')

    # model_tip = "Select the model you want to use."
    # model = st.sidebar.radio(
    #     "Choose LLM:",
    #     ("gemini-1.5-flash", "gemini-1.5-pro"),
    #     help=model_tip
    # )
    
    model = "gemini-1.5-flash"

    temp_tip = (
        '''
        Lower temperatures are suitable for prompts requiring less creativity, 
        while higher temperatures can lead to more diverse and creative results. 
        At a temperature of 0, the model always selects the most likely words.
        '''
    )
    temperature = st.sidebar.slider(
        "Temperature:", min_value=0.0, max_value=2.0, value=1.0, step=0.25, help=temp_tip
    )

    top_p_tip = (
        "Used for nucleus sampling. Lower values result in less random responses, "
        "while higher values result in more random responses."
    )
    top_p = st.sidebar.slider(
        "Top P:", min_value=0.0, max_value=1.0, value=0.94, step=0.01, help=top_p_tip
    )

    max_tokens_tip = "Number of response tokens. The limit is 8194."
    max_tokens = st.sidebar.slider(
        "Maximum Tokens:", min_value=100, max_value=5000, value=2000, step=100, help=max_tokens_tip
    )

    return model, temperature, top_p, max_tokens


def extract_images_from_pdf(pdf_file):
    """Extract images from a PDF file and save them as temporary files."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
        tmp_file.write(pdf_file.read())
        tmp_file_path = tmp_file.name

    doc = fitz.open(tmp_file_path)
    images = []
    for page in doc:
        pix = page.get_pixmap(
            matrix=fitz.Identity, dpi=None, colorspace=fitz.csRGB, clip=None, alpha=False, annots=True
        )
        img_path = f"pdfimage-{page.number}.jpg"
        pix.save(img_path)
        images.append(img_path)
    return images


def main():
    """Main function to run the Streamlit app."""
    setup_page()
    media_type = get_media_type()
    model, temperature, top_p, max_tokens = get_llm_settings()

    if media_type == "PDF":
        uploaded_files = st.file_uploader("Upload PDF file", type="pdf", accept_multiple_files=True)

        if uploaded_files:
            text = ""
            for pdf in uploaded_files:
                pdf_reader = PdfReader(pdf)
                for page in pdf_reader.pages:
                    text += page.extract_text()

            generation_config = {
                "temperature": temperature,
                "top_p": top_p,
                "max_output_tokens": max_tokens,
                "response_mime_type": "text/plain",
            }
            model = genai.GenerativeModel(
                model_name=model,
                generation_config=generation_config,
            )
            # st.write(model.count_tokens(text))
            question = st.text_input("Enter your question and hit return.")
            if question:
                response = model.generate_content([question, text])
                st.write(response.text)

    elif media_type == "Image":
        image_file = st.file_uploader("Upload an image file", type=["jpg", "jpeg", "png"])
        if image_file:
            image = PIL.Image.open(image_file)
            st.image(image, caption="Uploaded Image", use_container_width=True)

            prompt = st.text_input("Enter your prompt.")
            if prompt:
                generation_config = {
                    "temperature": temperature,
                    "top_p": top_p,
                    "max_output_tokens": max_tokens,
                }
                model = genai.GenerativeModel(model_name=model, generation_config=generation_config)
                response = model.generate_content([image, prompt], request_options={"timeout": 600})
                st.markdown(response.text)

    elif media_type == "Video (mp4)":
        video_file = st.file_uploader("Upload a video file", type=["mp4"])
        if video_file:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp_file:
                tmp_file.write(video_file.read())
                tmp_file_path = tmp_file.name

            st.video(tmp_file_path, format="video/mp4", start_time=0)

            video_file = genai.upload_file(path=tmp_file_path)

            while video_file.state.name == "PROCESSING":
                time.sleep(10)
                video_file = genai.get_file(video_file.name)
            if video_file.state.name == "FAILED":
                raise ValueError(video_file.state.name)

            prompt = st.text_input("Enter your prompt.")
            if prompt:
                model = genai.GenerativeModel(model_name=model)
                response = model.generate_content([video_file, prompt], request_options={"timeout": 600})
                st.markdown(response.text)

                genai.delete_file(video_file.name)
                print(f"Deleted file {video_file.uri}")

    elif media_type == "Audio (mp3)":
        audio_file = st.file_uploader("Upload an audio file", type=["mp3", "wav"])
        if audio_file:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp_file:
                tmp_file.write(audio_file.read())
                tmp_file_path = tmp_file.name

            st.audio(tmp_file_path, format="audio/mp3", start_time=0)

            audio_file = genai.upload_file(path=tmp_file_path)

            while audio_file.state.name == "PROCESSING":
                time.sleep(10)
                audio_file = genai.get_file(audio_file.name)
            if audio_file.state.name == "FAILED":
                raise ValueError(audio_file.state.name)

            prompt = st.text_input("Enter your prompt.")
            if prompt:
                model = genai.GenerativeModel(model_name=model)
                response = model.generate_content([audio_file, prompt], request_options={"timeout": 600})
                st.markdown(response.text)

                genai.delete_file(audio_file.name)
                print(f"Deleted file {audio_file.uri}")


if __name__ == "__main__":
    GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY_NEW")
    genai.configure(api_key=GOOGLE_API_KEY)
    main()
