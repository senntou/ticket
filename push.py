import requests
import os
from dotenv import load_dotenv

def send_line_broadcast(message: str, access_token: str) -> bool:
    """
    LINE公式アカウントから友だち全員に通知を送る関数
    
    Parameters
    ----------
    message : str
        送信したいテキスト
    access_token : str
        LINE Developers で発行したチャネルアクセストークン（長期）
    
    Returns
    -------
    bool
        True: 成功, False: 失敗
    """
    url = "https://api.line.me/v2/bot/message/broadcast"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    payload = {
        "messages": [
            {"type": "text", "text": message}
        ]
    }
    
    response = requests.post(url, headers=headers, json=payload)
    
    if response.status_code == 200:
        return True
    else:
        print("Error:", response.status_code, response.text)
        return False

def get_line_token() -> str:
    """
    環境変数からLINE アクセストークンを取得する
    
    Returns:
        str: LINEアクセストークン
    
    Raises:
        ValueError: トークンが見つからない場合
    """
    load_dotenv()
    token = os.getenv('LINE_ACCESS_TOKEN')
    if not token:
        raise ValueError("LINE_ACCESS_TOKEN が環境変数または.envファイルに設定されていません")
    return token

if __name__ == "__main__":
    # for test
    try:
        load_dotenv()  # .envファイルを読み込み
        message = "Hello, this is a test message from LINE Broadcast API."
        access_token = get_line_token()
        
        print("LINE通知をテスト送信中...")
        success = send_line_broadcast(message, access_token)
        
        if success:
            print("✅ LINE通知の送信に成功しました！")
        else:
            print("❌ LINE通知の送信に失敗しました。")
            
    except ValueError as e:
        print(f"❌ 設定エラー: {e}")
    except Exception as e:
        print(f"❌ 予期しないエラー: {e}") 
