from readability import Document
from newspaper import Article
from bs4 import BeautifulSoup

async def extract_url_local(url: str) -> str:
    article = Article(url)
    article.download()
    article.parse()

    html = article.html
    doc = Document(html)
    clean_html = doc.summary(html_partial=True)

    soup = BeautifulSoup(clean_html, "lxml")
    text = soup.get_text("\n")

    return text.strip()