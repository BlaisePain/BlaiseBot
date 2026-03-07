import discord
from discord.ext import commands
import re

ROLE_ID = 1463083432987852841
CATEGORY_ID = 1479786852020912221
LOG_CHANNEL_ID = 1479786852020912222


class Academy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # cauta canalul academy al unui user dupa topic
    def get_user_channel(self, category, user_id):
        for ch in category.text_channels:
            if ch.topic == f"academy-user:{user_id}":
                return ch
        return None

    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):

        print("Member update detected")

        before_roles = {role.id for role in before.roles}
        after_roles = {role.id for role in after.roles}

        guild = after.guild

        category = guild.get_channel(CATEGORY_ID)
        if not category:
            print("Category not found")
            return

        log_channel = self.bot.get_channel(LOG_CHANNEL_ID)
        if not log_channel:
            try:
                log_channel = await self.bot.fetch_channel(LOG_CHANNEL_ID)
            except:
                print("Log channel not found")
                log_channel = None

        existing_channel = self.get_user_channel(category, after.id)

        # ---------------- ROLE ADDED ---------------- #

        if ROLE_ID not in before_roles and ROLE_ID in after_roles:

            print("Role added")

            if existing_channel:
                print("Channel already exists")
                return

            name = re.sub(r'[^a-zA-Z0-9-]', '', after.display_name.lower().replace(" ", "-"))
            channel_name = f"academy-{name}"

            overwrites = {
                guild.default_role: discord.PermissionOverwrite(read_messages=False),
                after: discord.PermissionOverwrite(
                    read_messages=True,
                    send_messages=True,
                    attach_files=True,
                    read_message_history=True
                )
            }

            channel = await guild.create_text_channel(
                name=channel_name,
                category=category,
                overwrites=overwrites,
                topic=f"academy-user:{after.id}"
            )

            print("Channel created")

            embed = discord.Embed(
                title="🎓 Добро пожаловать в Академию!",
                description=(
                    f"Привет, {after.mention}!\n\n"
                    "Это твой личный канал для обучения.\n"
                    "Здесь ты можешь задавать вопросы.\n\n"
                    "**Правила:**\n"
                    "• Соблюдай субординацию\n"
                    "• Не стесняйся спрашивать\n\n"
                    "Удачи в обучении! 🚀"
                ),
                color=discord.Color.green()
            )

            embed.set_thumbnail(url=after.display_avatar.url)

            await channel.send(embed=embed)

            text = f"""
Приветствую, {after.mention},

Каждую неделю в воскресенье, будет проверяться твой актив в войсах за неделю (нахождение тебя в войсах семьи), так же твое участие на семейном контенте и фракционном контенте.

**Минимальные активности за неделю:**

Дропы: 8  
Поезд: 3  
Флаг/Вагонетка: 3  
Поставки материалов: 5  
Поставки аптек: 3  
Захват черного рынка: 3  
Графика: 10  

**Рекомендуемые активности:**

Дропы: 14  
Поезд: 5  
Флаг/Вагонетка: 5  
Поставки материалов: 7  
Поставки аптек: 5  
Захват черного рынка: 4  
Графика: 20  

После прочтения поставь реакцию или отпиши что ознакомлен!
"""

            await channel.send(text)

            if log_channel:
                log = discord.Embed(
                    title="📚 Academy Channel Created",
                    description=f"User: {after.mention}\nChannel: {channel.mention}",
                    color=discord.Color.green()
                )

                await log_channel.send(embed=log)

        # ---------------- ROLE REMOVED ---------------- #

        if ROLE_ID in before_roles and ROLE_ID not in after_roles:

            print("Role removed")

            if existing_channel:

                await existing_channel.delete(reason="Academy role removed")

                print("Channel deleted")

                if log_channel:
                    log = discord.Embed(
                        title="🗑 Academy Channel Deleted",
                        description=f"User: {after.mention}",
                        color=discord.Color.red()
                    )

                    await log_channel.send(embed=log)


async def setup(bot):
    await bot.add_cog(Academy(bot))