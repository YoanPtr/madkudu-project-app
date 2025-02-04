# B2B Company Analyzer

This application helps analyze B2B companies by gathering and analyzing information from their websites and LinkedIn profiles. It provides comprehensive insights about company overview, sales intelligence, pricing, firmographic data, and go-to-market strategy.

## Features

- 🔍 Company Search: Find and analyze companies by name
- 🌐 Website Analysis: Deep crawling and analysis of company websites
- 💼 LinkedIn Integration: Analysis of company LinkedIn profiles
- 📊 Comprehensive Reports: Detailed analysis across multiple dimensions
- 📥 Exportable Results: Download analysis results in JSON format

## Project Structure

### Core Files

- `app.py`: Main Streamlit application file that handles the user interface and orchestrates the analysis flow
- `get_websites_links.py`: Handles company website discovery using Google Custom Search
- `website_scraping.py`: Manages website crawling and content extraction
- `website_analyzer.py`: Analyzes website content using LLM to extract business intelligence
- `website_summarizer.py`: Creates comprehensive summaries from analyzed data
- `linkedin_analyzer.py`: Handles LinkedIn profile analysis

### Supporting Files

- `requirements.txt`: Lists all Python dependencies
- `.env`: Configuration file for API keys and settings
- `tests/`: Directory containing test files

## Setup Instructions

See [SETUP.md](SETUP.md) for detailed setup instructions.

## Usage

1. Start the application:
```bash
streamlit run app.py
```

2. Enter a company name in the search box

3. The application will:
   - Search for the company's online presence
   - Analyze the company website
   - Analyze LinkedIn profile if available
   - Generate comprehensive analysis and summary
   - Provide downloadable reports

## API Keys Required

The following API keys need to be configured in `.env`:
- `MISTRAL_API_KEY`: For LLM-based analysis
- `GOOGLE_API_KEY`: For Google Custom Search
- `GOOGLE_CSE_ID`: For Google Custom Search Engine

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request
