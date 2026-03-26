# BBot | Economic RPG System for Discord

BBot is a comprehensive, multi-functional bot written in discord.py that combines an economy, classic RPG elements, and moderation tools. The main focus is on player interaction through business, a resource market, and character development.

### Key Technologies:

- Language: Python 3.10+
- Library: Discord.py 2.x
- Database: JSON file system.
- Visualization: Matplotlib (dynamic crypto exchange charts), Pillow (leaderboard card generation).

## Functional Modules

### 1. Business and Monopoly
- Company Registration: Creating companies with automatic generation of private text channels.
- Real Estate: Purchasing and managing offices, farms, factories, warehouses, and servers.
- Logistics system: Ability to connect production facilities to warehouses for automatic resource collection.
- Rental market: Dynamic rental of warehouse space between players with daily payments.
- Asset depreciation: Durability system requiring repairs using resources or currency.

### 2. Economy and Finance
- Banking System: Deposits, collateralized loans, daily capital taxes, and the server treasury (SB).
- Cryptocurrency Exchange: Creation of custom tokens, trading with dynamic rates (dependent on supply and demand), and visualization of trends on charts.
- City Store: Purchase/sale of items with limited stock and an automatic restocking system.

### 3. Character RPG System
- Features: Leveling up 6 core stats (strength, agility, intelligence, etc.) that affect performance.
- Professions: Employment in other players’ companies (worker, manager, agronomist, logistics specialist, security guard).
- Criminal Interaction: A theft system with a success rate dependent on stats and the ability to “restrain” the thief (temporary ban from the team).

### 4. Production and Crafting
- Workshop: Creating items using recipes (requires raw materials and money).
- Crafting Queue: Sequential production of up to 5 items simultaneously, with estimated completion times.
- Success Rate: The probability of creating an item depends on the player’s level and the recipe’s quality.

### 5. Moderation and Administration
- Control Tools: Multi-functional commands (mute/kick/ban/clear) and a warning system.
- Logging: Automatic logging of deleted/edited messages to a dedicated channel.
- Flexible Configuration: Configure tax rates, fees, and event channels directly via slash commands.

### Architectural Features
- Data Isolation: Each server has its own folder with JSON files, ensuring economic independence.
- Task Loops: Background execution of processes (resource allocation, crypto rate updates, credit debits).
- UI/UX: Use of Discord components (Modals, Select Menus, Buttons) to minimize manual text input



*The current version of the bot is available only in Ukrainian*


# BBot | Економічна RPG-система для Discord

BBot — це комплексний багатофункціональний бот, написаний на discord.py, що поєднує в собі економіку, елементи класичної RPG та інструменти модерації. Основний акцент зроблений на взаємодію гравців через бізнес, ринок ресурсів та розвиток персонажа.

### основні Технології

- Мова: Python 3.10+
- Бібліотека: Discord.py 2.x
- База даних: Файлова JSON-система з ізоляцією даних для кожного сервера (Guild Isolation).
- Візуалізація: Matplotlib (динамічні графіки криптобіржі), Pillow (генерація карток лідербордів).

## Функціональні модулі

### 1. Бізнес та Монополія (Monopoly Engine)

- Реєстрація компаній: Створення фірм із автоматичною генерацією приватних текстових каналів.
- Нерухомість: Купівля та управління офісами, фермами, заводами, складами та серверами.
- Система логістики: Можливість підключення виробничих об'єктів до складів для автоматичного збору ресурсів.
- Ринок оренди: Динамічна оренда складських приміщень між гравцями з добовою оплатою.
- Знос майна: Система міцності (durability), що потребує ремонту за ресурси або валюту.

### 2. Економіка та Фінанси

- Банківська система: Депозити, кредитування під заставу, добові податки на капітал та казначейство сервера (СБ).
- Криптовалютна біржа: Створення власних токенів, торгівля з динамічними курсами (залежать від попиту/пропозиції) та візуалізація трендів на графіках.
- Міський магазин: Купівля/продаж предметів із обмеженим стоком та системою автоматичного поповнення.

### 3. RPG-система персонажа

- Характеристики: Прокачування 6 основних статів (сила, спритність, інтелект тощо), що впливають на ефективність роботи.
- Професії: Працевлаштування в компанії інших гравців (робітник, менеджер, агроном, логіст, охоронець).
- Кримінальна взаємодія: Система крадіжок (steal) із шансом успіху, що залежить від статів, та можливістю "зв'язати" крадія (тимчасовий бан на команди).

### 4. Виробництво та Крафт

- Майстерня: Створення предметів за рецептами (використання сировини та грошей).
- Черга крафту: Послідовне виготовлення до 5 предметів одночасно з розрахунком часу завершення.
- Шанс успіху: Ймовірність створення предмета залежить від рівня гравця та якості рецепта.

### 5. Модерація та Адміністрування

- Інструменти контролю: Мулти-функціональні команди (mute/kick/ban/clear) та система варнів.
- Логування: Автоматичний запит видалених/редагованих повідомлень у спеціальний канал.
- Гнучкий конфіг: Налаштування податкових ставок, комісій та каналів для івентів прямо через слеш-команди.

### Особливості архітектури

- Data Isolation: Кожен сервер має власну папку з JSON-файлами, що забезпечує незалежність економік.
- Task Loops: Фонове виконання процесів (нарахування ресурсів, оновлення курсів крипти, списання кредитів).
- UI/UX: Використання сучасних компонентів Discord (Modals, Select Menus, Buttons) для мінімізації введення тексту вручну.

*Поточна версія бота доступна лише українською мовою*
