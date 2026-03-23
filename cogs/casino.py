import discord
from discord.ext import commands, tasks
from discord import app_commands
import json, os, time, random, asyncio
from datetime import time as dt_time, timezone
from utils import load_guild_json, save_guild_json

DATA_FILE = "users.json"
ECONOMY_CONFIG = "economy_config.json"
CASINO_CONFIG = "casino_config.json"

def get_casino_config(guild_id: int):
    config = load_guild_json(guild_id, CASINO_CONFIG)
    if not config:
        config = {
            "bank": 0,
            "max_bet": 1000
        }
        save_guild_json(guild_id, CASINO_CONFIG, config)
    return config

def update_activity(user_data):
    user_data["last_casino_action"] = int(time.time())

def process_bet(user_data, casino_config, bet_amount: int) -> bool:
    if bet_amount <= 0: return False
    if bet_amount > casino_config.get("max_bet", 1000): return False
    if user_data.get("chips", 0) < bet_amount: return False
    if user_data.get("restricted_casino"): return False

    user_data["chips"] -= bet_amount
    update_activity(user_data)
    return True

class GenericBetModal(discord.ui.Modal, title="Встановлення ставки"):
    def __init__(self, game_view):
        super().__init__()
        self.game_view = game_view
        self.bet_input = discord.ui.TextInput(
            label="Ставка (у фішках)", 
            placeholder="Наприклад: 50", 
            style=discord.TextStyle.short, 
            required=True
        )
        self.add_item(self.bet_input)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            bet = int(self.bet_input.value)
            if bet <= 0: raise ValueError
            self.game_view.bet = bet
            await interaction.response.edit_message(embed=self.game_view.build_embed(), view=self.game_view)
        except ValueError:
            await interaction.response.send_message("❌ Введіть коректне додатне число.", ephemeral=True)

class BuyChipsModal(discord.ui.Modal, title="Купівля фішок"):
    amount_input = discord.ui.TextInput(label="Кількість (1 фішка = 100 AC)", style=discord.TextStyle.short, required=True)
    async def on_submit(self, interaction: discord.Interaction):
        try:
            amount = int(self.amount_input.value)
            if amount <= 0: raise ValueError
        except: return await interaction.response.send_message("❌ Некоректне число.", ephemeral=True)

        guild_id = interaction.guild.id
        data = load_guild_json(guild_id, DATA_FILE)
        uid = str(interaction.user.id)
        if uid not in data: data[uid] = {}
        user = data[uid]
        
        cost = amount * 100
        if user.get("balance", 0) < cost:
            return await interaction.response.send_message(f"❌ Недостатньо AC. Потрібно `{cost}`.", ephemeral=True)
            
        user["balance"] -= cost
        user["chips"] = user.get("chips", 0) + amount
        update_activity(user)
        conf = get_casino_config(guild_id)
        conf["bank"] += amount 
        save_guild_json(guild_id, DATA_FILE, data)
        save_guild_json(guild_id, CASINO_CONFIG, conf)
        await interaction.response.send_message(f"✅ Ви купили `{amount}` фішок.", ephemeral=True)

class SellChipsModal(discord.ui.Modal, title="Продаж фішок"):
    amount_input = discord.ui.TextInput(label="Кількість (1 фішка = 90 AC)", style=discord.TextStyle.short, required=True)
    async def on_submit(self, interaction: discord.Interaction):
        try:
            amount = int(self.amount_input.value)
            if amount <= 0: raise ValueError
        except: return await interaction.response.send_message("❌ Некоректне число.", ephemeral=True)

        guild_id = interaction.guild.id
        data = load_guild_json(guild_id, DATA_FILE)
        uid = str(interaction.user.id)
        user = data.get(uid, {})
        
        if user.get("chips", 0) < amount:
            return await interaction.response.send_message("❌ Недостатньо фішок.", ephemeral=True)
            
        revenue = amount * 90
        user["chips"] -= amount
        user["balance"] = user.get("balance", 0) + revenue
        conf = get_casino_config(guild_id)
        conf["bank"] -= amount
        save_guild_json(guild_id, DATA_FILE, data)
        save_guild_json(guild_id, CASINO_CONFIG, conf)
        await interaction.response.send_message(f"💸 Ви обміняли `{amount}` фішок на `{revenue} AC`.", ephemeral=True)

class SlotsGameView(discord.ui.View):
    def __init__(self, cog, player_id: int):
        super().__init__(timeout=300)
        self.cog = cog
        self.player_id = player_id
        self.bet = 0
        self.last_result_text = "Зробіть ставку та натисніть 'Крутити'!"
        self.embed_color = 0x2b2d31

    def build_embed(self) -> discord.Embed:
        return discord.Embed(title="🎰 Ігрові Автомати", description=f"**Поточна ставка:** `{self.bet}` фішок\n\n{self.last_result_text}", color=self.embed_color)

    @discord.ui.button(label="Встановити ставку", style=discord.ButtonStyle.primary)
    async def btn_set_bet(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.player_id: return await interaction.response.send_message("Це не ваш автомат!", ephemeral=True)
        await interaction.response.send_modal(GenericBetModal(self))

    @discord.ui.button(label="КРУТИТИ 🎰", style=discord.ButtonStyle.success)
    async def btn_spin(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.player_id: return await interaction.response.send_message("Це не ваш автомат!", ephemeral=True)
        if self.bet <= 0: return await interaction.response.send_message("Встановіть ставку!", ephemeral=True)

        guild_id = interaction.guild.id
        data = load_guild_json(guild_id, DATA_FILE)
        conf = get_casino_config(guild_id)
        user = data.get(str(interaction.user.id), {})

        if not process_bet(user, conf, self.bet):
            return await interaction.response.send_message("❌ Недостатньо фішок або ліміт!", ephemeral=True)

        conf["bank"] += self.bet
        save_guild_json(guild_id, DATA_FILE, data)
        save_guild_json(guild_id, CASINO_CONFIG, conf)

        for item in self.children: item.disabled = True
        self.embed_color = 0x2b2d31
        spin = "🌀"
        self.last_result_text = f"`[ {spin} | {spin} | {spin} ]` Крутимо..."
        await interaction.response.edit_message(embed=self.build_embed(), view=self)
        
        emojis = ["🍒", "🍋", "🔔", "🍉", "⭐", "💎"]
        roll = random.randint(1, 1000)
        if roll <= 600:
            res = [random.choice(emojis), random.choice(emojis), random.choice(emojis)] if random.random() > 0.3 else [random.choice(emojis)] * 2 + [random.choice(emojis)]
            mult = 0
        elif roll <= 800:
            a, b = random.choice(emojis), random.choice(emojis)
            res = [a, a, b]; random.shuffle(res)
            mult = 0.5
        elif roll <= 930:
            res = [random.choice(["🍒", "🍋", "🔔", "🍉"])] * 3
            mult = 2
        elif roll <= 990:
            res = ["⭐"] * 3
            mult = 5
        else:
            res = ["💎"] * 3
            mult = 20

        if mult > 0 and (self.bet * mult) > conf["bank"]: mult, res[2] = 0, "💀"

        payout = int(self.bet * mult)
        
        await asyncio.sleep(0.8)
        self.last_result_text = f"`[ {res[0]} | {spin} | {spin} ]`"
        await interaction.message.edit(embed=self.build_embed(), view=self)
        await asyncio.sleep(0.8)
        self.last_result_text = f"`[ {res[0]} | {res[1]} | {spin} ]`"
        await interaction.message.edit(embed=self.build_embed(), view=self)
        await asyncio.sleep(1.2 if res[0] == res[1] else 0.8)
        
        final_str = f"**РЕЗУЛЬТАТ:**\n`[ {res[0]} | {res[1]} | {res[2]} ]`\n\n"
        
        if payout > 0:
            user["chips"] += payout
            conf["bank"] -= payout
            self.embed_color = 0xf1c40f if mult >= 5 else 0x2ecc71
            self.last_result_text = final_str + f"🎉 Виграш `{payout}` фішок! (**{mult}x**)"
        else:
            self.embed_color = 0xe74c3c
            self.last_result_text = final_str + f"💀 Програш."

        save_guild_json(guild_id, DATA_FILE, data)
        save_guild_json(guild_id, CASINO_CONFIG, conf)

        for item in self.children: item.disabled = False
        await interaction.message.edit(embed=self.build_embed(), view=self)

class RouletteExactModal(discord.ui.Modal, title="Точне число"):
    num_input = discord.ui.TextInput(label="Введіть число (0-36)", style=discord.TextStyle.short)
    def __init__(self, view):
        super().__init__()
        self.game_view = view
    async def on_submit(self, interaction: discord.Interaction):
        try:
            val = int(self.num_input.value)
            if not (0 <= val <= 36): raise ValueError
            self.game_view.bet_type = "exact"
            self.game_view.bet_value = str(val)
            self.game_view.payout_mult = 36
            await interaction.response.edit_message(embed=self.game_view.build_embed(), view=self.game_view)
        except:
            await interaction.response.send_message("Введіть число від 0 до 36!", ephemeral=True)

class RouletteTypeSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="🔴 Червоне", value="color_Червоне", description="2x"),
            discord.SelectOption(label="⬛ Чорне", value="color_Чорне", description="2x"),
            discord.SelectOption(label="🔵 Парне", value="evenodd_Парне", description="2x"),
            discord.SelectOption(label="🟡 Непарне", value="evenodd_Непарне", description="2x"),
            discord.SelectOption(label="Дюжина 1-12", value="dozen_1-12", description="3x"),
            discord.SelectOption(label="Дюжина 13-24", value="dozen_13-24", description="3x"),
            discord.SelectOption(label="Дюжина 25-36", value="dozen_25-36", description="3x")
        ]
        super().__init__(placeholder="Оберіть тип ставки...", min_values=1, max_values=1, options=options, row=0)

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.view.player_id: return await interaction.response.send_message("Не ваш стіл!", ephemeral=True)
        t, v = self.values[0].split("_")
        self.view.bet_type = t
        self.view.bet_value = v
        self.view.payout_mult = 2 if t in ["color", "evenodd"] else 3
        await interaction.response.edit_message(embed=self.view.build_embed(), view=self.view)

class RouletteGameView(discord.ui.View):
    def __init__(self, cog, player_id: int):
        super().__init__(timeout=300)
        self.cog = cog
        self.player_id = player_id
        self.bet = 0
        self.bet_type = None
        self.bet_value = "Не обрано"
        self.payout_mult = 0
        self.embed_color = 0x2b2d31
        self.result_text = "Зробіть ставку та натисніть 'Крутити'!"
        self.add_item(RouletteTypeSelect())

    def build_embed(self) -> discord.Embed:
        desc = f"**Ставка:** `{self.bet}` фішок\n**На що ставимо:** `{self.bet_value}` (Множник: {self.payout_mult}x)\n\n{self.result_text}"
        return discord.Embed(title="🎰 Рулетка", description=desc, color=self.embed_color)

    @discord.ui.button(label="Сума", style=discord.ButtonStyle.primary, row=1)
    async def btn_bet(self, interaction, button):
        if interaction.user.id != self.player_id: return
        await interaction.response.send_modal(GenericBetModal(self))

    @discord.ui.button(label="Точне число", style=discord.ButtonStyle.secondary, row=1)
    async def btn_exact(self, interaction, button):
        if interaction.user.id != self.player_id: return
        await interaction.response.send_modal(RouletteExactModal(self))

    @discord.ui.button(label="КРУТИТИ 🎲", style=discord.ButtonStyle.success, row=1)
    async def btn_spin(self, interaction, button):
        if interaction.user.id != self.player_id: return
        if self.bet <= 0 or not self.bet_type: return await interaction.response.send_message("Встановіть суму і виберіть тип ставки!", ephemeral=True)

        guild_id = interaction.guild.id
        data = load_guild_json(guild_id, DATA_FILE)
        conf = get_casino_config(guild_id)
        user = data.get(str(interaction.user.id), {})

        if not process_bet(user, conf, self.bet): return await interaction.response.send_message("❌ Недостатньо фішок або ліміт!", ephemeral=True)
        conf["bank"] += self.bet

        for item in self.children: item.disabled = True
        self.embed_color = 0x2b2d31
        self.result_text = "Колесо крутиться... 🌀"
        await interaction.response.edit_message(embed=self.build_embed(), view=self)

        await asyncio.sleep(2.0)
        
        result_num = random.randint(0, 36)
        if conf["bank"] < (self.bet * self.payout_mult) * 2 and random.random() < 0.15: result_num = 0

        is_red = result_num in [1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36]
        c_emo = "🟢" if result_num == 0 else ("🔴" if is_red else "⬛")
        
        win = False
        if self.bet_type == "color" and ((self.bet_value == "Червоне" and is_red) or (self.bet_value == "Чорне" and not is_red and result_num != 0)): win = True
        elif self.bet_type == "evenodd" and result_num != 0 and ((self.bet_value == "Парне" and result_num % 2 == 0) or (self.bet_value == "Непарне" and result_num % 2 != 0)): win = True
        elif self.bet_type == "dozen":
            if self.bet_value == "1-12" and 1 <= result_num <= 12: win = True
            elif self.bet_value == "13-24" and 13 <= result_num <= 24: win = True
            elif self.bet_value == "25-36" and 25 <= result_num <= 36: win = True
        elif self.bet_type == "exact" and str(result_num) == self.bet_value: win = True

        if win:
            payout = self.bet * self.payout_mult
            user["chips"] += payout
            conf["bank"] -= payout
            self.embed_color = 0x2ecc71
            self.result_text = f"Випало: {c_emo} **{result_num}**\n🎉 Виграш `{payout}` фішок!"
        else:
            self.embed_color = 0xe74c3c
            self.result_text = f"Випало: {c_emo} **{result_num}**\n💀 Програш."

        save_guild_json(guild_id, DATA_FILE, data)
        save_guild_json(guild_id, CASINO_CONFIG, conf)

        for item in self.children: item.disabled = False
        await interaction.message.edit(embed=self.build_embed(), view=self)

class DiceGameView(discord.ui.View):
    def __init__(self, cog, player_id: int):
        super().__init__(timeout=300)
        self.cog = cog
        self.player_id = player_id
        self.bet = 0
        self.embed_color = 0x2b2d31
        self.result_text = "Зробіть ставку та натисніть 'Кинути'!"

    def build_embed(self) -> discord.Embed:
        return discord.Embed(title="🎲 Кості проти Дилера", description=f"**Ставка:** `{self.bet}` фішок\n\n{self.result_text}", color=self.embed_color)

    @discord.ui.button(label="Сума", style=discord.ButtonStyle.primary)
    async def btn_bet(self, interaction, button):
        if interaction.user.id != self.player_id: return
        await interaction.response.send_modal(GenericBetModal(self))

    @discord.ui.button(label="КИНУТИ 🎲", style=discord.ButtonStyle.success)
    async def btn_roll(self, interaction, button):
        if interaction.user.id != self.player_id: return
        if self.bet <= 0: return await interaction.response.send_message("Встановіть ставку!", ephemeral=True)

        guild_id = interaction.guild.id
        data = load_guild_json(guild_id, DATA_FILE)
        conf = get_casino_config(guild_id)
        user = data.get(str(interaction.user.id), {})

        if not process_bet(user, conf, self.bet): return await interaction.response.send_message("❌ Недостатньо фішок або ліміт!", ephemeral=True)
        conf["bank"] += self.bet

        p_roll, d_roll = random.randint(2, 12), random.randint(2, 12)
        if random.random() < 0.15: d_roll = min(12, d_roll + 2)

        if p_roll > d_roll:
            payout = self.bet * 2
            user["chips"] += payout
            conf["bank"] -= payout
            self.embed_color = 0x2ecc71
            self.result_text = f"Ваш кидок: **{p_roll}** | Дилер: **{d_roll}**\n🎉 Виграш `{payout}` фішок!"
        else:
            self.embed_color = 0xe74c3c
            self.result_text = f"Ваш кидок: **{p_roll}** | Дилер: **{d_roll}**\n💀 Програш."

        save_guild_json(guild_id, DATA_FILE, data)
        save_guild_json(guild_id, CASINO_CONFIG, conf)
        await interaction.response.edit_message(embed=self.build_embed(), view=self)

class MineButton(discord.ui.Button):
    def __init__(self, index: int, row: int):
        super().__init__(style=discord.ButtonStyle.success, label="\u200b", row=row)
        self.index = index
    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.view.player_id: return
        await self.view.process_click(interaction, self)

class CashoutButton(discord.ui.Button):
    def __init__(self, row: int):
        super().__init__(style=discord.ButtonStyle.secondary, label="Забрати ставку", emoji="💰", row=row)
    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.view.player_id: return
        await self.view.cashout(interaction)

class MinesGameView(discord.ui.View):
    def __init__(self, cog, player_id, guild_id, bet, total_cells, mines_count):
        super().__init__(timeout=600)
        self.cog = cog
        self.player_id = player_id
        self.guild_id = guild_id
        self.bet = bet
        self.total_cells = total_cells
        self.mines_count = mines_count
        self.safe_clicks = 0
        self.is_game_over = False
        self.mine_positions = random.sample(range(total_cells), mines_count)

        for i in range(total_cells): self.add_item(MineButton(index=i, row=i//5))
        self.cashout_btn = CashoutButton(row=4)
        self.add_item(self.cashout_btn)

    def get_mult(self):
        if self.safe_clicks == 0: return 1.0
        prob = 1.0
        for i in range(self.safe_clicks): prob *= (self.total_cells - self.mines_count - i) / (self.total_cells - i)
        return round((1.0 / prob) * 0.95, 2)

    def build_embed(self, status="playing"):
        mult = self.get_mult()
        win = int(self.bet * mult)
        if status == "playing":
            return discord.Embed(title="💣 Міни", description=f"Безпечних: `{self.safe_clicks}`\nМножник: **{mult}x**\nПоточний виграш: `{win}`", color=0x3498db)
        elif status == "won":
            return discord.Embed(title="🎉 ВИГРАШ!", description=f"Фінальний множник: **{mult}x**\nОтримано: `{win}` фішок", color=0x2ecc71)
        return discord.Embed(title="💀 БУУУМ!", description=f"Ви натрапили на міну. Ставка згоріла.", color=0xe74c3c)

    def reveal_all(self, hit=None):
        for item in self.children:
            item.disabled = True
            if isinstance(item, MineButton):
                if item.index in self.mine_positions:
                    item.style, item.emoji = discord.ButtonStyle.danger, ("💥" if item.index == hit else "💣")
                elif item.style == discord.ButtonStyle.success:
                    item.style, item.emoji = discord.ButtonStyle.secondary, "💎"

    async def process_click(self, interaction, button):
        if self.is_game_over: return
        if button.index in self.mine_positions:
            self.is_game_over = True
            self.reveal_all(hit=button.index)
            await interaction.response.edit_message(embed=self.build_embed("lost"), view=self)
        else:
            self.safe_clicks += 1
            button.style, button.emoji, button.disabled = discord.ButtonStyle.primary, "💎", True
            if self.safe_clicks == (self.total_cells - self.mines_count): await self.cashout(interaction, True)
            else:
                self.cashout_btn.label, self.cashout_btn.style = f"Забрати {int(self.bet * self.get_mult())} 🪙", discord.ButtonStyle.success
                await interaction.response.edit_message(embed=self.build_embed(), view=self)

    async def cashout(self, interaction, auto=False):
        if self.is_game_over: return
        self.is_game_over = True
        win = int(self.bet * self.get_mult())

        data = load_guild_json(self.guild_id, DATA_FILE)
        conf = get_casino_config(self.guild_id)
        if str(self.player_id) in data:
            data[str(self.player_id)]["chips"] += win
            conf["bank"] -= win
            save_guild_json(self.guild_id, DATA_FILE, data)
            save_guild_json(self.guild_id, CASINO_CONFIG, conf)

        self.reveal_all()
        embed = self.build_embed("won")
        if auto: embed.description = "🏆 **ІДЕАЛЬНА ГРА!**\n" + embed.description
        await interaction.response.edit_message(embed=embed, view=self)

class MinesSetupView(discord.ui.View):
    def __init__(self, cog, player_id):
        super().__init__(timeout=120)
        self.cog, self.player_id, self.bet, self.mines_count = cog, player_id, 0, 3

    def build_embed(self):
        return discord.Embed(title="💣 Налаштування Мін", description=f"**Поле:** 5x4 (20 клітинок)\n**Ставка:** `{self.bet}`\n**Кількість мін:** `{self.mines_count}`", color=0x3498db)

    @discord.ui.select(options=[discord.SelectOption(label=f"{i} мін", value=str(i)) for i in [3, 5, 7, 10, 15]], row=0)
    async def sel_mines(self, interaction, select):
        if interaction.user.id != self.player_id: return
        self.mines_count = int(select.values[0])
        await interaction.response.edit_message(embed=self.build_embed(), view=self)

    @discord.ui.button(label="Сума", style=discord.ButtonStyle.primary, row=1)
    async def btn_bet(self, interaction, button):
        if interaction.user.id != self.player_id: return
        await interaction.response.send_modal(GenericBetModal(self))

    @discord.ui.button(label="ПОЧАТИ ГРУ", style=discord.ButtonStyle.success, row=1)
    async def btn_start(self, interaction, button):
        if interaction.user.id != self.player_id: return
        if self.bet <= 0: return await interaction.response.send_message("Встановіть ставку!", ephemeral=True)

        guild_id = interaction.guild.id
        data, conf = load_guild_json(guild_id, DATA_FILE), get_casino_config(guild_id)
        user = data.get(str(interaction.user.id), {})

        if not process_bet(user, conf, self.bet): return await interaction.response.send_message("❌ Недостатньо фішок або ліміт!", ephemeral=True)
        conf["bank"] += self.bet
        save_guild_json(guild_id, DATA_FILE, data); save_guild_json(guild_id, CASINO_CONFIG, conf)

        game_view = MinesGameView(self.cog, self.player_id, guild_id, self.bet, 20, self.mines_count)
        await interaction.response.edit_message(embed=game_view.build_embed(), view=game_view)


class CasinoGamesSelect(discord.ui.Select):
    def __init__(self, cog):
        self.cog = cog
        options = [
            discord.SelectOption(label="Слоти", value="slots", description="Ігрові автомати (3 в ряд)", emoji="🎰"),
            discord.SelectOption(label="Рулетка", value="roulette", description="Класична рулетка з фішками", emoji="🎡"),
            discord.SelectOption(label="Міни", value="mines", description="Пошук діамантів", emoji="💣"),
            discord.SelectOption(label="Кості", value="dice", description="Гра проти дилера", emoji="🎲")
        ]
        super().__init__(placeholder="Виберіть гру...", min_values=1, max_values=1, options=options, row=1)

    async def callback(self, interaction: discord.Interaction):
        game = self.values[0]
        pid = interaction.user.id
        
        if game == "slots": view = SlotsGameView(self.cog, pid)
        elif game == "roulette": view = RouletteGameView(self.cog, pid)
        elif game == "dice": view = DiceGameView(self.cog, pid)
        elif game == "mines": view = MinesSetupView(self.cog, pid)

        await interaction.response.send_message(embed=view.build_embed(), view=view)
        self.placeholder = "Виберіть гру..."
        await interaction.message.edit(view=self.view)

class CasinoMainView(discord.ui.View):
    def __init__(self, cog):
        super().__init__(timeout=None)
        self.add_item(CasinoGamesSelect(cog))

    @discord.ui.button(label="Купити фішки", style=discord.ButtonStyle.success, emoji="🪙", row=0)
    async def btn_buy(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(BuyChipsModal())

    @discord.ui.button(label="Продати фішки", style=discord.ButtonStyle.secondary, emoji="💵", row=0)
    async def btn_sell(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(SellChipsModal())


class CasinoCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.auto_cashout_loop.start()
        self.casino_bank_sync_loop.start()

    def cog_unload(self):
        self.auto_cashout_loop.cancel()
        self.casino_bank_sync_loop.cancel()

    @tasks.loop(minutes=5)
    async def auto_cashout_loop(self):
        if not os.path.exists("server_data"): return
        current_time = int(time.time())
        for gid in os.listdir("server_data"):
            try:
                guild_id = int(gid)
                data = load_guild_json(guild_id, DATA_FILE)
                updated = False
                for uid, user in data.items():
                    chips = user.get("chips", 0)
                    if chips > 0 and (current_time - user.get("last_casino_action", 0)) > 1800:
                        ac_amount = chips * 90
                        user["chips"], user["balance"] = 0, user.get("balance", 0) + ac_amount
                        updated = True
                        guild = self.bot.get_guild(guild_id)
                        if guild and (member := guild.get_member(int(uid))):
                            try: await member.send(f"🎰 Ви були АФК 30 хв. Ваші `{chips}` фішок обміняні на `{ac_amount} AC`.")
                            except: pass
                if updated: save_guild_json(guild_id, DATA_FILE, data)
            except: pass

    @tasks.loop(time=dt_time(hour=1, minute=0, tzinfo=timezone.utc))
    async def casino_bank_sync_loop(self):
        if not os.path.exists("server_data"): return
        for gid in os.listdir("server_data"):
            try:
                guild_id = int(gid)
                eco_conf, cas_conf = load_guild_json(guild_id, ECONOMY_CONFIG), get_casino_config(guild_id)
                
                target = int(eco_conf.get("server_bank", 0) * 0.10)
                curr = cas_conf.get("bank", 0)
                
                if curr > target: eco_conf["server_bank"] += (curr - target)
                elif curr < target: eco_conf["server_bank"] -= (target - curr)
                
                cas_conf["bank"] = target
                save_guild_json(guild_id, ECONOMY_CONFIG, eco_conf)
                save_guild_json(guild_id, CASINO_CONFIG, cas_conf)
            except: pass

    @auto_cashout_loop.before_loop
    @casino_bank_sync_loop.before_loop
    async def before_loops(self):
        await self.bot.wait_until_ready()

    @app_commands.command(name="casino", description="Відкрити головне меню казино (Каса та Ігри)")
    @app_commands.guild_only()
    async def casino_menu(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="🎰 Вітаємо в Казино!",
            description="Обмінюйте AC на фішки та випробовуйте удачу!\n\n"
                        "**Курс:** 🪙 Купівля: 1 = 100 AC | 💵 Продаж: 1 = 90 AC\n\n"
                        "Оберіть дію або гру в меню нижче 👇",
            color=0x9b59b6
        )
        if interaction.guild.icon: embed.set_thumbnail(url=interaction.guild.icon.url)
        await interaction.response.send_message(embed=embed, view=CasinoMainView(self))

    @app_commands.command(name="chips", description="Переглянути свій баланс фішок казино")
    @app_commands.guild_only()
    async def chips_balance(self, interaction: discord.Interaction):
        data = load_guild_json(interaction.guild.id, DATA_FILE)
        user = data.get(str(interaction.user.id), {})
        embed = discord.Embed(title="Каса Казино", description=f"🪙 Фішки: `{user.get('chips', 0)}`\n💵 Готівка: `{user.get('balance', 0)} AC`", color=0xf1c40f)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="casino_set_maxbet", description="[АДМІН] Встановити максимальну ставку (у фішках)")
    @app_commands.default_permissions(administrator=True)
    async def set_maxbet(self, interaction: discord.Interaction, max_chips: int):
        conf = get_casino_config(interaction.guild.id)
        conf["max_bet"] = max_chips
        save_guild_json(interaction.guild.id, CASINO_CONFIG, conf)
        await interaction.response.send_message(f"Макс. ставка: `{max_chips}` фішок.", ephemeral=True)

    @app_commands.command(name="casino_fund", description="[АДМІН] Поповнити банк казино напряму")
    @app_commands.default_permissions(administrator=True)
    async def fund_casino(self, interaction: discord.Interaction, chips_amount: int):
        conf = get_casino_config(interaction.guild.id)
        conf["bank"] += chips_amount
        save_guild_json(interaction.guild.id, CASINO_CONFIG, conf)
        await interaction.response.send_message(f"Банк поповнено на `{chips_amount}`. Разом: `{conf['bank']}`.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(CasinoCog(bot))