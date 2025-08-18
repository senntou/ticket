#!/usr/bin/env python3
import time
import sys
import os
from datetime import datetime
from dotenv import load_dotenv
from ticket_checker import TicketChecker
from push import send_line_broadcast, get_line_token

class TicketMonitor:
    def __init__(self, url: str, check_interval: int = 60 * 15):
        """
        チケット監視システム
        
        Args:
            url: 監視対象のURL
            check_interval: チェック間隔（秒）
        """
        self.url = url
        self.check_interval = check_interval
        self.checker = TicketChecker()
        self.line_token = None
        self.last_notification_time = None
        self.notification_cooldown = 300  # 5分間は重複通知を避ける
        
        # LINE通知の設定
        try:
            self.line_token = get_line_token()
            print("✅ LINE通知の設定が完了しました")
        except Exception as e:
            print(f"❌ LINE通知の設定に失敗: {e}")
            print("通知なしで監視を続行します")
    
    def send_notification(self, message: str) -> bool:
        """
        LINE通知を送信する（重複通知防止付き）
        
        Args:
            message: 送信メッセージ
            
        Returns:
            bool: 送信成功したかどうか
        """
        if not self.line_token:
            print("LINE通知が設定されていません")
            return False
        
        # 重複通知防止
        current_time = time.time()
        if (self.last_notification_time and 
            current_time - self.last_notification_time < self.notification_cooldown):
            print("⏰ 通知クールダウン中（重複防止）")
            return False
        
        try:
            success = send_line_broadcast(message, self.line_token)
            if success:
                self.last_notification_time = current_time
                print("📱 LINE通知を送信しました")
            return success
        except Exception as e:
            print(f"❌ 通知送信エラー: {e}")
            return False
    
    def format_notification_message(self, result: dict) -> str:
        """
        通知メッセージをフォーマットする
        
        Args:
            result: check_ticket_status()の結果
            
        Returns:
            str: フォーマット済みメッセージ
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        if not result['is_sold_out']:
            message = f"""🎫 チケット販売状況更新！

❗️ 完売していません ❗️

時刻: {timestamp}
URL: {self.url}

すぐにチケットをチェックしてください！"""
        else:
            message = f"""💔 チケット完売中

時刻: {timestamp}
完売要素数: {result['sold_out_count']}

引き続き監視を続けます..."""
        
        return message
    
    def run_single_check(self) -> dict:
        """
        1回のチェックを実行する
        
        Returns:
            dict: チェック結果
        """
        print(f"[{datetime.now().strftime('%H:%M:%S')}] チケット状況をチェック中...")
        
        result = self.checker.check_ticket_status(self.url)
        
        if not result['success']:
            print(f"❌ チェック失敗: {result['message']}")
            return result
        
        # 結果表示
        status_emoji = "❌" if result['is_sold_out'] else "✅"
        print(f"{status_emoji} {result['message']}")
        
        # 完売していない場合は通知
        if not result['is_sold_out']:
            message = self.format_notification_message(result)
            print("\n🚨 完売していません！通知を送信します...")
            self.send_notification(message)
        
        return result
    
    def start_monitoring(self):
        """
        定期監視を開始する
        """
        print("🎫 チケット監視システムを開始します")
        print(f"📍 監視URL: {self.url}")
        print(f"⏰ チェック間隔: {self.check_interval}秒")
        print(f"🔍 検索クラス: {self.checker.class_name}")
        print(f"📱 LINE通知: {'有効' if self.line_token else '無効'}")
        print("-" * 60)
        
        try:
            while True:
                self.run_single_check()
                
                print(f"💤 {self.check_interval}秒待機中...")
                print("-" * 40)
                
                time.sleep(self.check_interval)
                
        except KeyboardInterrupt:
            print("\n\n⏹️  監視を停止します...")
            sys.exit(0)
        except Exception as e:
            print(f"\n❌ 予期しないエラー: {e}")
            # エラーが発生しても監視を続行
            time.sleep(30)
            print("🔄 監視を再開します...")
            self.start_monitoring()

def get_ticket_url() -> str:
    """
    環境変数からチケットURLを取得する
    
    Returns:
        str: チケット監視URL
    
    Raises:
        ValueError: URLが見つからない場合
    """
    load_dotenv()
    url = os.getenv('TICKET_URL')
    if not url:
        raise ValueError("TICKET_URL が環境変数または.envファイルに設定されていません")
    return url

def get_target_class() -> str:
    """
    環境変数からターゲットクラス名を取得する
    
    Returns:
        str: 検索対象のクラス名
    
    Raises:
        ValueError: クラス名が見つからない場合
    """
    load_dotenv()
    class_name = os.getenv('TARGET_CLASS')
    if not class_name:
        raise ValueError("TARGET_CLASS が環境変数または.envファイルに設定されていません")
    return class_name

def main():
    """メイン実行関数"""
    try:
        load_dotenv()  # .envファイルを読み込み
        
        # 設定
        url = get_ticket_url()
        target_class = get_target_class()
        check_interval = 60 * 15  # 15分間隔
        
        print("=" * 60)
        print("🎫 チケット監視システム")
        print("=" * 60)
        
        # 最初に1回テストチェック
        print("📋 初回チェックを実行します...")
        monitor = TicketMonitor(url, check_interval)
        monitor.checker.class_name = target_class  # クラス名を設定
        result = monitor.run_single_check()
        
        if not result['success']:
            print("❌ 初回チェックに失敗しました。設定を確認してください。")
            sys.exit(1)
        
        print("\n✅ 初回チェック完了")
        print("🚀 定期監視を開始します...\n")
        
        # 定期監視開始
        monitor.start_monitoring()
        
    except ValueError as e:
        print(f"❌ 設定エラー: {e}")
        print("📝 .envファイルにTICKET_URLとTARGET_CLASSを設定してください")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 予期しないエラー: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
