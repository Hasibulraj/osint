import os
import sqlite3
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import telebot

# ============ CONFIGURATION ============
BOT_TOKEN = os.environ.get("BOT_TOKEN", "YOUR_BOT_TOKEN")
ADMIN_ID = 5989928539  # Aapki Admin ID

bot = telebot.TeleBot(BOT_TOKEN)

# ============ DATABASE SETUP ============
def init_db():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        first_name TEXT
    )''')
    conn.commit()
    conn.close()

def add_user(user_id, first_name):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO users (user_id, first_name) VALUES (?, ?)", (user_id, first_name))
    conn.commit()
    conn.close()

def get_all_users():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("SELECT user_id FROM users")
    users = c.fetchall()
    conn.close()
    return [user[0] for user in users]

# ============ KEEPALIVE SERVER (Render ke liye) ============
class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(b"Bot is running successfully!")
    def log_message(self, format, *args):
        pass

def start_keepalive_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), HealthHandler)
    server.serve_forever()

def run_keepalive_in_thread():
    server_thread = threading.Thread(target=start_keepalive_server, daemon=True)
    server_thread.start()

# ============ JOIN REQUEST HANDLER ============
@bot.chat_join_request_handler()
def accept_join_request(message):
    try:
        user_id = message.from_user.id
        first_name = message.from_user.first_name or "User"
        
        # User ko database me save karo broadcast ke liye
        add_user(user_id, first_name)
        
        # Join request approve karo
        bot.approve_chat_join_request(chat_id=message.chat.id, user_id=user_id)
        
        # Welcome message bhejo
        welcome_text = f"Hello {first_name}! 👋\n\nYour join request has been accepted. Welcome!"
        bot.send_message(chat_id=user_id, text=welcome_text)
        
        print(f"Approved join request for user {user_id}")
    except Exception as e:
        print(f"Error approving join request: {e}")

# ============ START COMMAND ============
@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    first_name = message.from_user.first_name or "User"
    add_user(user_id, first_name)
    
    if user_id == ADMIN_ID:
        bot.reply_to(message, "Hello Admin! ✅\n\nSabhi users ko message bhejne ke liye use karein:\n`/broadcast [Aapka Message]`", parse_mode='Markdown')
    else:
        bot.reply_to(message, "Bot is active and running for channel join requests! ✅")

# ============ BROADCAST COMMAND (Admin Only) ============
@bot.message_handler(commands=['broadcast'])
def broadcast_message(message):
    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "❌ You are not authorized to use this command!")
        return
    
    # Message extract karo (/broadcast ke baad ka text)
    text_to_broadcast = message.text.replace('/broadcast', '').strip()
    if not text_to_broadcast:
        bot.reply_to(message, "⚠️ Please provide a message to broadcast!\nExample: `/broadcast Hello everyone!`", parse_mode='Markdown')
        return
    
    users = get_all_users()
    success = 0
    failed = 0
    
    status_msg = bot.reply_to(message, f"📢 Broadcasting to {len(users)} users...")
    
    for user_id in users:
        try:
            bot.send_message(user_id, f"📢 **Announcement:**\n\n{text_to_broadcast}", parse_mode='Markdown')
            success += 1
        except Exception as e:
            failed += 1
            print(f"Failed to send broadcast to {user_id}: {e}")
            
    bot.edit_message_text(
        chat_id=message.chat.id,
        message_id=status_msg.message_id,
        text=f"✅ **Broadcast Completed!**\n\nSuccessfully sent: `{success}`\nFailed (Blocked bot): `{failed}`",
        parse_mode='Markdown'
    )

if __name__ == "__main__":
    init_db()
    run_keepalive_in_thread()
    print("Bot is starting with Keepalive & Broadcast system...")
    bot.infinity_polling()
