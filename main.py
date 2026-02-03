import os
import requests
import time

# --- 1. 配置钥匙 ---
API_KEY = os.environ["RAPIDAPI_KEY"]
PUSHPLUS_TOKEN = os.environ["PUSHPLUS_TOKEN"]

# --- 2. 航线配置 ---
# ⚠️ 注意：如果 2026 年查不到票，建议先改成 2025 年测试效果
DATE = "2026-02-28" 
DEST = "CKG"
ORIGINS = {"JJN": "泉州", "FOC": "福州", "XMN": "厦门"}

# 廉航黑名单 (暂时缩减，防止误杀)
LCC_BLOCKLIST = ["Spring", "West Air", "9 Air", "Lucky"]

def get_flight(origin_code):
    HOST = "flights-sky.p.rapidapi.com"
    url = f"https://{HOST}/flights/search-one-way"
    
    headers = {
        "x-rapidapi-key": API_KEY,
        "x-rapidapi-host": HOST
    }

    querystring = {
        "fromEntityId": origin_code,
        "toEntityId": DEST,
        "departDate": DATE,
        "currency": "CNY",
        "market": "CN",
        "adults": "1"
    }

    try:
        print(f"📡 正在查询 {origin_code} -> {DEST}...")
        response = requests.get(url, headers=headers, params=querystring, timeout=20)
        
        if response.status_code == 200:
            data = response.json()
            # 这里的 .get() 方式可以防止程序因为找不到 key 而崩溃
            itineraries = data.get("data", {}).get("itineraries", [])
            
            if not itineraries:
                print(f"⚠️ {origin_code} 接口返回成功但没有航班数据 (可能日期太远未放票)")
                return None

            for f in itineraries:
                try:
                    # 灵活提取航司名字
                    legs = f.get("legs", [{}])[0]
                    carriers = legs.get("carriers", {}).get("marketing", [{}])
                    airline = carriers[0].get("name", "未知航司")
                    
                    # 灵活提取价格 (尝试三种常见的嵌套方式)
                    price_data = f.get("price", {})
                    price_str = price_data.get("formatted") or price_data.get("raw") or "价格待定"
                    
                    # 提取时间
                    dep_time = legs.get("departure", "----")[11:16]

                    # 检查黑名单
                    is_lcc = any(lcc.lower() in airline.lower() for lcc in LCC_BLOCKLIST)
                    
                    if is_lcc:
                        continue # 跳过廉航
                    
                    return {
                        "price": price_str,
                        "airline": airline,
                        "time": dep_time
                    }
                except Exception as inner_e:
                    print(f"🔎 某条航班解析跳过: {inner_e}")
                    continue
            
            print(f"⚠️ {origin_code} 剩下的全是不含行李的廉航")
        else:
            print(f"❌ 接口报错: {response.status_code}")
    except Exception as e:
        print(f"❌ 严重异常: {e}")
    return None

def main():
    report = [f"✈️ **机票比价 (2026-02-28)**"]
    has_any = False

    for code, name in ORIGINS.items():
        res = get_flight(code)
        if res:
            line = f"✅ **{name}**: <span style='color:red'>{res['price']}</span> ({res['airline']} {res['time']})"
            report.append(line)
            has_any = True
        else:
            report.append(f"❌ **{name}**: 暂无合适全服务航班")
        time.sleep(5)

    # 无论是否查到，都发个微信，方便调试
    content = "<br>".join(report)
    print("正在推送微信...")
    requests.post("http://www.pushplus.plus/send", json={
        "token": PUSHPLUS_TOKEN,
        "title": "机票比价日报",
        "content": content,
        "template": "html"
    })
    print("✅ 任务完成")

if __name__ == "__main__":
    main()
