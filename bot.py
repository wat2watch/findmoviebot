from telegram.ext import Updater, CommandHandler, InlineQueryHandler
from telegram import InlineQueryResultArticle, InputTextMessageContent, InlineKeyboardButton, InlineKeyboardMarkup
import telegram
from uuid import uuid4
import pymongo

from utils import list_users, make_movie_details_message, make_similar_movies_message
from movie import Movie, autocomplete, FindMovieError
from config import MAIN_TOKEN, TEST_TOKEN
import os

admins = [117053315]

is_server = os.environ.get('ISSERVER', False)

updater = Updater(TEST_TOKEN if not is_server else MAIN_TOKEN, workers=32, use_context=True)
dispatcher = updater.dispatcher

reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("Search 🔎", switch_inline_query_current_chat='')]])

myclient = pymongo.MongoClient("mongodb://localhost:27017/")
mydb = myclient["findmoviebot"]
mycol = mydb["users"]

help_gif = 'CgACAgQAAxkBAAIU1l-is4sLMvearUo_e-f-6WQvb7j0AALICAACt_8ZUbGDsAABaXNXYR4E'


def start(update, context):
    uid = update.message.from_user.id
    firstname = update.message.from_user.first_name
    update.message.reply_text('Welcome <b>{}</b>,\nI recommend movies similar to the ones you like 🙄🍿📺\nSearch for your favorite movie and select it from the list 👇'.format(firstname), reply_markup=reply_markup, parse_mode=telegram.ParseMode.HTML)
    user = {'chat_id': uid, 'firstname': firstname, 'lastname': update.message.from_user.last_name, 'username': update.message.from_user.username, 'blocked': False}
    mycol.update_one({'chat_id': uid}, {'$setOnInsert': user}, upsert=True)

def inlinequery(update, context):
    term = update.inline_query.query
    if not term:
        return
    try:
        movies = autocomplete(term)
    except FindMovieError as error:
        if error.code == 404:
            update.inline_query.answer([InlineQueryResultArticle(id=uuid4(), title='No results found ...', input_message_content=InputTextMessageContent('404'))])
        else:
            update.inline_query.answer([InlineQueryResultArticle(id=uuid4(), title='500 Internal Serevr Error !', input_message_content=InputTextMessageContent('500'))])
        return
    results = [InlineQueryResultArticle(id=uuid4(), title=movie['label'], thumb_url='https://bestsimilar.com'+movie['thumb'], input_message_content=InputTextMessageContent('/FindLike '+movie['url'].replace('/movies/', ''))) for movie in movies]
    update.inline_query.answer(results)

def FindMovies(update, context):
    status_message = context.bot.sendMessage(chat_id=update.message.chat_id, text='Searching for similar movies ...')
    movie_label = update.message.text.split()[-1]
    try:
        movie = Movie(movie_label)
        movie.make()
    except FindMovieError as error:
        if error.code == 404:
            context.bot.sendMessage(chat_id=update.message.chat_id, text='Movie not found 🤷‍♂️\nAnother movie ? 🙄', reply_markup=reply_markup, parse_mode=telegram.ParseMode.HTML)
        else:
            context.bot.sendMessage(chat_id=update.message.chat_id, text='500 Internal Serevr Error !')
        return
    context.bot.sendPhoto(chat_id=update.message.chat_id, photo=movie.thumb, caption=make_movie_details_message(movie), parse_mode=telegram.ParseMode.HTML)
    second_reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("Search Another Movie 🔎", switch_inline_query_current_chat='')]])
    context.bot.sendMessage(chat_id=update.message.chat_id, text=make_similar_movies_message(movie), reply_markup=second_reply_markup, parse_mode=telegram.ParseMode.HTML, disable_web_page_preview=True)
    status_message.delete()

def SendToAll(update, context):
    uid = update.message.from_user.id
    if uid not in admins: return
    try:
        mid = update.message.reply_to_message.message_id
    except AttributeError:
        context.bot.sendMessage(chat_id=uid, text='Reply a message !')
        return
    users = mycol.find()
    status_message = context.bot.sendMessage(chat_id=uid, text='Sending message ...')
    for user in users:
        if user['chat_id'] in admins: continue
        try:
            context.bot.forwardMessage(chat_id=user['chat_id'], from_chat_id=uid, message_id=mid)
        except:
            mycol.update_one({'chat_id': user['chat_id']}, {'$set': {'blocked': True}})
            continue
    status_message.edit_text(text='Message successfully sent to all members ✅')

def Users(update, context):
    uid = update.message.from_user.id
    if uid not in admins: return
    args = update.message.text.split(' ')
    if len(args) == 1:
        for message in list_users(mycol.find()):
            context.bot.sendMessage(chat_id=uid, text=message, parse_mode=telegram.ParseMode.HTML, disable_web_page_preview=True)
    else:
        users = mycol.find({args[1] : {'$regex' : ".*{}.*".format(args[2])}})
        for message in list_users(users):
            context.bot.sendMessage(chat_id=uid, text=message, parse_mode=telegram.ParseMode.HTML, disable_web_page_preview=True)

def Count(update, context):
    uid = update.message.from_user.id
    if uid not in admins: return
    context.bot.sendMessage(chat_id=uid, text=str(mycol.count_documents(filter={})))

def Blocks(update, context):
    uid = update.message.from_user.id
    if uid not in admins: return
    blocked_users = mycol.find({'blocked': True})
    for message in list_users(blocked_users):
        context.bot.sendMessage(chat_id=uid, text=message, parse_mode=telegram.ParseMode.HTML, disable_web_page_preview=True)

def Help(update, context):
    context.bot.send_animation(chat_id=update.message.chat_id, animation=help_gif, caption='👆 How to use ?!')

if __name__ == '__main__':

    dispatcher.add_handler(CommandHandler('start', start, run_async=True))
    dispatcher.add_handler(CommandHandler('FindLike', FindMovies, run_async=True)) # search for similar movies
    dispatcher.add_handler(CommandHandler('sendtoall', SendToAll, run_async=True)) # forward a message to all users
    dispatcher.add_handler(CommandHandler('users', Users, run_async=True)) # get list of users
    dispatcher.add_handler(CommandHandler('count', Count, run_async=True)) # number of users
    dispatcher.add_handler(CommandHandler('blocks', Blocks, run_async=True)) # Get users who block the bot
    dispatcher.add_handler(CommandHandler('help', Help, run_async=True)) # how to use gif

    dispatcher.add_handler(InlineQueryHandler(inlinequery, run_async=True)) # search movies

    if not is_server:
        updater.start_polling()
    else:
        updater.start_webhook(listen='0.0.0.0',
                        port=8443,
                        url_path=TOKEN,
                        key='./ssh/private.key',
                        cert='./ssh/cert.pem',
                        webhook_url='https://188.40.239.81:8443/'+TOKEN)
    updater.idle()
