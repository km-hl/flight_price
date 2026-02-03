import os
import requests
import time

# --- 1. 钥匙配置 ---
API_KEY = os.environ["RAPIDAPI_KEY"]
PUSHPLUS_TOKEN = os.environ["PUSHPLUS_TOKEN"]

# --- 2. 航线配置 ---
DEST = "CKG"   # 重庆
DATE = "2026-02-28"
ORIGINS = {
    "JJN": "泉州",
    "FOC": "福州",
    "XMN": "厦门"
}

# 🚫 廉航黑名单
LCC_BLOCKLIST = ["Spring", "West Air", "9 Air", "Lucky", "Urumqi", "Tianjin"]

def get_flight(origin_code):
    # --- ！！！这里是 Flights Sky 的专用地址 ！！！ ---
    HOST = "flights-sky.p.rapidapi.com"
    url = f"https://{HOST}/flights/search-one-way"
    
    headers = {
        "x-rapidapi-key": API_KEY,
        "x-rapidapi-host": HOST
    }

    # 根据你提供的截图，这个 API 使用 fromEntityId
    querystring = {
        "fromEntityId": origin_code,
        "toEntityId": DEST,
        "departDate": DATE,
        "currency": "CNY",
        "market": "CN",
        "locale": "zh-CN",
        "adults": "1"
    }

    try:
        print(f"📡 正在查询 {origin_code} -> {DEST}...")
        response = requests.get(url, headers=headers, params=querystring)
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            # --- 解析逻辑 (针对 search-one-way 结构) ---
            if "data" in data and "itineraries" in data["data"]:
                itineraries = data["data"]["itineraries"]
                
                for f in itineraries:
                    # 获取航司名称
                    airline = f["legs"][0]["carriers"]["marketing"][0]["name"]
                    
                    # 过滤黑名单
                    if any(lcc.lower() in airline.lower() for lcc in LCC_BLOCKLIST):
                        continue
                    
                    # 提取价格和时间
                    price = f["price"]["formatted"]
                    dep_time = f["legs"][0]["departure"][11:16]
                    
                    return {
                        "price": price,
                        "airline": airline,
                        "time": dep_time
                    }
                print(f"⚠️ {origin_code} 仅剩廉航或无合适航班")
            else:
                print(f"⚠️ {origin_code} 未查到数据 (API返回空)")
        else:
            print(f"❌ 接口报错: {response.text}")
            
    except Exception as e:
        print(f"❌ 程序异常: {e}")
        
    return None

def main():
    report = [f"✈️ **机票比价 (Flights Sky)**"]
    report.append(f"📅 日期: {DATE}<br>")
    
    has_any = False

    for code, name in ORIGINS.items():
        res = get_flight(code)
        if res:
            line = f"✅ **{name}**: <span style='color:red'>{res['price']}</span> ({res['airline']} {res['time']})"
            report.append(line)
            has_any = True
        else:
            report.append(f"❌ **{name}**: 未找到合适航班")
        
        # ⚠️ 防止请求过快
        time.sleep(5)

    if has_any:
        content = "<br>".join(report)
        print("正在发送微信通知...")
        requests.post("http://www.pushplus.plus/send", json={
            "token": PUSHPLUS_TOKEN,
            "title": f"机票比价: 2月28日去重庆",
            "content": content,
            "template": "html"
        })
        print("✅ 通知已发送")
    else:
        print("📭 没有查到任何有效航班")

if __name__ == "__main__":
    main()
