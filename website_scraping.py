import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from typing import List, Dict, Set
import os
from website_analyzer import WebsiteAnalyzer

class WebsiteScraper:
    def __init__(self, api_key: str):
        """
        Initialize the WebsiteScraper with a base URL
        
        Args:
            base_url: The starting URL to analyze
        """
        self.base_url = None
        self.analyzer = WebsiteAnalyzer(api_key)
        self.visited_urls: Set[str] = set()
        self.results: Dict[str, Dict] = {}
        
    def get_page_content(self, url: str) -> tuple[str, BeautifulSoup]:
        """Fetch and parse webpage content"""
        try:
            response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
            html = response.text
            soup = BeautifulSoup(html, 'html.parser')
            return html, soup
        except Exception as e:
            print(f"Error fetching {url}: {str(e)}")
            return "", None

    def extract_links(self, soup: BeautifulSoup, current_url: str) -> List[str]:
        """Extract and normalize all links from the page"""
        links = []
        if soup:
            base_domain = urlparse(self.base_url).netloc
            base_path = urlparse(self.base_url).path.rstrip('/')
            
            for link in soup.find_all('a', href=True):
                href = link['href']
                absolute_url = urljoin(current_url, href)
                parsed_url = urlparse(absolute_url)
                
                # Only include links from the same domain and that are extensions of base path
                if (parsed_url.netloc == base_domain and 
                    parsed_url.path.startswith(base_path) and
                    not any(ext in parsed_url.path.lower() for ext in ['.pdf', '.jpg', '.png', '.gif', '.svg']) and
                    '#' not in parsed_url.path and
                    not parsed_url.path.endswith('//')):
                    
                    # Clean the URL by removing query parameters and fragments
                    clean_url = f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}"
                    # Remove trailing slashes for consistency
                    clean_url = clean_url.rstrip('/')
                    links.append(clean_url)
                    
        return list(set(links))

    def analyze_page(self, url: str, html_content: str):
        """Analyze a single page using LangChain"""
        page_info = self.analyzer.analyze_content(html_content)
        if page_info:
            self.results[url] = page_info

    def crawl_website(self, url: str, depth: int = 2, max_links_per_depth: int = 10):
        """
        Recursively crawl the website up to specified depth
        
        Args:
            url: Current URL to process
            depth: Maximum depth to crawl
            max_links_per_depth: Maximum number of links to follow at each depth level
        """
        self.base_url = url
        self._crawl_recursive(url, depth, max_links_per_depth)

    def _crawl_recursive(self, url: str, depth: int, max_links_per_depth: int):
        """Helper method for recursive crawling"""
        if depth == 0 or url in self.visited_urls:
            return
            
        print(f"Crawling {url} (depth {depth})")
        self.visited_urls.add(url)
        
        html_content, soup = self.get_page_content(url)
        if not soup:
            return

        # Analyze the current page
        self.analyze_page(url, html_content)

        # Extract and process links
        links = self.extract_links(soup, url)
        sorted_links = sorted(links)[:max_links_per_depth]
        print(f"Found {len(links)} links, processing {len(sorted_links)} at depth {depth}")

        # Process all links recursively
        for link in sorted_links:
            self._crawl_recursive(link, depth - 1, max_links_per_depth)

    def get_results(self) -> Dict:
        """Return the final extracted information"""
        return self.results

if __name__ == "__main__":
    base_url = "https://www.madkudu.com/"
    scraper = WebsiteScraper()
    scraper.crawl_website(base_url,2,2)
    print(scraper.get_results())