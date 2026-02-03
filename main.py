import os
import requests
import time

# --- 1. 配置区域 ---
# 从 GitHub 仓库的 Secrets 里读取之前存好的钥匙
API_KEY = os.environ["RAPIDAPI_KEY"]
PUSHPLUS_TOKEN = os.environ["PUSHPLUS_TOKEN"]

# 设定日期和目的地
DESTINATION = "CKG"   # 重庆江北
DATE = "2026-02-28"   # 你的目标日期

# 设定出发地
ORIGINS = {
    "JJN": "泉州",
    "FOC": "福州",
    "XMN": "厦门"
}

# 🚫 廉航黑名单 (如果不想要这些航司，就在这里添加)
# 只要航司名字里包含这些词，就会被过滤掉
LCC_BLOCKLIST = [
    "Spring",       # 春秋航空
    "West Air",     # 西部航空 (重庆大本营，很多没行李的票)
    "China United", # 中联航
    "9 Air",        # 九元航空
    "Lucky",        # 祥鹏航空
    "Urumqi",       # 乌鲁木齐航空
    "Tianjin",      # 天津航空 (部分特价票无行李，建议屏蔽)
]

# --- 2. 功能函数 ---

def send_wechat_msg(title, content):
    """发送微信通知"""
    url = "http://www.pushplus.plus/send"
    data = {
        "token": PUSHPLUS_TOKEN,
        "title": title,
        "content": content,
        "template": "html"
    }
    requests.post(url, json=data)

def get_flight_price(origin_code):
    """查询单个城市的航班"""
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
        "sortBy": "price_low" # 让 API 按价格从低到高给数据
    }

    headers = {
        "X-RapidAPI-Key": API_KEY,
        "X-RapidAPI-Host": "sky-scrapper.p.rapidapi.com"
    }

    try:
        response = requests.get(url, headers=headers, params=querystring)
        data = response.json()
        
        # 检查数据是否有效
        if "data" in data and "itineraries" in data["data"]:
            itineraries = data["data"]["itineraries"]
            
            # 🔄 遍历航班列表，寻找非廉航
            for flight in itineraries:
                # 获取航司名称
                carrier_name = flight["legs"][0]["carriers"]["marketing"][0]["name"]
                
                # 检查是否是廉航
                is_lcc = False
                for lcc in LCC_BLOCKLIST:
                    if lcc.lower() in carrier_name.lower():
                        is_lcc = True
                        break
                
                if is_lcc:
                    continue # 如果是廉航，跳过，看下一条
                
                # ✅ 找到了符合条件的航班
                price_str = flight["price"]["formatted"] # 例如 "¥500"
                price_raw = flight["price"]["raw"]       # 例如 500
                time_str = flight["legs"][0]["departure"][11:16] # 截取时间
                
                return {
                    "price_str": price_str,
                    "price": price_raw,
                    "airline": carrier_name,
                    "time": time_str
                }
            
            return {"error": "仅有廉航"}
        else:
            return None

    except Exception as e:
        print(f"出错: {e}")
        return None

def main():
    report = []
    lowest_price = 99999
    best_city = ""

    # 构建消息头部
    report.append(f"✈️ **福建 -> 重庆 (非廉航)**")
    report.append(f"📅 {DATE}<br>")

    # 循环查询三个城市
    for code, city_name in ORIGINS.items():
        print(f"正在查询 {city_name}...")
        result = get_flight_price(code)
        
        if result and "price" in result:
            # 找到票了
            line = f"✅ **{city_name}**: <span style='color:#d32f2f;font-weight:bold'>{result['price_str']}</span>"
            line += f" ({result['airline']} {result['time']})"
            report.append(line)
            
            if result['price'] < lowest_price:
                lowest_price = result['price']
                best_city = city_name

        elif result and "error" in result:
            report.append(f"⚠️ **{city_name}**: 全是廉航，已过滤")
        else:
            report.append(f"❌ **{city_name}**: 查无航班")
        
        # 暂停一秒，防止请求太快
        time.sleep(1)

    # 汇总
    report.append("<br>------------------")
    if lowest_price < 99999:
        report.append(f"💡 推荐从 **{best_city}** 出发")
        
        # 发送微信
        content = "<br>".join(report)
        send_wechat_msg(f"机票日报: 最低 {lowest_price}元", content)
        print("微信推送已发送")
    else:
        print("没有查到有效数据，不发送通知")

if __name__ == "__main__":
    main()
