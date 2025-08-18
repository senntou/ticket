#!/usr/bin/env python3
"""
チケット状況を一回だけチェックするスクリプト
cronで定期実行する用
"""

import sys
import os
from datetime import datetime
from dotenv import load_dotenv
from ticket_checker import TicketChecker
from push import send_line_broadcast, get_line_token

def get_ticket_url() -> str:
    """環境変数からチケットURLを取得"""
    url = os.getenv('TICKET_URL')
    if not url:
        raise ValueError("TICKET_URL が環境変数または.envファイルに設定されていません")
    return url

def get_target_class() -> str:
    """環境変数からターゲットクラス名を取得"""
    class_name = os.getenv('TARGET_CLASS')
    if not class_name:
        raise ValueError("TARGET_CLASS が環境変数または.envファイルに設定されていません")
    return class_name

def send_notification_if_available(message: str) -> bool:
    """
    可能であればLINE通知を送信
    
    Args:
        message: 送信メッセージ
        
    Returns:
        bool: 送信成功したかどうか
    """
    try:
        token = get_line_token()
        success = send_line_broadcast(message, token)
        if success:
            print("📱 LINE通知を送信しました")
        return success
    except Exception as e:
        print(f"⚠️  通知送信に失敗: {e}")
        return False

def format_notification_message(result: dict, url: str) -> str:
    """通知メッセージをフォーマット"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    if not result['is_sold_out']:
        message = f"""🎫 チケット販売開始！

❗️ 完売していません ❗️

時刻: {timestamp}
URL: {url}

すぐにチケットをチェックしてください！"""
    else:
        # 完売時は通知しない（ログのみ）
        return ""
    
    return message

def main():
    """メイン実行関数"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    try:
        # 環境変数読み込み
        load_dotenv()
        url = get_ticket_url()
        target_class = get_target_class()
        
        print(f"[{timestamp}] チケットチェック開始")
        print(f"URL: {url}")
        print(f"クラス: {target_class}")
        
        # チケットチェッカーを初期化
        checker = TicketChecker(target_class)
        
        # チェック実行
        result = checker.check_ticket_status(url)
        
        if not result['success']:
            print(f"❌ チェック失敗: {result['message']}")
            sys.exit(1)
        
        # 結果表示
        status = "完売中" if result['is_sold_out'] else "販売中"
        print(f"結果: {status}")
        
        if result['is_sold_out']:
            print(f"完売要素数: {result['sold_out_count']}")
            print("📝 完売のため通知は送信しません")
        else:
            print("🚨 完売していません！通知を送信します...")
            
            # 通知メッセージ作成・送信
            message = format_notification_message(result, url)
            if message:
                success = send_notification_if_available(message)
                if not success:
                    print("⚠️  通知送信に失敗しましたが、処理を続行します")
        
        # 詳細情報をログ出力
        print(f"取得要素数: {result['details']['total_elements']}")
        if result['details']['all_texts']:
            print("取得テキスト:")
            for i, text in enumerate(result['details']['all_texts'], 1):
                print(f"  {i}. {text}")
        
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] チェック完了")
        
        # 完売していない場合は終了コード1（cronで検知しやすくするため）
        sys.exit(0 if result['is_sold_out'] else 1)
        
    except ValueError as e:
        print(f"❌ 設定エラー: {e}")
        print("📝 .envファイルにTICKET_URLとTARGET_CLASSを設定してください")
        sys.exit(2)
    except Exception as e:
        print(f"❌ 予期しないエラー: {e}")
        sys.exit(3)

if __name__ == "__main__":
    main()