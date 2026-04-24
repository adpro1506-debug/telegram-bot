import os
import telebot
import psycopg2
from datetime import datetime, timedelta
from flask import Flask, request

BOT_TOKEN = '8046489365:AAHAFBz4Ca07KcjqI0EJl76aIAu-rlVHw-4'
bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

def get_db():
    return psycopg2.connect(os.environ.get('DATABASE_URL'))

def init_db():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chat_logs (
            id SERIAL PRIMARY KEY,
            user_id BIGINT NOT NULL,
            username VARCHAR(255),
            first_name VARCHAR(255),
            group_id BIGINT NOT NULL,
            message_date TIMESTAMP NOT NULL,
            created_at TIMESTAMP DEFAULT NOW()
        )
    """)
    db.commit()
    cursor.close()
    db.close()

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
    
@bot.message_handler(commands=['test'])
def test_handler(message):
    bot.reply_to(message, "봇 작동 중! ✅")
@bot.message_handler(commands=['채팅'])
def my_stats(message):
    if message.chat.type == 'private':
        return
    user_id = message.from_user.id
    group_id = message.chat.id
    first_name = message.from_user.first_name or '사용자'

    try:
        db = get_db()
        cursor = db.cursor()

        today = datetime.now().date()
        cursor.execute("SELECT COUNT(*) FROM chat_logs WHERE user_id=%s AND group_id=%s AND DATE(message_date)=%s", (user_id, group_id, today))
        today_count = cursor.fetchone()[0]

        monday = today - timedelta(days=today.weekday())
        cursor.execute("SELECT COUNT(*) FROM chat_logs WHERE user_id=%s AND group_id=%s AND message_date>=%s", (user_id, group_id, monday))
        week_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM chat_logs WHERE user_id=%s AND group_id=%s AND EXTRACT(YEAR FROM message_date)=EXTRACT(YEAR FROM NOW()) AND EXTRACT(MONTH FROM message_date)=EXTRACT(MONTH FROM NOW())", (user_id, group_id))
        month_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM chat_logs WHERE user_id=%s AND group_id=%s", (user_id, group_id))
        total_count = cursor.fetchone()[0]

        cursor.close()
        db.close()

        text = f"📊 {first_name}님의 채팅 통계\n\n📅 오늘: {today_count}개\n📆 이번 주: {week_count}개\n🗓 이번 달: {month_count}개\n💬 전체: {total_count}개"
        bot.reply_to(message, text)
    except Exception as e:
        print(f"my_stats error: {e}")
        bot.reply_to(message, "오류가 발생했어요 😢")

@bot.message_handler(commands=['채팅랭킹'])
def weekly_ranking(message):
    if message.chat.type == 'private':
        return
    group_id = message.chat.id
    today = datetime.now().date()
    monday = today - timedelta(days=today.weekday())
    sunday = monday + timedelta(days=6)

    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute(
            "SELECT first_name, username, COUNT(*) as cnt FROM chat_logs WHERE group_id=%s AND message_date>=%s GROUP BY user_id, first_name, username ORDER BY cnt DESC LIMIT 5",
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
    except Exception as e:
        print(f"weekly_ranking error: {e}")
        bot.reply_to(message, "오류가 발생했어요 😢")

@bot.message_handler(func=lambda m: m.chat.type in ['group', 'supergroup'])
def log_message(message):
    try:
        save_message(
            message.from_user.id,
            message.from_user.username or '',
            message.from_user.first_name or '',
            message.chat.id
        )
    except Exception as e:
        print(f"log_message error: {e}")

@app.route('/' + BOT_TOKEN, methods=['POST'])
def webhook():
    try:
        update = telebot.types.Update.de_json(request.stream.read().decode('utf-8'))
        bot.process_new_updates([update])
    except Exception as e:
        print(f"webhook error: {e}")
    return 'OK', 200

@app.route('/')
def index():
    return 'Bot is running!', 200

try:
    init_db()
    print("DB 초기화 성공!")
except Exception as e:
    print(f"DB init error: {e}")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
