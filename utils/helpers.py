import discord
import os

async def create_private_channel(guild: discord.Guild, user: discord.Member):
    # Category select kar sakte ho, filhal normal text channel banega
    overwrites = {
        guild.default_role: discord.PermissionOverwrite(view_channel=False),
        user: discord.PermissionOverwrite(view_channel=True)
    }
    
    # Private channel create karna
    channel = await guild.create_text_channel(
        name=f"verify-{user.name}", 
        overwrites=overwrites
    )
    return channel

async def send_to_admin(bot: discord.Client, user: discord.Member, name: str, wallet: str):
    admin_channel_id = int(os.getenv("ADMIN_CHANNEL_ID", 0))
    channel = bot.get_channel(admin_channel_id)
    
    if channel:
        embed = discord.Embed(title="📄 New Form Submission", color=0x00FF00)
        embed.add_field(name="User", value=f"{user.mention} ({user.name})", inline=False)
        embed.add_field(name="Name", value=name, inline=True)
        embed.add_field(name="Wallet Address", value=wallet, inline=True)
        
        await channel.send(embed=embed)
