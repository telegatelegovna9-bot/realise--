import telegram
import os
from monitor.logger import log
from monitor.charts import create_chart

async def send_signal(symbol, timeframe, info):  # Изменён аргумент df → timeframe
    try:
        log(f"Начало отправки сигнала для {symbol}")
        from monitor.settings import load_config
        config = load_config()
        bot = telegram.Bot(token=config['telegram_token'])
        df = info.get('analyzed_df')  # Данные извлекаются из info
        last_close = float(df['close'].iloc[-1])
        prev_close = float(df['close'].iloc[-2])
        tf_change = (last_close - prev_close) / prev_close * 100 if prev_close != 0 else 0

        signal_type = info.get("type", "")
        count_triggered = info.get("count_triggered", 0)
        total_indicators = info.get("total_indicators", 0)
        count_str = f"Сработало {count_triggered} из {total_indicators} индикаторов"

        if signal_type == "pump":
            icon, label = "🚀", "ПАМП"
        elif signal_type == "dump":
            icon, label = "📉", "ДАМП"
        else:
            icon, label = "⚪", "СИГНАЛ"

        tradingview_url = f"https://www.tradingview.com/chart/?symbol=BYBIT:{symbol.replace('/', '').replace(':', '')}.P"

        html = (
            f"<b>{icon} {label}</b> | <b>{tf_change:.2f}% на момент сигнала</b>\n"
            f"Монета: <code>{symbol}</code>\n"
            f"Цена сейчас: <b>{last_close:.6f} USDT</b>\n"
            f"{count_str}\n"
            f"\nИндикаторы (подтверждение):\n"
        )
        if "rsi" in info:
            html += f"• RSI: <b>{info['rsi']:.1f}</b> (перекупленность/перепроданность)\n"
        if "macd" in info:
            html += f"• MACD: <b>{info['macd']:.6f}</b> (тренд)\n"
        if "adx" in info:
            html += f"• ADX: <b>{info['adx']:.1f}</b> (сила тренда)\n"
        if "volume_surge" in info:
            html += f"• Объём: <b>x{info['volume_surge']:.2f}</b> (поддержка движения)\n"
        if "bullish_divergence" in info or "bearish_divergence" in info:
            divergence = "бычья" if info['bullish_divergence'] else "медвежья" if info['bearish_divergence'] else "нет"
            html += f"• Дивергенция: <b>{divergence}</b> (RSI/MACD)\n"
        if "bullish_candle" in info or "bearish_candle" in info:
            candle = "Hammer" if info['bullish_candle'] else "Shooting Star" if info['bearish_candle'] else "нет"
            html += f"• Свечной паттерн: <b>{candle}</b>\n"
        if "volume_pre_surge" in info:
            html += f"• Рост объёма: <b>{'да' if info['volume_pre_surge'] else 'нет'}</b> (20-50%)\n"
        if "ema_cross_up" in info or "ema_cross_down" in info:
            ema_cross = "бычий" if info['ema_cross_up'] else "медвежий" if info['ema_cross_down'] else "нет"
            html += f"• EMA Crossover: <b>{ema_cross}</b> (EMA12/EMA26)\n"
        if "obv_trend" in info:
            obv = "растёт" if info['obv_trend'] > 0 else "падает" if info['obv_trend'] < 0 else "стабилен"
            html += f"• OBV: <b>{obv}</b> (объёмный тренд)\n"
        html += (
            f"\n{info['comment']}\n\n"
            f"<a href=\"{tradingview_url}\">Открыть график на TradingView</a>"
        )

        chart_path = create_chart(df, symbol, timeframe)  # Передаём timeframe
        log(f"Отправка сообщения в чат {config['chat_id']}...")
        await bot.send_photo(chat_id=config['chat_id'], photo=open(chart_path, 'rb'), caption=html, parse_mode="HTML")
        log(f"Сообщение успешно отправлено для {symbol}")
        os.remove(chart_path)
        log(f"График удалён: {chart_path}")
        log(f"[{symbol}] Сигнал отправлен: {label} | {tf_change:.2f}% | {last_close}. Детали: {info['debug']}")
    except Exception as e:
        log(f"Ошибка отправки сигнала для {symbol}: {e}")
        raise