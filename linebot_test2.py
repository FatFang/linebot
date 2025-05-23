from flask import Flask, request, abort, jsonify
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import *
import os
from datetime import datetime
import requests
import google.generativeai as genai

# Gemini 初始化
genai.configure(api_key=".")  # 請替換為你自己的金鑰
gemini_model = genai.GenerativeModel('gemini-2.0-flash-lite')
gemini_chat = gemini_model.start_chat(history=[])


app = Flask(__name__)

# Channel Access Token
line_bot_api = LineBotApi('.')
# Channel Secret
handler = WebhookHandler('.')

from flask import jsonify, request

# 對話歷史資料（模擬資料庫）
history_log = []
history_counter = 1  # 每則訊息唯一編號

@app.route("/api/history", methods=['GET'])
def get_history():
    return jsonify({"history": history_log}), 200

@app.route("/api/history", methods=['DELETE'])
def delete_all_history():
    history_log.clear()
    return jsonify({"message": "All history deleted!!!"}), 200

@app.route("/api/history/<int:msg_id>", methods=['GET'])
def get_history_by_id(msg_id):
    result = next((msg for msg in history_log if msg['id'] == msg_id), None)
    if result:
        return jsonify(result), 200
    return jsonify({"error": "Message not found"}), 404

@app.route("/api/history/<int:msg_id>", methods=['DELETE'])
def delete_history_by_id(msg_id):
    global history_log
    new_history = [msg for msg in history_log if msg['id'] != msg_id]
    if len(new_history) == len(history_log):
        return jsonify({"error": "Message not found"}), 404
    history_log = new_history
    return jsonify({"message": f"Message {msg_id} deleted"}), 200


@app.route("/")
def index():
    return "LINE Webhook is active!"

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    global history_counter
    user_text = event.message.text.lower()

    # 儲存對話紀錄
    history_log.append({
        "id": history_counter,
        "text": user_text,
        "timestamp": datetime.now().isoformat()
    })
    history_counter += 1

    reply = None

    if any(kw in user_text for kw in ['可愛', '貼圖', '搞笑']):
        reply = StickerSendMessage(
            package_id='446',
            sticker_id='1989'
        )
    elif any(kw in user_text for kw in ['圖片', 'image']):
        reply = ImageSendMessage(
            original_content_url='https://i.imgur.com/ExdKOOz.png',
            preview_image_url='https://i.imgur.com/ExdKOOz.png'
        )
    elif any(kw in user_text for kw in ['影片', 'video']):
        reply = VideoSendMessage(
            original_content_url='https://www.w3schools.com/html/mov_bbb.mp4',
            preview_image_url='https://peach.blender.org/wp-content/uploads/title_anouncement.jpg'
        )
    elif any(kw in user_text for kw in ['座標', 'location']):
        reply = LocationSendMessage(
            title="這是地點",
            address="台北101",
            latitude=25.033964,
            longitude=121.564468
        )
    elif '問題是' in user_text:
        gemini_response = gemini_chat.send_message(user_text)
        reply_text = gemini_response.text.strip()
        reply = TextSendMessage(text=reply_text)
    elif '天氣' in user_text:
        try:
            weather_url = "https://opendata.cwa.gov.tw/fileapi/v1/opendataapi/F-C0032-022?Authorization=rdec-key-123-45678-011121314&format=JSON"
            weather_response = requests.get(weather_url, timeout=5)
            weather_data = weather_response.json()

            parameters = weather_data["cwaopendata"]["dataset"]["parameterSet"]["parameter"]
            weather_text = "\n".join(p["parameterValue"] for p in parameters)

            prompt = f"""根據下列氣象描述，請用一句自然語言分析「桃園市明日天氣」的摘要與建議：{weather_text}請回答：1. 是否要帶傘？2. 會熱嗎？3. 要穿什麼？4. 是否適合戶外活動？5.其他建議?"""

            gemini_response = gemini_chat.send_message(prompt)
            reply = TextSendMessage(text=gemini_response.text.strip())
        except Exception as e:
            reply = TextSendMessage(text="無法取得天氣資訊，請稍後再試。")
    else:
        reply = TextSendMessage(text="我重複你的話，因為你是光 你是神 你是唯一的神話:"+user_text)

    line_bot_api.reply_message(event.reply_token, reply)




if __name__ == "__main__":
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)



#https://1cb4-122-116-207-128.ngrok-free.app/api/history
