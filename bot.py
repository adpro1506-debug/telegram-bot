import os
import telebot
import mysql.connector
from datetime import datetime, timedelta
from flask import Flask, request

BOT_TOKEN = '8046489365:AAHAFBz4Ca07KcjqI0EJl76aIAu-rlVHw-4'
bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

def get_db():
    return mysql.connector.connect(
        host=os.environ.get('DB_HOST'),
        user=os.environ.get('DB_USER'),
        password=os.environ.get('DB_PASS'),
        database=os.environ.get('DB_NAME')
    )

def save_message(user_id, username, first_name, group_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        "INSERT INTO chat_logs (user_id, username, first_name, group_id, message_date) VALUES (%s, %s, %s, %s, %s)",
        (user_id, username, first_name, group_id, datetime.now())
    )
    db.commit()
    cursor.close()
    db.close()

@bot.message_handler(commands=['채팅'])
def my_stats(message):
    if message.chat.type == 'private':
        return
    user_id = message.from_user.id
    group_id = message.chat.id
    first_name = message.from_user.first_name or '사용자'

    db = get_db()
    cursor = db.cursor()

    today = datetime.now().date()
    cursor.execute("SELECT COUNT(*) FROM chat_logs WHERE user_id=%s AND group_id=%s AND DATE(message_date)=%s", (user_id, group_id, today))
    today_count = cursor.fetchone()[0]

    monday = today - timedelta(days=today.weekday())
    cursor.execute("SELECT COUNT(*) FROM chat_logs WHERE user_id=%s AND group_id=%s AND message_date>=%s", (user_id, group_id, monday))
    week_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM chat_logs WHERE user_id=%s AND group_id=%s AND YEAR(message_date)=YEAR(NOW()) AND MONTH(message_date)=MONTH(NOW())", (user_id, group_id))
    month_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM chat_logs WHERE user_id=%s AND group_id=%s", (user_id, group_id))
    total_count = cursor.fetchone()[0]

    cursor.close()
    db.close()

    text = f"📊 {first_name}님의 채팅 통계\n\n📅 오늘: {today_count}개\n📆 이번 주: {week_count}개\n🗓 이번 달: {month_count}개\n💬 전체: {total_count}개"
    bot.reply_to(message, text)

@bot.message_handler(commands=['채팅랭킹'])
def weekly_ranking(message):
    if message.chat.type == 'private':
        return
    group_id = message.chat.id
    today = datetime.now().date()
    monday = today - timedelta(days=today.weekday())
    sunday = monday + timedelta(days=6)

    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        "SELECT first_name, username, COUNT(*) as cnt FROM chat_logs WHERE group_id=%s AND message_date>=%s GROUP BY user_id ORDER BY cnt DESC LIMIT 5",
        (group_id, monday)
    )
    rows = cursor.fetchall()
    cursor.close()
    db.close()

    medals = ['🥇', '🥈', '🥉', '4️⃣', '5️⃣']
    text = f"🏆 주간 채팅 랭킹\n📅 {monday} ~ {sunday}\n\n"

    if not rows:
        text += "이번 주 채팅 기록이 없어요 😅"
    else:
        for i, row in enumerate(rows):
            name = row[0] or row[1] or '익명'
            text += f"{medals[i]} {name} — {row[2]}개\n"

    bot.reply_to(message, text)

@bot.message_handler(func=lambda m: m.chat.type in ['group', 'supergroup'])
def log_message(message):
    save_message(
        message.from_user.id,
        message.from_user.username or '',
        message.from_user.first_name or '',
        message.chat.id
    )

@app.route('/' + BOT_TOKEN, methods=['POST'])
def webhook():
    bot.process_new_updates([telebot.types.Update.de_json(request.stream.read().decode('utf-8'))])
    return 'OK', 200

@app.route('/')
def index():
    return 'Bot is running!', 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))