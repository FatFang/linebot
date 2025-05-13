from flask import Flask, request, abort, jsonify
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import *
import os
from datetime import datetime

import google.generativeai as genai

# Gemini 初始化
genai.configure(api_key="AIzaSyBGeDBaiupzch0WYImfJxj3KFCfzNVBpgY")  # 請替換為你自己的金鑰
gemini_model = genai.GenerativeModel('gemini-2.0-pro-exp')
gemini_chat = gemini_model.start_chat(history=[])


app = Flask(__name__)

# Channel Access Token
line_bot_api = LineBotApi('whq/sw9WG1zp449bgSbnPJxocde7bXv0VLTKw8B+HPXHEwSbzX80QEzAW6xO8nPQs2tPo0eytGsDwr6AuntQSLJpmCrMmHGX/Hw9de6LTAJF3FA0KCOGQqED7Z0JhjFUVMzQGFKeCTw2YtqPqX6BaAdB04t89/1O/w1cDnyilFU=')
# Channel Secret
handler = WebhookHandler('70b8cfa99b593164fd403293c2d5e25c')

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
    else:
        reply = TextSendMessage(text="我重複你的話:"+user_text)

    line_bot_api.reply_message(event.reply_token, reply)




if __name__ == "__main__":
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
