from typing import Dict, List
from langchain_mistralai import ChatMistralAI
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser, OutputFixingParser
from pydantic import BaseModel, Field
import json
import httpx
import time


class WebsiteSummary(BaseModel):
    company_overview_summary: str = Field(description="Summary of company overview")
    sales_intelligence_summary: str = Field(description="Summary of sales intelligence")
    pricing_summary: str = Field(description="Summary of pricing information")
    firmographic_summary: str = Field(description="Summary of firmographic data")
    gtm_strategy_summary: str = Field(description="Summary of go-to-market strategy")
    overall_summary: str = Field(description="Overall website summary")


class WebsiteSummarizer:
    def __init__(self, website_analysis: Dict[str, Dict], linkedin_analysis: Dict, api_key: str):
        """Initialize the Website Summarizer with Mistral API key
        
        Args:
            website_analysis: Dictionary with URLs as keys and analysis sections as values
            linkedin_analysis: LinkedIn profile analysis data
            api_key: Mistral API key for LLM access
        """
        self.llm = ChatMistralAI(mistral_api_key=api_key)
        base_parser = PydanticOutputParser(pydantic_object=WebsiteSummary)
        self.parser = OutputFixingParser.from_llm(parser=base_parser, llm=self.llm)
        
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", "You are an expert at summarizing B2B company website analysis. Create concise yet comprehensive summaries."),
            ("user", """Create a summary of the analyzed website data, focusing on key insights and patterns.
            
            Create summaries for each section and an overall summary following this structure:
            
            {format_instructions}
            
            Website Analysis: {website}
            LinkedIn Data: {linkedin}
            
            Focus on the most important insights and patterns across all analyzed pages.""")
        ])
        
        self.website_analysis = website_analysis
        self.linkedin_analysis = linkedin_analysis

    def _create_section_text(self, data: Dict) -> str:
        """Convert a dictionary section into a readable text format"""
        text = []
        for key, value in data.items():
            if isinstance(value, (list, dict)):
                text.append(f"{key}: {json.dumps(value, indent=2)}")
            else:
                text.append(f"{key}: {value}")
        return "\n".join(text)

    def summarize_analysis(self) -> WebsiteSummary:
        """
        Create a comprehensive summary from the website analysis
        
        Returns:
            WebsiteSummary: Summarized website information
        """
        # Combine analysis from all URLs
        combined_analysis = {
            "company_overview": {},
            "sales_intelligence": {},
            "pricing": {},
            "firmographic": {},
            "gtm_strategy": {}
        }
        
        # Merge analysis from all URLs
        for url, sections in self.website_analysis.items():
            for section_name, section_data in sections.items():
                if section_name in combined_analysis:
                    combined_analysis[section_name].update(section_data)
        
        # Convert the analysis data to a format suitable for the LLM
        analysis_text = {
            section: self._create_section_text(data)
            for section, data in combined_analysis.items()
        }
        
        # Create chain
        chain = self.prompt | self.llm | self.parser
        
        try:
            # Get response
            response = chain.invoke({
                "format_instructions": self.parser.get_format_instructions(),
                "website": analysis_text,
                "linkedin": self.linkedin_analysis
            })
            
            return response.model_dump()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:  # Rate limit error
                print("Rate limit exceeded, waiting 5 seconds before retry...")
                time.sleep(10)  # Wait 2 seconds before retrying
                try:
                    # Retry once
                    response = chain.invoke({
                        "format_instructions": self.parser.get_format_instructions(),
                        "website": analysis_text,
                        "linkedin": self.linkedin_analysis
                    })
                    return response.model_dump()
                except Exception as retry_error:
                    print(f"Retry failed: {str(retry_error)}")
                    raise retry_error
            raise e
        except Exception as e:
            print(f"Error creating summary: {str(e)}")
            raise e
