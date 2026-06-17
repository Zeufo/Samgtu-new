from process import ProgrammProcess
import asyncio
import locale


locale.setlocale(locale.LC_TIME, 'ru_RU.UTF-8')
async def main():
    process = ProgrammProcess()
    await process.main_process()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass

