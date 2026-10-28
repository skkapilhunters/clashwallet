import discord
from discord.ext import commands
from discord import app_commands
from views.verification import StartVerifyView

class WelcomeCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="setup_welcome", description="Setup the verification embed")
    @app_commands.default_permissions(administrator=True) # Sirf admin chala sakta hai
    async def setup_welcome(self, interaction: discord.Interaction):
        embed = discord.Embed(
            description="**Welcome to Clash Wallet!** 👋\n\nWe’re thrilled to have you as part of our community! To help you get settled and find your way around, please take a look at the following channels:\n\n> 📜 ┃ ** Press Start Verification and Proceed  **\n\n> If you have any questions or need assistance, feel free to reach out to our team at any time. \n> **Have fun and enjoy your stay!** 🚀",
            color=10181046
        )
        embed.set_image(url="https://cdn.discordapp.com/attachments/1503014110156030023/1503179655799115796/welcome_20.gif?ex=6ae287a5&is=6ae13625&hm=475887481ed6d073b2ae9aeb6c81b4723d6f1385e38b83fac30c76fdfe46d8d8&")
        
        await interaction.channel.send(embed=embed, view=StartVerifyView())
        await interaction.response.send_message("✅ Welcome message setup successful!", ephemeral=True)

async def setup(bot):
    await bot.add_cog(WelcomeCog(bot))
