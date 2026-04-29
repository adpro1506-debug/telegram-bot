import os
import random
import telebot
import psycopg2
import urllib.parse
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
[도마민제휴]7️⃣우루스카지노 https://t.me/gamte59/60

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
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS points (
            id SERIAL PRIMARY KEY,
            user_id BIGINT NOT NULL,
            group_id BIGINT NOT NULL,
            first_name VARCHAR(255),
            username VARCHAR(255),
            point INTEGER DEFAULT 0,
            last_attendance DATE,
            UNIQUE(user_id, group_id)
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS refill_logs (
            id SERIAL PRIMARY KEY,
            user_id BIGINT NOT NULL,
            group_id BIGINT NOT NULL,
            first_name VARCHAR(255),
            username VARCHAR(255),
            refill_date DATE NOT NULL
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS highlow_games (
            id SERIAL PRIMARY KEY,
            user_id BIGINT NOT NULL,
            group_id BIGINT NOT NULL,
            current_card INTEGER NOT NULL,
            bet INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT NOW()
        )
    """)
    db.commit()
    cursor.close()
    db.close()

def get_point(user_id, group_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT point FROM points WHERE user_id=%s AND group_id=%s", (user_id, group_id))
    row = cursor.fetchone()
    cursor.close()
    db.close()
    return row[0] if row else 0

def update_point(user_id, group_id, first_name, username, amount):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("""
        INSERT INTO points (user_id, group_id, first_name, username, point)
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (user_id, group_id)
        DO UPDATE SET point = points.point + %s, first_name=%s, username=%s
    """, (user_id, group_id, first_name, username, amount, amount, first_name, username))
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

def card_emoji(num):
    cards = {1:'🂡 A', 2:'🂢 2', 3:'🂣 3', 4:'🂤 4', 5:'🂥 5',
             6:'🂦 6', 7:'🂧 7', 8:'🂨 8', 9:'🂩 9', 10:'🂪 10',
             11:'🂫 J', 12:'🂭 Q', 13:'🂮 K'}
    return cards.get(num, str(num))

@bot.message_handler(func=lambda m: True)
def handle_all(message):
    try:
        print(f"메시지 받음: '{message.text}' / 타입: {message.chat.type}")
        text = message.text or ''
        user_id = message.from_user.id
        group_id = message.chat.id
        first_name = message.from_user.first_name or '사용자'
        username = message.from_user.username or ''
        today = datetime.now().date()

        # ==================== /test ====================
        if '/test' in text:
            bot.reply_to(message, "봇 작동 중! ✅")

        # ==================== /노래 ====================
        elif '/노래' in text:
            query = text.replace('/노래', '').strip()
            if not query:
                bot.reply_to(message, "🎵 검색어를 입력해주세요!\n예시: /노래 아이유 좋은날")
                return
            encoded = urllib.parse.quote(query)
            youtube_url = f"https://www.youtube.com/results?search_query={encoded}"
            bot.reply_to(message, f"🎵 {query}\n\n🔗 유튜브 검색 결과:\n{youtube_url}")

        # ==================== /제휴 ====================
        elif '/제휴' in text:
            bot.reply_to(message, AFFILIATE_TEXT, disable_web_page_preview=True)

        # ==================== /출석 ====================
        elif '/출석' in text:
            if message.chat.type == 'private':
                return
            db = get_db()
            cursor = db.cursor()
            cursor.execute("SELECT last_attendance FROM points WHERE user_id=%s AND group_id=%s", (user_id, group_id))
            row = cursor.fetchone()

            if row and row[0] == today:
                cursor.close()
                db.close()
                bot.reply_to(message, "⏰ 오늘 이미 출석했어요!\n자정(00:00)이 지나면 다시 출석할 수 있어요 😊")
                return

            cursor.execute("""
                INSERT INTO points (user_id, group_id, first_name, username, point, last_attendance)
                VALUES (%s, %s, %s, %s, 100, %s)
                ON CONFLICT (user_id, group_id)
                DO UPDATE SET point = points.point + 100, last_attendance=%s, first_name=%s, username=%s
            """, (user_id, group_id, first_name, username, today, today, first_name, username))
            db.commit()

            cursor.execute("SELECT point FROM points WHERE user_id=%s AND group_id=%s", (user_id, group_id))
            total = cursor.fetchone()[0]
            cursor.close()
            db.close()

            bot.reply_to(message,
                f"╔══ ✅ 출석 완료 ══╗\n"
                f"  👤 {first_name}님\n\n"
                f"  🎁 획득: 100포인트\n"
                f"  💰 잔여: {total}포인트\n"
                f"  🔄 리셋: 매일 자정 00:00\n"
                f"╚══════════════════╝"
            )

        # ==================== /리필 ====================
        elif '/리필' in text:
            if message.chat.type == 'private':
                return
            db = get_db()
            cursor = db.cursor()

            cursor.execute("""
                SELECT COUNT(*) FROM refill_logs
                WHERE user_id=%s AND group_id=%s AND refill_date=%s
            """, (user_id, group_id, today))
            count = cursor.fetchone()[0]

            if count >= 5:
                cursor.close()
                db.close()
                bot.reply_to(message, "⚠️ 오늘 리필을 5번 모두 사용했어요!\n자정(00:00)이 지나면 다시 사용할 수 있어요 😊")
                return

            cursor.execute("""
                INSERT INTO refill_logs (user_id, group_id, first_name, username, refill_date)
                VALUES (%s, %s, %s, %s, %s)
            """, (user_id, group_id, first_name, username, today))
            db.commit()
            cursor.close()
            db.close()

            update_point(user_id, group_id, first_name, username, 100)
            new_point = get_point(user_id, group_id)
            remaining = 5 - (count + 1)

            bot.reply_to(message,
                f"╔══ 🔄 리필 완료 ══╗\n"
                f"  👤 {first_name}님\n\n"
                f"  🎁 획득: 100포인트\n"
                f"  💰 잔여: {new_point}포인트\n"
                f"  📊 오늘 남은 리필: {remaining}회\n"
                f"  🔄 리셋: 매일 자정 00:00\n"
                f"╚══════════════════╝"
            )

        # ==================== /포인트랭킹 ====================
        elif '/포인트랭킹' in text:
            if message.chat.type == 'private':
                return
            db = get_db()
            cursor = db.cursor()
            cursor.execute("""
                SELECT first_name, username, point
                FROM points
                WHERE group_id=%s
                ORDER BY point DESC
                LIMIT 5
            """, (group_id,))
            rows = cursor.fetchall()
            cursor.close()
            db.close()

            medals = ['🥇', '🥈', '🥉', '4️⃣', '5️⃣']
            result = "╔══ 💰 포인트 랭킹 ══╗\n\n"
            if not rows:
                result += "  포인트 기록이 없어요 😅\n"
            else:
                for i, row in enumerate(rows):
                    name = row[0] or row[1] or '익명'
                    result += f"  {medals[i]} {name:<10} {row[2]}포인트\n"
            result += "╚══════════════════╝"
            bot.reply_to(message, result)

        # ==================== /포인트 ====================
        elif '/포인트' in text:
            if message.chat.type == 'private':
                return
            point = get_point(user_id, group_id)
            bot.reply_to(message,
                f"╔══ 💰 포인트 ══╗\n"
                f"  👤 {first_name}님\n\n"
                f"  💰 잔여: {point}포인트\n"
                f"╚══════════════════╝"
            )

        # ==================== /게임 ====================
        elif text.strip() in ['/게임', '/게임@dopamin_ranking_bot']:
            bot.reply_to(message,
                "🎮 게임 목록\n\n"
                "🎰 /슬롯 [배팅] - 슬롯머신\n"
                "🎡 /룰렛 [배팅] - 룰렛\n"
                "✌️ /가위바위보 [가위/바위/보] - 가위바위보\n"
                "🃏 /하이로우 [배팅] - 하이로우\n\n"
                "⚠️ 최소 참가비: 20포인트"
            )

        # ==================== /하이로우 ====================
        elif '/하이로우' in text:
            if message.chat.type == 'private':
                return
            parts = text.split()

            # 진행중인 게임 확인
            db = get_db()
            cursor = db.cursor()
            cursor.execute("""
                SELECT id, current_card, bet FROM highlow_games
                WHERE user_id=%s AND group_id=%s
                ORDER BY created_at DESC LIMIT 1
            """, (user_id, group_id))
            game = cursor.fetchone()

            # 높음/낮음 선택한 경우
            if game and len(parts) >= 2 and parts[1] in ['높음', '낮음']:
                game_id, current_card, bet = game
                choice = parts[1]
                next_card = random.randint(1, 13)

                # 게임 삭제
                cursor.execute("DELETE FROM highlow_games WHERE id=%s", (game_id,))
                db.commit()
                cursor.close()
                db.close()

                point = get_point(user_id, group_id)
                if point < bet:
                    bot.reply_to(message, f"💸 포인트가 부족해요!\n현재 포인트: {point}포인트")
                    return

                if next_card == current_card:
                    result_text = "😅 같은 숫자! 무승부!"
                    won = 0
                elif (choice == '높음' and next_card > current_card) or \
                     (choice == '낮음' and next_card < current_card):
                    result_text = "🎉 정답! 이겼어요!"
                    won = bet
                    update_point(user_id, group_id, first_name, username, bet)
                else:
                    result_text = "💀 틀렸어요! 졌어요!"
                    won = -bet
                    update_point(user_id, group_id, first_name, username, -bet)

                new_point = get_point(user_id, group_id)
                bot.reply_to(message,
                    f"╔══ 🃏 하이로우 ══╗\n"
                    f"  이전 카드: {card_emoji(current_card)}\n"
                    f"  다음 카드: {card_emoji(next_card)}\n\n"
                    f"  {result_text}\n\n"
                    f"  배팅: {bet}포인트\n"
                    f"  {'획득: +' + str(won) if won > 0 else '무승부!' if won == 0 else '손실: ' + str(won)}포인트\n"
                    f"  잔여: {new_point}포인트\n"
                    f"╚══════════════════╝"
                )
                return

            # 새 게임 시작
            if len(parts) < 2 or not parts[1].isdigit():
                cursor.close()
                db.close()
                bot.reply_to(message,
                    "🃏 사용법: /하이로우 [배팅포인트]\n"
                    "예시: /하이로우 100\n\n"
                    "카드를 받은 후:\n"
                    "/하이로우 높음 → 다음 카드가 높을 것 같을 때\n"
                    "/하이로우 낮음 → 다음 카드가 낮을 것 같을 때\n\n"
                    "⚠️ 최소 배팅: 20포인트"
                )
                return

            bet = int(parts[1])
            if bet < 20:
                cursor.close()
                db.close()
                bot.reply_to(message, "⚠️ 최소 배팅은 20포인트예요!")
                return

            point = get_point(user_id, group_id)
            if point < bet:
                cursor.close()
                db.close()
                bot.reply_to(message, f"💸 포인트가 부족해요!\n현재 포인트: {point}포인트")
                return

            # 기존 게임 삭제 후 새 게임 시작
            cursor.execute("DELETE FROM highlow_games WHERE user_id=%s AND group_id=%s", (user_id, group_id))
            current_card = random.randint(1, 13)
            cursor.execute("""
                INSERT INTO highlow_games (user_id, group_id, current_card, bet)
                VALUES (%s, %s, %s, %s)
            """, (user_id, group_id, current_card, bet))
            db.commit()
            cursor.close()
            db.close()

            bot.reply_to(message,
                f"╔══ 🃏 하이로우 ══╗\n"
                f"  카드: {card_emoji(current_card)}\n\n"
                f"  다음 카드가 높을까요 낮을까요?\n\n"
                f"  👆 /하이로우 높음\n"
                f"  👇 /하이로우 낮음\n\n"
                f"  배팅: {bet}포인트\n"
                f"╚══════════════════╝"
            )

        # ==================== /슬롯 ====================
        elif '/슬롯' in text:
            if message.chat.type == 'private':
                return
            parts = text.split()
            if len(parts) < 2 or not parts[1].isdigit():
                bot.reply_to(message, "🎰 사용법: /슬롯 [배팅포인트]\n예시: /슬롯 100")
                return

            bet = int(parts[1])
            if bet < 20:
                bot.reply_to(message, "⚠️ 최소 배팅은 20포인트예요!")
                return

            point = get_point(user_id, group_id)
            if point < bet:
                bot.reply_to(message, f"💸 포인트가 부족해요!\n현재 포인트: {point}포인트")
                return

            symbols = ['🍋', '🍒', '🍇', '⭐', '7️⃣', '💎']
            weights = [30, 25, 20, 15, 7, 3]
            s1 = random.choices(symbols, weights=weights)[0]
            s2 = random.choices(symbols, weights=weights)[0]
            s3 = random.choices(symbols, weights=weights)[0]

            if s1 == s2 == s3:
                if s1 == '💎':
                    multiplier, result_text = 50, "💎 JACKPOT! 50배!"
                elif s1 == '7️⃣':
                    multiplier, result_text = 10, "7️⃣ 럭키세븐! 10배!"
                elif s1 == '⭐':
                    multiplier, result_text = 7, "⭐ 스타! 7배!"
                else:
                    multiplier, result_text = 5, "🎉 3개 일치! 5배!"
                won = bet * multiplier - bet
            elif s1 == s2 or s2 == s3 or s1 == s3:
                multiplier, result_text = 1.5, "✨ 2개 일치! 1.5배!"
                won = int(bet * 1.5) - bet
            else:
                multiplier, result_text = 0, "💀 꽝!"
                won = -bet

            update_point(user_id, group_id, first_name, username, won)
            new_point = get_point(user_id, group_id)

            bot.reply_to(message,
                f"╔══ 🎰 슬롯머신 ══╗\n"
                f"  [ {s1} | {s2} | {s3} ]\n\n"
                f"  {result_text}\n\n"
                f"  배팅: {bet}포인트\n"
                f"  {'획득: +' if won > 0 else '손실: '}{won}포인트\n"
                f"  잔여: {new_point}포인트\n"
                f"╚══════════════════╝"
            )

        # ==================== /룰렛 ====================
        elif '/룰렛' in text:
            if message.chat.type == 'private':
                return
            parts = text.split()
            if len(parts) < 2 or not parts[1].isdigit():
                bot.reply_to(message, "🎡 사용법: /룰렛 [배팅포인트]\n예시: /룰렛 100")
                return

            bet = int(parts[1])
            if bet < 20:
                bot.reply_to(message, "⚠️ 최소 배팅은 20포인트예요!")
                return

            point = get_point(user_id, group_id)
            if point < bet:
                bot.reply_to(message, f"💸 포인트가 부족해요!\n현재 포인트: {point}포인트")
                return

            roulette = [
                ('💀 꽝', 0, 55),
                ('🔵 1.5배', 1.5, 20),
                ('🟢 2배', 2, 15),
                ('🟡 3배', 3, 7),
                ('🔴 5배', 5, 2),
                ('💎 10배', 10, 1),
            ]
            idx = random.choices(range(len(roulette)), weights=[r[2] for r in roulette])[0]
            label, multiplier, _ = roulette[idx]
            won = int(bet * multiplier) - bet if multiplier > 0 else -bet

            update_point(user_id, group_id, first_name, username, won)
            new_point = get_point(user_id, group_id)

            bot.reply_to(message,
                f"╔══ 🎡 룰렛 ══╗\n"
                f"  결과: {label}\n\n"
                f"  배팅: {bet}포인트\n"
                f"  {'획득: +' if won > 0 else '손실: '}{won}포인트\n"
                f"  잔여: {new_point}포인트\n"
                f"╚══════════════════╝"
            )

        # ==================== /가위바위보 ====================
        elif '/가위바위보' in text:
            if message.chat.type == 'private':
                return

            point = get_point(user_id, group_id)
            if point < 20:
                bot.reply_to(message, f"💸 포인트가 부족해요!\n참가비: 20포인트\n현재 포인트: {point}포인트")
                return

            choices = ['✊ 바위', '✌️ 가위', '🖐 보']
            user_choice = None
            for c in choices:
                if c.split()[1] in text:
                    user_choice = c
                    break

            if not user_choice:
                bot.reply_to(message,
                    "✌️ 사용법: /가위바위보 [가위/바위/보]\n"
                    "예시: /가위바위보 가위\n\n"
                    "⚠️ 참가비: 20포인트\n"
                    "  이기면 40포인트 획득!"
                )
                return

            bot_choice = random.choice(choices)
            update_point(user_id, group_id, first_name, username, -20)

            if user_choice == bot_choice:
                result_text, won = "🤝 비겼어요!", 0
                update_point(user_id, group_id, first_name, username, 20)
            elif (user_choice == '✊ 바위' and bot_choice == '✌️ 가위') or \
                 (user_choice == '✌️ 가위' and bot_choice == '🖐 보') or \
                 (user_choice == '🖐 보' and bot_choice == '✊ 바위'):
                result_text, won = "🎉 이겼어요!", 20
                update_point(user_id, group_id, first_name, username, 40)
            else:
                result_text, won = "💀 졌어요!", -20

            new_point = get_point(user_id, group_id)
            bot.reply_to(message,
                f"╔══ ✌️ 가위바위보 ══╗\n"
                f"  나:  {user_choice}\n"
                f"  봇:  {bot_choice}\n\n"
                f"  {result_text}\n\n"
                f"  {'획득: +' + str(won) if won > 0 else '참가비 반환!' if won == 0 else '손실: ' + str(won)}포인트\n"
                f"  잔여: {new_point}포인트\n"
                f"╚══════════════════╝"
            )

        # ==================== /채팅랭킹 ====================
        elif '/채팅랭킹' in text:
            if message.chat.type == 'private':
                return
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
            result = f"╔══ 🏆 주간 랭킹 ══╗\n"
            result += f"  📅 {monday.strftime('%m/%d')} ~ {sunday.strftime('%m/%d')}\n\n"
            if not rows:
                result += "  채팅 기록이 없어요 😅\n"
            else:
                for i, row in enumerate(rows):
                    name = row[0] or row[1] or '익명'
                    result += f"  {medals[i]} {name:<10} {row[2]}개\n"
            result += "╚══════════════════╝"
            bot.reply_to(message, result)

        # ==================== /채팅 ====================
        elif '/채팅' in text:
            if message.chat.type == 'private':
                return
            db = get_db()
            cursor = db.cursor()
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
            result = f"╔══ 📊 채팅 통계 ══╗\n"
            result += f"  👤 {first_name}님\n\n"
            result += f"  ☀️ 오늘       {today_count}개\n"
            result += f"  📆 이번 주   {week_count}개\n"
            result += f"  🗓 이번 달   {month_count}개\n"
            result += f"  💬 전체      {total_count}개\n\n"
            result += f"  🎀 오늘도 열심히 채팅했어요!\n"
            result += "╚══════════════════╝"
            bot.reply_to(message, result)

        # ==================== 메시지 기록 ====================
        elif message.chat.type in ['group', 'supergroup']:
            save_message(user_id, username, first_name, group_id)

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
