import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import pandas as pd
from monitor.fetcher import get_all_futures_tickers, fetch_ohlcv  # Изменён импорт
from monitor.analyzer import analyze
from monitor.signals import send_signal
from monitor.logger import log
from monitor.settings import load_config

scheduler = AsyncIOScheduler()
semaphore = asyncio.Semaphore(10)  # Уменьшено с 50 до 10 для избежания HTTP 429

async def process_symbol(symbol, config):
    async with semaphore:
        await asyncio.sleep(0.1)  # Задержка 100 мс между запросами
        try:
            df = await fetch_ohlcv(symbol, config['timeframe'])  # Изменено на fetch_ohlcv
            if df.empty:
                log(f"{symbol} - пустой DataFrame после fetch_ohlcv", level="warning")
                return
            is_signal, info = analyze(df, config, symbol=symbol)  # Передаём symbol явно
            if is_signal:
                log(f"Начало отправки сигнала для {symbol}", level="info")
                await send_signal(symbol, config['timeframe'], info)
            else:
                log(f"[{symbol}] Нет сигнала. {info.get('debug', 'Нет дополнительной информации')}", level="info")
        except Exception as e:
            log(f"Ошибка обработки {symbol}: {str(e)}", level="error")

async def run_monitor():
    try:
        config = load_config()
        tickers = await get_all_futures_tickers()
        log(f"Получено {len(tickers)} тикеров для обработки", level="info")
        if not tickers:
            log("Список тикеров пуст", level="warning")
            return

        # Фильтрация по EXCLUDED_KEYWORDS
        EXCLUDED_KEYWORDS = ['ALPHA', 'WEB3', 'AI', 'BOT']
        tickers = [t for t in tickers if not any(kw in t for kw in EXCLUDED_KEYWORDS)]

        start_time = asyncio.get_event_loop().time()
        tasks = [process_symbol(symbol, config) for symbol in tickers]
        await asyncio.gather(*tasks)
        end_time = asyncio.get_event_loop().time()
        log(f"Обработано {len(tickers)} тикеров, сигналов: {sum(1 for t in tickers if 'signal' in locals() and t in locals()['signal'])}, время обработки: {end_time - start_time:.2f} сек", level="info")
    except Exception as e:
        log(f"Ошибка в run_monitor: {str(e)}", level="error")

def start_monitor():
    scheduler.add_job(run_monitor, 'interval', seconds=60)
    scheduler.start()
    log("Мониторинг запущен", level="info")

if __name__ == "__main__":
    start_monitor()
    asyncio.get_event_loop().run_forever()