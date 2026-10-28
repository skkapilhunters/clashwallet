import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
from views.verification import StartVerifyView, OpenFormView
from web_server import start_server

load_dotenv()

class MyBot(commands.Bot):
    def __init__(self):
        # Default intents on karke bot setup kar rahe hain
        super().__init__(command_prefix="!", intents=discord.Intents.default())

    async def setup_hook(self):
        # Views ko persistent banana taki bot restart hone par bhi buttons kaam karein
        self.add_view(StartVerifyView())
        self.add_view(OpenFormView())
        
        # Cogs load karna
        await self.load_extension("cogs.welcome")
        
        # Slash commands ko Discord se sync karna
        await self.tree.sync()
        
        # Web server start karna (Railway pe success page dikhane ke liye)
        await start_server()

    async def on_ready(self):
        print(f"✅ Logged in as {self.user} (ID: {self.user.id})")
        print("🟢 Bot is now ONLINE!")

bot = MyBot()

if __name__ == "__main__":
    bot.run(os.getenv("DISCORD_TOKEN"))
