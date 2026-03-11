import discord
from discord.ext import commands
from discord import app_commands
import time

cooldowns = {}


def is_staff(member: discord.Member, staff_roles):

    if not staff_roles:
        return False

    roles = [int(r) for r in staff_roles.split(",")]

    return any(role.id in roles for role in member.roles)


def create_panel_embed():

    embed = discord.Embed(
        title="🔥 Семья BLAISE • Набор открыт",
        description=(
            "Добро пожаловать в **семью BLAISE**.\n"
            "Мы ищем новых участников.\n\n"

            "━━━━━━━━━━━━━━━━━━━━\n\n"

            "📋 **Требования**\n"
            "• Адекватность\n"
            "• Активность\n"
            "• Желание развиваться\n\n"

            "📨 **Как подать заявку**\n"
            "Нажмите кнопку ниже и заполните форму.\n\n"

            "━━━━━━━━━━━━━━━━━━━━"
        ),
        color=0xff5500
    )

    embed.set_footer(text="BLAISE FAMILY • RECRUITMENT")

    return embed

class ApplySetupView(discord.ui.View):

    def __init__(self, cog):
        super().__init__(timeout=300)
        self.cog = cog

    @discord.ui.button(label="🎟 Канал панели", style=discord.ButtonStyle.blurple)
    async def panel_channel(self, interaction: discord.Interaction, button):

        select = discord.ui.ChannelSelect(channel_types=[discord.ChannelType.text])

        async def callback(inter):
            channel = select.values[0]

            await self.cog.bot.db.set_apply_panel_channel(
                inter.guild.id,
                channel.id
            )

            await inter.response.send_message(
                f"✅ Канал панели: {channel.mention}",
                ephemeral=True
            )

        select.callback = callback

        view = discord.ui.View()
        view.add_item(select)

        await interaction.response.send_message(
            "Выберите канал для панели:",
            view=view,
            ephemeral=True
        )

    @discord.ui.button(label="📥 Канал заявок", style=discord.ButtonStyle.blurple)
    async def app_channel(self, interaction: discord.Interaction, button):

        select = discord.ui.ChannelSelect(channel_types=[discord.ChannelType.text])

        async def callback(inter):

            channel = select.values[0]

            await self.cog.bot.db.set_apply_channel(
                inter.guild.id,
                channel.id
            )

            await inter.response.send_message(
                f"✅ Канал заявок: {channel.mention}",
                ephemeral=True
            )

        select.callback = callback

        view = discord.ui.View()
        view.add_item(select)

        await interaction.response.send_message(
            "Выберите канал:",
            view=view,
            ephemeral=True
        )

    @discord.ui.button(label="📜 Канал логов", style=discord.ButtonStyle.blurple)
    async def log_channel(self, interaction, button):

        select = discord.ui.ChannelSelect(channel_types=[discord.ChannelType.text])

        async def callback(inter):

            channel = select.values[0]

            await self.cog.bot.db.set_apply_logs(
                inter.guild.id,
                channel.id
            )

            await inter.response.send_message(
                f"✅ Канал логов: {channel.mention}",
                ephemeral=True
            )

        select.callback = callback

        view = discord.ui.View()
        view.add_item(select)

        await interaction.response.send_message(
            "Выберите канал логов:",
            view=view,
            ephemeral=True
        )

    @discord.ui.button(label="🎭 Staff роли", style=discord.ButtonStyle.blurple)
    async def staff_roles(self, interaction, button):

        select = discord.ui.RoleSelect(
            min_values=1,
            max_values=5,
            placeholder="Выберите staff роли"
        )

        async def callback(inter):

            roles = [r.id for r in select.values]

            await self.cog.bot.db.set_apply_staff(
                inter.guild.id,
                roles
            )

            await inter.response.send_message(
                "✅ Staff роли сохранены",
                ephemeral=True
            )

        select.callback = callback

        view = discord.ui.View()
        view.add_item(select)

        await interaction.response.send_message(
            "Выберите роли:",
            view=view,
            ephemeral=True
        )

    @discord.ui.button(label="🎭 Роль принятия", style=discord.ButtonStyle.green)
    async def accept_role(self, interaction, button):

        select = discord.ui.RoleSelect()

        async def callback(inter):

            role = select.values[0]

            await self.cog.bot.db.set_apply_accept(
                inter.guild.id,
                role.id
            )

            await inter.response.send_message(
                f"✅ Роль принятия: {role.mention}",
                ephemeral=True
            )

        select.callback = callback

        view = discord.ui.View()
        view.add_item(select)

        await interaction.response.send_message(
            "Выберите роль:",
            view=view,
            ephemeral=True
        )

    @discord.ui.button(label="🎭 Роль удаления", style=discord.ButtonStyle.red)
    async def remove_role(self, interaction, button):

        select = discord.ui.RoleSelect()

        async def callback(inter):

            role = select.values[0]

            await self.cog.bot.db.set_apply_remove(
                inter.guild.id,
                role.id
            )

            await inter.response.send_message(
                f"✅ Роль удаления: {role.mention}",
                ephemeral=True
            )

        select.callback = callback

        view = discord.ui.View()
        view.add_item(select)

        await interaction.response.send_message(
            "Выберите роль:",
            view=view,
            ephemeral=True
        )

    @discord.ui.button(label="📤 Опубликовать панель", style=discord.ButtonStyle.green)
    async def publish_panel(self, interaction: discord.Interaction, button):

        config = await self.cog.bot.db.get_apply_config(interaction.guild.id)

        if not config:
            return await interaction.response.send_message(
                "⚠ Сначала настрой систему.",
                ephemeral=True
            )

        application_channel, log_channel, staff_roles, accept_role, remove_role, ticket_panel_channel = config

        if not application_channel:
            return await interaction.response.send_message(
                "⚠ Канал заявок не установлен.",
                ephemeral=True
            )

        channel = interaction.guild.get_channel(ticket_panel_channel)

        if not channel:
            return await interaction.response.send_message(
                "❌ Канал не найден.",
                ephemeral=True
            )

        embed = create_panel_embed()

        file = discord.File("banner.png", filename="banner.png")

        embed.set_image(url="attachment://banner.png")

        await channel.send(
            embed=embed,
            file=file,
            view=ApplyButton(self.cog.bot)
        )

        await interaction.response.send_message(
            "✅ Панель заявок опубликована.",
            ephemeral=True
        )


class ApplyModal(discord.ui.Modal, title="📨 Заявка в семью BLAISE"):
    name = discord.ui.TextInput(
        label="Имя персонажа (IC)",
        placeholder="Например: Ivan Blaise",
        max_length=70
    )

    age = discord.ui.TextInput(
        label="Возраст (OOC)",
        placeholder="Например: 18",
        max_length=2
    )

    history = discord.ui.TextInput(
        label="Опыт в семьях",
        placeholder="Например: Blaise, Senseless, KAI",
        style=discord.TextStyle.long,
        max_length=200
    )

    motivation = discord.ui.TextInput(
        label="Почему именно BLAISE?",
        placeholder="Почему мы должны принять вас?",
        style=discord.TextStyle.long,
        max_length=200
    )

    online = discord.ui.TextInput(
        label="Ваш онлайн",
        placeholder="Например: 3-5 часов в день",
        max_length=50
    )

    def __init__(self, bot):
        super().__init__()
        self.bot = bot

    async def on_submit(self, interaction: discord.Interaction):

        now = time.time()

        if interaction.user.id in cooldowns:
            if now - cooldowns[interaction.user.id] < 1:
                return await interaction.response.send_message(
                    "⛔ Подождите перед новой заявкой.",
                    ephemeral=True
                )

        cooldowns[interaction.user.id] = now

        rows = await self.bot.db.get_user_applications(interaction.user.id)
        pending = [r for r in rows if r[5] == "pending"]

        if len(pending) >= 2:
            return await interaction.response.send_message(
                "❌ У вас уже есть 2 активные заявки.",
                ephemeral=True
            )

        try:
            age = int(self.age.value)
        except:
            return await interaction.response.send_message(
                "❌ Возраст должен быть числом.",
                ephemeral=True
            )

        app_id = await self.bot.db.create_application(
            interaction.user.id,
            interaction.user.display_name,
            self.name.value,
            age,
            self.history.value,
            self.motivation.value,
            self.online.value
        )

        config = await interaction.client.db.get_apply_config(interaction.guild.id)

        if not config:
            return await interaction.response.send_message(
                "⚠ Система заявок не настроена.",
                ephemeral=True
            )

        application_channel, log_channel, staff_roles, accept_role, remove_role, ticket_panel_channel = config


        channel = interaction.guild.get_channel(application_channel)

        if not channel:
            return await interaction.response.send_message(
                "❌ Канал заявок не найден.",
                ephemeral=True
            )

        embed = discord.Embed(
            title="📨 Новая заявка • BLAISE",
            color=0xff5500
        )

        embed.add_field(
            name="👤 Игрок",
            value=f"{interaction.user.mention}",
            inline=False
        )

        embed.add_field(
            name="🪪 IC Имя",
            value=f"```{self.name.value}```",
            inline=True
        )

        embed.add_field(
            name="🎂 Возраст",
            value=f"```{age}```",
            inline=True
        )

        embed.add_field(
            name="🏢 Опыт в семьях",
            value=f"```{self.history.value}```",
            inline=True
        )

        embed.add_field(
            name="🔥 Почему BLAISE",
            value=f"```{self.motivation.value}```",
            inline=False
        )

        embed.add_field(
            name="🕒 Онлайн",
            value=f"```{self.online.value}```",
            inline=False
        )

        embed.set_footer(text=f"BLAISE FAMILY • Application ID: {app_id} | Всего заявок: {len(rows)+1}")

        content = None

        if staff_roles:
            roles = staff_roles.split(",")

            mentions = [f"<@&{r}>" for r in roles]

            content = " ".join(mentions)

        await channel.send(
            content=content,
            embed=embed,
            view=StaffButtons()
        )


        await interaction.response.send_message(
            "✅ Заявка отправлена.",
            ephemeral=True
        )


class StaffButtons(discord.ui.View):

    def __init__(self):
        super().__init__(timeout=None)

    async def process(self, interaction, status):

        config = await interaction.client.db.get_apply_config(interaction.guild.id)

        if not config:
            return await interaction.response.send_message(
                "⚠ Apply система не настроена.",
                ephemeral=True
            )

        application_channel, log_channel, staff_roles, accept_role, remove_role, ticket_panel_channel = config

        if not is_staff(interaction.user, staff_roles):
            return await interaction.response.send_message(
                "❌ Нет доступа.",
                ephemeral=True
            )

        embed = interaction.message.embeds[0]

        footer = embed.footer.text
        app_id = int(footer.split("Application ID:")[1].split("|")[0].strip())

        data = await interaction.client.db.get_application_by_id(app_id)

        if not data:
            return await interaction.response.send_message("Ошибка БД.", ephemeral=True)

        user_id = data[0]

        await interaction.client.db.update_status(
            app_id,
            status,
            interaction.user.id,
            interaction.user.display_name
        )

        guild = interaction.guild
        user = guild.get_member(user_id)

        if log_channel:
            log_channel = guild.get_channel(log_channel)

        if status == "accepted":

            embed.color = discord.Color.green()

            for i, field in enumerate(embed.fields):
                if field.name == "📞 Обзвон":
                    embed.remove_field(i)
                    break

            embed.add_field(
                name="📊 Статус",
                value=f"✅ Принял {interaction.user.mention}",
                inline=False
            )

            if log_channel:
                log_embed = discord.Embed(
                    title="✅ Заявка принята",
                    color=discord.Color.green()
                )

                log_embed.add_field(name="Игрок", value=f"<@{user_id}>", inline=True)
                log_embed.add_field(name="Staff", value=interaction.user.mention, inline=True)
                log_embed.add_field(name="Application ID", value=str(app_id), inline=False)

                await log_channel.send(embed=log_embed)

            if accept_role:
                accept = guild.get_role(accept_role)
                if accept and user:
                    await user.add_roles(accept)

            if remove_role:
                remove = guild.get_role(remove_role)
                if remove and user and remove in user.roles:
                    await user.remove_roles(remove)

            if user:
                try:
                    await user.send("✅ Ваша заявка была **принята**!")
                except:
                    pass

            await interaction.message.edit(embed=embed, view=None)

            return await interaction.response.send_message(
                "Заявка принята.",
                ephemeral=True
            )


        elif status == "rejected":

            embed.color = discord.Color.red()

            for i, field in enumerate(embed.fields):
                if field.name == "📞 Обзвон":
                    embed.remove_field(i)
                    break

            embed.add_field(
                name="📊 Статус",
                value=f"❌ Отклонил {interaction.user.mention}",
                inline=False
            )

            if log_channel:
                log_embed = discord.Embed(
                    title="❌ Заявка Отклонена",
                    color=discord.Color.red()
                )

                log_embed.add_field(name="Игрок", value=f"<@{user_id}>", inline=True)
                log_embed.add_field(name="Staff", value=interaction.user.mention, inline=True)
                log_embed.add_field(name="Application ID", value=str(app_id), inline=False)

                await log_channel.send(embed=log_embed)

            if user:
                try:
                    await user.send("❌ Ваша заявка была **отклонена**.")
                except:
                        pass

            await interaction.message.edit(embed=embed, view=None)

            return await interaction.response.send_message(
                "Заявка отклонена.",
                ephemeral=True
            )


        elif status == "interview":

            embed.color = discord.Color.blurple()

            embed.add_field(
                name="📞 Обзвон",
                value=f"{interaction.user.mention} пригласил игрока",
                inline=False
            )

            if user:
                try:
                    await user.send("📞 Вас пригласили на **обзвон**.\n\n"
                                    "Зайдите в голосовой канал:\n"
                                    "<#1479327122588958922>"
                                )
                except:
                    pass


            # stergem doar butonul interview
            for item in self.children:
                if item.custom_id == "apply_interview":
                    self.remove_item(item)

            await interaction.message.edit(embed=embed, view=self)

            return await interaction.response.send_message(
                "Игрок приглашён на обзвон.",
                ephemeral=True
            )


    @discord.ui.button(label="Принять", style=discord.ButtonStyle.success, emoji="✅", custom_id="apply_accept")
    async def accept(self, interaction: discord.Interaction, button):
        await self.process(interaction, "accepted")

    @discord.ui.button(label="Отказать", style=discord.ButtonStyle.danger, emoji="❌", custom_id="apply_reject")
    async def reject(self, interaction: discord.Interaction, button):

        config = await interaction.client.db.get_apply_config(interaction.guild.id)

        if not config:
            return await interaction.response.send_message(
                "⚠ Apply система не настроена.",
                ephemeral=True
            )

        application_channel, log_channel, staff_roles, accept_role, remove_role, ticket_panel_channel = config

        if not is_staff(interaction.user, staff_roles):
            return await interaction.response.send_message(
                "❌ Нет доступа.",
                ephemeral=True
            )

        await interaction.response.send_modal(
            RejectModal(self, interaction)
        )

    @discord.ui.button(label="Обзвон", style=discord.ButtonStyle.primary, emoji="📞", custom_id="apply_interview")
    async def interview(self, interaction: discord.Interaction, button):
        await self.process(interaction, "interview")

    @discord.ui.button(label="Apps", style=discord.ButtonStyle.secondary, emoji="📊", custom_id="apply_apps")
    async def apps(self, interaction: discord.Interaction, button):

        await interaction.response.defer(ephemeral=True)

        config = await interaction.client.db.get_apply_config(interaction.guild.id)

        if not config:
            return await interaction.followup.send(
                "⚠ Apply система не настроена.",
                ephemeral=True
            )

        application_channel, log_channel, staff_roles, accept_role, remove_role, ticket_panel_channel = config

        if not is_staff(interaction.user, staff_roles):
            return await interaction.followup.send(
                "❌ Нет доступа.",
                ephemeral=True
            )

        embed = interaction.message.embeds[0]

        user_id = None

        for field in embed.fields:
            if field.name == "👤 Игрок":
                try:
                    user_id = int(field.value.replace("<@", "").replace(">", "").replace("!", ""))
                except:
                    pass
                break

        if not user_id:
            return await interaction.followup.send(
                "Не удалось найти ID игрока.",
                ephemeral=True
            )

        rows = await interaction.client.db.get_user_applications(user_id)

        if not rows:
            return await interaction.followup.send(
                "У игрока нет заявок.",
                ephemeral=True
            )

        result = discord.Embed(
            title="📋 История заявок",
            color=0xff5500
        )

        for r in rows[:10]:

            ic = r[0]
            age = r[1]
            status = r[5]
            created = r[6]
            reason = r[7]

            if status == "accepted":
                status_icon = "✅"
            elif status == "rejected":
                status_icon = "❌"
            elif status == "interview":
                status_icon = "📞"
            else:
                status_icon = "⏳"

            result.add_field(
                name=f"{status_icon} {ic}",
                value=f"Возраст: {age}\nДата: {created}\nПричина: {reason or '—'}",
                inline=False
            )

        result.set_footer(text=f"Всего заявок: {len(rows)}")

        await interaction.followup.send(embed=result, ephemeral=True)

class RejectModal(discord.ui.Modal, title="❌ Причина отклонения"):

    reason = discord.ui.TextInput(
        label="Причина",
        style=discord.TextStyle.long,
        max_length=200,
        placeholder="Укажите причину отклонения"
    )

    def __init__(self, view, interaction):
        super().__init__()
        self.view = view
        self.interaction = interaction

    async def on_submit(self, interaction: discord.Interaction):

        embed = self.interaction.message.embeds[0]

        footer = embed.footer.text
        app_id = int(footer.split("Application ID:")[1].split("|")[0].strip())

        data = await interaction.client.db.get_application_by_id(app_id)
        user_id = data[0]

        guild = interaction.guild
        user = guild.get_member(user_id)

        await interaction.client.db.update_status(
            app_id,
            "rejected",
            interaction.user.id,
            interaction.user.display_name,
            self.reason.value
        )

        embed.color = discord.Color.red()

        embed.add_field(
            name="📊 Статус",
            value=f"❌ Отклонил {interaction.user.mention}",
            inline=False
        )

        await self.interaction.message.edit(embed=embed, view=None)

        # DM
        if user:
            await user.send(
                f"❌ Ваша заявка была **отклонена**.\n\nПричина:\n```{self.reason.value}```"
            )

        # LOG
        log_channel = None

        config = await interaction.client.db.get_apply_config(interaction.guild.id)

        if config:
            _, log_channel, _, _, _, _ = config

            if log_channel:
                log_channel = guild.get_channel(log_channel)

        if log_channel:

            log = discord.Embed(
                title="❌ Заявка отклонена",
                color=discord.Color.red()
            )

            log.add_field(name="Игрок", value=f"<@{user_id}>")
            log.add_field(name="Staff", value=interaction.user.mention)
            log.add_field(name="Причина", value=self.reason.value, inline=False)

            await log_channel.send(embed=log)

        await interaction.response.send_message(
            "Заявка отклонена.",
            ephemeral=True
        )

class ApplyButton(discord.ui.View):

    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.button(label="Подать заявку", emoji="📨", style=discord.ButtonStyle.primary, custom_id="apply_button")
    async def apply(self, interaction: discord.Interaction, button):

        await interaction.response.send_modal(
            ApplyModal(self.bot)
        )

    @discord.ui.button(label="Правила", emoji="📜", style=discord.ButtonStyle.secondary, custom_id="rules_button")
    async def rules(self, interaction: discord.Interaction, button):

        embed = discord.Embed(
            title="📜 **Правила семьи BLAISE**",
            description=(
                "━━━━━━━━━━━━━━━━\n\n"
                "1️⃣ **Уважение**\n"
                "Запрещены оскорбления участников семьи или гостей.\n\n"
                "2️⃣ **Запрещённый контент**\n"
                "Запрещена пропаганда нацизма, расизма и других запрещённых идеологий.\n\n"
                "3️⃣ **Конфликты**\n"
                "Запрещено провоцировать или разжигать конфликты.\n\n"
                "4️⃣ **Недопустимые материалы**\n"
                "Запрещено отправлять контент, нарушающий законодательство РФ.\n\n"
                "5️⃣ **Флуд**\n"
                "Не злоупотребляйте флудом и спамом.\n\n"
                "6️⃣ **Лазейки правил**\n"
                "Запрещено использовать недоработки правил.\n\n"
                "━━━━━━━━━━━━━━━━"
            ),
            color=0xff5500
        )

        await interaction.response.send_message(embed=embed, ephemeral=True)


class ApplySetup(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="applysetup")
    @app_commands.checks.has_permissions(administrator=True)
    async def apply_setup(self, interaction: discord.Interaction):

        embed = discord.Embed(
            title="⚙ Настройка системы заявок",
            description=(
                "Используйте кнопки ниже для настройки.\n\n"
                "• канал заявок\n"
                "• канал логов\n"
                "• staff роли\n"
                "• роль принятия\n"
                "• роль удаления"
            ),
            color=discord.Color.orange()
        )

        await interaction.response.send_message(
            embed=embed,
            view=ApplySetupView(self),
            ephemeral=True
        )

async def setup(bot):

    await bot.add_cog(ApplySetup(bot))

    bot.add_view(ApplyButton(bot))
    bot.add_view(StaffButtons())