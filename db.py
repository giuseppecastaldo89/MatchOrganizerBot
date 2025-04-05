import mysql.connector
from mysql.connector import Error
import logging
import threading
import time

connection = None
db_config = None

# Configuration logging
logging.basicConfig(
    filename='/path-to-log-file/log.txt', ##EDIT HERE PATH TO LOG FILE
    level=logging.ERROR,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

def init_db():
    global connection, db_config
    # Create and get database connection
    db_config = {
    "host": "host",          ##EDIT HERE FOR DB SETUP
    "user": "user",          ##EDIT HERE FOR DB SETUP
    "password": "password$", ##EDIT HERE FOR DB SETUP
    "db": "db_name",         ##EDIT HERE FOR DB SETUP
}
    try:
        connection = mysql.connector.connect(**db_config)
        if connection.is_connected():
            print("✅ Connessione al datebase riuscita!")
            create_tables()
            threading.Thread(target=keep_db_alive, daemon=True).start() 
        return connection
    except Error as e:
        logging.error(f"Errore connessione DB: {e}")
        print(f"❌ Errore di connessione: {e}")
        return None

def get_connection():
    global connection, db_config
    try:
        if connection is None:
            connection = mysql.connector.connect(**db_config)
    except Exception as e:
        logging.error(f"Errore connessione DB -> get_db_connection: {e}")
        connection = None
    return connection

def get_cursor(): 
    global connection
    connection = get_connection()
    if connection:
        return connection.cursor()
    return None
    
### FUNC TO KEEP_ALIVE_DB DEPENDS ON HOST USED (Example: PythonAnywhere has a little wait_timeout, so this need to ping and keep alive db ###
def keep_db_alive():
    global connection
    while True:
        try:
            connection = get_connection()

            if connection and connection.is_connected():
                with connection.cursor() as cursor:
                    print("✅ Connessione attiva, eseguo SELECT 1")
                    cursor.execute("SELECT 1")
                    cursor.fetchone()
            else:
                print("⚠️ Connessione persa! Riproverò tra 15 secondi...")
                time.sleep(15)  # WAIT BEFORE RETRY
                continue  # restart cycle

            time.sleep(55)  # active connection each 55 seconds
        except mysql.connector.Error as e:
            logging.error(f"❌ Errore MySQL in keep_db_alive: {e}")
            print(f"⚠️ Errore MySQL in keep_db_alive: {e}")
            connection = None  # reset connection when raise error
            time.sleep(15)  # avoid loop in case of errors
        except Exception as e:
            logging.error(f"❌ Errore generico in keep_db_alive: {e}")
            print(f"⚠️ Errore generico in keep_db_alive: {e}")
            connection = None
            time.sleep(15)  # avoid loop
    
def create_tables():
    if connection:
        try:
        
            query_active_users = f"""
                CREATE TABLE IF NOT EXISTS active_users (
                user_id BIGINT PRIMARY KEY,
                name VARCHAR(255) NULL,
                username VARCHAR(255) NULL,
                is_admin BOOLEAN DEFAULT FALSE
                );
                """
            
            query_matches = f"""
                CREATE TABLE IF NOT EXISTS matches (
                id INT AUTO_INCREMENT PRIMARY KEY,
                date DATE NOT NULL UNIQUE,
                time VARCHAR(255),
                place VARCHAR(255),
                max_players INT DEFAULT 10,
                status ENUM('aperta', 'completa', 'annullata') NOT NULL,
                creator_id BIGINT NOT NULL
                );
                """
            

            query_players = f"""
                CREATE TABLE IF NOT EXISTS players (
                id INT AUTO_INCREMENT PRIMARY KEY,
                match_id INT NOT NULL,
                player_id BIGINT NOT NULL,
                username VARCHAR(255) NULL,
                name VARCHAR(255) NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (match_id) REFERENCES matches(id) ON DELETE CASCADE,
                UNIQUE (match_id, player_id)
                );
                """
            cursor = get_cursor()
            cursor.execute(query_active_users)
            cursor.execute(query_matches)
            cursor.execute(query_players)
            connection.commit()

        except Error as e:
            logging.error(f"Errore creazione tables: {e}")
            print(f"❌ Errore: {e}")


def create_match(date, time, place, creator_id, max_players):
    try:
        cursor = get_cursor()
        columns = ["date", "time", "place", "status", "creator_id"]
        values = [date, time, place, "aperta", creator_id]
        if max_players is not None:
            columns.append("max_players")
            values.append(max_players)
        query = f"""
        INSERT INTO matches ({", ".join(columns)})
        VALUES ({", ".join(["%s"] * len(values))});
        """
        cursor.execute(query, tuple(values))
        match_id = cursor.lastrowid  # Get ID match created

        connection.commit()

        return match_id
    except Exception as e:
        logging.error(f"Errore creazione partita: {e}")
        if connection:
            connection.rollback()
        return f"Errore: {e}"

def matches_list(status):
    try:
        cursor = get_cursor()
        query = "SELECT id, date, time, place, max_players FROM matches WHERE status = %s"
        cursor.execute(query, (status,))
        return cursor.fetchall()
    except Exception as e:
        logging.error(f"Errore matches_list: {e}")
        if connection:
            connection.rollback()
        return 0

def matches_list_by_player(user_id):
    try:
        cursor = get_cursor()
        query = """SELECT p.* 
                 FROM matches p 
                 JOIN players pa 
                 ON p.id = pa.match_id
                 WHERE pa.player_id = %s"""
        cursor.execute(query, (user_id,))
        return cursor.fetchall()
    except Exception as e:
        logging.error(f"Errore matches_list_by_player: {e}")
        if connection:
            connection.rollback()
        return 0

def players_count_in_match(match_id):
    try:
        cursor = get_cursor()
        query = "SELECT COUNT(*) FROM players WHERE match_id = %s"
        cursor.execute(query, (match_id,))
        return cursor.fetchone()[0]
    except Exception as e:
        logging.error(f"Errore players_count_in_match: {e}")
        if connection:
            connection.rollback()
        return 0

def players_in_match(match_id):
    try:
        cursor = get_cursor()
        query = "SELECT * FROM players WHERE match_id = %s"
        cursor.execute(query, (match_id,))
        return cursor.fetchall()
    except Exception as e:
        logging.error(f"Errore players_in_match: {e}")
        if connection:
            connection.rollback()
        return 0
    
def players_in_match_list_name(match_id):
    try:
        cursor = get_cursor()
        query = "SELECT name, username FROM players WHERE match_id = %s"
        cursor.execute(query, (match_id,))
        p_list = cursor.fetchall()
        names = [f"{p[0]} ({p[1]})" for p in p_list]
        return "\n".join(names)
    except Exception as e:
        logging.error(f"Errore players_in_match_list_name: {e}")
        if connection:
            connection.rollback()
        return 0
    
def check_player_in_match(user_id, match_id):
    try:
        cursor = get_cursor()
        query = "SELECT * FROM players WHERE player_id = %s AND match_id = %s"
        cursor.execute(query, (user_id, match_id))
        return cursor.fetchone()
    except Exception as e:
        logging.error(f"Errore check_player_in_match: {e}")
        if connection:
            connection.rollback()
        return 0
    
def check_if_match_exists(match_id):
    try:
        cursor = get_cursor()
        query_check = "SELECT * FROM matches WHERE id = %s"
        cursor.execute(query_check, (match_id,))
        return cursor.fetchone()
    except Exception as e:
        logging.error(f"Errore check_if_match_exists: {e}")
        if connection:
            connection.rollback()
        return 0
    
def check_if_match_is_full(match_id):
    try:
        cursor = get_cursor()
        query_check = "SELECT * FROM matches WHERE status = %s AND id = %s"
        cursor.execute(query_check, ('completa', match_id))
        return cursor.fetchone() is not None
    except Exception as e:
        logging.error(f"Errore check_if_match_is_full: {e}")
        if connection:
            connection.rollback()
        return 0

def add_player(match_id, player_id, username, name):
    try:
        cursor = get_cursor()
        query_insert = "INSERT INTO players (match_id, player_id, username, name) VALUES (%s, %s, %s, %s)"
        cursor.execute(query_insert, (match_id, player_id, username, name))
        connection.commit()
        return cursor.rowcount
    except Exception as e:
        logging.error(f"Errore add_player: {e}")
        if connection:
            connection.rollback()
        return 0

def add_guest(match_id, name, username):
    try:
        cursor = get_cursor()
        player_id = 0
        while True:
            # If record match_id player_id exists
            query_check = "SELECT COUNT(*) FROM players WHERE match_id = %s AND player_id = %s"
            cursor.execute(query_check, (match_id, player_id))
            result = cursor.fetchone()

            if result[0] == 0:  # If record doesnt exist go with insert
                query_insert = "INSERT INTO players (match_id, player_id, username, name) VALUES (%s, %s, %s, %s)"
                cursor.execute(query_insert, (match_id, player_id, username, name))
                connection.commit()
                return cursor.rowcount  
            else:
                # Increment player_id and retry
                player_id += 1

    except Exception as e:
        logging.error(f"Errore add_guest: {e}")
        if connection:
            connection.rollback()
        return 0
        
def delete_player(match_id, player_id):
    try:
        cursor = get_cursor()
        query_del = "DELETE FROM players WHERE match_id = %s AND player_id = %s"
        cursor.execute(query_del, (match_id, player_id))
        connection.commit()
        return cursor.rowcount
    except Exception as e:
        logging.error(f"Errore delete_player: {e}")
        if connection:
            connection.rollback()
        return 0

def delete_match(match_id):
    try:
        cursor = get_cursor()
        query = "DELETE FROM matches WHERE id = %s"
        cursor.execute(query, (match_id,))
        connection.commit()
        return cursor.rowcount
    except Exception as e:
        logging.error(f"Errore delete_match: {e}")
        if connection:
            connection.rollback()
        return 0

def update_match(match_id, time, place):
    try:
        cursor = get_cursor()
        query = "UPDATE matches SET time = %s, place = %s WHERE id = %s"
        cursor.execute(query, (time, place, match_id))
        connection.commit()
        return cursor.rowcount
    except Exception as e:
        logging.error(f"Errore update_match: {e}")
        if connection:
            connection.rollback()
        return 0

def update_match_status(match_id, status):
    try:
        cursor = get_cursor()
        query = "UPDATE matches SET status = %s WHERE id = %s"
        cursor.execute(query, (status, match_id))
        connection.commit()
        return cursor.rowcount
    except Exception as e:
        logging.error(f"Errore update_match_status: {e}")
        if connection:
            connection.rollback()
        return 0

def add_active_user(user_id, name, username):
    try:
        cursor = get_cursor()
        query_add = """INSERT INTO active_users (user_id, name, username) 
                       VALUES (%s, %s, %s) 
                       ON DUPLICATE KEY UPDATE
                       name = VALUES(name),
                       username = VALUES(username);
                       """
        cursor.execute(query_add, (user_id, name, username))
        connection.commit()
        return cursor.rowcount
    except Exception as e:
        logging.error(f"Errore add_active_user: {e}")
        if connection:
            connection.rollback()
        return 0

def get_active_users():
    try:
        cursor = get_cursor()
        cursor.execute("SELECT user_id FROM active_users")
        id_list = [row[0] for row in cursor.fetchall()]
        return id_list
    except Exception as e:
        logging.error(f"Errore get_active_users: {e}")
        if connection:
            connection.rollback()
        return 0
    
def get_admins():
    try:
        cursor = get_cursor()
        cursor.execute("SELECT user_id FROM active_users WHERE is_admin=1")
        id_list = [row[0] for row in cursor.fetchall()]
        return id_list
    except Exception as e:
        logging.error(f"Errore get_admins: {e}")
        if connection:
            connection.rollback()
        return 0
    
def is_admin(user_id):
    try:
        cursor = get_cursor()
        query = "SELECT * FROM active_users WHERE user_id = %s"
        cursor.execute(query, (user_id,))
        return cursor.fetchone()[3] == 1 #is_admin column
    except Exception as e:
        logging.error(f"Errore is_admin: {e}")
        if connection:
            connection.rollback()
        return 0