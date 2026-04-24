import os
import telebot
import psycopg2
import random
from io import BytesIO
from PIL import Image
from datetime import datetime, timedelta
from flask import Flask, request

BOT_TOKEN = '8046489365:AAHAFBz4Ca07KcjqI0EJl76aIAu-rlVHw-4'
bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

CARDS = list(range(1, 11)) * 2

def get_card_name(card):
    names = {1: '일', 2: '이', 3: '삼', 4: '사', 5: '오',
             6: '육', 7: '칠', 8: '팔', 9: '구', 10: '십'}
    return names[card]

def calc_score(c1, c2):
    return (c1 + c2) % 10

def get_hand_name(c1, c2):
    cards = sorted([c1, c2])
    if cards == [9, 4]:
        return ("구사", 100)
    if c1 == c2:
        if c1 == 10:
            return ("장땡", 99)
        return (f"{get_card_name(c1)}땡", 90 + c1)
    if cards == [1, 2]:
        return ("알리", 84)
    if cards == [1, 4]:
        return ("독사", 83)
    if cards == [9, 3]:
        return ("구삼", 82)
    if cards == [10, 3]:
        return ("장삼", 81)
    if cards == [3, 6]:
        return ("세륙", 80)
    if 10 in cards:
        other = c1 if c2 == 10 else c2
        if other in [4, 5, 6, 7, 8]:
            if calc_score(c1, c2) == 4:
                return ("갑오", 85)
    score = calc_score(c1, c2)
    if score == 0:
        return ("망통", 0)
    return (f"{score}끗", score)

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

@bot.message_handler(func=lambda m: True)
def handle_all(message):
    try:
        print(f"메시지 받음: '{message.text}' / 타입: {message.chat.type}")

        if message.text and '/test' in message.text:
            bot.reply_to(message, "봇 작동 중! ✅")

        elif message.text and '/섯다' in message.text:
            first_name = message.from_user.first_name or '사용자'
            deck = CARDS.copy()
            random.shuffle(deck)
            user_cards = [deck.pop(), deck.pop()]
            bot_cards = [deck.pop(), deck.pop()]

            user_hand, user_power = get_hand_name(user_cards[0], user_cards[1])
            bot_hand, bot_power = get_hand_name(bot_cards[0], bot_cards[1])

            if user_power > bot_power:
                result = f"🏆 {first_name}님이 이겼어요!"
            elif user_power < bot_power:
                result = f"🤖 봇이 이겼어요!"
            else:
                result = "🤝 비겼어요!"

            card_size = (200, 280)
            gap = 20
            total_width = card_size[0] * 4 + gap * 3
            total_height = card_size[1]
            result_img = Image.new('RGB', (total_width, total_height), (50, 50, 50))

            for i, card_num in enumerate(user_cards + bot_cards):
                path = f"cards/{card_num}.png"
                img = Image.open(path).convert('RGB')
                img = img.resize(card_size, Image.LANCZOS)
                x = i * (card_size[0] + gap)
                result_img.paste(img, (x, 0))

            buf = BytesIO()
            result_img.save(buf, format='PNG')
            buf.seek(0)

            caption = f"👤 {first_name}님 → {user_hand}\n"
            caption += f"🤖 봇 → {bot_hand}\n\n"
            caption += f"{result}"

            bot.send_photo(message.chat.id, buf, caption=caption, reply_to_message_id=message.message_id)

        elif message.text and '/채팅랭킹' in message.text:
            if message.chat.type == 'private':
                return
            group_id = message.chat.id
            today = datetime.now().date()
            monday = today - timedelta(days=today.weekday())
            sunday = monday + timedelta(days=6)
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
            text = f"╔══ 🏆 주간 랭킹 ══╗\n"
            text += f"  📅 {monday.strftime('%m/%d')} ~ {sunday.strftime('%m/%d')}\n\n"
            if not rows:
                text += "  채팅 기록이 없어요 😅\n"
            else:
                for i, row in enumerate(rows):
                    name = row[0] or row[1] or '익명'
                    text += f"  {medals[i]} {name:<10} {row[2]}개\n"
            text += "╚══════════════════╝"
            bot.reply_to(message, text)

        elif message.text and '/채팅' in message.text:
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
            cursor.execute("SELECT COUNT(*) FROM chat_logs WHERE user_id=%s AND group_id=%s AND EXTRACT(YEAR FROM message_date)=EXTRACT(YEAR FROM NOW()) AND EXTRACT(MONTH FROM message_date)=EXTRACT(MONTH FROM NOW())", (user_id, group_id))
            month_count = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM chat_logs WHERE user_id=%s AND group_id=%s", (user_id, group_id))
            total_count = cursor.fetchone()[0]
            cursor.close()
            db.close()
            text = f"╔══ 📊 채팅 통계 ══╗\n"
            text += f"  👤 {first_name}님\n\n"
            text += f"  ☀️ 오늘       {today_count}개\n"
            text += f"  📆 이번 주   {week_count}개\n"
            text += f"  🗓 이번 달   {month_count}개\n"
            text += f"  💬 전체      {total_count}개\n\n"
            text += f"  🎀 오늘도 열심히 채팅했어요!\n"
            text += "╚══════════════════╝"
            bot.reply_to(message, text)

        elif message.chat.type in ['group', 'supergroup']:
            save_message(
                message.from_user.id,
                message.from_user.username or '',
                message.from_user.first_name or '',
                message.chat.id
            )

    except Exception as e:
        import traceback
        print(f"handle_all error: {e}")
        print(traceback.format_exc())

@app.route('/' + BOT_TOKEN, methods=['POST'])
def webhook():
    try:
        json_str = request.stream.read().decode('utf-8')
        update = telebot.types.Update.de_json(json_str)
        if update.message:
            handle_all(update.message)
        print("처리 완료!")
    except Exception as e:
        import traceback
        print(f"webhook error: {e}")
        print(traceback.format_exc())
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
