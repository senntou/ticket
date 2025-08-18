#!/bin/bash
# cron用実行スクリプト

# スクリプトのディレクトリに移動
cd /home/tomfe/workspace/ticket

# 仮想環境をアクティベート
source venv/bin/activate

# チケットチェックを実行
python check_once.py

# 終了コードを保持
exit_code=$?

# 結果をログに記録
echo "[$(date)] Exit code: $exit_code" >> /home/tomfe/workspace/ticket/cron.log

exit $exit_code