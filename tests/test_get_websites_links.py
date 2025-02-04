import pytest
import os
from dotenv import load_dotenv
from app import GOOGLE_API_KEY
from get_websites_links import WebsiteFinder, search_google, get_company_website
import time

# Load environment variables
load_dotenv()

MISTRAL_API_KEY= os.getenv('MISTRAL_API_KEY')
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
GOOGLE_CSE_ID = os.getenv('GOOGLE_CSE_ID')


# Test data for different companies
COMPANY_TEST_CASES = [
    {
        'name': 'MadKudu',
        'expected_domain': 'madkudu.com',
        'expected_linkedin': 'linkedin.com/company/madkudu'
    },
    {
        'name': 'Alter Watt',
        'expected_domain': 'alter-watt.com',
        'expected_linkedin': 'linkedin.com/company/alter-watt'
    },
]
    
class TestWebsiteFinder:
    def setup_method(self):
        """Setup test environment with API key"""
        self.api_key = MISTRAL_API_KEY
        if not self.api_key:
            pytest.skip("MISTRAL_API_KEY not found in environment")
        self.finder = WebsiteFinder(self.api_key)
        time.sleep(2)  # Add delay between test methods

    @pytest.mark.parametrize("company_info", COMPANY_TEST_CASES)
    def test_analyze_search_companies(self, company_info):
        """Test analyze_search with different companies"""
        time.sleep(2)  # Add delay between API calls to avoid rate limiting
        
        company_name = company_info['name']
        search_results = search_google(company_name, num_results=5)
        
        result = self.finder.analyze_search(company_name, search_results)
        
        # Check structure
        assert isinstance(result, dict)
        assert 'company' in result
        assert 'website' in result
        assert 'linkedin' in result
        
        # Check company name
        assert result['company'].lower() == company_name.lower()
        
        # Check website domain
        if result['website'] != "None":
            assert company_info['expected_domain'] in result['website'].lower(), \
                f"Expected domain {company_info['expected_domain']} not found in website URL {result['website']}"
        
        # Check LinkedIn URL
        if result['linkedin'] != "None":
            assert company_info['expected_linkedin'] in result['linkedin'].lower(), \
                f"Expected LinkedIn {company_info['expected_linkedin']} not found in LinkedIn URL {result['linkedin']}"

    def test_analyze_search_empty_results(self):
        """Test analyze_search with empty results"""
        result = self.finder.analyze_search("NonexistentCompany", [])
        assert result['website'] == "None"
        assert result['linkedin'] == "None"

class TestGoogleSearch:
    def setup_method(self):
        """Setup test environment with API keys"""
        self.api_key = GOOGLE_API_KEY
        self.cx = GOOGLE_CSE_ID
        if not self.api_key or not self.cx:
            pytest.skip("GOOGLE_API_KEY or GOOGLE_CSE_ID not found in environment")

    @pytest.mark.parametrize("company_info", COMPANY_TEST_CASES)
    def test_search_google_companies(self, company_info):
        """Test Google search with different companies"""
        company_name = company_info['name']
        results = search_google(company_name)
        
        assert len(results) > 0
        # Check that each result has the required fields
        for result in results:
            assert 'title' in result
            assert 'link' in result
            assert 'description' in result
        
        # Check if company's website is in the results
        found_company = False
        expected_domain = company_info['expected_domain']
        for result in results:
            if expected_domain in result['link'].lower():
                found_company = True
                break
        assert found_company, f"{company_name}'s website ({expected_domain}) not found in search results"

    def test_search_google_with_limit(self):
        """Test Google search with result limit"""
        num_results = 3
        results = search_google("MadKudu", num_results=num_results)
        assert len(results) <= num_results

class TestGetCompanyWebsite:
    def setup_method(self):
        """Setup test environment"""
        self.api_key = MISTRAL_API_KEY
        self.google_api_key = GOOGLE_API_KEY
        self.cx = GOOGLE_CSE_ID
        if not all([self.api_key, self.google_api_key, self.cx]):
            pytest.skip("Required API keys not found in environment")

    @pytest.mark.parametrize("company_info", COMPANY_TEST_CASES)
    def test_get_company_website_companies(self, company_info):
        """Test get_company_website with different companies"""
        company_name = company_info['name']
        result = get_company_website(company_name,MISTRAL_API_KEY, GOOGLE_API_KEY, GOOGLE_CSE_ID)
        
        assert isinstance(result, dict)
        assert 'company' in result
        assert 'website' in result
        assert 'linkedin' in result
        
        # Check company name
        assert result['company'].lower() == company_name.lower()
        
        # Check website domain
        if result['website'] != "None":
            assert company_info['expected_domain'] in result['website'].lower(), \
                f"Expected domain {company_info['expected_domain']} not found in website URL {result['website']}"
        
        # Check LinkedIn URL
        if result['linkedin'] != "None":
            assert company_info['expected_linkedin'] in result['linkedin'].lower(), \
                f"Expected LinkedIn {company_info['expected_linkedin']} not found in LinkedIn URL {result['linkedin']}"

    def test_get_company_website_nonexistent(self):
        """Test get_company_website with a nonexistent company"""
        result = get_company_website("ThisCompanyDefinitelyDoesNotExist12345",mistral_api_key, google_api_key, cx)
        assert result['website'] == "None"
        assert result['linkedin'] == "None"
