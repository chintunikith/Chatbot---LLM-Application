from dotenv import load_dotenv
import os
import requests
import streamlit as st
import google.generativeai as genai
from audio_recorder_streamlit import audio_recorder
from gtts import gTTS
from io import BytesIO


load_dotenv()


genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
model = genai.GenerativeModel("gemini-pro")
chat = model.start_chat(history=[])

def get_gemini_response(question):
    try:
        response = chat.send_message(question, stream=True)
        return response
    except Exception as e:
        st.error(f"Error getting response from Gemini: {e}")
        return []

def speech_to_text(audio_file):
    url = 'https://api.deepgram.com/v1/listen'
    headers = {
        'Authorization': f'Token {os.getenv("DEEPGRAM_API_KEY")}',
        'Content-Type': 'audio/wav'
    }
    try:
        response = requests.post(url, headers=headers, data=audio_file)
        response.raise_for_status()  
        result = response.json()
        
        
        print("Deepgram response:", result)
        
        
        transcript = result.get('results', {}).get('channels', [{}])[0].get('alternatives', [{}])[0].get('transcript', "")
        return transcript
    except requests.exceptions.RequestException as e:
        st.error(f"Error in Deepgram request: {e}")
        return ""
    except Exception as e:
        st.error(f"Error processing Deepgram response: {e}")
        return ""

def text_to_speech(text):
    try:
        tts = gTTS(text, lang='en')
        audio_bytes = BytesIO()
        tts.write_to_fp(audio_bytes)
        audio_bytes.seek(0)
        return audio_bytes
    except Exception as e:
        st.error(f"Error generating speech: {e}")
        return None


st.set_page_config(page_title="Q&A Demo")
st.header("ChatBot - LLM Application")
st.write(f":blue[This application is enabled with both TTS and STT, It may take few seconds for conversion into text and generating response.]")
st.subheader("Step to follow:")
with st.expander("Click to see steps"):
    st.write(f"**Step 1:** Click the :blue[Start and Convert] button to access the mic")
    st.write(f"**Step 2:** Press on the mic symbol and record the question")
    st.write(f"**Step 3:** Press on the mic symbol to stop the recording")
    st.write(f"**Step 4:** Press on :blue[Start and Convert] again to enable STT conversion, it takes a few seconds to convert.")
    st.write(f"**Step 5:** Press on :blue[Generate] to generate the response from LLM, it may take a few seconds")
    st.write(f"**Step 6:** Click on the play button to listen to the response of the bot")


if 'chat_history' not in st.session_state:
    st.session_state['chat_history'] = []
if 'audio_data' not in st.session_state:
    st.session_state['audio_data'] = None
if 'transcript' not in st.session_state:
    st.session_state['transcript'] = None

st.subheader("Record Your Question")

st.session_state['audio_data'] = audio_recorder()  

if st.button("Start & Convert"):
    if st.session_state['audio_data']:
        
        st.session_state['transcript'] = speech_to_text(st.session_state['audio_data'])
        st.write("Question:", st.session_state['transcript'])
    else:
        st.warning("No audio recorded. Please start recording.")


if st.button("Generate"):
    transcript = st.session_state['transcript']
    if transcript:
        response = get_gemini_response(transcript)
        if response:
            
            st.session_state['chat_history'].append(("👤", transcript))
            
            st.subheader("Response:")
            response_text = ""
            for chunk in response:
                response_text += f"{chunk.text}\n"
            
            st.write(f"🤖 :blue[Bot:] {response_text}")

            
            audio_bytes = text_to_speech(response_text)
            if audio_bytes:
                st.audio(audio_bytes, format='audio/mp3')
            
            
            st.session_state['chat_history'].append(("🤖", response_text))
        else:
            st.error("Failed to generate a response from Gemini.")
    else:
        st.warning("No transcript available. Please convert audio first.")


st.subheader("The Chat History is")
user_printed = False
bot_printed = False
for role, text in st.session_state['chat_history']:
    if role == "You 👤" and not user_printed:
        st.write(f"{role}: {text}")
        user_printed = True
    elif role == "Bot 🤖" and not bot_printed:
        st.write(f"{role}: {text}")
        bot_printed = True
    else:
        st.write(f"{role}: {text}")
        user_printed = False
        bot_printed = False
