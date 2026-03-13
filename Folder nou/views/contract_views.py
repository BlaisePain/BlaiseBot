import discord
from discord import ui
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import asyncio

class ContractPanelState:
    """Хранит состояние выбора"""
    
    _states: Dict[int, Dict[str, Any]] = {}
    
    @classmethod
    def get(cls, user_id: int) -> Dict[str, Any]:
        if user_id not in cls._states:
            cls._states[user_id] = {'time': None, 'skills': None, 'deadline': None}
        return cls._states[user_id]
    
    @classmethod
    def set(cls, user_id: int, key: str, value: str):
        if user_id not in cls._states:
            cls._states[user_id] = {'time': None, 'skills': None, 'deadline': None}
        cls._states[user_id][key] = value
    
    @classmethod
    def clear(cls, user_id: int):
        if user_id in cls._states:
            del cls._states[user_id]
    
    @classmethod
    def is_complete(cls, user_id: int) -> bool:
        state = cls.get(user_id)
        return all(state.values())


class TimeSelectMenu(ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label='10 минут', value='10', emoji='⏱️'),
            discord.SelectOption(label='15 минут', value='15', emoji='🕐'),
            discord.SelectOption(label='20 минут', value='20', emoji='🕑'),
            discord.SelectOption(label='30 минут', value='30', emoji='🕒'),
        ]
        super().__init__(placeholder='⏳ Время на сбор...', options=options, custom_id='time_select')
    
    async def callback(self, interaction: discord.Interaction):
        ContractPanelState.set(interaction.user.id, 'time', self.values[0])
        await self.view.update_panel(interaction)


class SkillsSelectMenu(ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label='Да', value='Да', emoji='✅'),
            discord.SelectOption(label='Нет', value='Нет', emoji='❌'),
        ]
        super().__init__(placeholder='⚔️ С навыками?', options=options, custom_id='skills_select')
    
    async def callback(self, interaction: discord.Interaction):
        ContractPanelState.set(interaction.user.id, 'skills', self.values[0])
        await self.view.update_panel(interaction)


class DeadlineSelectMenu(ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label='Сразу', value='Сразу', emoji='⚡'),
            discord.SelectOption(label='До нулей', value='До нулей', emoji='🕛'),
            discord.SelectOption(label='До рестарта', value='До рестарта', emoji='🔄'),
            discord.SelectOption(label='Без разницы', value='Без разницы', emoji='♾️'),
        ]
        super().__init__(placeholder='📅 Дедлайн...', options=options, custom_id='deadline_select')
    
    async def callback(self, interaction: discord.Interaction):
        ContractPanelState.set(interaction.user.id, 'deadline', self.values[0])
        await self.view.update_panel(interaction)


class ContractPanelView(ui.View):
    def __init__(self, creator_id: int):
        super().__init__(timeout=300)
        self.creator_id = creator_id
        self.message: Optional[discord.Message] = None
        
        self.add_item(TimeSelectMenu())
        self.add_item(SkillsSelectMenu())
        self.add_item(DeadlineSelectMenu())
    
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.creator_id:
            await interaction.response.send_message('❌ Только создатель!', ephemeral=True)
            return False
        return True
    
    async def update_panel(self, interaction: discord.Interaction):
        state = ContractPanelState.get(interaction.user.id)
        embed = self._create_embed(state, interaction.user)
        await interaction.response.edit_message(embed=embed, view=self)
    
    def _create_embed(self, state: Dict[str, Any], user: discord.User) -> discord.Embed:
        embed = discord.Embed(title='📜 Создание контракта', color=discord.Color.blue())
        
        time_val = f'{state["time"]} мин' if state['time'] else '❌'
        skills_val = state['skills'] or '❌'
        deadline_val = state['deadline'] or '❌'
        
        t = '✅' if state['time'] else '⬜'
        s = '✅' if state['skills'] else '⬜'
        d = '✅' if state['deadline'] else '⬜'
        
        embed.add_field(name=f'{t} ⏳ Время', value=f'`{time_val}`', inline=True)
        embed.add_field(name=f'{s} ⚔️ Навыки', value=f'`{skills_val}`', inline=True)
        embed.add_field(name=f'{d} 📅 Дедлайн', value=f'`{deadline_val}`', inline=True)
        
        done = sum(1 for v in state.values() if v)
        embed.add_field(name='📊', value=f'{"🟩"*done}{"⬜"*(3-done)} ({done}/3)', inline=False)
        
        if ContractPanelState.is_complete(user.id):
            embed.color = discord.Color.green()
            embed.add_field(name='✅', value='Нажмите "Опубликовать"!', inline=False)
        
        embed.set_author(name=user.display_name, icon_url=user.display_avatar.url)
        return embed

    @ui.button(label='Опубликовать', style=discord.ButtonStyle.success, emoji='📜', row=4)
    async def publish_button(self, interaction: discord.Interaction, button: ui.Button):

        state = ContractPanelState.get(interaction.user.id)

        if not ContractPanelState.is_complete(interaction.user.id):
            await interaction.response.send_message(
                '❌ Выберите все параметры!', ephemeral=True
            )
            return

        await interaction.response.defer()

        collect_time = int(state['time'])
        end_time = datetime.now() + timedelta(minutes=collect_time)

        contract_embed = discord.Embed(
            title='📜 Новый контракт!',
            description='**Поставьте ✅ чтобы участвовать!**',
            color=discord.Color.gold(),
            timestamp=datetime.now()
        )

        contract_embed.add_field(name='👤 Заказчик', value=interaction.user.mention, inline=True)
        contract_embed.add_field(name='⏳ Сбор', value=f'{collect_time} мин', inline=True)
        contract_embed.add_field(name='⚔️ Навыки', value=state['skills'], inline=True)
        contract_embed.add_field(name='📅 Дедлайн', value=state['deadline'], inline=True)
        contract_embed.add_field(name='⏰ До', value=f'<t:{int(end_time.timestamp())}:T>', inline=True)
        contract_embed.add_field(name='📊 Статус', value='🟢 Сбор', inline=True)
        contract_embed.add_field(name='✅ Участники', value='*Пока никого*', inline=False)

        contract_embed.set_thumbnail(url=interaction.user.display_avatar.url)
        contract_embed.set_footer(text=f'ID: {interaction.user.id}')

        # trimite contractul
        contract_msg = await interaction.channel.send(embed=contract_embed)

        await contract_msg.add_reaction('✅')

        # creează thread
        thread = await contract_msg.create_thread(
            name=f'📜 Контракт - {interaction.user.display_name}'[:100],
            auto_archive_duration=1440
        )

        await thread.send(embed=discord.Embed(
            title='📜 Сбор на контракт!',
            description=(
                f'**Заказчик:** {interaction.user.mention}\n'
                f'**Время:** {collect_time} мин\n'
                f'**Навыки:** {state["skills"]}\n'
                f'**Дедлайн:** {state["deadline"]}\n\n'
                '**Поставьте ✅ на сообщение выше!**'
            ),
            color=discord.Color.blue()
        ))

        # salvează în DB
        await interaction.client.db.create_contract(
            interaction.guild.id,
            contract_msg.id,
            interaction.user.id,
            collect_time,
            state['skills'],
            state['deadline'],
            thread.id,
            end_time
        )

        # șterge panelul
        try:
            await interaction.message.delete()
        except:
            pass

        ContractPanelState.clear(interaction.user.id)

        await interaction.followup.send(
            f'✅ Контракт создан!\n📍 {thread.mention}',
            ephemeral=True
        )

        # timer final
        asyncio.create_task(self._end_collection(
            interaction.client,
            interaction.guild.id,
            contract_msg.id,
            thread.id,
            collect_time * 60
        ))
    
    async def _end_collection(self, bot, guild_id: int, message_id: int, thread_id: int, delay: int):
        await asyncio.sleep(delay)

        guild = bot.get_guild(guild_id)
        if not guild:
            return

        thread = guild.get_thread(thread_id)

        participants = await bot.db.get_participants(guild_id, message_id)

        channel = thread.parent
        msg = await channel.fetch_message(message_id)

        await msg.clear_reactions()

        if participants:

            plist = []

            for i, uid in enumerate(participants, 1):

                member = guild.get_member(uid)

                if member:
                    plist.append(f"{i}. {member.display_name}")
                else:
                    plist.append(f"{i}. <@{uid}>")

            text = "\n".join(plist)

        else:

            text = "*Никто не записался*"

        await thread.send(
            embed=discord.Embed(
                title="📋 Участники контракта",
                description=text,
                color=discord.Color.green()
            )
        )
        result_embed.add_field(name='👥 Список', value=ptext, inline=False)
        
        if thread:
            await thread.send(embed=result_embed)
            try:
                await thread.edit(name=f'✅ {thread.name}'[:100])
            except:
                pass
        
        await bot.db.update_contract_status(guild_id, message_id, "closed")
        
        config = bot.config_manager.get_guild_config(guild_id)
        ch_id = config.get('channels', {}).get('contract_reports')
        if ch_id:
            channel = guild.get_channel(ch_id)
            if channel:
                try:
                    msg = await channel.fetch_message(message_id)
                    if msg.embeds:
                        old = msg.embeds[0]
                        new = discord.Embed(
                            title='📜 Контракт (завершён)',
                            color=discord.Color.greyple(),
                            timestamp=old.timestamp
                        )
                        for f in old.fields:
                            if f.name == '📊 Статус':
                                new.add_field(name='📊', value='🔴 Завершён', inline=True)
                            elif f.name == '✅ Участники':
                                new.add_field(name='✅', value=f'{count} чел.', inline=False)
                            else:
                                new.add_field(name=f.name, value=f.value, inline=f.inline)
                        if old.thumbnail:
                            new.set_thumbnail(url=old.thumbnail.url)
                        await msg.edit(embed=new)
                        await msg.clear_reactions()
                except:
                    pass
    
    @ui.button(label='Отмена', style=discord.ButtonStyle.danger, emoji='❌', row=4)
    async def cancel_button(self, interaction: discord.Interaction, button: ui.Button):
        ContractPanelState.clear(interaction.user.id)
        await interaction.message.delete()
        await interaction.response.send_message('❌ Отменено.', ephemeral=True)
    
    @ui.button(label='Сброс', style=discord.ButtonStyle.secondary, emoji='🔄', row=4)
    async def reset_button(self, interaction: discord.Interaction, button: ui.Button):
        ContractPanelState.clear(interaction.user.id)
        state = ContractPanelState.get(interaction.user.id)
        embed = self._create_embed(state, interaction.user)
        await interaction.response.edit_message(embed=embed, view=self)
    
    async def on_timeout(self):
        ContractPanelState.clear(self.creator_id)
        if self.message:
            try:
                await self.message.edit(
                    embed=discord.Embed(title='⏰ Время вышло', color=discord.Color.red()),
                    view=None
                )
            except:
                pass


class ContractThreadView(ui.View):
    """Persistent view для ветки контракта"""
    
    def __init__(self):
        super().__init__(timeout=None)
    
    @ui.button(label='Помощь', style=discord.ButtonStyle.secondary, custom_id='contract_help_btn', emoji='❓')
    async def help_button(self, interaction: discord.Interaction, button: ui.Button):
        senior_roles = interaction.client.config_manager.get_senior_roles(interaction.guild.id)
        
        if senior_roles:
            mentions = []
            for role_id in senior_roles:
                role = interaction.guild.get_role(role_id)
                if role:
                    mentions.append(role.mention)
            
            if mentions:
                await interaction.channel.send(f'❓ {interaction.user.mention} просит помощи!\n{" ".join(mentions)}')
                await interaction.response.send_message('✅ Уведомлено!', ephemeral=True)
                return
        
        await interaction.response.send_message('⚠️ Роли не настроены.', ephemeral=True)


class ContractApproveView(ui.View):
    """Persistent view для подтверждения"""
    
    def __init__(self):
        super().__init__(timeout=None)
    
    @ui.button(label='Подтвердить', style=discord.ButtonStyle.success, custom_id='approve_contract_btn', emoji='✅')
    async def approve_button(self, interaction: discord.Interaction, button: ui.Button):
        from utils.permissions import has_senior_staff_role
        if not await has_senior_staff_role(interaction):
            await interaction.response.send_message('❌ Нет прав!', ephemeral=True)
            return
        
        await interaction.channel.send(embed=discord.Embed(
            title='✅ Подтверждено!',
            description=f'Проверил: {interaction.user.mention}',
            color=discord.Color.green()
        ))
        
        try:
            await interaction.channel.edit(archived=True, locked=True)
        except:
            pass
        
        await interaction.response.send_message('✅ Готово!', ephemeral=True)