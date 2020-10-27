import requests
import argparse
import googletrans
import random
from telegram.ext import Updater, MessageHandler, Filters
from telegram.ext import CallbackContext, CommandHandler
from telegram import ReplyKeyboardMarkup

# TOKEN = "1156352622:AAEo8fqFYKZet_jpcCW2SlnYWQRp-PzQGxw"
TOKEN = "1270714811:AAF9HfQldxlCZejjrwEwFm-AXN9fuzKtVms"

parser = argparse.ArgumentParser(description="Telegram bot for API testing.")
parser.add_argument('--api_hostname', default="localhost", help="ParlAI API hostname.")
parser.add_argument('--api_port', type=int, default=8080, help="ParlAI API port.")

args = parser.parse_args()
persona_file = "/home/azureuser/disk/ParlAI_M/data/blended_skill_talk/safe_personas.txt"
api_hostname = args.api_hostname
api_port = args.api_port
#api_uri = "http://{api_hostname}:{api_port}/api"
api_uri = f"http://localhost:8080/api"

translator = googletrans.Translator()

message_history = {}

def read_persona():
    num_lines = sum(1 for line in open(persona_file))
    f=open(persona_file);
    personas=f.readlines()
    f.close()
    persona_out = []
    n = random.sample(range(0,num_lines-1),3)
    for i in  n:
        index = personas[i].find('|')
        index2 = personas[i].find('|',index+1)
        out = "/set_p " + personas[i][0:index2]
        persona_out.append(out)
    return persona_out

def set_persona(update,context):
    # message_text = "your persona:" + persona 
    chat_id = update.message.chat_id
    message_history[chat_id] = []
    message_text = "[DONEEND]"
    response = requests.post(f'{api_uri}/send_message',
                             json={"message_text": message_text,
                                   "message_history": message_history[chat_id]})
    try:
        persona = send_response2(update,context, response)
        response = response.json()
        message_history[chat_id].append(response.get('text'))

        if "lang" in context.user_data:
            response["text"] = translate_message(response["text"],
                                                         src="en", dest=context.user_data["lang"]).text

        response["text"] = ""
        #send_response(update, context, response)
    except Exception as e:
        text = "We are unable to handle your request. Please try later."

        update.message.reply_text(text)
        raise e

def set_persona2(update,context):
    # message_text = "your persona:" + persona 
    chat_id = update.message.chat_id
    persona_text = update.message.text
    message_text = "your persona:" + persona_text[7:]
    print(message_text)
    message_history[chat_id] = []
    response = requests.post(f'{api_uri}/send_message',
                             json={"message_text": message_text,
                                   "message_history": message_history[chat_id]})
    try:
        response = response.json()
        message_history[chat_id].append(response.get('text'))

        if "lang" in context.user_data:
            response["text"] = translate_message(response["text"],
                                                         src="en", dest=context.user_data["lang"]).text

        send_response(update, context, response)
    except Exception as e:
        text = "We are unable to handle your request. Please try later."

        update.message.reply_text(text)
        raise e

def reset_conversation(update,context):
    text = "Resetting conversation"
    update.message.reply_text(text)
    message_text = "[DONE]"
    chat_id = update.message.chat_id
    message_history[chat_id] = [] 
    response = requests.post(f'{api_uri}/send_message',
                             json={"message_text": message_text,
                                   "message_history": message_history[chat_id]})
    try:
        response = response.json()
        message_history[chat_id].append(response.get('text'))

        if "lang" in context.user_data:
            response["text"] = translate_message(response["text"],
                                                         src="en", dest=context.user_data["lang"]).text

        send_response(update, context, response)
    except Exception as e:
        text = "We are unable to handle your request. Please try later."

        update.message.reply_text(text)
        raise e

def translate_message(message, src='auto', dest='en'):
    translation = translator.translate(message, src=src, dest=dest)

    return translation


def set_lang(update, context):
    try:
        lang = context.args[0]
        translation = translate_message("Language has set:", dest=lang).text + " " + lang

        update.message.reply_text(translation)
        context.user_data["lang"] = lang
    except Exception as e:
        text = "usage: /set_lang <language>"
        update.message.reply_text(text)


def send_response2(update, context, response):
    quick_replies = read_persona()
    
    print(quick_replies)
    text = "Resetting conversation, please select one of the personas in the quick reply"

    if quick_replies:
        keyboard = [quick_replies]
        markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)

        update.message.reply_text(text,
                                  reply_markup=markup)

        return
    update.message.reply_text(response.get('text'))


def send_response(update, context, response):
    quick_replies = response.get('quick_replies')
    
    if quick_replies:
        keyboard = [quick_replies]
        markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)

        update.message.reply_text(response.get('text'),
                                  reply_markup=markup)

        return
    update.message.reply_text(response.get('text'))


def send_message(update, context):
    chat_id = update.message.chat_id
    message_text = update.message.text

    if chat_id not in message_history:
        message_history[chat_id] = []

    message_history[chat_id].append(message_text)

    if "lang" in context.user_data:
        message_text = translate_message(message_text, src=context.user_data["lang"]).text

    response = requests.post(f'{api_uri}/send_message',
                             json={"message_text": message_text,
                                   "message_history": message_history[chat_id]})

    try:
        response = response.json()
        message_history[chat_id].append(response.get('text'))

        if "lang" in context.user_data:
            response["text"] = translate_message(response["text"],
                                                         src="en", dest=context.user_data["lang"]).text

        send_response(update, context, response)
    except Exception as e:
        text = "We are unable to handle your request. Please try later."

        update.message.reply_text(text)
        raise e


def help(update, context):
    message = f"ParlAI bot.\n"
    message += f"/set_lang <language> - set language.\n"
    message += f"/reset - resetting conversation.\n"
    message += f"/set_persona - set the bot's persona."
    message += "All messages will be passed to bot.\n"

    update.message.reply_text(message)


def main():
    updater = Updater(TOKEN, use_context=True)

    dp = updater.dispatcher

    text_handler = MessageHandler(Filters.text, send_message, pass_user_data=True)

    dp.add_handler(CommandHandler("help", help))
    dp.add_handler(CommandHandler("set_lang", set_lang, pass_user_data=True, pass_args=True))
    dp.add_handler(CommandHandler("reset",reset_conversation, pass_user_data=True, pass_args=True))
    dp.add_handler(CommandHandler("set_persona",set_persona, pass_user_data=True, pass_args=True))
    dp.add_handler(CommandHandler("set_p",set_persona2, pass_user_data=True, pass_args=True))

    dp.add_handler(text_handler)

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
