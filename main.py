import os
import requests
import time
import json

# --- 配置区域 ---
API_KEY = os.environ["RAPIDAPI_KEY"]
PUSHPLUS_TOKEN = os.environ["PUSHPLUS_TOKEN"]
DESTINATION = "CKG"   # 重庆
DATE = "2026-02-28"   # 目标日期
ORIGINS = { "JJN": "泉州", "FOC": "福州", "XMN": "厦门" }

# 简化的调试版黑名单
LCC_BLOCKLIST = ["Spring", "West Air", "9 Air", "Lucky", "Urumqi"]

def get_flight_price(origin_code):
    url = "https://sky-scrapper.p.rapidapi.com/api/v1/flights/searchFlights"
    querystring = {
        "originSkyId": origin_code,
        "destinationSkyId": DESTINATION,
        "originEntityId": origin_code,
        "destinationEntityId": DESTINATION,
        "date": DATE,
        "currency": "CNY",
        "market": "CN",
        "countryCode": "CN",
        "adults": "1",
        "sortBy": "price_low"
    }
    headers = {
        "X-RapidAPI-Key": API_KEY,
        "X-RapidAPI-Host": "sky-scrapper.p.rapidapi.com"
    }

    print(f"🔍 正在请求 API: {origin_code} -> {DESTINATION} ({DATE})")
    
    try:
        response = requests.get(url, headers=headers, params=querystring)
        
        # --- 🕵️‍♂️ 侦探部分：看看 API 到底回了什么 ---
        print(f"📡 状态码: {response.status_code}")
        
        if response.status_code != 200:
            print(f"❌ API 请求失败！错误信息: {response.text}")
            return None

        data = response.json()
        
        # 打印部分原始数据来看看结构
        if "data" not in data:
            print(f"⚠️ API 返回数据格式奇怪: {json.dumps(data)}")
            return None
            
        itineraries = data.get("data", {}).get("itineraries", [])
        print(f"🎫 这一趟查到了 {len(itineraries)} 个航班")

        if not itineraries:
            print("⚠️ 航班列表是空的！(可能是该日期没票，或 API 没抓到)")
            return None

        # 遍历一下前3个航班看看是什么
        print("   --- 前3个航班预览 ---")
        for i, flight in enumerate(itineraries[:3]):
            airline = flight["legs"][0]["carriers"]["marketing"][0]["name"]
            price = flight["price"]["formatted"]
            print(f"   [{i+1}] 航司: {airline} | 价格: {price}")
        print("   ---------------------")

        # 正常寻找逻辑
        for flight in itineraries:
            carrier_name = flight["legs"][0]["carriers"]["marketing"][0]["name"]
            # 简单检查黑名单
            is_lcc = False
            for lcc in LCC_BLOCKLIST:
                if lcc.lower() in carrier_name.lower():
                    is_lcc = True
                    break
            
            if is_lcc:
                continue 
            
            # 找到结果
            return {
                "price": flight["price"]["raw"],
                "info": f"{carrier_name} {flight['price']['formatted']}"
            }
            
        print("⚠️ 查到了航班，但全都被黑名单过滤掉了")
        return None

    except Exception as e:
        print(f"❌ 代码报错: {e}")
        return None

def main():
    print("🚀 开始调试运行...")
    has_result = False
    
    for code, city_name in ORIGINS.items():
        print(f"\n------ 处理 {city_name} ------")
        result = get_flight_price(code)
        if result:
            print(f"✅ 成功找到: {result['info']}")
            has_result = True
        time.sleep(1)

    if not has_result:
        print("\n❌ 最终结果: 所有城市都没有有效数据。")

if __name__ == "__main__":
    main()
