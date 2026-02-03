import os
import requests
import time

# 只需要你的微信通知 Token
PUSHPLUS_TOKEN = os.environ["PUSHPLUS_TOKEN"]

def check_qunar():
    # 这是一个模拟去哪儿低价日历的接口 (示例)
    # 出发地: 厦门(XMN), 目的地: 重庆(CKG), 日期: 2026-02-28
    # 注意：国内接口非常容易变动，这只是一个尝试
    url = "https://m.flight.qunar.com/flight/api/tower/calendar"
    params = {
        "dep": "厦门",
        "arr": "重庆",
        "depDate": "2026-02-28"
    }
    headers = {
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1"
    }

    try:
        print("正在通过公共接口尝试查询...")
        # 这里我们换一个更简单的逻辑：如果 API 搞不定，我们直接发一个测试成功消息
        # 确保你的 GitHub Actions 通道是畅通的
        requests.post("http://www.pushplus.plus/send", json={
            "token": PUSHPLUS_TOKEN,
            "title": "GitHub Action 运行状态",
            "content": "如果你看到这条消息，说明你的 GitHub 环境和微信通知已经全部打通了！<br>现在只剩 API 数据获取这一步了。",
            "template": "html"
        })
        print("测试通知已发出，请检查微信。")
    except Exception as e:
        print(f"出错: {e}")

if __name__ == "__main__":
    check_qunar()
