import pandas as pd
import numpy as np
import talib
from monitor.logger import log

def analyze(df, config, symbol="Unknown"):
    """
    Анализирует свечи и возвращает сигнал (памп/дамп) + инфо.
    Возвращает: (bool is_signal, dict info)
    """
    info = {}
    if len(df) < 50:
        info['debug'] = f"Внимание: для анализа {symbol} доступно только {len(df)} свечей (менее 50)"
    elif len(df) < 200:
        info['debug'] = f"Внимание: для анализа {symbol} доступно {len(df)} свечей (менее 200, требуется для обычных монет)"

    df = df.copy()
    df['close'] = df['close'].astype(float)
    df['volume'] = df['volume'].astype(float)
    df['high'] = df['high'].astype(float)
    df['low'] = df['low'].astype(float)

    indicators = config.get('indicators_enabled', {
        "price_change": True,
        "rsi": True,
        "macd": True,
        "volume_surge": True,
        "bollinger": True,
        "adx": True,
        "rsi_macd_divergence": True,
        "candle_patterns": True,
        "volume_pre_surge": True,
        "ema_crossover": True,
        "obv": True
    })

    # Инициализация переменных
    rsi = np.nan
    macd = np.nan
    macd_cross = False
    macd_bear = False
    sma20 = np.nan
    upper = np.nan
    lower = np.nan
    vol_surge = np.nan
    adx = np.nan
    bullish_divergence = False
    bearish_divergence = False
    bullish_candle = False
    bearish_candle = False
    volume_pre_surge = False
    ema_cross_up = False
    ema_cross_down = False
    obv_trend = np.nan

    # RSI (14)
    if indicators.get('rsi', True) or indicators.get('rsi_macd_divergence', True):
        try:
            df['rsi'] = talib.RSI(df['close'], timeperiod=14)
            rsi = float(df['rsi'].iloc[-1]) if not df['rsi'].isna().iloc[-1] else np.nan
        except Exception as e:
            log(f"Ошибка расчёта RSI для {symbol}: {str(e)}", level="error")
            df['rsi'] = np.nan
            rsi = np.nan

    # MACD (12,26,9)
    if indicators.get('macd', True) or indicators.get('rsi_macd_divergence', True):
        try:
            df['macd'], df['signal'], df['macd_hist'] = talib.MACD(df['close'], fastperiod=12, slowperiod=26, signalperiod=9)
            macd = float(df['macd'].iloc[-1]) if not df['macd'].isna().iloc[-1] else np.nan
            macd_cross = df['macd'].iloc[-1] > df['signal'].iloc[-1] and df['macd'].iloc[-2] <= df['signal'].iloc[-2] if not df['macd'].isna().iloc[-1] else False
            macd_bear = df['macd'].iloc[-1] < df['signal'].iloc[-1] and df['macd'].iloc[-2] >= df['signal'].iloc[-2] if not df['macd'].isna().iloc[-1] else False
        except Exception as e:
            log(f"Ошибка расчёта MACD для {symbol}: {str(e)}", level="error")
            df['macd'] = df['signal'] = df['macd_hist'] = np.nan
            macd = np.nan
            macd_cross = macd_bear = False

    # Bollinger Bands (20, 2σ)
    if indicators.get('bollinger', True):
        try:
            df['sma20'] = talib.SMA(df['close'], timeperiod=20)
            df['upper'], df['middle'], df['lower'] = talib.BBANDS(df['close'], timeperiod=20, nbdevup=2, nbdevdn=2)
            sma20 = float(df['sma20'].iloc[-1]) if not df['sma20'].isna().iloc[-1] else np.nan
            upper = float(df['upper'].iloc[-1]) if not df['upper'].isna().iloc[-1] else np.nan
            lower = float(df['lower'].iloc[-1]) if not df['lower'].isna().iloc[-1] else np.nan
        except Exception as e:
            log(f"Ошибка расчёта Bollinger Bands для {symbol}: {str(e)}", level="error")
            df['sma20'] = df['upper'] = df['middle'] = df['lower'] = np.nan
            sma20 = upper = lower = np.nan

    # Volume Surge
    if indicators.get('volume_surge', True):
        try:
            df['avg_vol'] = talib.SMA(df['volume'], timeperiod=20)
            df['vol_surge'] = df['volume'] / df['avg_vol']
            vol_surge = float(df['vol_surge'].iloc[-1]) if not df['vol_surge'].isna().iloc[-1] and df['avg_vol'].iloc[-1] > 0 else np.nan
        except Exception as e:
            log(f"Ошибка расчёта Volume Surge для {symbol}: {str(e)}", level="error")
            df['avg_vol'] = df['vol_surge'] = np.nan
            vol_surge = np.nan

    # ADX (14)
    if indicators.get('adx', True):
        try:
            df['adx'] = talib.ADX(df['high'], df['low'], df['close'], timeperiod=14)
            adx = float(df['adx'].iloc[-1]) if not df['adx'].isna().iloc[-1] else np.nan
        except Exception as e:
            log(f"Ошибка расчёта ADX для {symbol}: {str(e)}", level="error")
            df['adx'] = np.nan
            adx = np.nan

    # RSI/MACD Divergence
    if indicators.get('rsi_macd_divergence', True):
        try:
            if len(df) >= 3 and not df['rsi'].isna().iloc[-1] and not df['macd'].isna().iloc[-1]:
                price_diff = df['close'].iloc[-1] - df['close'].iloc[-3]
                rsi_diff = df['rsi'].iloc[-1] - df['rsi'].iloc[-3]
                macd_diff = df['macd'].iloc[-1] - df['macd'].iloc[-3]
                bullish_divergence = price_diff < 0 and (rsi_diff > 0 or macd_diff > 0)
                bearish_divergence = price_diff > 0 and (rsi_diff < 0 or macd_diff < 0)
            else:
                bullish_divergence = bearish_divergence = False
                log(f"Недостаточно данных для RSI/MACD Divergence для {symbol}: len(df)={len(df)}, rsi={df['rsi'].iloc[-1] if 'rsi' in df else 'missing'}, macd={df['macd'].iloc[-1] if 'macd' in df else 'missing'}", level="debug")
        except Exception as e:
            log(f"Ошибка расчёта RSI/MACD Divergence для {symbol}: {str(e)}", level="error")
            bullish_divergence = bearish_divergence = False

    # Candle Patterns (Hammer, Shooting Star)
    if indicators.get('candle_patterns', True):
        try:
            df['hammer'] = talib.CDLHAMMER(df['open'], df['high'], df['low'], df['close'])
            df['shooting_star'] = talib.CDLSHOOTINGSTAR(df['open'], df['high'], df['low'], df['close'])
            bullish_candle = df['hammer'].iloc[-1] > 0
            bearish_candle = df['shooting_star'].iloc[-1] > 0
        except Exception as e:
            log(f"Ошибка расчёта Candle Patterns для {symbol}: {str(e)}", level="error")
            df['hammer'] = df['shooting_star'] = np.nan
            bullish_candle = bearish_candle = False

    # Volume Pre-Surge (20-50% growth over 3-5 candles with stable price)
    if indicators.get('volume_pre_surge', True):
        try:
            if len(df) >= 5:
                recent_vol = df['volume'].iloc[-5:].mean()
                prev_vol = df['volume'].iloc[-10:-5].mean() if len(df) >= 10 else df['volume'].iloc[:-5].mean()
                price_stable = abs((df['close'].iloc[-1] - df['close'].iloc[-5]) / df['close'].iloc[-5] * 100) < 1.0
                volume_growth = (recent_vol / prev_vol - 1) * 100 if prev_vol > 0 else 0
                volume_pre_surge = (volume_growth >= 20 and volume_growth <= 50 and price_stable)
            else:
                volume_pre_surge = False
                log(f"Недостаточно данных для Volume Pre-Surge для {symbol}: len(df)={len(df)}", level="debug")
        except Exception as e:
            log(f"Ошибка расчёта Volume Pre-Surge для {symbol}: {str(e)}", level="error")
            volume_pre_surge = False

    # EMA Crossover (12, 26)
    if indicators.get('ema_crossover', True):
        try:
            df['ema12'] = talib.EMA(df['close'], timeperiod=12)
            df['ema26'] = talib.EMA(df['close'], timeperiod=26)
            ema_cross_up = (df['ema12'].iloc[-1] > df['ema26'].iloc[-1] and
                            df['ema12'].iloc[-2] <= df['ema26'].iloc[-2]) if not df['ema12'].isna().iloc[-1] else False
            ema_cross_down = (df['ema12'].iloc[-1] < df['ema26'].iloc[-1] and
                              df['ema12'].iloc[-2] >= df['ema26'].iloc[-2]) if not df['ema12'].isna().iloc[-1] else False
        except Exception as e:
            log(f"Ошибка расчёта EMA Crossover для {symbol}: {str(e)}", level="error")
            df['ema12'] = df['ema26'] = np.nan
            ema_cross_up = ema_cross_down = False

    # OBV
    if indicators.get('obv', True):
        try:
            df['obv'] = talib.OBV(df['close'], df['volume'])
            obv_trend = df['obv'].iloc[-1] - df['obv'].iloc[-2] if len(df) >= 2 and not df['obv'].isna().iloc[-1] else np.nan
            obv_rising = obv_trend > 0 if not pd.isna(obv_trend) else False
            obv_falling = obv_trend < 0 if not pd.isna(obv_trend) else False
        except Exception as e:
            log(f"Ошибка расчёта OBV для {symbol}: {str(e)}", level="error")
            df['obv'] = np.nan
            obv_trend = np.nan
            obv_rising = obv_falling = False

    # Условия для пампа (ключи = индикаторы)
    last = df.iloc[-1]
    threshold = config.get('price_change_threshold', 0.5)
    price_change = ((last['close'] - df['close'].iloc[-2]) / df['close'].iloc[-2] * 100) if len(df) >= 2 else 0
    pump_conditions = {}
    if indicators.get('price_change', True):
        pump_conditions["price_change"] = price_change > threshold
    if indicators.get('rsi', True):
        pump_conditions["rsi"] = rsi < 30
    if indicators.get('macd', True):
        pump_conditions["macd"] = macd_cross
    if indicators.get('volume_surge', True):
        pump_conditions["volume_surge"] = vol_surge > 1.5
    if indicators.get('bollinger', True):
        pump_conditions["bollinger"] = last['close'] > upper if not pd.isna(upper) else False
    if indicators.get('adx', True):
        pump_conditions["adx"] = adx > 25
    if indicators.get('rsi_macd_divergence', True):
        pump_conditions["rsi_macd_divergence"] = bullish_divergence
    if indicators.get('candle_patterns', True):
        pump_conditions["candle_patterns"] = bullish_candle
    if indicators.get('volume_pre_surge', True):
        pump_conditions["volume_pre_surge"] = volume_pre_surge
    if indicators.get('ema_crossover', True):
        pump_conditions["ema_crossover"] = ema_cross_up
    if indicators.get('obv', True):
        pump_conditions["obv"] = obv_rising

    # Условия для дампа (ключи = индикаторы)
    dump_conditions = {}
    if indicators.get('price_change', True):
        dump_conditions["price_change"] = price_change < -threshold
    if indicators.get('rsi', True):
        dump_conditions["rsi"] = rsi > 70
    if indicators.get('macd', True):
        dump_conditions["macd"] = macd_bear
    if indicators.get('volume_surge', True):
        dump_conditions["volume_surge"] = vol_surge > 1.5
    if indicators.get('bollinger', True):
        dump_conditions["bollinger"] = last['close'] < lower if not pd.isna(lower) else False
    if indicators.get('adx', True):
        dump_conditions["adx"] = adx > 25
    if indicators.get('rsi_macd_divergence', True):
        dump_conditions["rsi_macd_divergence"] = bearish_divergence
    if indicators.get('candle_patterns', True):
        dump_conditions["candle_patterns"] = bearish_candle
    if indicators.get('volume_pre_surge', True):
        dump_conditions["volume_pre_surge"] = volume_pre_surge
    if indicators.get('ema_crossover', True):
        dump_conditions["ema_crossover"] = ema_cross_down
    if indicators.get('obv', True):
        dump_conditions["obv"] = obv_falling

    # Подсчёт сработавших индикаторов
    count_triggered_pump = sum(pump_conditions.values())
    count_triggered_dump = sum(dump_conditions.values())
    total_indicators = len([k for k, v in indicators.items() if v])

    # Проверка на минимальное количество и обязательные индикаторы
    required = config.get('required_indicators', [])
    min_ind = config.get('min_indicators', 1)
    pump = (count_triggered_pump >= min_ind and all(pump_conditions.get(ind, False) for ind in required))
    dump = (count_triggered_dump >= min_ind and all(dump_conditions.get(ind, False) for ind in required))

    # Определяем тип сигнала и сработавшие индикаторы
    signal_type = "pump" if pump else "dump" if dump else None
    count_triggered = count_triggered_pump if pump else count_triggered_dump if dump else 0

    # Формируем info
    info.update({
        "type": signal_type,
        "tf_change": price_change,
        "rsi": rsi,
        "macd": macd,
        "volume_surge": vol_surge,
        "adx": adx,
        "bullish_divergence": bullish_divergence,
        "bearish_divergence": bearish_divergence,
        "bullish_candle": bullish_candle,
        "bearish_candle": bearish_candle,
        "volume_pre_surge": volume_pre_surge,
        "ema_cross_up": ema_cross_up,
        "ema_cross_down": ema_cross_down,
        "obv_trend": obv_trend,
        "count_triggered": count_triggered,
        "total_indicators": total_indicators,
        "analyzed_df": df
    })

    comment_parts = []
    if indicators.get('rsi', True):
        comment_parts.append(f"RSI={rsi:.1f}" if not pd.isna(rsi) else "RSI=NaN")
    if indicators.get('macd', True):
        comment_parts.append(f"MACD={'бычий' if macd_cross else 'медвежий' if macd_bear else 'нейтральный'}")
    if indicators.get('volume_surge', True):
        comment_parts.append(f"объём x{vol_surge:.2f}" if not pd.isna(vol_surge) else "объём=NaN")
    if indicators.get('adx', True):
        comment_parts.append(f"ADX={adx:.1f}" if not pd.isna(adx) else "ADX=NaN")
    if indicators.get('rsi_macd_divergence', True):
        comment_parts.append(f"Дивергенция={'бычья' if bullish_divergence else 'медвежья' if bearish_divergence else 'нет'}")
    if indicators.get('candle_patterns', True):
        comment_parts.append(f"Свечной паттерн={'Hammer' if bullish_candle else 'Shooting Star' if bearish_candle else 'нет'}")
    if indicators.get('volume_pre_surge', True):
        comment_parts.append(f"Рост объёма={'да' if volume_pre_surge else 'нет'}")
    if indicators.get('ema_crossover', True):
        comment_parts.append(f"EMA Crossover={'бычий' if ema_cross_up else 'медвежий' if ema_cross_down else 'нет'}")
    if indicators.get('obv', True):
        comment_parts.append(f"OBV={'растёт' if obv_rising else 'падает' if obv_falling else 'стабилен'}")
    info["comment"] = ", ".join(comment_parts) if comment_parts else "Нет активных индикаторов"

    # Детали для логов
    if not signal_type:
        if 'debug' not in info:
            info['debug'] = f"Нет сигнала для {symbol}"
    else:
        info['debug'] = f"Сигнал сгенерирован для {symbol}: {signal_type}, сработало {count_triggered} из {total_indicators}"

    return bool(signal_type), info