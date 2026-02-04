import os
import requests
import time

# --- 1. 配置钥匙 ---
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

# 🚫 廉航黑名单 (过滤掉不需要的)
LCC_BLOCKLIST = [
    "Spring", "春秋", "9C",
    "West", "西部", "PN",
    "9 Air", "九元", "AQ",
    "Lucky", "祥鹏", "8L",
    "Urumqi", "乌鲁木齐", "UQ",
    "Tianjin", "天津", "GS",
    "Capital", "首都", "JD",
    "China United", "联合", "KN",
    "Chengdu", "成都航空", "EU"
]

def get_flight_list(origin_code):
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
        "locale": "zh-CN",
        "adults": "1"
    }

    valid_flights = []

    try:
        print(f"📡 正在拉取全量数据: {origin_code} -> {DEST}...")
        response = requests.get(url, headers=headers, params=querystring, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            itineraries = data.get("data", {}).get("itineraries", [])
            
            for f in itineraries:
                try:
                    leg = f["legs"][0]
                    airline = leg["carriers"]["marketing"][0]["name"]
                    
                    # 1. 过滤廉航
                    if any(lcc.lower() in airline.lower() for lcc in LCC_BLOCKLIST):
                        continue 

                    # 2. 提取信息
                    price_obj = f.get("price", {})
                    price_raw = price_obj.get("raw", 99999)
                    price_fmt = price_obj.get("formatted") or f"¥{price_raw}"
                    
                    dep_time = leg.get("departure", "")[11:16]
                    arr_time = leg.get("arrival", "")[11:16]
                    
                    valid_flights.append({
                        "price_val": price_raw,
                        "price_str": price_fmt,
                        "airline": airline,
                        "dep": dep_time,
                        "arr": arr_time
                    })
                except:
                    continue
            
            # 按价格从低到高排序
            valid_flights.sort(key=lambda x: x["price_val"])
            return valid_flights
        else:
            print(f"❌ 接口报错: {response.status_code}")
            return []
    except Exception as e:
        print(f"❌ 程序异常: {e}")
        return []

def main():
    report = [f"✈️ **机票全列表比价 ({DATE})**"]
    report.append("<small>含机建燃油 | 已过滤廉航</small>")
    
    found_any = False

    for code, name in ORIGINS.items():
        print(f"正在分析 {name} 航班...")
        flights = get_flight_list(code)
        
        report.append(f"<br>📍 **{name} 出发**")
        
        if flights:
            found_any = True
            # 只取前 8 个结果，防止消息过长被微信截断
            for f in flights[:8]:
                line = f"• <span style='color:#d32f2f'>{f['price_str']}</span> | {f['airline']}<br>"
                line += f"&nbsp;&nbsp;<small>🕒 {f['dep']} ➔ {f['arr']}</small>"
                report.append(line)
        else:
            report.append("  <span style='color:#999'>暂无合适全服务航班</span>")
        
        time.sleep(5) # 频率保护

    if found_any:
        content = "<br>".join(report)
        print("准备推送全列表...")
        requests.post("http://www.pushplus.plus/send", json={
            "token": PUSHPLUS_TOKEN,
            "title": f"机票全列表: {DATE} 重庆",
            "content": content,
            "template": "html"
        })
        print("✅ 推送成功")
    else:
        print("📭 全网无票，不发送。")

if __name__ == "__main__":
    main()
