import discord
from discord.ext import commands
import datetime
import asyncio
from discord import app_commands
import pytz

# Setează fusul orar al Moscovei
MOSCOW_TZ = datetime.timezone(datetime.timedelta(hours=3))


def utc_to_moscow(utc_dt):
    """Convertește UTC în ora Moscovei (UTC+3)"""
    if utc_dt.tzinfo is None:
        utc_dt = utc_dt.replace(tzinfo=datetime.timezone.utc)
    return utc_dt.astimezone(MOSCOW_TZ)


def moscow_now():
    """Returnează data și ora curentă în fusul Moscovei"""
    return datetime.datetime.now(MOSCOW_TZ)


def format_moscow_time(dt):
    """Formatează un datetime în formatul orei Moscovei"""
    moscow_dt = utc_to_moscow(dt) if dt.tzinfo else dt.replace(tzinfo=MOSCOW_TZ)
    return moscow_dt.strftime("%H:%M")


def progress_bar(current, total, length=3):
    filled = int(length * current / total)
    empty = length - filled
    bar = "🟩" * filled + "⬛" * empty
    return f"{bar} ({current}/{total})"


def build_creator_embed(author, time_val, skills_val, deadline_val):
    def mark(v):
        return "❌ Не выбрано" if v is None else f"✅ {v}"

    embed = discord.Embed(
        title="📜 Создание контракта",
        description="Выберите параметры сбора:",
        color=0x2F3136
    )

    embed.set_author(
        name=f"Заказчик: {author.display_name}",
        icon_url=author.display_avatar.url
    )

    embed.add_field(name="⏳ Время на сбор", value=mark(time_val), inline=True)
    embed.add_field(name="⚔ С навыками", value=mark(skills_val), inline=True)
    embed.add_field(name="📅 Дедлайн", value=mark(deadline_val), inline=True)

    filled = sum(x is not None for x in [time_val, skills_val, deadline_val])
    embed.add_field(name="📊 Прогресс", value=progress_bar(filled, 3), inline=False)
    embed.set_footer(text="Панель активна 5 минут")

    return embed


def build_contract_embed(
        author,
        time_val,
        skills_val,
        deadline_val,
        participants=None,
        finish_time="--:--",
        status="🟢 Сбор",
        finished=False
):
    participants = participants or []

    embed = discord.Embed(
        title="📜 Новый контракт!",
        description="Поставьте ✅ чтобы участвовать!",
        color=0xF1C40F
    )

    embed.set_thumbnail(url=author.display_avatar.url)

    embed.add_field(name="👤 Заказчик", value=author.mention, inline=True)
    embed.add_field(name="⏳ Сбор", value=f"{time_val} мин", inline=True)
    embed.add_field(name="⚔ Навыки", value=skills_val, inline=True)

    embed.add_field(name="📅 Дедлайн", value=deadline_val, inline=True)
    embed.add_field(name="⏰ До", value=finish_time, inline=True)
    embed.add_field(name="📊 Статус", value=status, inline=True)

    if finished:
        plist = f"**{len(participants)}** чел."
    else:
        if participants:
            plist = "\n".join(
                f"{i + 1}. {p.mention} | {p.display_name}"
                for i, p in enumerate(participants)
            )
        else:
            plist = "Пока никого"

    embed.add_field(name="✅ Участники", value=plist, inline=False)

    embed.set_footer(
        text=f"ID: {author.id} • {format_moscow_time(discord.utils.utcnow())} (МСК)"
    )

    return embed


class ContractCreatorView(discord.ui.View):
    def __init__(self, author, bot):
        super().__init__(timeout=300)
        self.author = author
        self.bot = bot
        self.time_val = None
        self.skills_val = None
        self.deadline_val = None

    def preview(self):
        return build_creator_embed(
            self.author,
            self.time_val,
            self.skills_val,
            self.deadline_val
        )

    @discord.ui.select(
        placeholder="⏳ Время на сбор...",
        options=[
            discord.SelectOption(label="5 минут", value="5"),
            discord.SelectOption(label="10 минут", value="10"),
            discord.SelectOption(label="15 минут", value="15"),
            discord.SelectOption(label="20 минут", value="20"),
            discord.SelectOption(label="30 минут", value="30")
        ]
    )
    async def time_select(self, interaction, select):
        self.time_val = select.values[0]
        await interaction.response.edit_message(
            embed=self.preview(),
            view=self
        )

    @discord.ui.select(
        placeholder="⚔ С навыками?",
        options=[
            discord.SelectOption(label="Да", value="Да"),
            discord.SelectOption(label="Нет", value="Нет")
        ]
    )
    async def skill_select(self, interaction, select):
        self.skills_val = select.values[0]
        await interaction.response.edit_message(
            embed=self.preview(),
            view=self
        )

    @discord.ui.select(
        placeholder="📅 Дедлайн...",
        options=[
            discord.SelectOption(label="Сразу", value="Сразу"),
            discord.SelectOption(label="До нулей", value="До нулей"),
            discord.SelectOption(label="До рестарта", value="До рестарта"),
            discord.SelectOption(label="Без разницы", value="Без разницы")
        ]
    )
    async def deadline_select(self, interaction, select):
        self.deadline_val = select.values[0]
        await interaction.response.edit_message(
            embed=self.preview(),
            view=self
        )

    @discord.ui.button(label="📜 Опубликовать", style=discord.ButtonStyle.green)
    async def publish(self, interaction, _):
        if not all([self.time_val, self.skills_val, self.deadline_val]):
            await interaction.response.send_message(
                "Заполните все параметры!",
                ephemeral=True
            )
            return

        await interaction.response.defer(ephemeral=True)

        cog = interaction.client.get_cog("ContractCog")

        if cog is None:
            print("ContractCog not loaded")
            return

        # Folosim UTC pentru toate calculele interne
        now_utc = discord.utils.utcnow()
        end_time_utc = now_utc + datetime.timedelta(minutes=int(self.time_val))

        # Pentru afișare, convertim în ora Moscovei
        finish_time_moscow = format_moscow_time(end_time_utc)

        msg = await interaction.channel.send(
            embed=build_contract_embed(
                self.author,
                self.time_val,
                self.skills_val,
                self.deadline_val,
                [],
                finish_time_moscow
            )
        )

        await msg.add_reaction("✅")

        thread = await msg.create_thread(
            name=f"Контракт - {self.author.display_name}"
        )

        # Salvează în database cu UTC
        try:
            await self.bot.db.create_contract(
                interaction.guild.id,
                msg.id,
                self.author.id,
                int(self.time_val),
                self.skills_val,
                self.deadline_val,
                thread.id,
                end_time_utc,
                now_utc  # <- AI adăugat created_a
            )
            print(f"✅ Contract salvat în DB: {msg.id}")

            # Verifică dacă s-a salvat
            count = await self.bot.db.get_contract_count(interaction.guild.id)
            print(f"📊 Total contracte în DB: {count}")

        except Exception as e:
            print(f"❌ Eroare la salvare în DB: {e}")

        cog.contracts[msg.id] = {
            "author": self.author,
            "thread": thread,
            "participants": [],
            "time": self.time_val,
            "skills": self.skills_val,
            "deadline": self.deadline_val,
            "end_time": end_time_utc,
            "finish_time": finish_time_moscow,
            "guild_id": interaction.guild.id,
            "channel_id": interaction.channel.id
        }

        cog.tasks[msg.id] = asyncio.create_task(
            cog.countdown(msg)
        )
        print(f"✅ Task creat pentru contract {msg.id}")

        start_embed = discord.Embed(
            title="📜 Сбор на контракт!",
            color=discord.Color.orange()
        )

        start_embed.add_field(
            name="Заказчик",
            value=self.author.mention,
            inline=False
        )
        start_embed.add_field(
            name="Время",
            value=f"{self.time_val} мин",
            inline=True
        )
        start_embed.add_field(
            name="Навыки",
            value=self.skills_val,
            inline=True
        )
        start_embed.add_field(
            name="Дедлайн",
            value=self.deadline_val,
            inline=True
        )
        start_embed.set_footer(
            text=f"Поставьте ✅ на сообщение выше! • {format_moscow_time(now_utc)} (МСК)"
        )

        await thread.send(embed=start_embed)

        # Șterge mesajul de configurare
        await interaction.delete_original_response()


class ContractCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.contracts = {}
        self.tasks = {}

    async def restore_contracts(self):
        """Restabilește contractele active după restart"""
        await self.bot.wait_until_ready()

        for guild in self.bot.guilds:
            contracts = await self.bot.db.get_all_contracts(guild.id)

            for contract in contracts:
                if contract["status"] != "collecting":
                    continue

                # Găsește canalul cu mesajul
                channel = None
                for ch in guild.text_channels:
                    try:
                        msg = await ch.fetch_message(contract["message_id"])
                        channel = ch
                        break
                    except:
                        continue

                if not channel:
                    continue

                try:
                    message = await channel.fetch_message(contract["message_id"])
                except:
                    continue

                thread = guild.get_thread(contract["thread_id"])

                if not thread:
                    continue

                creator = guild.get_member(contract["creator_id"])

                # Asigură-te că end_time este timezone-aware UTC
                end_time = contract["end_time"]
                if isinstance(end_time, str):
                    end_time = datetime.datetime.strptime(end_time, '%Y-%m-%d %H:%M:%S')
                if end_time.tzinfo is None:
                    end_time = end_time.replace(tzinfo=datetime.timezone.utc)

                participants_ids = await self.bot.db.get_participants(
                    guild.id,
                    contract["message_id"]
                )

                participants = [
                    guild.get_member(uid)
                    for uid in participants_ids
                    if guild.get_member(uid)
                ]

                now_utc = discord.utils.utcnow()
                finish_time_moscow = format_moscow_time(end_time)

                # Verifică dacă contractul a expirat
                if end_time <= now_utc:
                    self.contracts[message.id] = {
                        "author": creator,
                        "thread": thread,
                        "participants": participants,
                        "time": contract["collect_time"],
                        "skills": contract["skills"],
                        "deadline": contract["deadline"],
                        "end_time": end_time,
                        "finish_time": finish_time_moscow,
                        "guild_id": guild.id,
                        "channel_id": channel.id
                    }
                    await self.finish_contract(message)
                    print(f"✔ Contract auto-closed after restart {message.id}")
                    continue

                # Contractul este încă activ
                self.contracts[message.id] = {
                    "author": creator,
                    "thread": thread,
                    "participants": participants,
                    "time": contract["collect_time"],
                    "skills": contract["skills"],
                    "deadline": contract["deadline"],
                    "end_time": end_time,
                    "finish_time": finish_time_moscow,
                    "guild_id": guild.id,
                    "channel_id": channel.id
                }

                self.tasks[message.id] = self.bot.loop.create_task(
                    self.countdown(message)
                )

                print(f"✔ Contract restored {message.id}")

    async def cog_load(self):
        self.bot.loop.create_task(self.restore_contracts())

    async def finish_contract(self, message):
        """Închide un contract"""
        if message.id not in self.contracts:
            print(f"❌ Contract {message.id} nu există în self.contracts")
            return

        data = self.contracts.get(message.id)
        if not data:
            return

        # IMPORTANT: Verifică dacă task-ul există înainte să-l anulezi
        # Dar nu anula dacă e același task care a apelat această funcție
        if message.id in self.tasks:
            task = self.tasks[message.id]
            # Verifică dacă task-ul nu e cel curent (cazul countdown)
            if task is not asyncio.current_task():
                task.cancel()
                del self.tasks[message.id]
                print(f"✅ Task anulat pentru contract {message.id}")
            else:
                print(f"ℹ️ Task-ul curent pentru {message.id} nu se auto-anulează")

        try:
            await self.bot.db.update_contract_status(
                message.guild.id,
                message.id,
                "closed"
            )
            print(f"✅ Contract {message.id} marcat ca closed în DB")
        except Exception as e:
            print(f"❌ Eroare la update DB pentru contract {message.id}: {e}")

        try:
            # Creează embed-ul pentru contract închis
            embed = build_contract_embed(
                data["author"],
                data["time"],
                data["skills"],
                data["deadline"],
                data["participants"],
                data["finish_time"],
                "🔴 Закрыто",
                finished=True
            )

            await message.edit(embed=embed)
            await message.clear_reactions()
            print(f"✅ Embed actualizat pentru contract {message.id}")

        except discord.NotFound:
            print(f"❌ Mesajul {message.id} nu mai există")
        except Exception as e:
            print(f"❌ Eroare la editarea mesajului {message.id}: {e}")

        try:
            plist = "\n".join(
                f"{i + 1}. {p.mention} | {p.display_name}"
                for i, p in enumerate(data["participants"])
            ) if data["participants"] else "Никого"

            end_embed = discord.Embed(
                title="🏁 Сбор окончен!",
                description=f"Участников: **{len(data['participants'])}**",
                color=discord.Color.green()
            )

            end_embed.add_field(
                name="👥 Список",
                value=plist,
                inline=False
            )

            end_embed.set_footer(
                text=f"{format_moscow_time(discord.utils.utcnow())} (МСК)"
            )

            await data["thread"].send(embed=end_embed)
            print(f"✅ Mesaj trimis în thread pentru contract {message.id}")

        except Exception as e:
            print(f"❌ Eroare la trimiterea mesajului în thread {message.id}: {e}")

        # Șterge din memory doar după ce ai terminat toate operațiile
        if message.id in self.contracts:
            # Nu șterge dacă e același task care a apelat
            if message.id in self.tasks and self.tasks[message.id] is asyncio.current_task():
                # Lasă task-ul să se termine natural
                pass
            else:
                del self.contracts[message.id]
                print(f"✅ Contract {message.id} șters din memory")

    async def countdown(self, message):
        """Countdown timer pentru contract"""
        try:
            print(f"🚀 Countdown pornit pentru contract {message.id}")

            while message.id in self.contracts:
                data = self.contracts[message.id]
                now_utc = discord.utils.utcnow()

                # Calculează timpul rămas
                remaining = (data["end_time"] - now_utc).total_seconds()

                # Dacă timpul a expirat
                if remaining <= 0:
                    print(f"⏰ Timp expirat pentru contract {message.id}")
                    # IMPORTANT: Nu mai anula task-ul aici, lasă-l să se termine natural
                    await self.finish_contract(message)
                    break  # Ieși din loop, dar nu anula task-ul

                embed = build_contract_embed(
                    data["author"],
                    data["time"],
                    data["skills"],
                    data["deadline"],
                    data["participants"],
                    data["finish_time"],
                    "🟢 Сбор"
                )

                try:
                    await message.edit(embed=embed)
                except discord.NotFound:
                    print(f"❌ Mesaj {message.id} nu a fost găsit pentru editare")
                    break
                except Exception as e:
                    print(f"❌ Eroare la actualizare mesaj {message.id}: {e}")

                # Verifică la fiecare secundă pentru precizie
                await asyncio.sleep(1)

            print(f"🏁 Countdown oprit pentru contract {message.id}")

        except asyncio.CancelledError:
            # Asta se întâmplă doar dacă altcineva anulează task-ul (ex: comanda /cc)
            print(f"🛑 Countdown pentru {message.id} a fost anulat manual")
            raise
        except Exception as e:
            print(f"💥 Eroare în countdown pentru {message.id}: {e}")

    @app_commands.command(name="cc", description="Закрыть контракт")
    @app_commands.describe(message_id="ID сообщения контракта")
    async def cc(self, interaction: discord.Interaction, message_id: str):
        await interaction.response.defer(ephemeral=True)

        try:
            msg_id = int(message_id)
        except ValueError:
            return await interaction.followup.send(
                "ID сообщения должен быть числом!",
                ephemeral=True
            )

        contract = await self.bot.db.get_contract(
            interaction.guild.id,
            msg_id
        )

        if not contract:
            return await interaction.followup.send(
                "Контракт не найден.",
                ephemeral=True
            )

        try:
            message = await interaction.channel.fetch_message(msg_id)
        except discord.NotFound:
            return await interaction.followup.send(
                "Сообщение с контрактом не найдено в этом канале.",
                ephemeral=True
            )

        await self.finish_contract(message)

        await interaction.followup.send(
            "✅ Контракт закрыт.",
            ephemeral=True
        )

    @app_commands.command(name="cs", description="Статистика контрактов")
    async def cs(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        contracts = await self.bot.db.get_all_contracts(interaction.guild.id)

        total = len(contracts)
        open_c = sum(1 for c in contracts if c["status"] == "collecting")
        closed = sum(1 for c in contracts if c["status"] == "closed")

        embed = discord.Embed(
            title="📊 Статистика контрактов",
            color=discord.Color.blurple()
        )

        embed.add_field(name="📜 Всего", value=total)
        embed.add_field(name="🟢 Открытых", value=open_c)
        embed.add_field(name="🔴 Закрытых", value=closed)

        embed.set_footer(
            text=f"{format_moscow_time(discord.utils.utcnow())} (МСК)"
        )

        await interaction.followup.send(
            embed=embed,
            ephemeral=True
        )

    @app_commands.command(name="cp", description="Создать контракт")
    async def create_contract(self, interaction: discord.Interaction):
        view = ContractCreatorView(interaction.user, self.bot)
        await interaction.response.send_message(
            embed=view.preview(),
            view=view,
            ephemeral=True
        )

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        # Verifică dacă e reacția corectă
        if str(payload.emoji) != "✅":
            return

        # Ignoră reacțiile botului
        if payload.user_id == self.bot.user.id:
            return

        # Verifică dacă mesajul este un contract activ
        if payload.message_id not in self.contracts:
            return

        guild = self.bot.get_guild(payload.guild_id)
        if not guild:
            return

        user = guild.get_member(payload.user_id)
        if user is None:
            return

        data = self.contracts[payload.message_id]

        # Verifică dacă user-ul nu e deja în listă
        if user not in data["participants"]:
            # Adaugă în database
            added = await self.bot.db.add_participant(
                payload.guild_id,
                payload.message_id,
                payload.user_id
            )

            if added:
                # Adaugă în memory
                data["participants"].append(user)

                # Obține canalul și mesajul
                channel = self.bot.get_channel(payload.channel_id)
                if not channel:
                    return

                try:
                    message = await channel.fetch_message(payload.message_id)
                except discord.NotFound:
                    return

                # Actualizează embed-ul cu noua listă de participanți
                embed = build_contract_embed(
                    data["author"],
                    data["time"],
                    data["skills"],
                    data["deadline"],
                    data["participants"],
                    data["finish_time"]
                )

                await message.edit(embed=embed)

                # Trimite mesaj în thread
                await data["thread"].send(
                    f"✅ {user.mention} записался на контракт!\n"
                    f"👥 Всего участников: **{len(data['participants'])}**"
                )

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        # Verifică dacă e reacția corectă
        if str(payload.emoji) != "✅":
            return

        # Verifică dacă mesajul este un contract activ
        if payload.message_id not in self.contracts:
            return

        guild = self.bot.get_guild(payload.guild_id)
        if not guild:
            return

        user = guild.get_member(payload.user_id)
        if user is None:
            return

        data = self.contracts[payload.message_id]

        # Verifică dacă user-ul e în listă
        if user in data["participants"]:
            # Elimină din database
            removed = await self.bot.db.remove_participant(
                payload.guild_id,
                payload.message_id,
                payload.user_id
            )

            if removed:
                # Elimină din memory
                data["participants"].remove(user)

                # Obține canalul și mesajul
                channel = self.bot.get_channel(payload.channel_id)
                if not channel:
                    return

                try:
                    message = await channel.fetch_message(payload.message_id)
                except discord.NotFound:
                    return

                # Actualizează embed-ul cu noua listă de participanți
                embed = build_contract_embed(
                    data["author"],
                    data["time"],
                    data["skills"],
                    data["deadline"],
                    data["participants"],
                    data["finish_time"]
                )

                await message.edit(embed=embed)

                # Trimite mesaj în thread
                await data["thread"].send(
                    f"❌ {user.mention} вышел из контракта.\n"
                    f"👥 Осталось участников: **{len(data['participants'])}**"
                )


async def setup(bot):
    await bot.add_cog(ContractCog(bot))