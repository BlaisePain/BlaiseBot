import discord
from discord.ext import commands, tasks
from discord import app_commands
import datetime
import calendar
from zoneinfo import ZoneInfo

MONTHS = {
    1:"Январь",2:"Февраль",3:"Март",4:"Апрель",
    5:"Май",6:"Июнь",7:"Июль",8:"Август",
    9:"Сентябрь",10:"Октябрь",11:"Ноябрь",12:"Декабрь"
}


# ---------------- MODAL ---------------- #

class BirthdayModal(discord.ui.Modal):

    def __init__(self, cog):
        super().__init__(title="Добавить день рождения")
        self.cog = cog

        self.day = discord.ui.TextInput(label="День")
        self.month = discord.ui.TextInput(label="Месяц")

        self.add_item(self.day)
        self.add_item(self.month)

    async def on_submit(self, interaction: discord.Interaction):

        try:
            day = int(self.day.value)
            month = int(self.month.value)
        except:
            await interaction.response.send_message(
                "❌ Неверная дата",
                ephemeral=True
            )
            return

        if month < 1 or month > 12:
            await interaction.response.send_message("❌ Месяц 1-12", ephemeral=True)
            return

        max_day = calendar.monthrange(2024, month)[1]

        if day < 1 or day > max_day:
            await interaction.response.send_message(
                f"❌ Максимум {max_day} дней",
                ephemeral=True
            )
            return

        await self.cog.bot.db.set_birthday(
            interaction.user.id,
            interaction.user.display_name,
            day,
            month
        )

        await interaction.response.send_message(
            "✅ День рождения сохранён",
            ephemeral=True
        )

        await self.cog.update_embed()


# ---------------- PUBLIC PANEL VIEW ---------------- #

class BirthdayView(discord.ui.View):

    def __init__(self, cog):
        super().__init__(timeout=None)
        self.cog = cog

    @discord.ui.button(label="🎂 Добавить / Редактировать", style=discord.ButtonStyle.green, custom_id="bday_add")
    async def add(self, interaction: discord.Interaction, button: discord.ui.Button):

        await interaction.response.send_modal(
            BirthdayModal(self.cog)
        )

    @discord.ui.button(label="❌ Удалить", style=discord.ButtonStyle.red, custom_id="bday_remove")
    async def remove(self, interaction: discord.Interaction, button: discord.ui.Button):

        await self.cog.bot.db.remove_birthday(interaction.user.id)

        await interaction.response.send_message(
            "🗑 День рождение удалён",
            ephemeral=True
        )

        await self.cog.update_embed()


# ---------------- SETUP PANEL ---------------- #

class SetupView(discord.ui.View):

    def __init__(self, cog):
        super().__init__(timeout=300)
        self.cog = cog

    @discord.ui.button(label="📢 Выбрать канал", style=discord.ButtonStyle.blurple)
    async def set_channel(self, interaction: discord.Interaction, button: discord.ui.Button):

        select = ChannelSelect(self.cog)
        view = discord.ui.View()
        view.add_item(select)

        await interaction.response.send_message(
            "Выбрать канал:",
            view=view,
            ephemeral=True
        )

    @discord.ui.button(label="🔒 Роли без которых типы удалятся с таблицы", style=discord.ButtonStyle.blurple)
    async def set_required(self, interaction: discord.Interaction, button: discord.ui.Button):
        select = RequiredRoleSelect(self.cog)
        view = discord.ui.View()
        view.add_item(select)

        await interaction.response.send_message(
            "Selectează rolurile necesare:",
            view=view,
            ephemeral=True
        )
    @discord.ui.button(label="🎭 Выбрать роль для Дня Рождение", style=discord.ButtonStyle.blurple)
    async def set_role(self, interaction: discord.Interaction, button: discord.ui.Button):

        select = RoleSelect(self.cog)
        view = discord.ui.View()
        view.add_item(select)

        await interaction.response.send_message(
            "Выбрать роль:",
            view=view,
            ephemeral=True
        )

    @discord.ui.button(label="📤 Опубликировать таблицу", style=discord.ButtonStyle.green)
    async def publish(self, interaction: discord.Interaction, button: discord.ui.Button):

        config = await self.cog.bot.db.get_config(interaction.guild.id)

        if not config:
            await interaction.response.send_message(
                "❌ Установи изначально канал",
                ephemeral=True
            )
            return

        channel_id, role_id, required_roles, message_id = config

        channel = interaction.guild.get_channel(channel_id)

        embed = await self.cog.generate_embed()

        msg = await channel.send(
            embed=embed,
            view=BirthdayView(self.cog)
        )

        await self.cog.bot.db.set_message(
            interaction.guild.id,
            msg.id
        )

        await interaction.response.send_message(
            "✅ Панель дней рождения опубликована",
            ephemeral=True
        )


# ---------------- SELECT MENUS ---------------- #

class RequiredRoleSelect(discord.ui.RoleSelect):

    def __init__(self, cog):
        super().__init__(
            placeholder="Выбирай роли",
            min_values=1,
            max_values=10
        )
        self.cog = cog

    async def callback(self, interaction: discord.Interaction):

        roles = [role.id for role in self.values]

        await self.cog.bot.db.set_required_roles(
            interaction.guild.id,
            roles
        )

        await interaction.response.send_message(
            "✅ Роли были сохранены",
            ephemeral=True
        )

class ChannelSelect(discord.ui.ChannelSelect):

    def __init__(self, cog):
        super().__init__(
            channel_types=[discord.ChannelType.text],
            placeholder="Выберите канал для поздравлений:"
        )
        self.cog = cog

    async def callback(self, interaction: discord.Interaction):

        channel = self.values[0]

        await self.cog.bot.db.set_channel(
            interaction.guild.id,
            channel.id
        )

        await interaction.response.send_message(
            f"✅ Канал утсановлен на: {channel.mention}",
            ephemeral=True
        )


class RoleSelect(discord.ui.RoleSelect):

    def __init__(self, cog):
        super().__init__(placeholder="Выберите роль дня рождения:")
        self.cog = cog

    async def callback(self, interaction: discord.Interaction):

        role = self.values[0]

        await self.cog.bot.db.set_role(
            interaction.guild.id,
            role.id
        )

        await interaction.response.send_message(
            f"✅ Роль установлена на: {role.mention}",
            ephemeral=True
        )


# ---------------- COG ---------------- #

class Birthday(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.check_birthdays.start()

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):

        try:
            await self.bot.db.remove_birthday(member.id)
        except:
            pass

        await self.update_embed()

    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):

        if before.roles == after.roles:
            return

        config = await self.bot.db.get_config(after.guild.id)

        if not config:
            return

        _, _, required_roles, _ = config

        if not required_roles:
            return

        required_roles = [int(r) for r in required_roles.split(",")]

        has_required = any(role.id in required_roles for role in after.roles)

        if not has_required:
            await self.bot.db.remove_birthday(after.id)

            await self.update_embed()

    async def cog_load(self):

        self.bot.add_view(BirthdayView(self))

    async def generate_embed(self):

        today = datetime.datetime.now(ZoneInfo("Europe/Moscow"))

        months = {i: [] for i in range(1, 13)}

        rows = await self.bot.db.get_birthdays()

        for user_id, name, day, month in rows:
            months[month].append((user_id, name, day))

        embed = discord.Embed(
            title="🎂 Happy Birthday",
            color=discord.Color.pink()
        )

        for m in range(1, 13):

            text = ""

            for user_id, name, day in sorted(months[m], key=lambda x: x[2]):

                if day == today.day and m == today.month:
                    text += f"⭐ **{day} — <@{user_id}> (TODAY)** 🎉\n"
                else:
                    text += f"• {day} — <@{user_id}>\n"

            if not text:
                text = "—"

            embed.add_field(
                name=MONTHS[m],
                value=text,
                inline=False
            )

        return embed


    async def update_embed(self):

        for guild in self.bot.guilds:

            config = await self.bot.db.get_config(guild.id)

            if not config:
                continue

            channel_id, role_id, required_roles, message_id = config

            channel = guild.get_channel(channel_id)

            if not channel:
                continue

            try:
                msg = await channel.fetch_message(message_id)

                embed = await self.generate_embed()

                await msg.edit(embed=embed)
            except:
                pass

        async def cleanup_birthdays(self):

            rows = await self.bot.db.get_birthdays()

            for user_id, name, day, month in rows:

                exists = False

                for guild in self.bot.guilds:
                    if guild.get_member(user_id):
                        exists = True
                        break

                if not exists:
                    await self.bot.db.remove_birthday(user_id)

# ---------------- ADMIN COMMAND ---------------- #

    @app_commands.command(name="bdaypanel")
    @app_commands.checks.has_permissions(administrator=True)
    async def setup_panel(self, interaction: discord.Interaction):

        embed = discord.Embed(
            title="🎂 Настройка системы дней рождения",
            description=(
                "Добро пожаловать в панель настройки.\n\n"
                "Используйте кнопки ниже чтобы:\n"
                "• выбрать канал для поздравлений\n"
                "• выбрать роль дня рождения\n"
                "• опубликовать таблицу дней рождения"
            ),
            color=discord.Color.blurple()
        )

        embed.add_field(
            name="📋 Шаги настройки",
            value=(
                "1️⃣ Установите канал\n"
                "2️⃣ Установите роль\n"
                "3️⃣ Опубликуйте панель"
            ),
            inline=False
        )

        embed.set_footer(text="Birthday System • Настройка администратора")

        await interaction.response.send_message(
            embed=embed,
            view=SetupView(self),
            ephemeral=True
        )


# ---------------- BIRTHDAY CHECK ---------------- #

    @tasks.loop(time=datetime.time(hour=0, minute=0, tzinfo=ZoneInfo("Europe/Moscow")))
    async def check_birthdays(self):

        today = datetime.datetime.now(ZoneInfo("Europe/Moscow"))

        await self.cleanup_birthdays()

        users = await self.bot.db.get_today_birthdays(
            today.day,
            today.month
        )

        for guild in self.bot.guilds:

            config = await self.bot.db.get_config(guild.id)

            if not config:
                continue

            channel_id, role_id, _ = config

            channel = guild.get_channel(channel_id)
            role = guild.get_role(role_id)

            if not channel:
                continue

            for user_id, name in users:

                member = guild.get_member(user_id)

                if not member:
                    continue

                msg = await channel.send(
                    f"🎉 Today is {member.mention}'s birthday!"
                )

                if role:

                    await member.add_roles(role)

                    self.bot.loop.create_task(
                        self.remove_role_later(member, role)
                    )

                await msg.delete(delay=86400)


    async def remove_role_later(self, member, role):

        await discord.utils.sleep_until(
            datetime.datetime.utcnow() + datetime.timedelta(hours=24)
        )

        try:
            await member.remove_roles(role)
        except:
            pass


async def setup(bot):
    await bot.add_cog(Birthday(bot))