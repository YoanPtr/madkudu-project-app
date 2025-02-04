import streamlit as st
import json
import os
from dotenv import load_dotenv
from website_scraping import WebsiteScraper
from linkedin_analyzer import LinkedInAnalyzer
from website_summarizer import WebsiteSummarizer
from urllib.parse import urlparse
from get_websites_links import get_company_website
import time

MISTRAL_API_KEY = st.secrets["MISTRAL_API_KEY"]
GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
CX = st.secrets["GOOGLE_CSE_ID"]

# Configure Streamlit page
st.set_page_config(
    page_title="Company Intelligence Bot",
    page_icon="🔍",
    layout="wide"
)

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
    # Add the initial welcome message
    st.session_state.messages.append({
        "role": "assistant",
        "content": """👋 Welcome! I can help you analyze companies, just type a company name (e.g., "Madkudu")
        
I'll analyze the company and provide insights about:
- Company overview and description
- Products and services
- Target market and customer segments
- Sales approach and go-to-market strategy
- Company size and location
- And more!

What company would you like to analyze?"""
    })



def get_companies_websites(user_input):
    print(f"Searching for {user_input}'s online presence...")
    with st.status(f"🔍 Searching for {user_input}'s online presence...") as status:
        info = get_company_website(user_input, MISTRAL_API_KEY, GOOGLE_API_KEY, CX)
        print(f"Company info retrieved: {info}")

    if info.get('website') or info.get('linkedin'):
        print(f"Found sources for company: {user_input}")
        message = "I found the following sources:"
        if info.get('website'):
            message += f" <br> &nbsp;&nbsp;&nbsp;&nbsp;🌐 Website: {info['website']}"
            st.session_state.results['website_url'] = info['website']
        if info.get('linkedin'):
            message += f" <br> &nbsp;&nbsp;&nbsp;&nbsp;💼 LinkedIn: {info['linkedin']}"
            st.session_state.results['linkedin_url'] = info['linkedin']
        with st.chat_message("assistant"):
            st.markdown(message, unsafe_allow_html=True)
            st.session_state.messages.append({"role": "assistant", "content": message})
            st.button("Yes, analyze these sources", on_click=analyse_links)
        
    else:
        print(f"No sources found for company: {user_input}")
        st.warning("No website or LinkedIn profile found for this company.")
        return None
        
def analyze_input(user_input: str) -> dict:
    """Analyze user input and return appropriate response"""
    print(f"Analyzing input: {user_input}")

    # Treat as company name
    return get_companies_websites(user_input)

    
def set_state(i):
    st.session_state.stage = i

def analyse_links(): 
    st.session_state.stage = 1
    with st.chat_message("user"):
        message = "Yes, analyze these sources"
        st.markdown(message)
        st.session_state.messages.append({"role": "user", "content": message})
    
    

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"], unsafe_allow_html=True)

if 'stage' not in st.session_state:
    st.session_state.stage = 0
    
if 'results' not in st.session_state :
    st.session_state.results = {}

if st.session_state.stage == 0:
    prompt = st.chat_input("Enter a company name, LinkedIn URL, or website URL")
    if prompt:
        print(f"Received user input: {prompt}")
        # Display user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Generate and display assistant response
        analyze_input(prompt)

if st.session_state.stage == 1:
    print("Starting detailed analysis of sources")
    if st.session_state.results.get('website_url'):
        print(f"Analyzing website: {st.session_state.results['website_url']}")
        with st.status(f"📊 Analyzing website: {st.session_state.results['website_url']}"):
            analyzer = WebsiteScraper(MISTRAL_API_KEY)
            analyzer.crawl_website(st.session_state.results['website_url'], depth=1, max_links_per_depth=1)
            st.session_state.results["website_analyse_quick"] = analyzer.get_results()
    
    if st.session_state.results.get('linkedin_url'):
        print(f"Analyzing LinkedIn: {st.session_state.results['linkedin_url']}")
        with st.status(f"💼 Analyzing LinkedIn: {st.session_state.results['linkedin_url']}"):
            linkedin_analyzer = LinkedInAnalyzer(api_key=MISTRAL_API_KEY)
            result = linkedin_analyzer.scrape_and_analyze(st.session_state.results['linkedin_url'])
            st.session_state.results["linkedin"] = result
    
    print("Creating analysis summary")
    with st.status("🤖 Creating analysis summary..."):
        summary = WebsiteSummarizer(st.session_state.results["website_analyse_quick"], st.session_state.results["linkedin"],MISTRAL_API_KEY).summarize_analysis()
        st.session_state.results["summary_quick"] = summary

    # Format the summary with section titles and emojis
    formatted_summary = f"""
🏢 Company Overview <br>
{summary['company_overview_summary']}

📊 Sales Intelligence <br>
{summary['sales_intelligence_summary']}

💰 Pricing Information <br>
{summary['pricing_summary']}

📈 Firmographic Data <br>
{summary['firmographic_summary']}

🎯 Go-to-Market Strategy <br>
{summary['gtm_strategy_summary']}

📝 Overall Summary <br>
{summary['overall_summary']}
"""

    with st.chat_message("assistant"):
        st.markdown(formatted_summary, unsafe_allow_html=True)
        
    # Save the summary to chat history
    st.session_state.messages.append({"role": "assistant", "content": formatted_summary})
    
    st.session_state.stage = 2
    
if st.session_state.stage == 2:
    # Add download buttons for each analysis type
    st.markdown("📥 Download Analysis Results")
    col1, col2, col3, col4,col5 = st.columns(5)
    
    # Add reset button
    if st.button("🔄 Start New Analysis", type="primary"):
        st.session_state.stage = 0
        st.session_state.results = {}
        st.rerun()
    
    with col1:
        if st.session_state.results.get('website_analyse_quick'):
            if st.download_button(
                label="📊 Website Analysis",
                data=json.dumps(st.session_state.results["website_analyse_quick"], indent=2),
                file_name="website_analysis.json",
                mime="application/json"
            ):
                print("Website analysis downloaded")
    
    with col2:
        if st.session_state.results.get('linkedin'):
            if st.download_button(
                label="💼 LinkedIn Analysis",
                data=json.dumps(st.session_state.results["linkedin"], indent=2),
                file_name="linkedin_analysis.json",
                mime="application/json"
            ):
                print("LinkedIn analysis downloaded")
    
    with col3:
        if st.session_state.results.get('summary_quick'):
            if st.download_button(
                label="📝 Summary",
                data=json.dumps(st.session_state.results["summary_quick"], indent=2),
                file_name="company_summary.json",
                mime="application/json"
            ):
                print("Summary downloaded")
    with col4:
        if st.session_state.results.get('website_analyse_deep'):
            if st.download_button(
                label="📊 Deep Website Analysis",
                data=json.dumps(st.session_state.results["website_analyse_deep"], indent=2),
                file_name="website_analysis.json",
                mime="application/json"
            ):
                print("Deep website analysis downloaded")
        elif st.session_state.results.get('website_analyse_quick'):
            if st.button("📊 Create Deep Website Analysis"):
                st.session_state.stage = 3
    with col5:
        if st.session_state.results.get('summary_deep'):
            if st.download_button(
                label="📝 Summary Deep",
                data=json.dumps(st.session_state.results["summary_deep"], indent=2),
                file_name="company_summary.json",
                mime="application/json"
            ):
                print("Summary downloaded")
                
    print("Analysis completed successfully")

if st.session_state.stage == 3:
    with st.chat_message("user"):
        message = "Create deep website analysis"
        st.markdown(message)
        st.session_state.messages.append({"role": "user", "content": message})
    
    print("Starting deep analysis of website")
    if st.session_state.results.get('website_url'):
        print(f"Deep Analyzing website: {st.session_state.results['website_url']}")
        with st.status(f"📊 Analyzing website: {st.session_state.results['website_url']}"):
            analyzer = WebsiteScraper(MISTRAL_API_KEY)
            analyzer.crawl_website(st.session_state.results['website_url'], depth=3, max_links_per_depth=5)
            st.session_state.results["website_analyse_deep"] = analyzer.get_results()
        
        with st.status("🤖 Creating analysis summary..."):
            summary = WebsiteSummarizer(st.session_state.results["website_analyse_deep"], st.session_state.results["linkedin"], MISTRAL_API_KEY).summarize_analysis()
            st.session_state.results["summary_deep"] = summary 
            # Format the summary with section titles and emojis
        formatted_summary = f"""
🏢 Company Overview <br>
{summary['company_overview_summary']}

📊 Sales Intelligence <br>
{summary['sales_intelligence_summary']}

💰 Pricing Information <br>
{summary['pricing_summary']}

📈 Firmographic Data <br>
{summary['firmographic_summary']}

🎯 Go-to-Market Strategy <br>
{summary['gtm_strategy_summary']}

📝 Overall Summary <br>
{summary['overall_summary']}
"""

        with st.chat_message("assistant"):
            st.markdown(formatted_summary, unsafe_allow_html=True)
            
        # Save the summary to chat history
        st.session_state.messages.append({"role": "assistant", "content": formatted_summary})
        
        st.session_state.stage = 2
        st.rerun()
