"""
Neural-Bridge v0.2 Extractor Service
Action Map 提取與 Token 計算專用模組
"""

import re
from typing import List, Optional, Tuple
from bs4 import BeautifulSoup, Comment
from .cleaner import CleanerService


class ActionExtractor:
    """
    行動地圖提取器
    從 HTML 中識別並提取所有可操作元件
    """
    
    # CTA (Call-to-Action) 關鍵字 - 用於判斷高重要性
    HIGH_IMPORTANCE_KEYWORDS = [
        'submit', 'login', 'sign in', 'sign up', 'register', 'buy', 'purchase',
        'checkout', 'add to cart', 'download', 'search', 'subscribe', 'confirm',
        '登入', '註冊', '購買', '加入購物車', '搜尋', '下載', '確認', '提交'
    ]
    
    # 表單相關關鍵字 - 用於判斷中等重要性
    MEDIUM_IMPORTANCE_KEYWORDS = [
        'email', 'password', 'username', 'name', 'phone', 'address',
        'filter', 'sort', 'select', 'choose', 'option',
        '電子郵件', '密碼', '用戶名', '姓名', '電話', '地址'
    ]
    
    def __init__(self):
        """初始化提取器"""
        self.cleaner = CleanerService()
    
    def extract_actions(self, html_content: str) -> List[dict]:
        """
        從 HTML 提取所有可操作元件（行動地圖）
        
        Args:
            html_content: 原始 HTML 字串
            
        Returns:
            List[dict]: 可操作元件列表，每個元件包含 type, label, selector, importance
        """
        try:
            soup = BeautifulSoup(html_content, 'lxml')
            actions = []
            seen_selectors = set()  # 避免重複
            
            # 1. 提取按鈕
            actions.extend(self._extract_buttons(soup, seen_selectors))
            
            # 2. 提取輸入框
            actions.extend(self._extract_inputs(soup, seen_selectors))
            
            # 3. 提取文字區域
            actions.extend(self._extract_textareas(soup, seen_selectors))
            
            # 4. 提取下拉選單
            actions.extend(self._extract_selects(soup, seen_selectors))
            
            # 5. 提取重要連結 (CTA)
            actions.extend(self._extract_cta_links(soup, seen_selectors))
            
            # 按重要性排序 (high -> medium -> low)
            importance_order = {'high': 0, 'medium': 1, 'low': 2}
            actions.sort(key=lambda x: importance_order.get(x.get('importance', 'low'), 2))
            
            return actions[:50]  # 限制最多 50 個元件
            
        except Exception as e:
            print(f"Warning: extract_actions failed: {e}")
            return []
    
    def _extract_buttons(self, soup: BeautifulSoup, seen: set) -> List[dict]:
        """提取所有按鈕元件"""
        actions = []
        
        for btn in soup.find_all(['button', 'input']):
            if btn.name == 'input' and btn.get('type') not in ['submit', 'button', 'reset']:
                continue
            
            label = self._get_element_label(btn, 'Button')
            selector = self._generate_unique_selector(btn)
            
            if not selector or selector in seen:
                continue
            
            seen.add(selector)
            importance = self._evaluate_importance(label, 'button')
            
            actions.append({
                'type': 'button',
                'label': label[:100],
                'selector': selector,
                'importance': importance
            })
        
        return actions
    
    def _extract_inputs(self, soup: BeautifulSoup, seen: set) -> List[dict]:
        """提取所有輸入框元件"""
        actions = []
        
        for inp in soup.find_all('input'):
            input_type = inp.get('type', 'text')
            
            # 跳過非輸入型態
            if input_type in ['submit', 'button', 'reset', 'hidden', 'image']:
                continue
            
            # 決定 action type
            if input_type == 'checkbox':
                action_type = 'checkbox'
            else:
                action_type = 'input'
            
            label = self._get_element_label(inp, f'{input_type.capitalize()} Input')
            selector = self._generate_unique_selector(inp)
            
            if not selector or selector in seen:
                continue
            
            seen.add(selector)
            importance = self._evaluate_importance(label, action_type)
            
            action = {
                'type': action_type,
                'label': label[:100],
                'selector': selector,
                'importance': importance
            }
            
            # 添加額外資訊
            if inp.get('placeholder'):
                action['placeholder'] = inp['placeholder'][:100]
            if inp.get('value') and input_type not in ['password']:
                action['value'] = inp['value'][:100]
            
            actions.append(action)
        
        return actions
    
    def _extract_textareas(self, soup: BeautifulSoup, seen: set) -> List[dict]:
        """提取所有文字區域元件"""
        actions = []
        
        for textarea in soup.find_all('textarea'):
            label = self._get_element_label(textarea, 'Textarea')
            selector = self._generate_unique_selector(textarea)
            
            if not selector or selector in seen:
                continue
            
            seen.add(selector)
            importance = self._evaluate_importance(label, 'textarea')
            
            action = {
                'type': 'textarea',
                'label': label[:100],
                'selector': selector,
                'importance': importance
            }
            
            if textarea.get('placeholder'):
                action['placeholder'] = textarea['placeholder'][:100]
            
            actions.append(action)
        
        return actions
    
    def _extract_selects(self, soup: BeautifulSoup, seen: set) -> List[dict]:
        """提取所有下拉選單元件"""
        actions = []
        
        for select in soup.find_all('select'):
            label = self._get_element_label(select, 'Select')
            selector = self._generate_unique_selector(select)
            
            if not selector or selector in seen:
                continue
            
            seen.add(selector)
            importance = self._evaluate_importance(label, 'select')
            
            # 獲取選項
            options = []
            for option in select.find_all('option')[:20]:
                opt_text = option.get_text(strip=True)
                if opt_text:
                    options.append(opt_text)
            
            action = {
                'type': 'select',
                'label': label[:100],
                'selector': selector,
                'importance': importance
            }
            
            if options:
                action['options'] = options
            
            actions.append(action)
        
        return actions
    
    def _extract_cta_links(self, soup: BeautifulSoup, seen: set) -> List[dict]:
        """提取重要連結 (CTA)"""
        actions = []
        
        for link in soup.find_all('a', href=True):
            link_text = link.get_text(strip=True).lower()
            classes = ' '.join(link.get('class', [])).lower()
            
            # 判斷是否為 CTA
            is_cta = any(kw in link_text for kw in self.HIGH_IMPORTANCE_KEYWORDS)
            is_button_style = any(kw in classes for kw in ['btn', 'button', 'cta'])
            
            if not (is_cta or is_button_style):
                continue
            
            label = link.get_text(strip=True) or link.get('aria-label') or 'Link'
            selector = self._generate_unique_selector(link)
            
            if not selector or selector in seen:
                continue
            
            seen.add(selector)
            importance = 'high' if is_cta else 'medium'
            
            actions.append({
                'type': 'link',
                'label': label[:100],
                'selector': selector,
                'importance': importance
            })
        
        return actions
    
    def _get_element_label(self, element, default: str) -> str:
        """獲取元素的最佳標籤"""
        # 嘗試多種來源
        label = (
            element.get_text(strip=True) or
            element.get('aria-label') or
            element.get('title') or
            element.get('placeholder') or
            element.get('value') or
            element.get('name') or
            element.get('id') or
            default
        )
        return label.strip() if label else default
    
    def _generate_unique_selector(self, element) -> Optional[str]:
        """
        為元素生成唯一的 CSS 選擇器
        優先級: id > data-testid > name > class > tag
        """
        # 1. 優先使用 ID (最可靠)
        if element.get('id'):
            element_id = element['id']
            # 確保 ID 是有效的 CSS 選擇器
            if re.match(r'^[a-zA-Z_][a-zA-Z0-9_-]*$', element_id):
                return f"#{element_id}"
            else:
                return f"[id='{element_id}']"
        
        # 2. 使用 data-testid (測試友好)
        if element.get('data-testid'):
            return f"[data-testid='{element['data-testid']}']"
        
        # 3. 使用 name 屬性
        if element.get('name'):
            name = element['name']
            return f"{element.name}[name='{name}']"
        
        # 4. 使用 aria-label
        if element.get('aria-label'):
            aria_label = element['aria-label']
            return f"{element.name}[aria-label='{aria_label}']"
        
        # 5. 使用 class 組合
        classes = element.get('class', [])
        if classes:
            # 過濾掉動態生成的 class (通常是隨機字符)
            stable_classes = [c for c in classes if not re.match(r'^[a-z]{1,3}\d+', c) and len(c) > 2]
            if stable_classes:
                class_selector = '.'.join(stable_classes[:2])
                return f"{element.name}.{class_selector}"
        
        # 6. 使用 type 屬性 (用於 input)
        if element.name == 'input' and element.get('type'):
            input_type = element['type']
            placeholder = element.get('placeholder')
            if placeholder:
                return f"input[type='{input_type}'][placeholder='{placeholder}']"
            return f"input[type='{input_type}']"
        
        # 7. 使用 placeholder
        if element.get('placeholder'):
            return f"{element.name}[placeholder='{element['placeholder']}']"
        
        # 8. 回退到 tag 名稱 (不太可靠，但總比沒有好)
        return element.name
    
    def _evaluate_importance(self, label: str, element_type: str) -> str:
        """
        評估元件的重要性
        
        Returns:
            str: 'high', 'medium', 'low'
        """
        label_lower = label.lower()
        
        # 檢查高重要性關鍵字
        if any(kw in label_lower for kw in self.HIGH_IMPORTANCE_KEYWORDS):
            return 'high'
        
        # 搜尋框特別標記為高重要性
        if element_type == 'input' and any(kw in label_lower for kw in ['search', '搜尋', 'query']):
            return 'high'
        
        # 檢查中等重要性關鍵字
        if any(kw in label_lower for kw in self.MEDIUM_IMPORTANCE_KEYWORDS):
            return 'medium'
        
        # 登入相關元素標記為中等
        if element_type in ['input', 'textarea']:
            return 'medium'
        
        return 'low'


class TokenCalculator:
    """
    Token 計算器
    計算原始 HTML 與清洗後內容的 Token 節省率
    """
    
    # 估計每個 Token 大約 4 個字元
    CHARS_PER_TOKEN = 4
    
    @staticmethod
    def calculate_token_savings(original_html: str, cleaned_text: str) -> Tuple[str, dict]:
        """
        計算 Token 節省率
        
        Args:
            original_html: 原始 HTML 字串
            cleaned_text: 清洗後的文字
            
        Returns:
            Tuple[str, dict]: (百分比字串, 詳細資訊)
        """
        original_size = len(original_html.encode('utf-8'))
        cleaned_size = len(cleaned_text.encode('utf-8'))
        
        # 確保數值有效
        original_size = max(1, original_size)
        cleaned_size = max(0, cleaned_size)
        
        # 計算 Token 數
        original_tokens = original_size // TokenCalculator.CHARS_PER_TOKEN
        cleaned_tokens = cleaned_size // TokenCalculator.CHARS_PER_TOKEN
        tokens_saved = max(0, original_tokens - cleaned_tokens)
        
        # 計算節省百分比
        if original_size > cleaned_size:
            reduction = ((original_size - cleaned_size) / original_size) * 100
            reduction = min(reduction, 99.9)  # 限制最大值
        else:
            reduction = 0.0
        
        # 格式化為百分比字串 (PRD 規格)
        savings_str = f"{reduction:.1f}%"
        
        details = {
            'original_size': original_size,
            'cleaned_size': cleaned_size,
            'original_tokens': original_tokens,
            'cleaned_tokens': cleaned_tokens,
            'tokens_saved': tokens_saved,
            'reduction_percent': round(reduction, 1)
        }
        
        return savings_str, details
