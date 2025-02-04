import os
from dotenv import load_dotenv
from googleapiclient.discovery import build
import json
from langchain_mistralai import ChatMistralAI
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser,OutputFixingParser

# Load environment variables from .env
load_dotenv()

class WebsiteResults(BaseModel):
    company: str = Field(description="Name of the company",default="None")
    website: str = Field(description="URL of the company's website",default="None")
    linkedin: str = Field(description="URL of the company's LinkedIn profile",default="None")

class WebsiteFinder:
    """A class to find and extract company websites and information from search results using LLM."""
    
    def __init__(self, api_key: str):
        """Initialize the WebsiteFinder with Mistral API key.
        
        Args:
            api_key (str): The Mistral API key for LLM access
        """
        self.llm = ChatMistralAI(mistral_api_key=api_key)
        base_parser = PydanticOutputParser(pydantic_object=WebsiteResults)
        self.parser = OutputFixingParser.from_llm(parser=base_parser, llm=self.llm)
        
        self.prompt = ChatPromptTemplate.from_messages([
    ("system", """You are an expert at analyzing search results and extracting official company websites and LinkedIn profiles.
Always return valid JSON data with all specified fields as a SINGLE DICTIONARY (not a list).
Only return the JSON data, do not add any explanatory text before or after.
For LinkedIn profiles, prioritize company pages over individual profiles.
IMPORTANT: Do not escape underscores in the JSON keys."""),
    ("user", """Analyze the following search results for {company}:

{search_result}

Extract the company's official website URL and LinkedIn profile URL. Follow these rules:
1. Only select the main company website (avoid subpages, blogs, etc.)
2. For LinkedIn, only use company pages (linkedin.com/company/...), not individual profiles
3. Ignore third-party websites and directories
4. If no valid URL is found, use "None"

Return ONLY the following JSON without any additional text:
{format_instructions}""")
])
       
    def analyze_search(self, company: str, search_results):
        """Analyze search results to extract company website, LinkedIn profile, and description.
        
        Args:
            company (str): Name of the company to analyze
            search_results (list): List of dictionaries containing search results with 'title', 'link', and 'description'
            
        Returns:
            dict: Dictionary containing company information with the following keys:
                - company: Name of the company
                - website: URL of company's main website
                - linkedin: URL of company's LinkedIn profile
                - description: Brief description of the company
                
        Raises:
            Exception: If there's an error during analysis
        """
        try:
            # Create chain
            chain = self.prompt | self.llm | self.parser
            
            # Invoke chain
            response = chain.invoke({
                "company": company,
                "search_result": json.dumps(search_results, indent=2, ensure_ascii=False), 
                "format_instructions": self.parser.get_format_instructions()
            })
            
            return response.model_dump()
            
        except Exception as e:
            print(f"Error analyzing content: {e}")
            raise e

def search_google(query: str, google_api_key, cx, num_results: int = 5) -> list:
    """Search Google Custom Search API for given query.
    
    Args:
        query (str): Search query string
        num_results (int, optional): Number of results to return. Defaults to 10.
        
    Returns:
        list: List of dictionaries containing search results with 'title', 'link', and 'description'
        
    Raises:
        ValueError: If required environment variables are not set
    """
    
    if not google_api_key or not cx:
        raise ValueError("GOOGLE_API_KEY and GOOGLE_CSE_ID environment variables must be set")
    
    try:
        service = build('customsearch', 'v1', developerKey=google_api_key)
        
        result = service.cse().list(q=query, cx=cx, num=num_results).execute()
        if 'items' in result:
            return [{
                'title': item.get('title', ''),
                'link': item.get('link', ''),
                'description': item.get('snippet', '')
            } for item in result['items']]
        return []
        
    except Exception as e:
        print(f"Error during Google search: {str(e)}")
        return []

def get_company_website(company: str,mistral_api_key, google_api_key, cx) -> dict:
    """Get company website and related information using Google search and LLM analysis.
    
    Args:
        company (str): Name of the company to search for
        
    Returns:
        dict: Dictionary containing company information with website URL, LinkedIn profile, and description
    """
   
    # General search for the official website
    search_results = search_google(company, google_api_key, cx, num_results=5) + search_google(f"{company} linkedin", google_api_key, cx, num_results=5)
    
    results = WebsiteFinder(mistral_api_key).analyze_search(company, search_results)
    return results

if __name__ == "__main__":
    
    mistral_api_key = os.getenv('MISTRAL_API_KEY')
    google_api_key = os.getenv('GOOGLE_API_KEY')
    cx = os.getenv('GOOGLE_CSE_ID')
    print(get_company_website("Madkudu",mistral_api_key, google_api_key, cx))