# Game Match Management Bot 🤖⚽🏀🎾

Welcome to our amazing Telegram bot! 🌟 Are you ready to organize epic matches with your friends? With this bot, you can easily create, manage, and join matches in no time! Whether you're looking to set up a football game, a card match, or any other game, this bot is just what you need. 🏆

Admins can create and update matches, while users can sign up, get reminders, and have fun with friends or strangers. Ready for some fun? Then start now and enjoy the game! 🎉

## Features ⚙️

- **Create and Manage Matches**: Admins can easily create and update game events.
- **Join Matches**: Users can sign up to participate in games.
- **Match Reminders**: Stay on top of your upcoming matches with automatic reminders.
- **Easy to Use**: Simple commands to start and manage your game.
- **Multiple Game Types**: Although it's designed for football matches, this bot can also be used for other sports! 

## 🛠️ Technologies Used

- **Python**: The main programming language.
- **python-telegram-bot**: Library to interact with the Telegram API.
- **MySQL**: Database for managing matches and users.
- **Asyncio**: For asynchronous management of message sending operations.
- **Schedule**: For scheduling tasks (like sending reminders).

## ⚙️ Installation

1. **Clone the repository**:

   ```git clone https://github.com/giuseppecastaldo89/matchorganizerbot.git```

   Run locally or host somewhere (i used PythonAnywhere but db need to keep alive, explained in comment in db.py)

3. **Install the required dependencies**:

   ```pip install -r requirements.txt```
   
4. **Configure your Telegram bot**:  

   Create a new bot with [BotFather](https://core.telegram.org/bots#botfather), and then add the bot token in bot.py or use enviroment var.
   
5. **Run Locally**

   You can run the bot locally by executing bot.py
   
6. **Host online**

   If you want your bot to run continuously without depending on your local machine being always on, you can host it online.
   For hosting the bot online, I personally used **PythonAnywhere**, which is a simple and reliable platform for running Python applications in the cloud.
   PythonAnywhere provides a free tier for smaller projects, but you may need to upgrade if your bot starts requiring more resources (e.g., CPU, memory, etc.).
   When hosting the bot online, it’s important to ensure that the database remains connected and active. In the `db.py` file, you’ll find comments explaining
   how to keep the database connection alive when deploying your bot online.
   PythonAnywhere is just one of many hosting platforms available. You can also consider using others depending on your project’s scale and your specific requirements.

## 🚀 User Commands

1. **`/start`**  
   **Description**: Sends a welcome message and shows the bot's main information.  
   **Parameters**: None.

2. **`/lista`**  
   **Description**: Displays a list of available games for the user. The user can choose to join a game.  
   **Parameters**: None.

3. **`/abbandona`**  
   **Description**: Allows the user to quit a current game.  
   **Parameters**: None.

---

## 🛠️ Admin Commands

1. **`/crea <date> <time> <where> <number_of_player>`**  
   **Description**: Creates a new game.  
   **Parameters**:  
   - `<date>`: Date of the game to create.
   - `<time>`: The time of the game to create. (otpional)
   - `<where>`: Where to play game. (optional)
   - `<number_of_player>`: Max player for match. (optional, default 10)

2. **`/annulla <game_id>`**  
   **Description**: Ends an existing game.  
   **Parameters**:  
   - `<game_id>`: The ID of the game to end.

3. **`/aggiorna <match_id> <time> <where>`**  
   **Description**: Update existing match by time and place.  
   **Parameters**:
   - `<match_id>`: match id.
   - `<time>`: The time of the game to create.
   - `<where>`: Where to play game.

5. **`/partita <match_id>`**  
   **Description**: Show player and info for a match. 
   **Parameters**:  
   - `<match_id>`: match id.

6. **`/aggiungi <match_id> <name> <from>`**  
   **Description**: Add guest to match.  
   **Parameters**:  
   - `<match_id>`: Match id.
   - `<name>`: Guest name.
   - `<from>`: from?.


**Note:** The commands and messages are in Italian because this bot was originally created for an Italian-speaking group.
However, it could easily be adapted to support multiple languages in the future. 🌍


Made with ❤️⚽ by **Giuseppe Castaldo**
Feel free to reach out or contribute to the project!
