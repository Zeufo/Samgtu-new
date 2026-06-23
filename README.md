

# SamGTU schedule bot

An asynchronous Telegram bot designed to display group schedules and instantly notify users about changes in real time.

## Screenshots

<img width="272" height="473" alt="Снимок экрана_20260622_123640" src="https://github.com/user-attachments/assets/898a7a4d-cdfa-44e8-af1b-f22acec52346" />

<img width="296" height="478" alt="Снимок экрана_20260622_123600" src="https://github.com/user-attachments/assets/a8f40cd1-a896-4946-9ab1-10e59e31dd04" />

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

## 👤 Author

- GitHub: <https://github.com/Zeufo>
- Telegram: @Zeufo

## License

[MIT](https://choosealicense.com/licenses/mit/)
