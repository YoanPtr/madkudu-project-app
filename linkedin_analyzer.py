import requests
from bs4 import BeautifulSoup
from typing import Dict, List
import json
import os
from dotenv import load_dotenv
from langchain_mistralai import ChatMistralAI
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser
import httpx
import time

# Load environment variables
load_dotenv()

class LinkedInEmployee(BaseModel):
    name: str = Field(description="Employee name")
    role: str = Field(description="Employee role")

class LinkedInCompany(BaseModel):
    name: str = Field(description="Company name")
    description: str = Field(description="Company description", default="Not specified")
    industry: str = Field(description="Company industry", default="Not specified")
    company_size: str = Field(description="Employee count or range", default="Not specified")
    headquarters: str = Field(description="Location", default="Not specified")
    website: str = Field(description="URL", default="Not specified")
    founded: str = Field(description="Year founded", default="Not specified")
    specialties: List[str] = Field(description="Company specialties", default_factory=list)
    employees: List[LinkedInEmployee] = Field(description="Key employees", default_factory=list)

class LinkedInAnalyzer:
    def __init__(self, api_key: str):
        """Initialize the LinkedIn analyzer with Mistral API key"""
        self.llm = ChatMistralAI(mistral_api_key=api_key)
        self.parser = PydanticOutputParser(pydantic_object=LinkedInCompany)
        # Create prompt template for analysis
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", "You are an expert at analyzing LinkedIn company profiles. Always return valid JSON data with all specified fields."),
            ("human", """Extract company information from the following LinkedIn page content.
Focus on finding these specific details about {company_name}:
1. Company name
2. Description/About
3. Industry
4. Company size (number of employees)
5. Headquarters location
6. Website URL
7. Year founded
8. Specialties or key areas of focus
9. Key employees with their roles (focus on leadership: CEO, Founder, CTO, Directors, etc.)

Content from LinkedIn page:
{content}

Return the information in this exact JSON format (include all fields even if null):
{format_instructions}

Only return the JSON object, no other text. For employees, focus on finding leadership roles and list up to 10 employees.""")
        ])
        
    def _extract_content_from_html(self, html_content: str) -> str:
        """Extract readable text content from HTML.
        
        Args:
            html_content: Raw HTML content
            
        Returns:
            str: Clean text content from the HTML
        """
        soup = BeautifulSoup(html_content, 'lxml')
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        
        # Get text content
        text = soup.get_text(separator='\n', strip=True)
        
        # Clean up text
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = '\n'.join(chunk for chunk in chunks if chunk)
        
        return text

    def analyze_content(self, content: str, company_name: str = None) -> dict:
        """Analyze LinkedIn content using LLM.
        
        Args:
            content (str): LinkedIn profile content to analyze
            company_name (str, optional): Company name for context
            
        Returns:
            dict: Analyzed LinkedIn data
        """
        try:
            # Create chain
            chain = self.prompt | self.llm | self.parser
            
            # Get response
            response = chain.invoke({
                "content": content,
                "company_name": company_name,
                "format_instructions": self.parser.get_format_instructions()
            })
            
            return response.model_dump()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:  # Rate limit error
                print("Rate limit exceeded, waiting 5 seconds before retry...")
                time.sleep(2)  # Wait 2 seconds before retrying
                try:
                    # Retry once
                    response = chain.invoke({
                        "content": content,
                        "company_name": company_name,
                        "format_instructions": self.parser.get_format_instructions()
                    })
                    return response.model_dump()
                except Exception as retry_error:
                    print(f"Retry failed: {str(retry_error)}")
                    raise retry_error
            raise e
        except Exception as e:
            print(f"Error analyzing LinkedIn content: {str(e)}")
            raise e

    def scrape_and_analyze(self, linkedin_url: str) -> Dict:
        """Scrape and analyze a LinkedIn company page.
        
        Args:
            linkedin_url: URL of the LinkedIn company page
            
        Returns:
            dict: Dictionary containing extracted company information
            
        Raises:
            ValueError: If the URL is not a valid LinkedIn company URL
        """
        # Validate LinkedIn URL
        if not (linkedin_url.startswith(('http://', 'https://')) and 
                'linkedin' in linkedin_url.lower() and 
                'company' in linkedin_url.lower()):
            raise ValueError("Invalid LinkedIn URL. Must be a LinkedIn company page URL (e.g., https://www.linkedin.com/company/company-name)")

        try:
            # Send GET request to the LinkedIn URL
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Cache-Control': 'max-age=0'
            }
            
            response = requests.get(linkedin_url, headers=headers)
            
            # Extract text content
            content = self._extract_content_from_html(response.text)
            
            # Get company name from URL for better context
            company_name = linkedin_url.split('company/')[1].split('/')[0].replace('-', ' ').title()
            
            # Analyze content
            return self.analyze_content(content, company_name)
            
        except requests.RequestException as e:
            print(f"Error scraping LinkedIn page: {e}")
            raise e
        except Exception as e:
            print(f"Error in analysis pipeline: {e}")
            raise e

if __name__ == "__main__":
    linkedin_url = "https://www.linkedin.com/company/madkudu"
    analyzer = LinkedInAnalyzer(os.getenv('MISTRAL_API_KEY'))
    print(analyzer.scrape_and_analyze(linkedin_url))