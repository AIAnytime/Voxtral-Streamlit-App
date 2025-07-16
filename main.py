import os
import streamlit as st
import requests
import json
import pandas as pd
import numpy as np
import time
import plotly.graph_objects as go
import plotly.express as px
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()


st.set_page_config(
    page_title="RepRadar - AI-Powered Sales Call Intelligence",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)


# Initialize session state variables
if 'uploaded_audio' not in st.session_state:
    st.session_state.uploaded_audio = None

if 'audio_url' not in st.session_state:
    st.session_state.audio_url = ""

if 'transcript' not in st.session_state:
    st.session_state.transcript = ""

if 'segments' not in st.session_state:
    st.session_state.segments = []

if 'call_stages' not in st.session_state:
    st.session_state.call_stages = {}

if 'objections' not in st.session_state:
    st.session_state.objections = ""

if 'competitor_mentions' not in st.session_state:
    st.session_state.competitor_mentions = ""

if 'rep_scores' not in st.session_state:
    st.session_state.rep_scores = {}

if 'coaching_tips' not in st.session_state:
    st.session_state.coaching_tips = ""

if 'processing' not in st.session_state:
    st.session_state.processing = False

if 'api_key' not in st.session_state:
    st.session_state.api_key = ""

# Load Mistral API key from .env file as fallback
DEFAULT_MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")


st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1E3A8A;
        margin-bottom: 1rem;
        width: 100%;
        text-align: left;
    }
    .app-description {
        margin-bottom: 20px;
    }
    .sub-header {
        font-size: 1.5rem;
        color: #2563EB;
        margin-bottom: 1rem;
        width: 100%;
    }
    .info-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #EFF6FF;
        border-left: 5px solid #3B82F6;
        margin-bottom: 1rem;
    }
    .success-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #ECFDF5;
        border-left: 5px solid #10B981;
        margin-bottom: 1rem;
    }
    .warning-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #FEF3C7;
        border-left: 5px solid #F59E0B;
        margin-bottom: 1rem;
    }
    /* Improved tab styling with more spacing */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        flex-wrap: wrap;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: #F3F4F6;
        border-radius: 4px 4px 0px 0px;
        padding: 10px 15px;
        margin-right: 5px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #DBEAFE;
        color: #1E3A8A;
    }
    div[data-testid="stSidebarNav"] li div a {
        margin-left: 1rem;
        padding: 1rem;
        width: 300px;
        border-radius: 0.5rem;
    }
    div[data-testid="stSidebarNav"] li div::focus-visible {
        background-color: rgba(151, 166, 195, 0.15);
    }
    /* Make all containers full width */
    .block-container {
        max-width: 100% !important;
        padding: 1rem 1rem !important;
    }
    /* Header container full width */
    header[data-testid="stHeader"] {
        width: 100%;
    }
</style>
""", unsafe_allow_html=True)



def transcribe_audio(audio_url=None, audio_file=None):
    """Transcribe audio using Mistral API with timestamps"""
    try:
        # Get API key from session state or use default
        api_key = st.session_state.api_key if st.session_state.api_key else DEFAULT_MISTRAL_API_KEY
        
        if not api_key:
            return None, "API key is required. Please provide a Mistral API key in the API Configuration section."
        
        url = "https://api.mistral.ai/v1/audio/transcriptions"
        headers = {"x-api-key": api_key}
        
        if audio_url:
            data = {
                'file_url': audio_url,
                'model': "voxtral-mini-2507",
                'timestamp_granularities': "segment"
            }
            response = requests.post(url, headers=headers, data=data)
        elif audio_file:
            files = {
                'file': audio_file,
                'model': (None, "voxtral-mini-2507"),
                'timestamp_granularities': (None, "segment")
            }
            response = requests.post(url, headers=headers, files=files)
        else:
            return None, "No audio provided"
        
        if response.status_code == 200:
            result = response.json()
            return result, None
        else:
            return None, f"API Error: {response.status_code} - {response.text}"
    except Exception as e:
        return None, f"Exception: {str(e)}"

def chat_with_audio(audio_url=None, audio_file=None, prompt=""):
    """Chat with audio using Mistral API"""
    try:
        api_key = st.session_state.api_key if st.session_state.api_key else DEFAULT_MISTRAL_API_KEY
        
        if not api_key:
            return None, "API key is required. Please provide a Mistral API key in the API Configuration section."
            
        url = "https://api.mistral.ai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        # Prepare the message content
        message_content = []
        
        # Add audio content
        if audio_url:
            message_content.append({
                "type": "input_audio",
                "input_audio": {
                    "data": audio_url,
                    "format": "mp3"  
                }
            })
        
        
        message_content.append({
            "type": "text",
            "text": prompt
        })
        
        data = {
            "model": "voxtral-mini-2507",
            "messages": [
                {
                    "role": "user",
                    "content": message_content
                }
            ]
        }
        
        response = requests.post(url, headers=headers, json=data)
        
        if response.status_code == 200:
            result = response.json()
            return result["choices"][0]["message"]["content"], None
        else:
            return None, f"API Error: {response.status_code} - {response.text}"
    except Exception as e:
        return None, f"Exception: {str(e)}"

def segment_call(segments):
    """Segment the call into different stages based on transcript segments"""
    call_stages = {
        "intro": [],
        "discovery": [],
        "demo": [],
        "objections": [],
        "closing": []
    }
    
    total_segments = len(segments)
    
    if total_segments > 0:
        intro_end = max(1, int(total_segments * 0.15))
        discovery_end = max(2, int(total_segments * 0.4))
        demo_end = max(3, int(total_segments * 0.65))
        objections_end = max(4, int(total_segments * 0.85))
        
        call_stages["intro"] = segments[:intro_end]
        call_stages["discovery"] = segments[intro_end:discovery_end]
        call_stages["demo"] = segments[discovery_end:demo_end]
        call_stages["objections"] = segments[demo_end:objections_end]
        call_stages["closing"] = segments[objections_end:]
    
    return call_stages

def calculate_talk_ratio(segments):
    """Calculate talk-to-listen ratio from transcript segments"""
    rep_duration = 0
    customer_duration = 0
    
    for i, segment in enumerate(segments):
        duration = segment.get("end", 0) - segment.get("start", 0)
        if i % 2 == 0:
            rep_duration += duration
        else:
            customer_duration += duration
    
    if customer_duration == 0:
        customer_duration = 1 
    
    return rep_duration / customer_duration

def extract_call_metrics(transcript, segments):
    """Extract basic metrics from the call transcript"""
    word_count = len(transcript.split())
    
    duration = segments[-1]["end"] if segments else 0
    
    talk_ratio = calculate_talk_ratio(segments)
    
    filler_words = ["um", "uh", "like", "you know", "actually", "basically"]
    filler_count = sum(transcript.lower().count(word) for word in filler_words)
    
    metrics = {
        "word_count": word_count,
        "duration": duration,
        "talk_ratio": talk_ratio,
        "filler_words": filler_count,
        "filler_frequency": filler_count / (word_count if word_count > 0 else 1)
    }
    
    return metrics

def analyze_call(transcript, segments):
    """Generate comprehensive call analysis using Chat with Audio API"""
    objections_prompt = "Analyze this sales call transcript and list the top 3 customer objections. Format as bullet points."
    competitor_prompt = "Identify any competitor names or products mentioned in this call. Format as a bulleted list."
    rep_scoring_prompt = "Evaluate the salesperson on structure, clarity, confidence, and closing technique. Give a score out of 10 for each criterion and brief explanation."
    coaching_prompt = "Provide 3 specific coaching tips to improve this sales call. Focus on handling objections better, clearer messaging, and effective closing."
    
    text_transcript = transcript
    
    objections_response, error = chat_with_audio(prompt=objections_prompt + "\n\n" + text_transcript)
    objections = objections_response if not error else "Error analyzing objections"
    
    competitor_response, error = chat_with_audio(prompt=competitor_prompt + "\n\n" + text_transcript)
    competitors = competitor_response if not error else "Error analyzing competitor mentions"
    
    scoring_response, error = chat_with_audio(prompt=rep_scoring_prompt + "\n\n" + text_transcript)
    scoring = scoring_response if not error else "Error analyzing rep performance"
    
    coaching_response, error = chat_with_audio(prompt=coaching_prompt + "\n\n" + text_transcript)
    coaching = coaching_response if not error else "Error generating coaching tips"
    
    scores = {}
    try:
        if "structure:" in scoring.lower():
            structure_score = int(scoring.lower().split("structure:")[1].split("/")[0].strip())
            scores["structure"] = structure_score
        if "clarity:" in scoring.lower():
            clarity_score = int(scoring.lower().split("clarity:")[1].split("/")[0].strip())
            scores["clarity"] = clarity_score
        if "confidence:" in scoring.lower():
            confidence_score = int(scoring.lower().split("confidence:")[1].split("/")[0].strip())
            scores["confidence"] = confidence_score
        if "closing:" in scoring.lower():
            closing_score = int(scoring.lower().split("closing:")[1].split("/")[0].strip())
            scores["closing"] = closing_score
    except:
        scores = {
            "structure": 7,
            "clarity": 6,
            "confidence": 8,
            "closing": 5
        }
    
    return {
        "objections": objections,
        "competitors": competitors,
        "scoring": scoring,
        "scores": scores,
        "coaching": coaching
    }

def render_header():
    """Render the app header"""
    st.markdown("<h1 class='main-header'>RepRadar</h1>", unsafe_allow_html=True)
    st.markdown("<p><strong>AI-Powered Sales Call Intelligence</strong></p>", unsafe_allow_html=True)
    
    # Add app description in an expander
    with st.expander("About RepRadar"):
        st.markdown("""<div class='app-description'>
            <p><strong>RepRadar</strong> is an AI-powered sales call analysis tool built with Mistral's Voxtral model. 
            It helps sales teams improve their performance by:</p>
            <ul>
                <li>Transcribing and analyzing sales call recordings</li>
                <li>Identifying customer objections and competitive mentions</li>
                <li>Providing insights on rep performance with metrics like talk-to-listen ratio</li>
                <li>Generating actionable coaching recommendations to improve sales techniques</li>
            </ul>
            <p>This application leverages Mistral's new Voxtral model to process audio directly and generate 
            intelligent insights about sales conversations.</p>
        </div>""", unsafe_allow_html=True)
    
    # API Key Configuration
    with st.expander("API Configuration"):
        st.markdown("<p>Enter your <a href='https://console.mistral.ai/' target='_blank'>Mistral AI API key</a> below to use the app.</p>", unsafe_allow_html=True)
        api_key = st.text_input("Mistral API Key", type="password", placeholder="Enter your API key here", value=st.session_state.api_key)
        
        if api_key:
            st.session_state.api_key = api_key
            st.success("API key saved! You can now analyze sales calls.")
        elif DEFAULT_MISTRAL_API_KEY:
            st.info("Using default API key from environment. You can provide your own API key above.")
        else:
            st.warning("No API key provided. Please enter a Mistral API key to use the app.")

def render_audio_upload():
    """Render the audio upload section"""
    st.markdown("<h2 class='sub-header'>Upload Sales Call Recording</h2>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("<div class='info-box'><strong>Upload Audio File</strong></div>", unsafe_allow_html=True)
        uploaded_file = st.file_uploader("Choose an audio file", type=["mp3", "wav"], label_visibility="collapsed")
        if uploaded_file:
            st.session_state.uploaded_audio = uploaded_file
            st.audio(uploaded_file, format='audio/mp3')
    
    with col2:
        st.markdown("<div class='info-box'><strong>Or Provide Audio URL</strong></div>", unsafe_allow_html=True)
        audio_url = st.text_input("Enter URL to MP3 audio", placeholder="https://example.com/sales-call.mp3", label_visibility="collapsed")
        if audio_url:
            st.session_state.audio_url = audio_url
            st.markdown(f"Audio URL: {audio_url}")
            
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("Analyze Call", use_container_width=True):
            if st.session_state.uploaded_audio or st.session_state.audio_url:
                st.session_state.processing = True
                process_audio()
                st.session_state.processing = False
            else:
                st.error("Please upload an audio file or provide an audio URL")

def process_audio():
    """Process the uploaded audio file or URL"""
    with st.spinner("Processing audio... This may take a minute."):
        # Transcribe audio  
        if st.session_state.uploaded_audio:
            result, error = transcribe_audio(audio_file=st.session_state.uploaded_audio)
        elif st.session_state.audio_url:
            result, error = transcribe_audio(audio_url=st.session_state.audio_url)
        else:
            st.error("No audio provided")
            return
        
        if error:
            st.error(f"Error: {error}")
            return
        
        # Store transcript and segments
        st.session_state.transcript = result.get("text", "")
        st.session_state.segments = result.get("segments", [])
        
        # Segment the call
        st.session_state.call_stages = segment_call(st.session_state.segments)
        
        # Analyze the call
        with st.spinner("Analyzing call content..."):
            analysis_results = analyze_call(st.session_state.transcript, st.session_state.segments)
            st.session_state.objections = analysis_results["objections"]
            st.session_state.competitor_mentions = analysis_results["competitors"]
            st.session_state.rep_scores = analysis_results["scores"]
            st.session_state.coaching_tips = analysis_results["coaching"]
        
        # Set active tab to results
        st.session_state.active_tab = 1
        st.rerun()

def render_results_tabs():
    """Render the results in tabs"""
    if not st.session_state.transcript:
        return
    
    st.markdown("<h2 class='sub-header'>Call Analysis Results</h2>", unsafe_allow_html=True)
    
    tabs = st.tabs(["Transcript", "Overview", "Objections", "Rep Performance", "Coaching"])
    
    with tabs[0]:
        render_transcript_tab()
    
    with tabs[1]:
        render_overview_tab()
    
    with tabs[2]:
        render_objections_tab()
    
    with tabs[3]:
        render_performance_tab()
    
    with tabs[4]:
        render_coaching_tab()

def render_transcript_tab():
    """Render the transcript tab"""
    st.markdown("### Call Transcript with Timestamps")
    
    if st.session_state.segments:
        # Create a DataFrame for the transcript segments
        segments_data = []
        for segment in st.session_state.segments:
            segments_data.append({
                "Start": f"{segment['start']:.1f}s",
                "End": f"{segment['end']:.1f}s",
                "Duration": f"{segment['end'] - segment['start']:.1f}s",
                "Text": segment["text"]
            })
        
        # Display as a DataFrame
        df = pd.DataFrame(segments_data)
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        # Call segmentation
        st.markdown("### Call Segmentation")
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.markdown("**Intro**")
            intro_text = " ".join([s["text"] for s in st.session_state.call_stages.get("intro", [])])
            st.markdown(f"<div style='height:150px;overflow-y:auto;font-size:0.9em;'>{intro_text}</div>", unsafe_allow_html=True)
        
        with col2:
            st.markdown("**Discovery**")
            discovery_text = " ".join([s["text"] for s in st.session_state.call_stages.get("discovery", [])])
            st.markdown(f"<div style='height:150px;overflow-y:auto;font-size:0.9em;'>{discovery_text}</div>", unsafe_allow_html=True)
        
        with col3:
            st.markdown("**Demo**")
            demo_text = " ".join([s["text"] for s in st.session_state.call_stages.get("demo", [])])
            st.markdown(f"<div style='height:150px;overflow-y:auto;font-size:0.9em;'>{demo_text}</div>", unsafe_allow_html=True)
        
        with col4:
            st.markdown("**Objections**")
            objections_text = " ".join([s["text"] for s in st.session_state.call_stages.get("objections", [])])
            st.markdown(f"<div style='height:150px;overflow-y:auto;font-size:0.9em;'>{objections_text}</div>", unsafe_allow_html=True)
        
        with col5:
            st.markdown("**Closing**")
            closing_text = " ".join([s["text"] for s in st.session_state.call_stages.get("closing", [])])
            st.markdown(f"<div style='height:150px;overflow-y:auto;font-size:0.9em;'>{closing_text}</div>", unsafe_allow_html=True)
    else:
        st.warning("No transcript segments available")

def render_overview_tab():
    """Render the overview tab"""
    st.markdown("### Call Overview")
    
    if st.session_state.transcript and st.session_state.segments:
        # Extract metrics
        metrics = extract_call_metrics(st.session_state.transcript, st.session_state.segments)
        
        # Display metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Call Duration", f"{metrics['duration']:.1f}s")
        
        with col2:
            st.metric("Word Count", metrics["word_count"])
        
        with col3:
            talk_ratio = metrics["talk_ratio"]
            talk_ratio_formatted = f"{talk_ratio:.1f}:1"
            st.metric("Talk Ratio (Rep:Customer)", talk_ratio_formatted)
        
        with col4:
            st.metric("Filler Words", metrics["filler_words"])
        
        # Create a timeline visualization
        st.markdown("### Call Timeline")
        
        if st.session_state.segments:
            # Create a DataFrame for the timeline
            timeline_data = []
            for i, segment in enumerate(st.session_state.segments):
                # Simple alternating speaker assignment - odd segments are rep, even are customer
                speaker = "Rep" if i % 2 == 0 else "Customer"
                
                # Determine segment type based on call stages
                segment_type = "Unknown"
                for stage_name, stage_segments in st.session_state.call_stages.items():
                    if segment in stage_segments:
                        segment_type = stage_name.capitalize()
                        break
                
                timeline_data.append({
                    "Start": segment["start"],
                    "End": segment["end"],
                    "Speaker": speaker,
                    "Type": segment_type,
                    "Text": segment["text"][:50] + "..." if len(segment["text"]) > 50 else segment["text"]
                })
            
            # Create a Gantt chart
            fig = px.timeline(
                timeline_data,
                x_start="Start",
                x_end="End",
                y="Speaker",
                color="Type",
                hover_data=["Text"],
                title="Call Timeline by Speaker and Stage"
            )
            
            # Update layout
            fig.update_layout(
                xaxis_title="Time (seconds)",
                yaxis_title="Speaker",
                height=300,
                margin=dict(l=10, r=10, t=50, b=30)
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Word cloud or highlight keywords
            st.markdown("### Key Topics & Highlights")
            
            # Display highlights using a simple bulleted list
            keywords = ["price", "cost", "budget", "competitor", "timeline", "deadline", "alternative", "concern", "issue"]
            highlights = []
            
            for segment in st.session_state.segments:
                for keyword in keywords:
                    if keyword in segment["text"].lower():
                        highlights.append(f"• {segment['text']}")
                        break
            
            if highlights:
                st.markdown("\n".join(highlights))
            else:
                st.info("No key highlights detected")
    else:
        st.warning("No call data available")

def render_objections_tab():
    """Render the objections tab"""
    st.markdown("### Customer Objections")
    
    if st.session_state.objections:
        st.markdown("<div class='warning-box'>" + st.session_state.objections + "</div>", unsafe_allow_html=True)
    else:
        st.info("No objections analysis available")
    
    st.markdown("### Competitor Mentions")
    
    if st.session_state.competitor_mentions:
        st.markdown("<div class='info-box'>" + st.session_state.competitor_mentions + "</div>", unsafe_allow_html=True)
    else:
        st.info("No competitor mentions detected")

def render_performance_tab():
    """Render the performance tab"""
    st.markdown("### Rep Performance Scores")
    
    if st.session_state.rep_scores:
        scores = st.session_state.rep_scores
        
        # Create radar chart
        categories = list(scores.keys())
        values = list(scores.values())
        
        # Add the first value at the end to close the loop
        categories.append(categories[0])
        values.append(values[0])
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatterpolar(
            r=values,
            theta=categories,
            fill='toself',
            name='Rep Performance',
            line_color='#3B82F6',
            fillcolor='rgba(59, 130, 246, 0.3)'
        ))
        
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 10]
                )
            ),
            showlegend=False,
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Display scores as metrics
        cols = st.columns(len(scores))
        for i, (metric, score) in enumerate(scores.items()):
            with cols[i]:
                st.metric(metric.capitalize(), f"{score}/10")
        
        # Talk time analysis
        st.markdown("### Talk Time Analysis")
        
        if st.session_state.segments:
            # Calculate talk time distribution
            rep_time = 0
            customer_time = 0
            
            for i, segment in enumerate(st.session_state.segments):
                duration = segment.get("end", 0) - segment.get("start", 0)
                # Simple alternating assignment
                if i % 2 == 0:
                    rep_time += duration
                else:
                    customer_time += duration
            
            total_time = rep_time + customer_time
            
            # Create data for pie chart
            labels = ['Rep', 'Customer']
            values = [rep_time, customer_time]
            
            fig = go.Figure(data=[go.Pie(
                labels=labels,
                values=values,
                hole=.4,
                marker_colors=['#3B82F6', '#10B981']
            )])
            
            fig.update_layout(
                title="Talk Time Distribution",
                annotations=[dict(text=f'{rep_time/total_time:.0%}<br>Rep', x=0.5, y=0.5, font_size=15, showarrow=False)],
                height=300
            )
            
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("No performance metrics available")

def render_coaching_tab():
    """Render the coaching tab"""
    st.markdown("### Coaching Recommendations")
    
    if st.session_state.coaching_tips:
        st.markdown("<div class='success-box'>" + st.session_state.coaching_tips + "</div>", unsafe_allow_html=True)
    else:
        st.info("No coaching recommendations available")
    
    # Add example responses section
    st.markdown("### Suggested Responses to Objections")
    
    # These are pre-defined example responses to common objections
    objection_responses = {
        "Price": "'I understand budget considerations are important. Many of our customers initially had similar concerns until they saw the ROI within the first 90 days. Would it help if I shared a case study showing the exact timeline to value?'",
        "Need more time": "'I completely understand. This is an important decision. What specific information would make you more comfortable moving forward now? I can focus on those areas to help you make a confident decision.'",
        "Need to consult others": "'That makes perfect sense. Who else is typically involved in these decisions? I'd be happy to join a call to address any questions they might have directly.'",
        "Current solution works fine": "'I'm glad to hear your current solution is working. Many of our clients were in a similar position before they realized they were leaving significant [efficiency/revenue/savings] on the table. Could I show you a quick comparison?'"
    }
    
    for objection, response in objection_responses.items():
        st.markdown(f"**Objection: {objection}**")
        st.markdown(f"<div style='padding:10px; background-color:#F3F4F6; border-radius:5px; margin-bottom:10px;'>{response}</div>", unsafe_allow_html=True)

# Main App
def render_footer():
    """Render the app footer with creator information"""
    st.markdown("---")
    st.markdown(
        """
        <div style="text-align: center; padding: 10px; margin-top: 30px; opacity: 0.8;">
            <p>Created by <strong>AI Anytime</strong> | 
            <a href="https://aianytime.net" target="_blank">Website</a> | 
            <a href="https://sonukumar.site" target="_blank">Portfolio</a> | 
            Reach out for collaborations</p>
        </div>
        """, 
        unsafe_allow_html=True
    )

def main():
    """Main function to run the app"""
    # Render the header
    render_header()
    
    # Render the audio upload section
    render_audio_upload()
    
    # Show a separator
    st.markdown("---")
    
    # Render results if available
    render_results_tabs()
    
    # Render footer
    render_footer()

# Run the app
if __name__ == "__main__":
    main()
