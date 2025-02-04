# Setup Instructions

## Prerequisites

- Python 3.8 or higher
- pip (Python package installer)
- Virtual environment (recommended)

## Installation Steps

1. Clone the repository:
```bash
git clone <repository-url>
cd <repository-name>
```

2. Create and activate a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Unix/macOS
# OR
.venv\Scripts\activate  # On Windows
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up API keys:
   - Create a `.env` file in the root directory
   - Add the following keys:
```env
MISTRAL_API_KEY=your_mistral_api_key
GOOGLE_API_KEY=your_google_api_key
GOOGLE_CSE_ID=your_google_cse_id
```

### Getting API Keys

1. **Mistral API Key**:
   - Visit [Mistral AI Platform](https://mistral.ai)
   - Create an account
   - Generate an API key from your dashboard

2. **Google API Key and CSE ID**:
   - Visit [Google Cloud Console](https://console.cloud.google.com)
   - Create a new project
   - Enable the Custom Search API
   - Create credentials (API key)
   - Visit [Google Programmable Search Engine](https://programmablesearch.google.com/about/)
   - Create a new search engine
   - Get your Search Engine ID (CSE ID)

## Verifying Installation

1. Run the tests:
```bash
pytest tests/
```

2. Start the application:
```bash
streamlit run app.py
```
