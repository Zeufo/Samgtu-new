# SamGTU schedule bot

An asynchronous Telegram bot designed to display group schedules and instantly notify users about changes in real time.

## Run with Docker

'''bash
Not done yet
'''

## Functional

- [x] Get your group schedule

- [x] Changes alarm

## Technologies used

| Layer | Technologies |
|------|-----------|
| **Frontend** | aiogram |
| **Backend** | Python, SQLAlchemy, UV (менеджер пакетов) |
| **База данных** | PostgreSQL |

## 📂 Структура проекта

```text
├── src/
│   ├── database/    # Alchemy table models and database logic
│   ├── handlers/    # aiogram logic handlers
│   ├── parse/       # Data parsing and cleaning
│   ├── services/    # Bussines logic
│   ├── utils/       # Helping utils (monitoring, logging)
│   └── main.py      # Bot start point
|   └── keyboards.py # reply keyboards in bot
|   └── process.py   # Main process where everything starting
|   └── config.py    # Config file
├── pyproject.toml   # dependencies and configuration (uv, ruff, pyright)
└── README.md
```

## Environment Variables

To run this project you need no add this Environment Variables to your .env file in bot dir

`BOT_TOKEN` | "Your_bot_token"

`PROXY_LINK` | LINK |  From where you will take week num

`DB_HOST`    | Database host (postgre)

`DB_PORT` | Database port

`DB_NAME` | Database name

`DB_USER` | User name

`DB_PASSWORD` | Password

## Roadmap

- [ ] change design

- [ ] increase functional

- [ ] Optimise Database requests

## Run Locally

Clone the project

```bash
  git clone https://github.com/Zeufo/Samgtu-new
```

Go to the project directory

```bash
  cd bot-remake
```

Install dependencies

```bash
  uv sync
```

run the programm

```bash
  uv run src/main.py
```

## Screenshots

![App Screenshot](https://dummyimage.com/468x300?text=App+Screenshot+Here)

## License

[MIT](https://choosealicense.com/licenses/mit/)
