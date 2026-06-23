
# SamGTU schedule bot

An asynchronous Telegram bot designed to display group schedules and instantly notify users about changes in real time.

## Run with Docker

```bash
# Not implemented yet
```

## Features

- [x] View group schedule

- [x] Receive change notifications

## Technologies Used

| Layer | Technologies |
|------|-----------|
| **Frontend** | aiogram |
| **Backend** | Python, SQLAlchemy, UV (package manager) |
| **DataBase** | PostgreSQL |

## 📂 Project Structure

```text
├── src/
│   ├── database/    # SQLAlchemy table models and database logic
│   ├── handlers/    # aiogram handlers for bot commands
│   ├── parse/       # Data parsing and cleaning
│   ├── services/    # Business logic
│   ├── utils/       # Helper utilities (monitoring, logging)
│   ├── main.py      # Bot entry point
│   ├── keyboards.py # Reply keyboards for the bot
│   ├── process.py   # Main process where everything starts
│   └── config.py    # Configuration file
├── pyproject.toml   # Dependencies and configuration (uv, ruff, pyright)
└── README.md
```

## Environment Variables

To run this project, you need to add the following environment variables to your `.env` file in the bot directory:

| Variable      | Description                                      |
|---------------|--------------------------------------------------|
| `BOT_TOKEN`   | Your bot token from BotFather                    |
| `PROXY_LINK`  | URL to fetch the current week number (university website) |
| `DB_HOST`     | Database host                                    |
| `DB_PORT`     | Database port                                    |
| `DB_NAME`     | Database name                                    |
| `DB_USER`     | Database user                                    |
| `DB_PASSWORD` | Database password                                |

## Roadmap

- [ ] Redesign UI
- [ ] Add more functionality
- [ ] Optimize database queries

## Run Locally

Clone the project

```bash
  git clone https://github.com/Zeufo/Samgtu-new
```

Go to the project directory

```bash
  cd Samgtu-new
```

Install dependencies

```bash
  uv sync
```

Run the program

```bash
  uv run src/main.py
```

## Screenshots

![App Screenshot](https://dummyimage.com/468x300?text=App+Screenshot+Here)

## 👤 Author

- GitHub: <https://github.com/Zeufo>
- Telegram: @Zeufo

## License

[MIT](https://choosealicense.com/licenses/mit/)
