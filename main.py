import os
import requests
import time

# --- 1. 配置钥匙 (从 Secrets 读取) ---
API_KEY = os.environ["RAPIDAPI_KEY"]
PUSHPLUS_TOKEN = os.environ["PUSHPLUS_TOKEN"]

# --- 2. 这里是关键！请根据你网页上看到的修改 ---
# 如果你订阅的是 Sky-Scanner3，通常是这个地址：
URL = "https://sky-scrapper3.p.rapidapi.com/find/selector" 
# 如果你订阅的是别的，请把上面引号里的内容换成你网页上看到的 url

HOST = "sky-scrapper3.p.rapidapi.com" 
# 同样，把这里换成你网页上看到的 X-RapidAPI-Host

def get_flight_price(origin, dest, date):
    # 这里是参数，不同的 API 参数名不一样
    # 如果网页上是 fromEntityId，这里就写 fromEntityId
    querystring = {
        "fromEntityId": origin,
        "toEntityId": dest,
        "departDate": date,
        "currency": "CNY"
    }
    # 注意：如果网页上的参数名是 originSkyId，请对应修改上面的 key

    headers = {
        "X-RapidAPI-Key": API_KEY,
        "X-RapidAPI-Host": HOST
    }

    try:
        print(f"正在请求: {origin} -> {dest}")
        response = requests.get(URL, headers=headers, params=querystring)
        print(f"收到状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            # 简化逻辑：直接打印前3条结果看能不能查到
            print("查询成功，正在处理数据...")
            return data
        else:
            print(f"错误信息: {response.text}")
            return None
    except Exception as e:
        print(f"发生异常: {e}")
        return None

def main():
    # 临时测试一个城市，成功了再加循环
    print("🚀 开始单点测试...")
    result = get_flight_price("XMN", "CKG", "2026-02-28")
    
    if result:
        # 这里只是简单的打印，确认能拿到数据
        print("✅ 拿到数据了！")
        # 发送一个简单的通知
        url = "http://www.pushplus.plus/send"
        requests.post(url, json={
            "token": PUSHPLUS_TOKEN,
            "title": "机票测试成功",
            "content": "API 终于跑通了！"
        })
    else:
        print("❌ 还是没拿到数据，请检查 URL 和参数名")

if __name__ == "__main__":
    main()
