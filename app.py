import os
import telebot
import psycopg2
from datetime import datetime, timedelta
from flask import Flask, request

BOT_TOKEN = '8046489365:AAHAFBz4Ca07KcjqI0EJl76aIAu-rlVHw-4'
bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

AFFILIATE_TEXT = """❤️카지노❤️
[평생제휴] 1️⃣렛츠뱃 https://t.me/gamte59/31
[평생제휴] 2️⃣예스뱃 https://t.me/gamte59/28
[도파민제휴]3️⃣지엑스뱃 https://t.me/gamte59/44
[도파민제휴]4️⃣케이비씨겜 https://t.me/gamte59/46
[도파민제휴]5️⃣블록체인바카라 https://t.me/gamte59/49
[도파민제휴]6️⃣썬뱃 https://t.me/gamte59/51

❤️급전❤️
[도파민제휴]1️⃣OR급전 https://t.me/gamte59/16
[도파민제휴]2️⃣프리티켓 https://t.me/gamte59/33

❤️장집❤️
[도파민제휴]1️⃣미호 장집 https://t.me/gamte59/37

❤️반환팀❤️
[도파민제휴]1️⃣울프 반환팀 https://t.me/gamte59/39

❤️충전 계좌매입❤️
[평생제휴]1️⃣저승사자 https://t.me/gamte59/42
[도파민제휴]2️⃣김여포 https://t.me/gamte59/58"""

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

        elif message.text and '/노래' in message.text:
            query = message.text.replace('/노래', '').strip()
            if not query:
                bot.reply_to(message, "🎵 검색어를 입력해주세요!\n예시: /노래 아이유 좋은날")
                return
            bot.reply_to(message, "🔍 검색 중...")
            try:
                import yt_dlp
                ydl_opts = {'quiet': True, 'skip_download': True}
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    results = ydl.extract_info(f"ytsearch1:{query}", download=False)
                    video = results['entries'][0]
                    title = video['title']
                    link = f"https://youtube.com/watch?v={video['id']}"
                    duration = video.get('duration_string', '알 수 없음')
                    channel = video.get('uploader', '알 수 없음')
                    text = f"🎵 {title}\n"
                    text += f"👤 {channel}\n"
                    text += f"⏱ {duration}\n\n"
                    text += f"🔗 {link}"
                    bot.reply_to(message, text)
            except Exception as e:
                print(f"youtube search error: {e}")
                bot.reply_to(message, "😢 검색 중 오류가 발생했어요!")

        elif message.text and '/제휴' in message.text:
            bot.reply_to(message, AFFILIATE_TEXT, disable_web_page_preview=True)

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
