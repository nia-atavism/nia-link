"""
Neural-Bridge HTML Cleaner Service
HTML 清洗與格式轉換服務 - 優化版
"""

import re
from typing import Optional
from bs4 import BeautifulSoup, Comment, NavigableString
import html2text


class CleanerService:
    """
    HTML 內容清洗與轉換服務
    將雜亂的 HTML 轉換為乾淨的 Markdown/Text 格式
    
    優化特性：
    - GitHub README 特殊處理
    - 新聞網站優化提取
    - 智慧內容截斷
    - 程式碼區塊保留
    """
    
    # 需要移除的標籤
    REMOVE_TAGS = [
        'script', 'style', 'nav', 'footer', 'header', 'aside',
        'iframe', 'noscript', 'svg', 'canvas', 'video', 'audio',
        'advertisement', 'ads', 'ad', 'banner', 'meta', 'link',
        'iframe', 'embed', 'object', 'applet'
    ]
    
    # 增加「語義清洗」關鍵字
    NOISE_PATTERNS = [
        r'ad[s]?[-_]?', r'advertisement', r'banner', r'popup',
        r'sidebar', r'widget', r'social[-_]?share', r'comment[-_]?section',
        r'related[-_]?articles', r'recommend', r'footer', r'header',
        r'nav[-_]?bar', r'menu', r'breadcrumb', r'pagination', r'cookie',
        r'newsletter', r'subscribe', r'promo', r'sponsor', r'outbrain', r'taboola'
    ]
    
    # GitHub 專用的內容選擇器
    GITHUB_CONTENT_SELECTORS = [
        'article.markdown-body',
        '.readme',
        '#readme',
        '.Box-body',
        '.repository-content'
    ]
    
    # 新聞網站常用的內容選擇器
    NEWS_CONTENT_SELECTORS = [
        'article[class*="article"]',
        '.article-content',
        '.article-body',
        '.post-content',
        '.entry-content',
        '.story-body',
        '[itemprop="articleBody"]',
        '.content-body'
    ]
    
    # 最大內容長度（字符數）
    MAX_CONTENT_LENGTH = 100000  # ~100KB
    
    def __init__(self):
        """初始化 HTML 轉 Markdown 轉換器"""
        self.h2t = html2text.HTML2Text()
        self.h2t.ignore_links = False
        self.h2t.ignore_images = False
        self.h2t.ignore_emphasis = False
        self.h2t.body_width = 0  # 不換行
        self.h2t.skip_internal_links = False
        self.h2t.inline_links = True
        self.h2t.protect_links = True
        self.h2t.wrap_links = False
        self.h2t.unicode_snob = True
        self.h2t.escape_snob = True
    
    def detect_site_type(self, html_content: str, url: str = "") -> str:
        """
        偵測網站類型以應用特殊處理
        
        Returns:
            str: 'github', 'news', 'docs', 'general'
        """
        url_lower = url.lower()
        
        if 'github.com' in url_lower or 'github.io' in url_lower:
            return 'github'
        
        news_domains = ['techcrunch', 'theverge', 'wired', 'engadget', 'arstechnica',
                        'medium.com', 'dev.to', 'hackernews', 'reddit.com']
        if any(domain in url_lower for domain in news_domains):
            return 'news'
        
        docs_indicators = ['docs.', 'documentation', 'wiki', 'readme']
        if any(indicator in url_lower for indicator in docs_indicators):
            return 'docs'
        
        return 'general'
    
    def clean_html(self, html_content: str, preserve_code: bool = True) -> BeautifulSoup:
        """
        清洗 HTML 內容，移除雜訊元素與低資訊密度節點
        """
        soup = BeautifulSoup(html_content, 'lxml')
        
        # 1. 移除基礎雜訊標籤
        for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
            comment.extract()
        
        for tag in self.REMOVE_TAGS:
            for element in soup.find_all(tag):
                element.decompose()

        # 2. 語義層級清洗：移除低資訊密度節點 (Entropy Filter)
        # 邏輯：如果一個節點內部只有連結且字數極少，通常是導航或廣告
        for container in soup.find_all(['div', 'section', 'ul']):
            text_len = len(container.get_text(strip=True))
            links = container.find_all('a')
            if text_len < 20 and len(links) > 3:
                container.decompose()
            elif text_len == 0:
                container.decompose()

        # 3. 原本的 class/id 正則清洗邏輯...
        noise_regex = re.compile('|'.join(self.NOISE_PATTERNS), re.IGNORECASE)
        
        # (保持原有的 class/id 遍歷邏輯)
        
        elements_to_remove = []
        for element in soup.find_all(True):
            if element is None or not hasattr(element, 'get'):
                continue
            
            try:
                # 跳過重要的內容區域
                if element.name in ['article', 'main', 'section']:
                    continue
                
                # 檢查 class 屬性
                classes = element.get('class', [])
                if classes:
                    class_str = ' '.join(classes)
                    if noise_regex.search(class_str):
                        # 確保不是主要內容區域
                        if 'content' not in class_str.lower() and 'article' not in class_str.lower():
                            elements_to_remove.append(element)
                            continue
                
                # 檢查 id 屬性
                element_id = element.get('id', '')
                if element_id and noise_regex.search(element_id):
                    if 'content' not in element_id.lower() and 'article' not in element_id.lower():
                        elements_to_remove.append(element)
                        continue
            except (AttributeError, TypeError):
                continue
        
        # 統一刪除收集到的元素
        for element in elements_to_remove:
            try:
                element.decompose()
            except (AttributeError, TypeError):
                pass
        
        return soup
    
    def extract_github_content(self, soup: BeautifulSoup) -> Optional[BeautifulSoup]:
        """
        專門提取 GitHub README 內容
        
        Args:
            soup: BeautifulSoup DOM
            
        Returns:
            Optional[BeautifulSoup]: README 內容區塊
        """
        # 嘗試多種 GitHub 內容選擇器
        for selector in self.GITHUB_CONTENT_SELECTORS:
            content = soup.select_one(selector)
            if content:
                return content
        
        # 嘗試找 markdown-body
        markdown_body = soup.find(class_=re.compile(r'markdown-body', re.I))
        if markdown_body:
            return markdown_body
        
        return None
    
    def extract_news_content(self, soup: BeautifulSoup) -> Optional[BeautifulSoup]:
        """
        專門提取新聞網站內容
        
        Args:
            soup: BeautifulSoup DOM
            
        Returns:
            Optional[BeautifulSoup]: 文章內容區塊
        """
        # 嘗試多種新聞內容選擇器
        for selector in self.NEWS_CONTENT_SELECTORS:
            content = soup.select_one(selector)
            if content:
                return content
        
        # 嘗試找 article 標籤
        article = soup.find('article')
        if article:
            return article
        
        return None
    
    def extract_main_content(self, soup: BeautifulSoup, site_type: str = 'general') -> BeautifulSoup:
        """
        智慧提取主要內容區域
        
        Args:
            soup: BeautifulSoup DOM
            site_type: 網站類型
            
        Returns:
            BeautifulSoup: 主要內容區塊
        """
        # 根據網站類型嘗試特殊提取
        if site_type == 'github':
            content = self.extract_github_content(soup)
            if content:
                return content
        elif site_type == 'news':
            content = self.extract_news_content(soup)
            if content:
                return content
        
        # 通用內容提取策略
        main_content = (
            soup.find('main') or
            soup.find('article') or
            soup.find(attrs={'role': 'main'}) or
            soup.find(attrs={'id': re.compile(r'^(content|main|article)$', re.I)}) or
            soup.find(attrs={'class': re.compile(r'(^|\s)(content|main|article)(-|_|\s|$)', re.I)}) or
            soup.body or
            soup
        )
        
        return main_content
    
    def extract_metadata(self, soup: BeautifulSoup) -> dict:
        """
        從 HTML 提取元數據
        
        Args:
            soup: BeautifulSoup DOM
            
        Returns:
            dict: 包含 title, author, description, published_date 的字典
        """
        metadata = {
            'title': None,
            'author': None,
            'description': None,
            'published_date': None,
            'keywords': None,
            'image': None
        }
        
        # 提取標題（優先使用 og:title）
        og_title = soup.find('meta', attrs={'property': 'og:title'})
        if og_title and og_title.get('content'):
            metadata['title'] = og_title['content']
        else:
            title_tag = soup.find('title')
            if title_tag:
                metadata['title'] = title_tag.get_text(strip=True)
        
        # 嘗試從 meta 標籤提取資訊
        meta_mappings = {
            'author': ['author', 'article:author', 'og:author', 'twitter:creator'],
            'description': ['description', 'og:description', 'twitter:description'],
            'published_date': ['article:published_time', 'date', 'pubdate', 'publishdate', 'datePublished'],
            'keywords': ['keywords'],
            'image': ['og:image', 'twitter:image']
        }
        
        for field, meta_names in meta_mappings.items():
            for name in meta_names:
                # 檢查 name 屬性
                meta = soup.find('meta', attrs={'name': name})
                if meta and meta.get('content'):
                    metadata[field] = meta['content']
                    break
                
                # 檢查 property 屬性（Open Graph）
                meta = soup.find('meta', attrs={'property': name})
                if meta and meta.get('content'):
                    metadata[field] = meta['content']
                    break
                
                # 檢查 itemprop 屬性（Schema.org）
                meta = soup.find('meta', attrs={'itemprop': name})
                if meta and meta.get('content'):
                    metadata[field] = meta['content']
                    break
        
        # 如果沒有從 meta 取得標題，嘗試從 h1 取得
        if not metadata['title']:
            h1 = soup.find('h1')
            if h1:
                metadata['title'] = h1.get_text(strip=True)
        
        # GitHub 特殊處理：嘗試從 repo 名稱取得標題
        repo_name = soup.find(attrs={'itemprop': 'name'})
        if repo_name and not metadata['title']:
            metadata['title'] = repo_name.get_text(strip=True)
        
        return metadata
    
    def extract_links(self, soup: BeautifulSoup, base_url: str = "") -> list[str]:
        """
        提取頁面中的所有連結
        
        Args:
            soup: BeautifulSoup DOM
            base_url: 基礎 URL（用於相對路徑）
            
        Returns:
            list[str]: 連結列表
        """
        links = []
        for a in soup.find_all('a', href=True):
            href = a['href']
            
            # 跳過錨點連結和 JavaScript
            if href.startswith('#') or href.startswith('javascript:'):
                continue
            
            if href.startswith('http'):
                links.append(href)
            elif href.startswith('/') and base_url:
                links.append(f"{base_url.rstrip('/')}{href}")
            elif base_url and not href.startswith(('mailto:', 'tel:')):
                links.append(f"{base_url.rstrip('/')}/{href}")
        
        # 去重並限制數量
        return list(dict.fromkeys(links))[:50]

    
    def to_markdown(self, html_content: str, url: str = "") -> str:
        """
        將 HTML 轉換為 Markdown
        
        Args:
            html_content: HTML 字串
            url: 原始 URL（用於網站類型偵測）
            
        Returns:
            str: Markdown 格式內容
        """
        soup = self.clean_html(html_content)
        site_type = self.detect_site_type(html_content, url)
        
        # 提取主要內容
        main_content = self.extract_main_content(soup, site_type)
        
        # 特殊處理：保留程式碼區塊的格式
        if site_type in ['github', 'docs']:
            # 確保程式碼區塊有正確的語言標記
            for pre in main_content.find_all('pre'):
                code = pre.find('code')
                if code:
                    # 嘗試獲取語言
                    classes = code.get('class', [])
                    lang = ''
                    for cls in classes:
                        if cls.startswith('language-') or cls.startswith('lang-'):
                            lang = cls.split('-', 1)[1]
                            break
                    if lang:
                        code['data-lang'] = lang
        
        # 轉換為 Markdown
        markdown = self.h2t.handle(str(main_content))
        
        # 清理多餘的空行
        markdown = re.sub(r'\n{3,}', '\n\n', markdown)
        
        # 清理轉義字符問題
        markdown = markdown.replace('\\[', '[').replace('\\]', ']')
        markdown = markdown.replace('\\(', '(').replace('\\)', ')')
        
        markdown = markdown.strip()
        
        # 截斷過長的內容
        if len(markdown) > self.MAX_CONTENT_LENGTH:
            markdown = self._truncate_content(markdown, self.MAX_CONTENT_LENGTH)
        
        return markdown
    
    def _truncate_content(self, content: str, max_length: int) -> str:
        """
        智慧截斷內容，保持結構完整
        
        Args:
            content: 原始內容
            max_length: 最大長度
            
        Returns:
            str: 截斷後的內容
        """
        if len(content) <= max_length:
            return content
        
        # 在段落邊界截斷
        truncated = content[:max_length]
        last_double_newline = truncated.rfind('\n\n')
        
        if last_double_newline > max_length * 0.7:
            truncated = truncated[:last_double_newline]
        else:
            last_newline = truncated.rfind('\n')
            if last_newline > max_length * 0.8:
                truncated = truncated[:last_newline]
        
        return truncated + "\n\n---\n\n*[內容已截斷，原始長度：{} 字符]*".format(len(content))
    
    def to_text(self, html_content: str) -> str:
        """
        將 HTML 轉換為純文字
        
        Args:
            html_content: HTML 字串
            
        Returns:
            str: 純文字內容
        """
        soup = self.clean_html(html_content)
        
        # 獲取純文字
        text = soup.get_text(separator='\n', strip=True)
        
        # 清理多餘的空行
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        text = text.strip()
        
        # 截斷過長的內容
        if len(text) > self.MAX_CONTENT_LENGTH:
            text = self._truncate_content(text, self.MAX_CONTENT_LENGTH)
        
        return text
    
    def to_json_structure(self, html_content: str) -> dict:
        """
        將 HTML 轉換為結構化的 JSON
        
        Args:
            html_content: HTML 字串
            
        Returns:
            dict: 結構化內容
        """
        soup = self.clean_html(html_content)
        metadata = self.extract_metadata(BeautifulSoup(html_content, 'lxml'))
        
        # 提取階層式內容
        sections = []
        current_section = None
        
        for element in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'pre', 'code']):
            if element.name.startswith('h'):
                if current_section:
                    sections.append(current_section)
                current_section = {
                    'heading': element.get_text(strip=True),
                    'level': int(element.name[1]),
                    'paragraphs': [],
                    'code_blocks': []
                }
            elif element.name == 'p' and current_section:
                text = element.get_text(strip=True)
                if text:
                    current_section['paragraphs'].append(text)
            elif element.name in ['pre', 'code'] and current_section:
                code_text = element.get_text(strip=True)
                if code_text and len(code_text) > 10:
                    current_section['code_blocks'].append(code_text[:1000])
        
        if current_section:
            sections.append(current_section)
        
        return {
            'metadata': metadata,
            'sections': sections[:50],  # 限制 section 數量
            'links': self.extract_links(soup)
        }
    
    def calculate_savings(self, original_size: int, cleaned_size: int) -> dict:
        """
        計算 Token 節省資訊
        
        Args:
            original_size: 原始大小（位元組）
            cleaned_size: 清洗後大小（位元組）
            
        Returns:
            dict: 成本資訊
        """
        # 確保數值有效
        original_size = max(1, original_size)  # 避免除以零
        cleaned_size = max(0, cleaned_size)
        
        # 確保 cleaned_size 不大於 original_size（邏輯上的修正）
        if cleaned_size > original_size:
            cleaned_size = original_size
        
        # 估計 Token 數（大約每 4 個字元 = 1 Token）
        original_tokens = original_size // 4
        cleaned_tokens = cleaned_size // 4
        tokens_saved = max(0, original_tokens - cleaned_tokens)
        
        # 計算縮減百分比（限制在 0-99.9% 之間，100% 表示沒有內容，這是異常情況）
        reduction = 0.0
        if original_size > 0:
            reduction = round((1 - cleaned_size / original_size) * 100, 1)
            reduction = min(reduction, 99.9)  # 防止 100% 的情況
        
        return {
            'original_size': original_size,
            'cleaned_size': cleaned_size,
            'tokens_saved': tokens_saved,
            'reduction_percent': reduction
        }
