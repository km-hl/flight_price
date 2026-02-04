import os
import requests
import time

# --- 1. 配置钥匙 ---
API_KEY = os.environ["RAPIDAPI_KEY"]
PUSHPLUS_TOKEN = os.environ["PUSHPLUS_TOKEN"]

# --- 2. 航线配置 ---
DEST = "CKG"   # 重庆
DATE = "2026-02-28" # 如果查不到，记得改成 2025-02-28 试试
ORIGINS = {
    "JJN": "泉州",
    "FOC": "福州",
    "XMN": "厦门"
}

# 🚫 终极黑名单 (中英文 + 代码 + 关键词)
# 只要航司名字里包含下面任意一个词，就会被剔除
LCC_BLOCKLIST = [
    "Spring", "春秋", "9C",
    "West", "西部", "PN", "China West", # 专门针对西部航空加强过滤
    "9 Air", "九元", "AQ",
    "Lucky", "祥鹏", "8L",
    "Urumqi", "乌鲁木齐", "UQ",
    "Tianjin", "天津", "GS",
    "Capital", "首都", "JD",
    "China United", "联合", "KN",
    "Chengdu", "成都航空", "EU"
]

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
        "locale": "zh-CN",
        "adults": "1"
    }

    try:
        print(f"📡 正在查询 {origin_code} -> {DEST}...")
        response = requests.get(url, headers=headers, params=querystring, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            itineraries = data.get("data", {}).get("itineraries", [])
            
            if not itineraries:
                return {"error": "无航班"}

            # 遍历所有结果，找到第一个非廉航
            for f in itineraries:
                # 获取航司名称
                try:
                    airline = f["legs"][0]["carriers"]["marketing"][0]["name"]
                except:
                    continue

                # 🚫 核心过滤逻辑
                is_lcc = False
                for block_word in LCC_BLOCKLIST:
                    # 统一转小写进行匹配，防止 Case 差异
                    if block_word.lower() in airline.lower():
                        is_lcc = True
                        # print(f"  🔪 过滤掉廉航: {airline}") # 调试用
                        break
                
                if is_lcc:
                    continue 

                # ✅ 找到合适的了！
                try:
                    # 尝试获取价格，如果没有 formatted 就拿 raw 拼一下
                    price_obj = f.get("price", {})
                    price = price_obj.get("formatted")
                    if not price:
                        price = f"¥{price_obj.get('raw')}"
                    
                    dep_time = f["legs"][0]["departure"][11:16]
                    
                    return {
                        "price": price,
                        "airline": airline,
                        "time": dep_time
                    }
                except:
                    continue
            
            return {"error": "仅剩廉航"}
            
        else:
            print(f"❌ 接口报错: {response.status_code}")
    except Exception as e:
        print(f"❌ 程序异常: {e}")
        
    return None

def main():
    report = [f"✈️ **机票比价 ({DATE})**"]
    report.append("<small>注: 价格通常为含税总价</small><br>")
    
    has_valid_flight = False

    for code, name in ORIGINS.items():
        res = get_flight(code)
        
        if res and "price" in res:
            line = f"✅ **{name}**: <span style='color:#d32f2f;font-weight:bold'>{res['price']}</span>"
            line += f" ({res['airline']} {res['time']})"
            report.append(line)
            has_valid_flight = True
        elif res and res.get("error") == "仅剩廉航":
            report.append(f"⚠️ **{name}**: 全是廉航(已过滤)")
        else:
            report.append(f"❌ **{name}**: 暂无航班")
        
        time.sleep(5)

    # 只有当查到至少一张有效票，或者全是廉航被过滤时，才发通知
    # 避免完全报错时发空消息
    content = "<br>".join(report)
    
    print("正在推送微信...")
    requests.post("http://www.pushplus.plus/send", json={
        "token": PUSHPLUS_TOKEN,
        "title": "机票比价日报",
        "content": content,
        "template": "html"
    })
    print("✅ 完成")

if __name__ == "__main__":
    main()
