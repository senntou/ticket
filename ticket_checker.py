from playwright.sync_api import sync_playwright
import time
from typing import List, Dict, Optional

class TicketChecker:
    def __init__(self, class_name: str = 'sc-1dvehrx-0'):
        self.class_name = class_name
        self.sold_out_text = '完売しました'
    
    def get_page_elements(self, url: str) -> Optional[List[Dict]]:
        """
        指定されたURLからページの要素を取得する
        
        Returns:
            List[Dict]: 要素情報のリスト（tag_name, text, href, html）
            None: エラーが発生した場合
        """
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            # User-Agentを設定
            page.set_extra_http_headers({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            })
            
            try:
                print(f"Accessing page: {url}")
                page.goto(url, wait_until='networkidle')
                page.wait_for_timeout(3000)
                
                # 指定されたクラス名の要素を検索
                elements = page.query_selector_all(f'.{self.class_name}')
                
                if not elements:
                    print(f"No elements found with class '{self.class_name}'")
                    browser.close()
                    return None
                
                element_data = []
                for element in elements:
                    data = {
                        'tag_name': element.evaluate('el => el.tagName').lower(),
                        'text': element.inner_text().strip(),
                        'href': element.get_attribute('href') if element.evaluate('el => el.tagName').lower() == 'a' else None,
                        'html': element.inner_html()
                    }
                    element_data.append(data)
                
                browser.close()
                return element_data
                
            except Exception as e:
                print(f"Error: {e}")
                browser.close()
                return None
    
    def check_sold_out(self, elements: List[Dict]) -> Dict:
        """
        要素リストから「完売しました」の文字列をチェックする
        
        Args:
            elements: get_page_elements()から返された要素リスト
            
        Returns:
            Dict: チェック結果
                - is_sold_out: bool（完売かどうか）
                - sold_out_elements: List（完売テキストを含む要素）
                - all_texts: List（すべての要素のテキスト）
        """
        if not elements:
            return {
                'is_sold_out': False,
                'sold_out_elements': [],
                'all_texts': []
            }
        
        sold_out_elements = []
        all_texts = []
        
        for element in elements:
            text = element['text']
            all_texts.append(text)
            
            if self.sold_out_text in text:
                sold_out_elements.append(element)
        
        return {
            'is_sold_out': len(sold_out_elements) > 0,
            'sold_out_elements': sold_out_elements,
            'all_texts': all_texts
        }
    
    def check_ticket_status(self, url: str) -> Dict:
        """
        チケットの状態を総合的にチェックする
        
        Args:
            url: チェック対象のURL
            
        Returns:
            Dict: チェック結果
                - success: bool（処理が成功したか）
                - is_sold_out: bool（完売かどうか）
                - sold_out_count: int（完売要素の数）
                - message: str（結果メッセージ）
                - details: Dict（詳細情報）
        """
        elements = self.get_page_elements(url)
        
        if elements is None:
            return {
                'success': False,
                'is_sold_out': False,
                'sold_out_count': 0,
                'message': 'ページの取得に失敗しました',
                'details': {}
            }
        
        sold_out_result = self.check_sold_out(elements)
        
        message = f"完売状態: {'はい' if sold_out_result['is_sold_out'] else 'いいえ'}"
        if sold_out_result['is_sold_out']:
            message += f" ({len(sold_out_result['sold_out_elements'])}個の要素で確認)"
        
        return {
            'success': True,
            'is_sold_out': sold_out_result['is_sold_out'],
            'sold_out_count': len(sold_out_result['sold_out_elements']),
            'message': message,
            'details': {
                'sold_out_elements': sold_out_result['sold_out_elements'],
                'all_texts': sold_out_result['all_texts'],
                'total_elements': len(elements)
            }
        }
    
    def monitor_ticket_status(self, url: str, interval: int = 30):
        """
        定期的にチケット状態を監視する
        
        Args:
            url: 監視対象のURL
            interval: チェック間隔（秒）
        """
        print(f"チケット監視を開始します（{interval}秒間隔）...")
        print(f"監視URL: {url}")
        print(f"検索対象クラス: {self.class_name}")
        print(f"完売キーワード: {self.sold_out_text}")
        print("-" * 50)
        
        while True:
            current_time = time.strftime('%Y-%m-%d %H:%M:%S')
            print(f"\n[{current_time}] チェック中...")
            
            result = self.check_ticket_status(url)
            print(f"結果: {result['message']}")
            
            if result['success'] and result['details']['all_texts']:
                print("取得されたテキスト:")
                for i, text in enumerate(result['details']['all_texts'], 1):
                    print(f"  {i}. {text}")
            
            time.sleep(interval)

def main():
    """メイン実行関数"""
    url = "https://www.asoview.com/channel/ticket/IwRkAqwybp/ticket0000041589/"
    checker = TicketChecker()
    
    # 一回だけチェック
    result = checker.check_ticket_status(url)
    print("=== チケット状態チェック結果 ===")
    print(f"処理成功: {result['success']}")
    print(f"メッセージ: {result['message']}")
    
    if result['success']:
        print(f"完売状態: {result['is_sold_out']}")
        print(f"完売要素数: {result['sold_out_count']}")
        print(f"総要素数: {result['details']['total_elements']}")
        
        print("\n取得されたすべてのテキスト:")
        for i, text in enumerate(result['details']['all_texts'], 1):
            print(f"  {i}. {text}")
        
        if result['details']['sold_out_elements']:
            print("\n完売要素の詳細:")
            for i, element in enumerate(result['details']['sold_out_elements'], 1):
                print(f"  {i}. タグ: {element['tag_name']}, テキスト: {element['text']}")
                if element['href']:
                    print(f"      リンク: {element['href']}")
    
    # 監視モードを使いたい場合は以下をコメントアウト
    # checker.monitor_ticket_status(url, 30)

if __name__ == "__main__":
    main()