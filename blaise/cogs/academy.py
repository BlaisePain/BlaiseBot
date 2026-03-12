import discord
from discord.ext import commands, tasks
from discord import app_commands
import re
import asyncio


def sanitize(name: str):
    name = name.lower().replace(" ", "-")
    name = re.sub(r"[^a-z0-9\-]", "", name)

    if not name:
        return "user"

    return name


def create_academy_embed(member: discord.Member):

    embed = discord.Embed(
        title="🎓 Добро пожаловать в Академию!",
        description=(
            f"Привет, {member.mention}!\n\n"
            "Это твой личный канал для обучения.\n"
            "Здесь ты можешь задавать вопросы.\n\n"
            "**Правила:**\n"
            "• Соблюдай субординацию\n"
            "• Не стесняйся спрашивать\n\n"
            "Удачи в обучении! 🚀"
        ),
        color=discord.Color.green()
    )

    embed.set_thumbnail(url=member.display_avatar.url)

    return embed


# -------------------------------------------------
# SETUP VIEW
# -------------------------------------------------

class AcademySetupView(discord.ui.View):

    def __init__(self, cog):
        super().__init__(timeout=300)
        self.cog = cog
        self.channel_lock = asyncio.Lock()

    @discord.ui.button(label="🎓 Роль академии", style=discord.ButtonStyle.blurple)
    async def academy_role(self, interaction: discord.Interaction, button):

        select = discord.ui.RoleSelect()

        async def callback(inter):

            role = select.values[0]

            await self.cog.bot.db.set_academy_role(
                inter.guild.id,
                role.id
            )

            await inter.response.send_message(
                f"✅ Роль сохранена: {role.mention}",
                ephemeral=True
            )

        select.callback = callback

        view = discord.ui.View()
        view.add_item(select)

        await interaction.response.send_message(
            "Выберите роль академии:",
            view=view,
            ephemeral=True
        )

    @discord.ui.button(label="📜 Канал логов", style=discord.ButtonStyle.blurple)
    async def academy_logs(self, interaction, button):

        select = discord.ui.ChannelSelect(
            channel_types=[discord.ChannelType.text]
        )

        async def callback(inter):

            channel = select.values[0]

            await self.cog.bot.db.set_academy_logs(
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


# -------------------------------------------------
# MAIN SYSTEM
# -------------------------------------------------

class Academy(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.channel_lock = asyncio.Lock()
        self.bot.loop.create_task(self.start_tasks())

    # -------------------------------------------------

    async def start_tasks(self):
        await self.bot.wait_until_ready()
        self.academy_check.start()

    async def ensure_category(self, guild):

        config = await self.bot.db.get_academy_config(guild.id)

        if not config:
            return None

        role_id, category_id, log_channel_id = config

        category = None

        if category_id:
            category = guild.get_channel(category_id)

        if category:
            return category

        category = await guild.create_category("🎓 Academy")

        await self.bot.db.set_academy_category(
            guild.id,
            category.id
        )

        return category

    # -------------------------------------------------

    def get_user_channel(self, category, user_id):

        for ch in category.text_channels:

            if ch.topic == f"academy-user:{user_id}":
                return ch

        return None

    # -------------------------------------------------

    async def remove_duplicate_channels(self, category):

        seen = {}

        for ch in category.text_channels:

            if not ch.topic:
                continue

            if not ch.topic.startswith("academy-user:"):
                continue

            user_id = ch.topic.split(":")[1]

            if user_id in seen:
                await ch.delete(reason="Duplicate academy channel")
            else:
                seen[user_id] = ch

    # -------------------------------------------------
    # ROLE UPDATE
    # -------------------------------------------------

    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):

        before_roles = {r.id for r in before.roles}
        after_roles = {r.id for r in after.roles}

        if before.display_name != after.display_name:

            channel = self.get_user_channel(after.guild, after.id)

            if channel:

                new_name = f"academy-{sanitize(after.display_name)}"

                if channel.name != new_name:
                    await channel.edit(name=new_name)

        if before_roles == after_roles:
            return

        config = await self.bot.db.get_academy_config(after.guild.id)

        if not config:
            return

        role_id, category_id, log_channel_id = config
        guild = after.guild

        category = await self.ensure_category(guild)

        if not category:
            return

        log_channel = guild.get_channel(log_channel_id) if log_channel_id else None

        existing = self.get_user_channel(category, after.id)

        # ROLE ADDED

        if role_id not in before_roles and role_id in after_roles:

            if existing:
                return

            await asyncio.sleep(0.3)

            existing = self.get_user_channel(category, after.id)

            if existing:
                return

            name = sanitize(after.display_name)

            try:

                channel = await guild.create_text_channel(
                    name=f"academy-{name}",
                    category=category,
                    topic=f"academy-user:{after.id}",
                    overwrites={
                        guild.default_role: discord.PermissionOverwrite(read_messages=False),
                        after: discord.PermissionOverwrite(
                            read_messages=True,
                            send_messages=True,
                            read_message_history=True
                        )
                    }
                )

                await asyncio.sleep(1)

                await channel.send(
                    content=after.mention,
                    embed=create_academy_embed(after)
                )

                if log_channel:

                    embed = discord.Embed(
                        title="📚 Academy Channel Created",
                        description=f"{after.mention}\n{channel.mention}",
                        color=discord.Color.green()
                    )

                    await log_channel.send(embed=embed)

            except Exception as e:
                print("ACADEMY ERROR:", e)


        # ROLE REMOVED

        if role_id in before_roles and role_id not in after_roles:

            if existing:

                await existing.delete(reason="Academy role removed")

                if log_channel:

                    embed = discord.Embed(
                        title="🗑 Academy Channel Deleted",
                        description=f"{after.mention}",
                        color=discord.Color.red()
                    )

                    await log_channel.send(embed=embed)

    # -------------------------------------------------
    # CHANNEL DELETE DETECT
    # -------------------------------------------------

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel):

        if not isinstance(channel, discord.TextChannel):
            return

        if not channel.topic:
            return

        if not channel.topic.startswith("academy-user:"):
            return

        guild = channel.guild

        config = await self.bot.db.get_academy_config(guild.id)

        if not config:
            return

        role_id, category_id, log_channel_id = config

        log_channel = guild.get_channel(log_channel_id) if log_channel_id else None

        user_id = int(channel.topic.split(":")[1])
        member = guild.get_member(user_id)

        if not member:
            return

        role = guild.get_role(role_id)

        # daca userul NU mai are rol academy -> nu recream canal
        if role not in member.roles:
            return

        deleter = "Unknown"

        async for entry in guild.audit_logs(limit=5, action=discord.AuditLogAction.channel_delete):

            if entry.target.id == channel.id:
                deleter = entry.user
                break

        if log_channel:

            embed = discord.Embed(
                title="⚠ Academy Channel Deleted",
                description=(
                    f"Канал: **{channel.name}**\n"
                    f"Удалил: {deleter.mention if deleter != 'Unknown' else 'Unknown'}\n"
                    f"Пользователь: <@{user_id}>"
                ),
                color=discord.Color.red()
            )

            await log_channel.send(embed=embed)

        category = await self.ensure_category(guild)

        if not category or not member:
            return

        name = sanitize(member.display_name)

        try:

            new_channel = await guild.create_text_channel(
                name=f"academy-{name}",
                category=category,
                topic=f"academy-user:{member.id}",
                overwrites={
                    guild.default_role: discord.PermissionOverwrite(read_messages=False),
                    member: discord.PermissionOverwrite(
                        read_messages=True,
                        send_messages=True,
                        read_message_history=True
                    )
                }
            )

            await new_channel.send(
                content=member.mention,
                embed=create_academy_embed(member)
            )

        except Exception as e:
            print("ACADEMY RECREATE ERROR:", e)

    # -------------------------------------------------
    # FIX SYSTEM
    # -------------------------------------------------

    async def fix_academy_channels(self, guild):

        async with self.channel_lock:

            config = await self.bot.db.get_academy_config(guild.id)

            if not config:
                return

            role_id, category_id, log_channel_id = config

            role = guild.get_role(role_id)

            if not role:
                return

            category = await self.ensure_category(guild)

            if not category:
                return

            await self.remove_duplicate_channels(category)

            valid_members = {m.id for m in role.members}

            # șterge canale ale celor fără rol
            for ch in category.text_channels:

                if not ch.topic:
                    continue

                if not ch.topic.startswith("academy-user:"):
                    continue

                user_id = int(ch.topic.split(":")[1])

                if user_id not in valid_members:

                    try:
                        await ch.delete(reason="User no longer has academy role")
                    except:
                        pass

            # creează canale pentru membri care nu au
            for member in role.members:

                existing = self.get_user_channel(category, member.id)

                if existing:
                    continue

                name = sanitize(member.display_name)

                channel = await guild.create_text_channel(
                    name=f"academy-{name}",
                    category=category,
                    topic=f"academy-user:{member.id}",
                    overwrites={
                        guild.default_role: discord.PermissionOverwrite(read_messages=False),
                        member: discord.PermissionOverwrite(
                            read_messages=True,
                            send_messages=True,
                            read_message_history=True
                        )
                    }
                )

                await asyncio.sleep(0.5)

                await channel.send(
                    content=member.mention,
                    embed=create_academy_embed(member)
                )

    # -------------------------------------------------

    @commands.Cog.listener()
    async def on_ready(self):

        for guild in self.bot.guilds:

            try:
                await self.fix_academy_channels(guild)
            except:
                pass

    # -------------------------------------------------

    @tasks.loop(minutes=30)
    async def academy_check(self):

        for guild in self.bot.guilds:

            try:
                await self.fix_academy_channels(guild)
            except:
                pass

    @academy_check.before_loop
    async def before_academy_check(self):
        await self.bot.wait_until_ready()


# -------------------------------------------------
# SETUP COMMAND
# -------------------------------------------------

class AcademySetup(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="academysetup")
    @app_commands.checks.has_permissions(administrator=True)
    async def academy_setup(self, interaction: discord.Interaction):

        embed = discord.Embed(
            title="⚙ Настройка Academy",
            description=(
                "Настройте систему academy.\n\n"
                "• роль academy\n"
                "• канал логов\n\n"
                "Категория создаётся автоматически."
            ),
            color=discord.Color.orange()
        )

        await interaction.response.send_message(
            embed=embed,
            view=AcademySetupView(self),
            ephemeral=True
        )


# -------------------------------------------------
# LOAD
# -------------------------------------------------

async def setup(bot):

    await bot.add_cog(Academy(bot))
    await bot.add_cog(AcademySetup(bot))