import logging
import time
import schedule
import asyncio
import threading
from datetime import datetime
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, CallbackContext, Updater, CallbackQueryHandler
import unicodedata
import db
import utils
import mysql.connector
from mysql.connector import Error
import httpx

db.init_db()

logger = logging.getLogger()
logger.setLevel(logging.INFO)  # Level INFO & ERROR

# Handler log file
file_handler = logging.FileHandler('/path-to-log-file/log.txt') ##EDIT HERE PATH TO LOG FILE
file_handler.setLevel(logging.INFO)
file_formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
file_handler.setFormatter(file_formatter)

# Console handler
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_formatter = logging.Formatter("%(levelname)s - %(message)s")
console_handler.setFormatter(console_formatter)

logger.addHandler(file_handler)
logger.addHandler(console_handler)

# BOT TOKEN 
import os
#TOKEN = os.getenv("TOKEN") ##GET TOKEN FROM ENVIROMENT OR SET HERE
TOKEN = "TELEGRAM BOT TOKEN" 

if not TOKEN:
    raise ValueError("❌ ERROR: TOKEN NOT FOUND!")
    
async def broadcast_message(app: Application, msg: str):
    id_active_users = db.get_active_users()
    for user_id in id_active_users:
        try:
            await app.bot.send_message(chat_id=user_id, text=msg)
        except Exception as e:
            logging.error(f"Errore nell'invio del messaggio a {user_id}: {e}")

async def broadcast_admin_message(app: Application, msg: str):
    id_admins = db.get_admins()
    for adminId in id_admins:
        try:
            await app.bot.send_message(chat_id=adminId, text=msg)
        except Exception as e:
            logging.error(f"Errore nell'invio del messaggio a {adminId}: {e}")
            
#### /start WELCOME COMMAND ####
async def start(update: Update, context: CallbackContext):
    try:
        user = update.effective_user ## User object
        user_id = user.id
        username = user.username if user.username else None
        first_name = user.first_name
        last_name = user.last_name if user.last_name else ""
        name = f"{first_name} {last_name}" 
        row_added = db.add_active_user(user_id, name, username)
        
        if(row_added > 0):
            message = f"Utente registrato: {username}"
            await broadcast_admin_message(context.application, message)
    
        start_message_user = """👋 Benvenuto nel bot delle partite!
    Ecco i comandi disponibili:
        
    📋<b>Vedi la lista delle partite\n    per partecipare:</b>
    /lista
         
    🚪<b>Abbandona una partita:</b> 
    /abbandona
    
    📢 Quando un admin crea una partita,\n    riceverai automaticamente\n    un messaggio con i dettagli.
    Puoi usare i comandi disponibili per\n    partecipare o abbandonare la partita.\n
    ⏰ Se sei iscritto a una partita, riceverai\n    un promemoria automatico\n    ogni giorno
    """
        
        
        await update.message.reply_text(start_message_user, parse_mode="HTML")
        
    except Exception as e:
        if isinstance(e, mysql.connector.Error):
            err_msg = f"Utente già presente, {username} aggiornato!"
            logging.error(err_msg)
            await update.message.reply_text(err_msg)
        elif isinstance(e, httpx.ConnectError):
            err_msg = f"/start Errore di connessione: {e}"
            logging.error(err_msg)
            await update.message.reply_text(err_msg)
        else:
            err_msg = f"/start Errore generico"
            logging.error(err_msg)
            await update.message.reply_text(err_msg)
            
#### /admin SHOW ADMIN COMMANDS ####
async def admin_commands(update: Update, context: CallbackContext):
    user_id = update.message.chat_id
    is_admin = db.is_admin(user_id)
  
    if not is_admin:
        await update.message.reply_text("Non hai i permessi da Admin!")
        return
    start_message_admin = """Comandi ADMIN:

        ⚽<b>Crea una partita</b>  
        /crea <i>data (obbligatorio) ora luogo\n        n.giocatori</i>

        🔄<b>Aggiorna i dettagli</b>  
        /aggiorna <i>match_id ora luogo</i>

        ❌<b>Annulla una partita</b>  
        /annulla <i>match_id</i>

        ℹ️<b>Visualizza i dettagli</b>  
        /partita <i>match_id</i>

        ➕<b>Aggiungi un giocatore guest</b>  
        /aggiungi <i>match_id nome chiamato_da</i>

        
        Usa questi comandi per organizzare\n        facilmente le tue partite!"""
    await update.message.reply_text(start_message_admin, parse_mode="HTML")
    
#### /crea COMMAND TO CREATE NEW MATCH
async def create_match(update: Update, context: CallbackContext):
   
    user_id = update.message.chat_id
    is_admin = db.is_admin(user_id)
  
    if not is_admin:
        await update.message.reply_text("Non puoi creare una partita, non hai i permessi da Admin!")
        return
    if len(context.args) < 1:
        await update.message.reply_text("Per favore, usa il comando nel formato: /crea <data>(obbligatorio) <ora> <luogo>")
        return
    # Take arguments
    date = context.args[0]  # format 'YYYY-MM-DD'
    time = None
    place = None
    max_players = None
    if len(context.args) > 2:
        time = context.args[1]
        place = context.args[2]
    
    if len(context.args) > 3:    
        max_players = context.args[3]
        
    creator_id = update.message.from_user.id
    match_id = db.create_match(date, time, place, creator_id, max_players)
    
    time_place_string = f"{place} {time}"
    if(time is None and place is None):
        time_place_string = "Da stabilire"
    if isinstance(match_id, int):
        await broadcast_message(context.application, f"(Tutti) Nuova partita disponibile!\nID partita: {match_id}.\nData: {date}\nCampo/Ora: {time_place_string}")
    else:
        await update.message.reply_text(f"Errore data formato errato o partita già presente!") 

#### /lista MATCHES LIST - SHOW MATCHES BUTTONS ####
async def show_matches_list(update: Update, context: CallbackContext):

    matches = db.matches_list('aperta')
    # No matches, show 
    if not matches:
        await update.message.reply_text("Nessuna partita disponibile al momento o già iscritto a quelle disponibili\nusa /abbandona per vedere quelle a cui sei iscritto.")
        return

    user_id = update.message.chat_id
    
    # Create buttons for every match
    keyboard = []
    for match in matches:
        match_id, date, time, place, max_players = match
        n_players = db.players_count_in_match(match_id)
        day_month = utils.get_day_weekday_toString(date)
        players_string = f"Giocatori {n_players}/{max_players}"
        place_time = f"{place} {time}"
        ## Player already in match
        if(db.check_player_in_match(user_id, match_id)):
            players_string = f"SEI DENTRO!{n_players}/{max_players}" 
        if place is None and time is None: 
            place_time = ""
        button_text = f"{day_month} {place_time} {players_string}"
        callback_data = f"join_{match_id}"
        keyboard.append([InlineKeyboardButton(button_text, callback_data=callback_data)])

    # Markup for buttons
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Show buttons with message
    await update.message.reply_text("Seleziona una partita per partecipare:", reply_markup=reply_markup)

#### CALLBACK ON CLICK JOIN MATCH ####
async def join_match(update: Update, context: CallbackContext):
    user_id = update.callback_query.from_user.id
    query_data = update.callback_query.data
    match_id = query_data.split("_")[1]  # Get ID match
    user = update.effective_user ## User object   
    username = user.username if user.username else None
    first_name = user.first_name
    last_name = user.last_name if user.last_name else ""
    name = f"{first_name} {last_name}" 
    
    # Check if match exists
    match = db.check_if_match_exists(match_id)
    if not match:
        await update.callback_query.answer("partita non trovata.")
        return
    
    n_players = db.players_count_in_match(match_id)
    if(n_players == match[4]):
        await context.bot.send_message(chat_id=user_id, text=f"Non puoi unirti, Partita al completo!")
        return
    # Add player to match
    added_row = db.add_player(match_id, user_id, username, name)

    if (added_row > 0):
        await update.callback_query.answer(f"Sei stato aggiunto alla partita con ID {match_id}!")
        await context.bot.send_message(chat_id=user_id, text=f"Sei stato aggiunto alla partita: {match_id} {match[1]} {match[2]} {match[3]}!")
        await broadcast_admin_message(context.application, f"(ADMIN)\n{name}:{username} si è unito alla partita: {match_id}->{match[1]}")
    else:
        await update.callback_query.answer(f"Partecipi già! -> id: {match_id} {match[1]} {match[2]} {match[3]}")
        await context.bot.send_message(chat_id=user_id, text=f"Partecipi già! id: {match_id}-> {match[1]} {match[2]} {match[3]}")
     
   
    if(n_players == match[4]-1):
        ##Set match complete
        db.update_match_status(match_id, "completa")
        ##Players list name in match
        players_list = db.players_in_match_list_name(match_id)
        
        await broadcast_message(context.application, f"(Tutti) Partita al completo -> id:{match_id}\n{match[1]} {match[2]} {match[3]}\nLista Giocatori:\n{players_list}!")
    

#### /abbandona GET MATCHES LIST - CLICK TO LEAVE MATCH ####
async def leave_match_list(update: Update, context: CallbackContext):
    
    user_id = update.message.chat_id
    matches = db.matches_list_by_player(user_id)
    # No matches, show message
    if not matches:
        await update.message.reply_text("Non partecipi a nessuna partita al momento")
        return
  
    # Create buttons for all matches
    keyboard = []
    for match in matches:
        match_id, date, time, place, max_players, _, _ = match
        n_players = db.players_count_in_match(match_id)
        day_week = utils.get_day_weekday_toString(date)
        players_string = f"Giocatori {n_players}/{max_players}"
        place_time = f"{place} {time}"
        if(db.check_player_in_match(user_id, match_id)):
            players_string = f"SEI DENTRO!{n_players}/{max_players}" 
        if place is None and time is None: 
            place_time = ""
        button_text = f"{day_week} {place_time} {players_string}"
        callback_data = f"leave_{match_id}"
        keyboard.append([InlineKeyboardButton(button_text, callback_data=callback_data)])

    # Markup for buttons
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Show buttons with message
    await update.message.reply_text("Seleziona una match da abbandonare:", reply_markup=reply_markup)

#### CALLBACK ON CLICK LEAVE MATCH ####
async def leave(update: Update, context: CallbackContext):
    user_id = update.callback_query.from_user.id
    query_data = update.callback_query.data
    match_id = query_data.split("_")[1]
    user = update.effective_user ## User object 
    user_first_name = user.first_name
    username = user.username if user.username else None
    # Check if match exists
    match = db.check_if_match_exists(match_id)
    if not match:
        await update.callback_query.answer("Partita non trovata.")
        return
    match_is_full = db.check_if_match_is_full(match_id)
    # Add player to match
    deleted_rows = db.delete_player(match_id, user_id)
    logging.info(f"match is full: {match_is_full}")
    logging.info(f"deleted rows: {deleted_rows}")
    if (deleted_rows > 0):
        if match_is_full:
            db.update_match_status(match_id, 'aperta')
            await broadcast_message(context.application, f"(Tutti) Si è liberato un posto nella partita: {match_id} {match[1]} {match[2]} {match[3]}!")
        await update.callback_query.answer(f"Hai abbandonato la partita: {match_id} {match[1]} {match[2]} {match[3]}!")
        await context.bot.send_message(chat_id=user_id, text=f"Hai abbandonato la partita: {match_id} {match[1]} {match[2]} {match[3]}!")
        await broadcast_admin_message(context.application, f"(ADMIN)\nIl giocatore {user_first_name}:{username} ha lasciato la partita {match_id}->{match[1]} {match[2]} {match[3]}!")
    else:
        await context.bot.send_message(chat_id=user_id, text=f"Si è verificato un errore: {match_id}")

#### /annulla DELETE MATCH ####
async def delete_match(update: Update, context: CallbackContext):
    user_id = update.message.chat_id
    is_admin = db.is_admin(user_id)
    if not is_admin:
        await update.message.reply_text("Non puoi annullare una partita, non hai i permessi da Admin!")
        return
        
    if len(context.args) < 1:
        await update.message.reply_text("Per favore, usa il comando nel formato: /annulla <partita_id>")
        return
    match_id = context.args[0]
    match = db.check_if_match_exists(match_id)
    if not match:
        await update.message.reply_text("Partita non trovata.")
        return
    del_row = db.delete_match(match_id)
    
    if (del_row > 0):
        await broadcast_message(context.application, f"(Tutti) Partita ANNULLATA {match_id} {match[1]} {match[2]} {match[3]}!!!")
    else:
        await update.message.reply_text(f"Si è verificato un errore: id partita:{match_id}")

#### /aggiorna UPDATE MATCH ####
async def update_match(update: Update, context: CallbackContext):
    user_id = update.message.chat_id
    is_admin = db.is_admin(user_id)
    if not is_admin:
        await update.message.reply_text("Non hai i permessi da Admin!")
        return
        
    if len(context.args) < 3:
        await update.message.reply_text("Per favore, usa il comando nel formato: /aggiorna <id_partita> <ora> <luogo>")
        return
    match_id = context.args[0]
    time = context.args[1]
    place = context.args[2]
    
    match = db.check_if_match_exists(match_id)
    if not match:
        await update.message.reply_text("Partita non trovata.")
        return
    updated_row = db.update_match(match_id, time, place)
        
    if updated_row == 1:
        players_list = db.players_in_match_list_name(match_id)
        await broadcast_message(context.application, f"(Tutti) Campo prenotato -> {place} \n{match[1]} {time}\nLista Giocatori:\n{players_list}")
    else:
        await update.message.reply_text("Errore aggiornamento partita!")

#### /aggiungi ADD PLAYER GUEST ####
async def add_player_guest(update: Update, context: CallbackContext):
    user_id = update.message.chat_id
    is_admin = db.is_admin(user_id)
    if not is_admin:
        await update.message.reply_text("Non hai i permessi da Admin!")
        return
        
    if len(context.args) < 3:
        await update.message.reply_text("Per favore, usa il comando nel formato: /aggiungi <id_partita> <nome> <chiamatoDa>")
        return
    user_id = update.message.chat_id
    match_id = context.args[0]
    name = context.args[1]
    fromm = context.args[2]
    match = db.check_if_match_exists(match_id)
    if not match:
        await update.message.reply_text("Partita non trovata.")
        return
    n_players = db.players_count_in_match(match_id)
    if(n_players == match[4]):
        await context.bot.send_message(chat_id=user_id, text=f"Non puoi aggiungerlo, Partita al completo!")
        return
    # Add guest to match
    added_row = db.add_guest(match_id, name, fromm)

    if (added_row > 0):
        await context.bot.send_message(chat_id=user_id, text=f"Hai aggiunto {name} alla partita: {match_id} {match[1]} {match[2]} {match[3]}!")
        await broadcast_admin_message(context.application, f"(ADMIN)\n{name}->{fromm} è stato aggiunto alla partita: {match_id}->{match[1]}")
    else:
        await context.bot.send_message(chat_id=user_id, text="Errore aggiunta giocatore")
     
   
    if(n_players == match[4]-1):
        ##Set match complete
        db.update_match_status(match_id, "completa")
        ##Players list name in match
        players_list = db.players_in_match_list_name(match_id)
        
        await broadcast_message(context.application, f"(Tutti) Partita al completo -> id:{match_id}\n{match[1]} {match[2]} {match[3]}\nLista Giocatori:\n{players_list}!")
    
#### /partita SHOW PLAYERS IN MATCH ####
async def show_players_in_match(update: Update, context: CallbackContext):
    user_id = update.message.chat_id
    is_admin = db.is_admin(user_id)
    if not is_admin:
        await update.message.reply_text("Non hai i permessi da Admin!")
        return
        
    if len(context.args) < 1:
        await update.message.reply_text("Per favore, usa il comando nel formato: /partita <id_partita>")
        return
    match_id = context.args[0]
    match = db.check_if_match_exists(match_id)
    if not match:
        await update.message.reply_text("Partita non trovata.")
        return
    players_list = db.players_in_match_list_name(match_id)
    n_players = db.players_count_in_match(match_id)
    match_info = "Partita "
    logging.info(f"players in partita {n_players}")
    logging.info(f"max players = {match[4]}")
    if(n_players == match[4]):
        match_info = "Partita al completo"
    await broadcast_message(context.application, f"(Tutti) {match_info} -> id:{match_id}\n{match[1]} {match[2]} {match[3]}\nLista Giocatori:\n{players_list}")

#### REMINDER FOR MATCHES COMPLETE ####
async def reminder(app):
    logging.info("Reminder sent!")
    matches_list = db.matches_list('completa')
    active_users = db.get_active_users()
    for match in matches_list:
        players = db.players_in_match(match[0])
        for player in players:
            if player[2] in active_users: ##Check if user is registered
                await app.bot.send_message(chat_id = player[2], text=f"Reminder partita {match[1]} {match[3]} {match[2]}")

async def error_handler(update, context):
    logging.error(f"ERROR HANDLER -> Update:{update} caused error {context.error}")

def run_scheduler():
    while True:
        schedule.run_pending()
        time.sleep(1000) ## Time wait to check for reminder

if __name__ == "__main__":
    
    # Init bot
    app = Application.builder().token(TOKEN).build()

    # Scheduler reminder match
    schedule.every().day.at("18:00").do(lambda: asyncio.run(reminder(app)))
    
    # Aggiunta comandi al bot
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("crea", create_match))
    app.add_handler(CommandHandler("lista", show_matches_list))
    app.add_handler(CommandHandler("abbandona", leave_match_list))
    app.add_handler(CommandHandler("annulla", delete_match))
    app.add_handler(CommandHandler("aggiorna", update_match))
    app.add_handler(CommandHandler("aggiungi", add_player_guest))
    app.add_handler(CommandHandler("partita", show_players_in_match))
    app.add_handler(CommandHandler("admin", admin_commands))
    app.add_handler(CallbackQueryHandler(join_match, pattern="^join_"))
    app.add_handler(CallbackQueryHandler(leave, pattern="^leave_"))
    app.add_error_handler(error_handler)

    threading.Thread(target=run_scheduler, daemon=True).start()
    app.run_polling(timeout=60, read_latency=4)
