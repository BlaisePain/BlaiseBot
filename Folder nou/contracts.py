import discord
from discord.ext import commands
from datetime import datetime
from views.contract_views import ContractPanelView, ContractPanelState


CONTRACT_ROLES = [
    1462918028097359873,
    1463082232833904643
]

class ContractsCog(commands.Cog, name='Contract'):
    """Модуль контрактов"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):

        if payload.user_id == self.bot.user.id:
            return

        if str(payload.emoji) != '✅':
            return

        guild = self.bot.get_guild(payload.guild_id)
        if not guild:
            return

        contract = await self.bot.db.get_contract(guild.id, payload.message_id)

        if not contract:
            return

        if contract.get('status') != 'collecting':
            return

        added = await self.bot.db.add_participant(
            guild.id,
            payload.message_id,
            payload.user_id
        )

        if added:

            await self._update_participants(guild, payload.message_id)

            thread_id = contract.get('thread_id')

            if thread_id:

                thread = guild.get_thread(thread_id)

                if thread:

                    member = guild.get_member(payload.user_id)

                    if member:
                        await thread.send(f'✅ {member.mention} записался на контракт!')

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload: discord.RawReactionActionEvent):

        if payload.user_id == self.bot.user.id:
            return

        if str(payload.emoji) != '✅':
            return

        guild = self.bot.get_guild(payload.guild_id)

        if not guild:
            return

        contract = await self.bot.db.get_contract(guild.id, payload.message_id)

        if not contract:
            return

        if contract.get('status') != 'collecting':
            return

        removed = await self.bot.db.remove_participant(
            guild.id,
            payload.message_id,
            payload.user_id
        )

        if removed:

            await self._update_participants(guild, payload.message_id)

            thread_id = contract.get('thread_id')

            if thread_id:

                thread = guild.get_thread(thread_id)

                if thread:

                    member = guild.get_member(payload.user_id)

                    if member:
                        await thread.send(f'❌ {member.mention} отписался от контракта.')

    async def _update_participants(self, guild: discord.Guild, message_id: int):

        participants = await self.bot.db.get_participants(guild.id, message_id)

        contract = await self.bot.db.get_contract(guild.id, message_id)

        if not contract:
            return

        thread_id = contract.get("thread_id")

        thread = guild.get_thread(thread_id)

        if not thread:
            return

        channel = thread.parent

        try:
            message = await channel.fetch_message(message_id)
        except:
            return

        embed = message.embeds[0]

        if participants:

            names = []

            for i, uid in enumerate(participants, 1):

                member = guild.get_member(uid)

                if member:
                    names.append(f"{i}. {member.display_name}")
                else:
                    names.append(f"{i}. <@{uid}>")

            participants_text = "\n".join(names)

        else:
            participants_text = "*Пока никого*"

        for i, field in enumerate(embed.fields):

            if field.name == "✅ Участники":
                embed.set_field_at(
                    i,
                    name="✅ Участники",
                    value=participants_text,
                    inline=False
                )

                break

        await message.edit(embed=embed)

    # ==================== COMMANDS ====================

    @commands.command(name='contract_panel', aliases=['cp', 'контракт'])
    @commands.has_any_role(*CONTRACT_ROLES)
    async def contract_panel(self, ctx: commands.Context):

        ContractPanelState.clear(ctx.author.id)

        view = ContractPanelView(ctx.author.id)

        embed = discord.Embed(
            title='📜 Создание контракта',
            description='Выберите параметры сбора:',
            color=discord.Color.blue()
        )

        embed.add_field(name='⬜ ⏳ Время на сбор', value='`❌ Не выбрано`', inline=True)
        embed.add_field(name='⬜ ⚔️ С навыками', value='`❌ Не выбрано`', inline=True)
        embed.add_field(name='⬜ 📅 Дедлайн', value='`❌ Не выбрано`', inline=True)
        embed.add_field(name='📊 Прогресс', value='⬜⬜⬜ (0/3)', inline=False)

        embed.set_author(name=f'Заказчик: {ctx.author.display_name}', icon_url=ctx.author.display_avatar.url)

        embed.set_footer(text='Панель активна 5 минут')

        message = await ctx.send(embed=embed, view=view)

        view.message = message

        try:
            await ctx.message.delete()

        except:
            pass

    @commands.command(name='close_contract', aliases=['cc'])
    @commands.has_any_role(*CONTRACT_ROLES)
    async def close_contract(self, ctx: commands.Context, message_id: int = None):

        if message_id is None and ctx.message.reference:
            message_id = ctx.message.reference.message_id

        if message_id is None:
            await ctx.send('❌ Укажите ID сообщения с контрактом или ответьте на него!', delete_after=10)

            return

        contract = await self.bot.db.get_contract(ctx.guild.id, message_id)

        if not contract:
            await ctx.send('❌ Контракт не найден!', delete_after=10)

            return

        if contract.get('status') != 'collecting':
            await ctx.send('❌ Этот контракт уже закрыт!', delete_after=10)

            return

        await self.bot.db.update_contract_status(ctx.guild.id, message_id, "closed")

        participants = await self.bot.db.get_participants(ctx.guild.id, message_id)

        if participants:

            participants_list = [
                f'{i}. {ctx.guild.get_member(uid).mention if ctx.guild.get_member(uid) else f"<@{uid}>"}'
                for i, uid in enumerate(participants, 1)
            ]

            participants_text = '\n'.join(participants_list)

            count = len(participants)

        else:

            participants_text = '*Никто не записался*'

            count = 0

        thread_id = contract.get('thread_id')

        if thread_id:

            thread = ctx.guild.get_thread(thread_id)

            if thread:
                result_embed = discord.Embed(
                    title='🏁 Сбор окончен досрочно!',
                    description=f'**Закрыл:** {ctx.author.mention}\n**Итого участников:** {count}',
                    color=discord.Color.orange(),
                    timestamp=datetime.now()
                )

                result_embed.add_field(name='👥 Список участников', value=participants_text, inline=False)

                await thread.send(embed=result_embed)

        await ctx.send('✅ Контракт закрыт досрочно!', delete_after=5)

        await ctx.message.delete()

    @commands.command(name='contracts_stats', aliases=['cs'])
    @commands.has_any_role(*CONTRACT_ROLES)
    async def contracts_stats(self, ctx: commands.Context):

        contracts = await self.bot.db.get_all_contracts(ctx.guild.id)

        total = len(contracts)

        collecting = len([c for c in contracts if c.get('status') == 'collecting'])

        closed = len([c for c in contracts if c.get('status') == 'closed'])

        embed = discord.Embed(
            title='📊 Статистика контрактов',
            color=discord.Color.blue(),
            timestamp=datetime.now()
        )

        embed.add_field(name='📋 Всего', value=str(total), inline=True)

        embed.add_field(name='🟢 Идёт сбор', value=str(collecting), inline=True)

        embed.add_field(name='🔴 Закрытых', value=str(closed), inline=True)

        await ctx.send(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(ContractsCog(bot))