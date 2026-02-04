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

# 🚫 廉航黑名单
LCC_BLOCKLIST = ["Spring", "春秋", "West Air", "西部", "9 Air", "九元", "Lucky", "祥鹏", "Urumqi", "乌鲁木齐", "Tianjin", "天津", "Capital", "首都", "China United", "联合"]

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
        print(f"📡 正在拉取 {origin_code} 全量数据...")
        response = requests.get(url, headers=headers, params=querystring, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            itineraries = data.get("data", {}).get("itineraries", [])
            
            for f in itineraries:
                try:
                    leg = f["legs"][0]
                    # 获取航司和航班号
                    carrier_info = leg["carriers"]["marketing"][0]
                    airline = carrier_info["name"]
                    flight_no = leg["segments"][0].get("flightNumber", "")
                    carrier_code = carrier_info.get("displayCode", "")
                    
                    full_flight_code = f"{carrier_code}{flight_no}" if flight_no else airline

                    # 1. 过滤廉航
                    if any(lcc.lower() in airline.lower() for lcc in LCC_BLOCKLIST):
                        continue 

                    # 2. 提取价格
                    price_obj = f.get("price", {})
                    price_raw = price_obj.get("raw", 99999)
                    price_fmt = price_obj.get("formatted") or f"¥{price_raw}"
                    
                    # 3. 提取时间
                    dep_time = leg.get("departure", "")[11:16]
                    arr_time = leg.get("arrival", "")[11:16]
                    
                    valid_flights.append({
                        "price_val": price_raw,
                        "price_str": price_fmt,
                        "airline": airline,
                        "flight_code": full_flight_code,
                        "dep": dep_time,
                        "arr": arr_time
                    })
                except Exception as e:
                    continue
            
            # 排序并返回
            valid_flights.sort(key=lambda x: x["price_val"])
            return valid_flights
        else:
            print(f"❌ 报错: {response.status_code}")
            return []
    except Exception as e:
        print(f"❌ 异常: {e}")
        return []

def main():
    report = [f"✈️ **机票全列表 ({DATE})**"]
    report.append("<small>含税参考价 | 航班号辅助核对</small>")
    
    found_any = False

    for code, name in ORIGINS.items():
        flights = get_flight_list(code)
        report.append(f"<br>📍 **{name} 出发**")
        
        if flights:
            found_any = True
            # 展示前 10 条，确保涵盖山东、东海、厦航等
            for f in flights[:10]:
                line = f"• <span style='color:#d32f2f;font-weight:bold'>{f['price_str']}</span> | **{f['airline']}** ({f['flight_code']})<br>"
                line += f"&nbsp;&nbsp;<small>🕒 {f['dep']} ➔ {f['arr']}</small>"
                report.append(line)
        else:
            report.append("  <span style='color:#999'>暂无合适非廉航航班</span>")
        
        time.sleep(5)

    if found_any:
        content = "<br>".join(report)
        requests.post("http://www.pushplus.plus/send", json={
            "token": PUSHPLUS_TOKEN,
            "title": f"机票监控: {DATE} 重庆",
            "content": content,
            "template": "html"
        })
        print("✅ 推送成功")
    else:
        print("📭 无效数据")

if __name__ == "__main__":
    main()
