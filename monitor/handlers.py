from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from monitor.logger import log
from monitor.settings import load_config, save_config, parse_human_number, human_readable_number

def update_config(key, value):
    """Обновляет конфигурацию и сохраняет её в файл."""
    config = load_config()
    config[key] = value
    save_config(config)
    log(f"Конфигурация обновлена: {key} = {value}", level="info")
    return config

async def start(update: Update, context):
    config = load_config()
    buttons = [
        [KeyboardButton("📴 Выключить бота"), KeyboardButton("📡 Включить бота")],
        [KeyboardButton("📊 Изменить таймфрейм"), KeyboardButton("📈 Изменить порог цены")],
        [KeyboardButton("💹 Изменить фильтр объёма"), KeyboardButton("🛠️ Сбросить настройки")],
        [KeyboardButton("⚙️ Управление индикаторами"), KeyboardButton("🔑 Управление обязательными")],
        [KeyboardButton("📏 Мин. индикаторов")]
    ]
    reply_markup = ReplyKeyboardMarkup(buttons, resize_keyboard=True)
    required_count = len(config.get('required_indicators', []))
    min_ind = config.get('min_indicators', 1)
    await update.message.reply_text(
        f"🚀 Бот активен: {config['bot_status']}\n"
        f"Таймфрейм: {config['timeframe']}\n"
        f"Порог цены: {config['price_change_threshold']}%\n"
        f"Фильтр объёма: {human_readable_number(config['volume_filter'])} USDT\n"
        f"Индикаторы: {sum(config['indicators_enabled'].values())}/{len(config['indicators_enabled'])} включено\n"
        f"Мин. индикаторов: {min_ind}\n"
        f"Обязательные: {required_count}/{len(config['indicators_enabled'])}\n\n"
        "Выберите действие:",
        reply_markup=reply_markup
    )

async def test_telegram(update: Update, context):
    await update.message.reply_text("✅ Тест: Бот работает!")

async def indicators(update: Update, context):
    config = load_config()
    indicators = config.get('indicators_enabled', {})
    buttons = [
        [InlineKeyboardButton(f"{'✅' if indicators.get('price_change', True) else '❌'} Price Change", callback_data='toggle_price_change')],
        [InlineKeyboardButton(f"{'✅' if indicators.get('rsi', True) else '❌'} RSI", callback_data='toggle_rsi')],
        [InlineKeyboardButton(f"{'✅' if indicators.get('macd', True) else '❌'} MACD", callback_data='toggle_macd')],
        [InlineKeyboardButton(f"{'✅' if indicators.get('volume_surge', True) else '❌'} Volume Surge", callback_data='toggle_volume_surge')],
        [InlineKeyboardButton(f"{'✅' if indicators.get('bollinger', True) else '❌'} Bollinger Bands", callback_data='toggle_bollinger')],
        [InlineKeyboardButton(f"{'✅' if indicators.get('adx', True) else '❌'} ADX", callback_data='toggle_adx')],
        [InlineKeyboardButton(f"{'✅' if indicators.get('rsi_macd_divergence', True) else '❌'} RSI/MACD Divergence", callback_data='toggle_rsi_macd_divergence')],
        [InlineKeyboardButton(f"{'✅' if indicators.get('candle_patterns', True) else '❌'} Candle Patterns", callback_data='toggle_candle_patterns')],
        [InlineKeyboardButton(f"{'✅' if indicators.get('volume_pre_surge', True) else '❌'} Volume Pre-Surge", callback_data='toggle_volume_pre_surge')],
        [InlineKeyboardButton(f"{'✅' if indicators.get('ema_crossover', True) else '❌'} EMA Crossover", callback_data='toggle_ema_crossover')],
        [InlineKeyboardButton(f"{'✅' if indicators.get('obv', True) else '❌'} OBV", callback_data='toggle_obv')]
    ]
    reply_markup = InlineKeyboardMarkup(buttons)
    await update.message.reply_text("⚙️ Управление индикаторами:", reply_markup=reply_markup)

async def required_indicators(update: Update, context):
    config = load_config()
    required = config.get('required_indicators', [])
    indicators = config.get('indicators_enabled', {})
    buttons = [
        [InlineKeyboardButton(f"{'🔒' if 'price_change' in required else '🔓'} Price Change", callback_data='toggle_required_price_change')],
        [InlineKeyboardButton(f"{'🔒' if 'rsi' in required else '🔓'} RSI", callback_data='toggle_required_rsi')],
        [InlineKeyboardButton(f"{'🔒' if 'macd' in required else '🔓'} MACD", callback_data='toggle_required_macd')],
        [InlineKeyboardButton(f"{'🔒' if 'volume_surge' in required else '🔓'} Volume Surge", callback_data='toggle_required_volume_surge')],
        [InlineKeyboardButton(f"{'🔒' if 'bollinger' in required else '🔓'} Bollinger Bands", callback_data='toggle_required_bollinger')],
        [InlineKeyboardButton(f"{'🔒' if 'adx' in required else '🔓'} ADX", callback_data='toggle_required_adx')],
        [InlineKeyboardButton(f"{'🔒' if 'rsi_macd_divergence' in required else '🔓'} RSI/MACD Divergence", callback_data='toggle_required_rsi_macd_divergence')],
        [InlineKeyboardButton(f"{'🔒' if 'candle_patterns' in required else '🔓'} Candle Patterns", callback_data='toggle_required_candle_patterns')],
        [InlineKeyboardButton(f"{'🔒' if 'volume_pre_surge' in required else '🔓'} Volume Pre-Surge", callback_data='toggle_required_volume_pre_surge')],
        [InlineKeyboardButton(f"{'🔒' if 'ema_crossover' in required else '🔓'} EMA Crossover", callback_data='toggle_required_ema_crossover')],
        [InlineKeyboardButton(f"{'🔒' if 'obv' in required else '🔓'} OBV", callback_data='toggle_required_obv')]
    ]
    reply_markup = InlineKeyboardMarkup(buttons)
    await update.message.reply_text("🔑 Управление обязательными индикаторами:", reply_markup=reply_markup)

async def toggle_indicator(update: Update, context):
    query = update.callback_query
    await query.answer()
    data = query.data
    config = load_config()
    if 'toggle_required_' in data:
        indicator = data.replace('toggle_required_', '')
        required = config.get('required_indicators', [])
        if indicator in required:
            required.remove(indicator)
        else:
            if indicator in config['indicators_enabled'] and config['indicators_enabled'][indicator]:
                required.append(indicator)
            else:
                await query.message.reply_text(f"Индикатор {indicator.upper()} не включён, нельзя сделать обязательным")
                return
        config['required_indicators'] = required
        save_config(config)
        log(f"Обязательный индикатор {indicator} изменён", level="info")
        await query.message.reply_text(f"Индикатор {indicator.upper()} {'обязательный' if indicator in required else 'не обязательный'}")
        # Обновляем сообщение с кнопками для required
        buttons = [
            [InlineKeyboardButton(f"{'🔒' if 'price_change' in required else '🔓'} Price Change", callback_data='toggle_required_price_change')],
            [InlineKeyboardButton(f"{'🔒' if 'rsi' in required else '🔓'} RSI", callback_data='toggle_required_rsi')],
            [InlineKeyboardButton(f"{'🔒' if 'macd' in required else '🔓'} MACD", callback_data='toggle_required_macd')],
            [InlineKeyboardButton(f"{'🔒' if 'volume_surge' in required else '🔓'} Volume Surge", callback_data='toggle_required_volume_surge')],
            [InlineKeyboardButton(f"{'🔒' if 'bollinger' in required else '🔓'} Bollinger Bands", callback_data='toggle_required_bollinger')],
            [InlineKeyboardButton(f"{'🔒' if 'adx' in required else '🔓'} ADX", callback_data='toggle_required_adx')],
            [InlineKeyboardButton(f"{'🔒' if 'rsi_macd_divergence' in required else '🔓'} RSI/MACD Divergence", callback_data='toggle_required_rsi_macd_divergence')],
            [InlineKeyboardButton(f"{'🔒' if 'candle_patterns' in required else '🔓'} Candle Patterns", callback_data='toggle_required_candle_patterns')],
            [InlineKeyboardButton(f"{'🔒' if 'volume_pre_surge' in required else '🔓'} Volume Pre-Surge", callback_data='toggle_required_volume_pre_surge')],
            [InlineKeyboardButton(f"{'🔒' if 'ema_crossover' in required else '🔓'} EMA Crossover", callback_data='toggle_required_ema_crossover')],
            [InlineKeyboardButton(f"{'🔒' if 'obv' in required else '🔓'} OBV", callback_data='toggle_required_obv')]
        ]
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text("🔑 Управление обязательными индикаторами:", reply_markup=reply_markup)
    else:
        indicator = data.replace('toggle_', '')
        config['indicators_enabled'][indicator] = not config['indicators_enabled'].get(indicator, True)
        save_config(config)
        log(f"Индикатор {indicator} изменён на {config['indicators_enabled'][indicator]}", level="info")
        await query.message.reply_text(f"Индикатор {indicator.upper()} {'включен' if config['indicators_enabled'][indicator] else 'выключен'}")
        # Обновляем сообщение с кнопками для enabled
        buttons = [
            [InlineKeyboardButton(f"{'✅' if config['indicators_enabled'].get('price_change', True) else '❌'} Price Change", callback_data='toggle_price_change')],
            [InlineKeyboardButton(f"{'✅' if config['indicators_enabled'].get('rsi', True) else '❌'} RSI", callback_data='toggle_rsi')],
            [InlineKeyboardButton(f"{'✅' if config['indicators_enabled'].get('macd', True) else '❌'} MACD", callback_data='toggle_macd')],
            [InlineKeyboardButton(f"{'✅' if config['indicators_enabled'].get('volume_surge', True) else '❌'} Volume Surge", callback_data='toggle_volume_surge')],
            [InlineKeyboardButton(f"{'✅' if config['indicators_enabled'].get('bollinger', True) else '❌'} Bollinger Bands", callback_data='toggle_bollinger')],
            [InlineKeyboardButton(f"{'✅' if config['indicators_enabled'].get('adx', True) else '❌'} ADX", callback_data='toggle_adx')],
            [InlineKeyboardButton(f"{'✅' if config['indicators_enabled'].get('rsi_macd_divergence', True) else '❌'} RSI/MACD Divergence", callback_data='toggle_rsi_macd_divergence')],
            [InlineKeyboardButton(f"{'✅' if config['indicators_enabled'].get('candle_patterns', True) else '❌'} Candle Patterns", callback_data='toggle_candle_patterns')],
            [InlineKeyboardButton(f"{'✅' if config['indicators_enabled'].get('volume_pre_surge', True) else '❌'} Volume Pre-Surge", callback_data='toggle_volume_pre_surge')],
            [InlineKeyboardButton(f"{'✅' if config['indicators_enabled'].get('ema_crossover', True) else '❌'} EMA Crossover", callback_data='toggle_ema_crossover')],
            [InlineKeyboardButton(f"{'✅' if config['indicators_enabled'].get('obv', True) else '❌'} OBV", callback_data='toggle_obv')]
        ]
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text("⚙️ Управление индикаторами:", reply_markup=reply_markup)

async def handle_message(update: Update, context):
    text = update.message.text
    config = load_config()

    if 'awaiting' in context.user_data:
        key = context.user_data['awaiting']
        try:
            if key == 'volume_filter':
                value = parse_human_number(text)
                config = update_config(key, value)
                await update.message.reply_text(f"✅ Фильтр объёма изменён на {human_readable_number(value)} USDT")
            elif key == 'price_change_threshold':
                value = float(text)
                config = update_config(key, value)
                await update.message.reply_text(f"✅ Порог цены изменён на {value}%")
            elif key == 'timeframe':
                if text not in ['1m', '5m', '15m', '1h']:
                    await update.message.reply_text("❌ Неверный таймфрейм. Доступны: 1m, 5m, 15m, 1h")
                    return
                config = update_config(key, text)
                await update.message.reply_text(f"✅ Таймфрейм изменён на {text}")
            elif key == 'min_indicators':
                value = int(text)
                if value < 1 or value > len(config['indicators_enabled']):
                    await update.message.reply_text(f"❌ Значение должно быть от 1 до {len(config['indicators_enabled'])}")
                    return
                config = update_config(key, value)
                await update.message.reply_text(f"✅ Мин. индикаторов изменено на {value}")
        except ValueError as e:
            await update.message.reply_text(f"❌ Ошибка: {str(e)}")
        context.user_data.pop('awaiting')
        return

    if text == "📴 Выключить бота":
        config = update_config('bot_status', False)
        await update.message.reply_text("📴 Бот выключен")
    elif text == "📡 Включить бота":
        config = update_config('bot_status', True)
        await update.message.reply_text("📡 Бот включен")
    elif text == "🛠️ Сбросить настройки":
        default_config = {
            'timeframe': '1m',
            'volume_filter': 5000000.0,
            'price_change_threshold': 0.5,
            'bot_status': True,
            'indicators_enabled': {
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
            },
            'min_indicators': 1,
            'required_indicators': []
        }
        save_config(default_config)
        await update.message.reply_text("🛠️ Настройки сброшены")
    elif text == "📊 Изменить таймфрейм":
        context.user_data['awaiting'] = 'timeframe'
        await update.message.reply_text("Введите таймфрейм (1m, 5m, 15m, 1h):")
    elif text == "💹 Изменить фильтр объёма":
        context.user_data['awaiting'] = 'volume_filter'
        await update.message.reply_text("Введите минимальный объём (например, 5M, 100K):")
    elif text == "📈 Изменить порог цены":
        context.user_data['awaiting'] = 'price_change_threshold'
        await update.message.reply_text("Введите порог изменения цены в % (например, 0.5):")
    elif text == "⚙️ Управление индикаторами":
        await indicators(update, context)
    elif text == "🔑 Управление обязательными":
        await required_indicators(update, context)
    elif text == "📏 Мин. индикаторов":
        context.user_data['awaiting'] = 'min_indicators'
        await update.message.reply_text("Введите минимальное количество индикаторов (целое число, от 1):")