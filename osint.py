import os
import telebot

# Environment variable se bot token lein (ya direct apna token daal dein)
BOT_TOKEN = os.environ.get("BOT_TOKEN", "YOUR_BOT_TOKEN")
bot = telebot.TeleBot(BOT_TOKEN)

# Channel Join Request Handler
@bot.chat_join_request_handler()
def accept_join_request(message):
    try:
        # 1. Join request approve karne wali line
        bot.approve_chat_join_request(chat_id=message.chat.id, user_id=message.from_user.id)
        
        # 2. Welcome message bhejne ke liye code
        welcome_text = f"Hello {message.from_user.first_name}! 👋 /start \n\njoin request accepted Welcome!"
        bot.send_message(chat_id=message.from_user.id, text=welcome_text)
        
        print(f"Successfully approved join request for user {message.from_user.id}")
    except Exception as e:
        print(f"Error approving join request: {e}")

# Optional: Simple /start command check karne ke liye ki bot chal raha hai ya nahi
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Bot is active and running for channel join requests! ✅")

if __name__ == "__main__":
    print("Bot is starting...")
    bot.infinity_polling()
    
