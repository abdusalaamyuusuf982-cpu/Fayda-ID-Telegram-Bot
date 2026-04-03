import os
import re
import cv2
from PIL import Image, ImageDraw, ImageFont
import pytesseract
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ContextTypes
from config import BOT_TOKEN, ADMIN_ID
from services.user_manager import get_or_create_user, update_user_credits, update_user_mode, increment_user_generated, update_user_trials
from services.image_processor import process_image_to_png
from models import ProcessingMode

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user = get_or_create_user(user_id)
    
    keyboard = [
        ["📷 Upload Photo"],
        ["📊 My Status", "💳 Get Package"],
        ["🎨 Change Mode", "🔙 Back"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    await update.message.reply_text(
        "👋 Welcome to Fayda ID Style Bot 🇪🇹\n\n"
        "🎁 You have 2 FREE trials!\n\n"
        "Send LEFT ID → get RIGHT style PNG\n\n"
        "Use menu 👇",
        reply_markup=reply_markup
    )

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user = get_or_create_user(user_id)
    
    is_admin = str(user_id) == str(ADMIN_ID)
    
    if not is_admin and user.trials <= 0 and user.credits <= 0:
        await update.message.reply_text("❌ No credits or free trials.")
        return

    message = await update.message.reply_text("✅ Photo received!\nDownloading...")
    
    photo = update.message.photo[-1]
    file = await photo.get_file()
    
    os.makedirs("temp", exist_ok=True)
    file_path = f"temp/id_{user_id}.jpg"
    await file.download_to_drive(file_path)
    
    await message.edit_text("⏳ Processing image to clean PNG...")
    
    try:
        # Process to PNG based on user preference
        png_path = process_image_to_png(file_path, user_id, user.mode)
        
        # Send PNG
        with open(png_path, "rb") as png:
            await update.message.reply_document(
                png,
                filename=f"Fayda_Digital_ID_{user.mode.value.upper()}.png",
                caption="✅ Your clean printable PNG is ready!\nSend another photo when you buy more credits."
            )
            
        # Deduct
        if not is_admin:
            if user.trials > 0:
                update_user_trials(user_id, -1)
            else:
                update_user_credits(user_id, -1)
        increment_user_generated(user_id)
        
        # Cleanup
        if os.path.exists(png_path):
            os.remove(png_path)
            
    except Exception as e:
        logger.error(f"Error processing image for user {user_id}: {e}")
        await message.edit_text("❌ An error occurred during processing. Your credits have not been deducted.")
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)

async def my_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user = get_or_create_user(user_id)
    is_admin = str(user_id) == str(ADMIN_ID)
    
    trials_text = "`Unlimited`" if is_admin else f"`{user.trials}`"
    credits_text = "`Unlimited`" if is_admin else f"`{user.credits}`"
    
    await update.message.reply_text(
        f"📊 *Your Status*\n\n"
        f"🎁 Free Trials: {trials_text}\n"
        f"💰 Balance: {credits_text} credits\n"
        f"🖼️ Total IDs Generated: `{user.total_generated}`\n"
        f"⚙️ Current Mode: `{'Color' if user.mode == ProcessingMode.COLOR else 'Black & White'}`",
        parse_mode="Markdown"
    )

async def get_package(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("10 IDs - 200 Birr", callback_data="buy_10")],
        [InlineKeyboardButton("50 IDs - 1000 Birr", callback_data="buy_50")],
        [InlineKeyboardButton("100 IDs - 2000 Birr", callback_data="buy_100")]
    ]
    await update.message.reply_text(
        "💳 Send payment to:\n📱 0965003122 (CBE Birr)\n\n"
        "After payment, send screenshot here with the word 'payment' in the caption.",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def upload_photo_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📷 Please send me a clear photo of your ID card now. I am ready to process it!")

async def mode_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🎨 Color Mode", callback_data="mode_color")],
        [InlineKeyboardButton("⚫⚪ Black & White", callback_data="mode_bw")]
    ]
    
    if update.message:
        await update.message.reply_text("Choose processing mode:", reply_markup=InlineKeyboardMarkup(keyboard))
    elif update.callback_query:
        await context.bot.send_message(chat_id=update.callback_query.from_user.id, text="Choose processing mode:", reply_markup=InlineKeyboardMarkup(keyboard))

async def handle_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id

    photo = update.message.photo[-1]
    file = await photo.get_file()

    os.makedirs("payments", exist_ok=True)
    path = f"payments/{user_id}.jpg"
    await file.download_to_drive(path)

    try:
        # OCR
        img = cv2.imread(path)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        gray = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)[1]

        text = pytesseract.image_to_string(gray)
        logger.info(f"OCR TEXT: {text}")

        # DETECT AMOUNT
        amounts = re.findall(r"\d{3,4}", text)
        detected = None
        for amt in amounts:
            if amt in ["200", "1000", "2000"]:
                detected = int(amt)
                break

        if not ADMIN_ID:
            await update.message.reply_text("❌ ADMIN_ID not configured in variables.")
            return

        # Send to admin with buttons
        keyboard = [
            [
                InlineKeyboardButton("✅ Approve 10", callback_data=f"approve_10_{user_id}"),
                InlineKeyboardButton("✅ Approve 50", callback_data=f"approve_50_{user_id}"),
                InlineKeyboardButton("✅ Approve 100", callback_data=f"approve_100_{user_id}")
            ],
            [
                InlineKeyboardButton("❌ Reject", callback_data=f"reject_{user_id}")
            ]
        ]
        
        await context.bot.send_photo(
            chat_id=ADMIN_ID,
            photo=photo.file_id,
            caption=(
                f"💰 Payment Request\n"
                f"👤 {user.first_name}\n"
                f"🆔 {user_id}\n"
                f"🔍 Detected: {detected}"
            ),
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

        await update.message.reply_text("⏳ Waiting for admin approval...")
    except Exception as e:
        logger.error(f"OCR Error: {e}")
        await update.message.reply_text("❌ Error processing payment.")
    finally:
        if os.path.exists(path):
            os.remove(path)

async def admin_actions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data.split("_")
    action = data[0]
    user_id = int(data[-1])

    if action == "approve":
        credits = int(data[1])
        update_user_credits(user_id, credits)

        await context.bot.send_message(
            chat_id=user_id,
            text=f"✅ Payment approved! {credits} credits added."
        )
        await query.edit_message_caption(caption=query.message.caption + f"\n\n✅ APPROVED: {credits} credits")
    elif action == "reject":
        await context.bot.send_message(
            chat_id=user_id,
            text="❌ Payment rejected. Send clear screenshot."
        )
        await query.edit_message_caption(caption=query.message.caption + "\n\n❌ REJECTED")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.lower() if update.message.text else ""

    if "status" in text:
        await my_status(update, context)
    elif "package" in text:
        await get_package(update, context)
    elif "mode" in text:
        await mode_command(update, context)
    elif "upload" in text:
        await upload_photo_command(update, context)
    elif "back" in text:
        await start(update, context)
        
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    
    if query.data.startswith("buy_"):
        await query.message.reply_text(
            "📥 Send payment screenshot after paying to:\n📱 0965003122. Ensure caption contains the word 'payment'."
        )
    elif query.data == "change_mode":
        await mode_command(update, context)
    elif query.data.startswith("mode_"):
        mode = ProcessingMode.COLOR if query.data == "mode_color" else ProcessingMode.BW
        update_user_mode(user_id, mode)
        await context.bot.send_message(chat_id=user_id, text=f"✅ Mode changed to {'Color' if mode == ProcessingMode.COLOR else 'Black & White'}.")

def main():
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN is missing in environment variables.")
        return

    app = Application.builder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("my_status", my_status))
    app.add_handler(CommandHandler("get_package", get_package))
    app.add_handler(CommandHandler("mode", mode_command))
    app.add_handler(CommandHandler("upload", upload_photo_command))
    
    app.add_handler(MessageHandler(filters.PHOTO & filters.CaptionRegex("(?i)payment"), handle_payment))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    app.add_handler(CallbackQueryHandler(admin_actions, pattern="^(approve|reject)"))
    app.add_handler(CallbackQueryHandler(button_callback))
    
    logger.info("🤖 Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
