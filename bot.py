# bot.py - Telegram AI Summarizer / Enhancer Bot
# Monetizable with freemium (limited free summaries) + Telegram Stars or Stripe

import os
import logging
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from openai import OpenAI

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
# Optional: XAI_API_KEY for Grok

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

SYSTEM_PROMPT = """You are a helpful AI assistant. Summarize or enhance the user's text clearly and concisely.
For summaries: use bullet points. For rewrites: improve clarity and engagement."""

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 AI Summarizer Bot\n\n"
        "Send me any text, URL, or document and I'll summarize or enhance it.\n\n"
        "Commands:\n"
        "/summarize - Summarize the next message or reply\n"
        "/rewrite - Rewrite for clarity\n"
        "/expand - Add more detail\n\n"
        "Free tier: limited uses. Upgrade for unlimited."
    )

async def summarize_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args and not update.message.reply_to_message:
        await update.message.reply_text("Reply to a message or send text after /summarize")
        return
    text = " ".join(context.args) if context.args else update.message.reply_to_message.text
    await process_ai(update, text, "Summarize this text clearly in bullet points:")

async def rewrite_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = " ".join(context.args) if context.args else (update.message.reply_to_message.text if update.message.reply_to_message else "")
    if not text:
        await update.message.reply_text("Provide text to rewrite.")
        return
    await process_ai(update, text, "Rewrite this text to be clearer, more professional, and engaging:")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text and len(text) > 50:
        await process_ai(update, text, "Provide a concise summary of the following text:")

async def process_ai(update: Update, text: str, instruction: str):
    if not client:
        await update.message.reply_text("Bot not configured with AI API key.")
        return
    
    # Simple free tier: track in user_data (use DB for production)
    user_id = update.effective_user.id
    uses = context.user_data.get("uses", 0)
    if uses >= 5:  # Free limit
        await update.message.reply_text("Free limit reached. Upgrade for unlimited access (coming soon / Stars).")
        return
    context.user_data["uses"] = uses + 1

    await update.message.reply_text("Processing with AI...")
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"{instruction}\n\n{text[:8000]}"}
            ],
            temperature=0.5,
            max_tokens=800
        )
        result = response.choices[0].message.content
        await update.message.reply_text(result)
    except Exception as e:
        logger.error(e)
        await update.message.reply_text(f"Error: {str(e)[:200]}")

def main():
    if not TELEGRAM_TOKEN:
        raise ValueError("TELEGRAM_BOT_TOKEN required")
    
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("summarize", summarize_command))
    app.add_handler(CommandHandler("rewrite", rewrite_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    logger.info("Bot starting...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
