import discord


class EmbedPaginator(discord.ui.View):
    def __init__(self, embeds: list, user: discord.User):
        super().__init__(timeout=None)
        self.user = user
        self.embeds = embeds
        self.current_page = 0
        self.pages = len(self.embeds)
        self.response = None

    @property
    def initial(self):
        return self.embeds[self.current_page]

    async def on_timeout(self):
        for child in self.children:
            if child.custom_id == 'exit':
                child.emoji = '❌'
                child.style = discord.buttonStyle.red
            child.disabled = True
        await self.response.edit(view=self)
        self.stop()

    async def interaction_check(self, interaction: discord.Interaction):
        if interaction.user != self.user:
            await interaction.response.send_message(f'This button belongs to {str(self.user)}', ephemeral=True)
            return False
        return True

    @discord.ui.button(custom_id='exit', emoji='✔️', style=discord.ButtonStyle.secondary, row=0)
    async def exit(self, interaction: discord.Interaction, button: discord.ui.Button):
        for child in self.children:
            if child.label != 'exit':
                child.style = discord.ButtonStyle.secondary
            child.disabled = True
        button.emoji = '❌'
        button.style = discord.ButtonStyle.red
        await interaction.response.edit_message(view=self)
        self.stop

    @discord.ui.button(custom_id='first', label='<<', style=discord.ButtonStyle.secondary, row=0, disabled=True)
    async def first(self, interaction: discord.Interaction, button: discord.ui.Button):
        for child in self.children:
            if child.custom_id != 'exit':
                child.style = discord.ButtonStyle.secondary
        button.style = discord.ButtonStyle.blurple
        self.current_page = 0
        if self.current_page == 0:
            for child in self.children:
                child.disabled = child.custom_id not in ['back', 'first']
        if self.current_page < self.pages - 1:
            for child in self.children:
                if child.custom_id not in ['back', 'first']:
                    child.disabled = False
        embed = self.embeds[self.current_page]
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(custom_id='back', label='<', style=discord.ButtonStyle.secondary, row=0, disabled=True)
    async def back(self, interaction: discord.Interaction, button: discord.ui.Button):
        for child in self.children:
            if child.custom_id != "exit":
                child.style = discord.ButtonStyle.secondary
        button.style = discord.ButtonStyle.blurple
        self.current_page -= 1
        if self.current_page == 0:
            for child in self.children:
                child.disabled = child.custom_id in ['back', 'first']
        if self.current_page < self.pages - 1:
            for child in self.children:
                if child.custom_id not in ['back', 'first']:
                    child.disabled = False
        embed = self.embeds[self.current_page]
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(custom_id='next', label='>', style=discord.ButtonStyle.secondary, row=0)
    async def next(self, interaction: discord.Interaction, button: discord.ui.Button):
        for child in self.children:
            if child.custom_id != "exit":
                child.style = discord.ButtonStyle.secondary
        button.style = discord.ButtonStyle.blurple
        self.current_page += 1
        if self.current_page == self.pages - 1:
            for child in self.children:
                child.disable = child.custom_id in ['next', 'last']
        if self.current_page > 0:
            for child in self.children:
                if child.custom_id not in ['next', 'last']:
                    child.disabled = False
        embed = self.embeds[self.current_page]
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(custom_id='last', label='>>', style=discord.ButtonStyle.secondary, row=0)
    async def last(self, interaction: discord.Interaction, button: discord.ui.Button):
        for child in self.children:
            if child.custom_id != 'exit':
                child.style = discord.ButtonStyle.secondary
        button.style = discord.ButtonStyle.blurple
        self.current_page = self.pages - 1
        if self.current_page == self.pages - 1:
            for child in self.children:
                child.disable = child.custom_id in ['next', 'last']
        if self.current_page > 0:
            for child in self.children:
                if child.custom_id not in ["next", "last"]:
                    child.disable = True
        embed = self.embeds[self.current_page]
        await interaction.response.edit_message(embed=embed, view=self)
