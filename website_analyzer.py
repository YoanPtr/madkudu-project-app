from typing import Dict, List
from langchain_mistralai import ChatMistralAI
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser,OutputFixingParser
from bs4 import BeautifulSoup
from pydantic import BaseModel, Field
from typing import List

class CompanyOverview(BaseModel):
    name: str = Field(description="Company name",default="Not specified")
    description: str = Field(description="Company description",default="Not specified")
    mission: str = Field(description="Company mission statement",default="Not specified")
    products_services: List[str] = Field(description="List of products and services",default_factory=list)
    target_market: List[str] = Field(description="Target market segments",default_factory=list)
    differentiators: List[str] = Field(description="Key differentiators",default_factory=list)
    company_size: str = Field(description="Company size",default="Not specified")
    maturity_stage: str = Field(description="Company maturity stage",default="Not specified")

class SalesIntelligence(BaseModel):
    sales_approach: str = Field(description="Sales approach (self-serve, sales-led, etc.)",default="Not specified")
    target_profiles: List[str] = Field(description="Target customer profiles",default_factory=list)
    pain_points: List[str] = Field(description="Customer pain points addressed",default_factory=list)
    benefits: List[str] = Field(description="Benefits offered",default_factory=list)
    success_stories: List[str] = Field(description="Customer success stories",default_factory=list)
    cta_patterns: List[str] = Field(description="Call-to-action patterns",default_factory=list)

class PricingTier(BaseModel):
    name: str = Field(description="Tier name",default="Not specified")
    price: str = Field(description="Price",default="Not specified")
    features: List[str] = Field(description="Features included",default_factory=list)

class Pricing(BaseModel):
    models: List[str] = Field(description="Pricing models",default_factory=list)
    price_points: List[str] = Field(description="Price points",default_factory=list)
    billing_frequency: List[str] = Field(description="Billing frequency",default_factory=list)
    tiers: List[PricingTier] = Field(description="Pricing tiers",default_factory=list)
    has_enterprise_pricing: bool = Field(description="Whether enterprise pricing is available",default=False)

class Firmographic(BaseModel):
    industry: List[str] = Field(description="Industry focus",default_factory=list)
    locations: List[str] = Field(description="Geographic locations",default_factory=list)
    employee_count: str = Field(description="Number of employees",default="Not specified")
    technologies: List[str] = Field(description="Technologies used",default_factory=list)
    partners: List[str] = Field(description="Partner companies",default_factory=list)
    certifications: List[str] = Field(description="Certifications and compliance",default_factory=list)

class GTMStrategy(BaseModel):
    sales_motion: str = Field(description="Sales motion type",default="Not specified")
    marketing_channels: List[str] = Field(description="Marketing channels used",default_factory=list)
    content_strategy: str = Field(description="Content strategy approach",default="Not specified")
    partner_program: str = Field(description="Partner program details",default="Not specified")
    acquisition_approach: str = Field(description="Customer acquisition approach",default="Not specified")

class WebsiteAnalysis(BaseModel):
    company_overview: CompanyOverview
    sales_intelligence: SalesIntelligence
    pricing: Pricing
    firmographic: Firmographic
    gtm_strategy: GTMStrategy

class WebsiteAnalyzer:
    def __init__(self, api_key: str):
        """Initialize the LangChain analyzer with Mistral API key"""
        self.llm = ChatMistralAI(mistral_api_key=api_key)
        base_parser = PydanticOutputParser(pydantic_object=WebsiteAnalysis)
        self.parser = OutputFixingParser.from_llm(parser=base_parser, llm=self.llm)
        
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert at analyzing B2B company websites and extracting comprehensive business intelligence. 
Always return valid JSON data with all specified fields.
IMPORTANT: Do not escape underscores in the JSON keys. For example, use "company_overview" not "company\_overview"."""),
            ("user", """Analyze this website content and extract comprehensive business information focusing on B2B sales intelligence.

Extract ALL relevant information that matches these categories, following the exact JSON structure below. Do not escape underscores in field names:

{format_instructions}

Content to analyze:
{text}

Extract as much information as possible from the content. If a piece of information is not found, use 'Not specified' for strings and empty lists for lists. Focus on factual information present in the content.""")
        ])

    def _clean_html(self, html_content: str) -> str:
        """Clean HTML and return text content"""
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Remove script and style elements
        for element in soup(["script", "style", "meta", "link"]):
            element.decompose()
            
        # Get clean text
        text = soup.get_text(separator='\n', strip=True)
        
        # Clean up text
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        return '\n'.join(chunk for chunk in chunks if chunk)

    def analyze_content(self, html_content: str) -> Dict:
        """
        Analyze content using LangChain and Mistral to extract business information
        
        Args:
            html_content: Raw HTML content
            
        Returns:
            Dict: Dictionary containing the analyzed information
        """
        try:
            # Clean content
            clean_content = self._clean_html(html_content)
            
            # Create chain
            chain = self.prompt | self.llm | self.parser
            
            # Invoke chain
            response = chain.invoke({
                "text": clean_content, 
                "format_instructions": self.parser.get_format_instructions()
            })
            
            return response.model_dump()
            
        except Exception as e:
            print(f"Error analyzing content: {e}")
            raise e
