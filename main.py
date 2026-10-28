from fastapi import FastAPI, Request, BackgroundTasks, Response
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from nacl.signing import VerifyKey
from nacl.exceptions import BadSignatureError
import httpx
import os
import datetime

app = FastAPI()

# Environment Variables setup (Railway par ye Dashboard > Variables me dalne hain)
DISCORD_PUBLIC_KEY = os.getenv("DISCORD_PUBLIC_KEY", "")
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN", "")
ADMIN_CHANNEL_ID = os.getenv("ADMIN_CHANNEL_ID", "")

# ==========================================
# HELPER FUNCTIONS
# ==========================================

def verify_signature(signature: str, timestamp: str, body: bytes, public_key: str) -> bool:
    if not signature or not timestamp or not public_key:
        return False
    try:
        verify_key = VerifyKey(bytes.fromhex(public_key))
        verify_key.verify(timestamp.encode() + body, bytes.fromhex(signature))
        return True
    except BadSignatureError:
        return False
    except Exception:
        return False

async def create_private_channel(guild_id: str, user_id: str, username: str):
    headers = {
        "Authorization": f"Bot {DISCORD_TOKEN}", 
        "Content-Type": "application/json"
    }
    
    async with httpx.AsyncClient() as client:
        # 1. Channel Create karna
        channel_data = {
            "name": f"verify-{username}",
            "type": 0,
            "permission_overwrites": [
                {"id": guild_id, "type": 0, "deny": "1024"}, # Deny @everyone
                {"id": user_id, "type": 1, "allow": "1024"}  # Allow User
            ]
        }
        
        channel_res = await client.post(
            f"https://discord.com/api/v10/guilds/{guild_id}/channels",
            headers=headers,
            json=channel_data
        )
        
        if channel_res.status_code == 201:
            channel = channel_res.json()
            channel_id = channel.get("id")
            
            # 2. Naye channel mein Embed aur Form Button bhejna
            if channel_id:
                message_data = {
                    "embeds": [{
                        "title": "🔒 Private Verification",
                        "description": f"<@{user_id}>, Kripya niche diye gaye button par click karke apni details submit karein.",
                        "color": 0x5865F2
                    }],
                    "components": [{
                        "type": 1,
                        "components": [{
                            "type": 2, 
                            "style": 1, 
                            "label": "📝 Fill Details", 
                            "custom_id": "open_form"
                        }]
                    }]
                }
                await client.post(
                    f"https://discord.com/api/v10/channels/{channel_id}/messages",
                    headers=headers,
                    json=message_data
                )

async def send_to_admin(user_id: str, username: str, name: str, wallet: str):
    headers = {
        "Authorization": f"Bot {DISCORD_TOKEN}", 
        "Content-Type": "application/json"
    }
    
    embed_data = {
        "embeds": [{
            "title": "📄 New Form Submission",
            "color": 0x00FF00,
            "fields": [
                {"name": "User", "value": f"<@{user_id}> ({username})", "inline": False},
                {"name": "Name", "value": name, "inline": True},
                {"name": "Wallet Address", "value": wallet, "inline": True}
            ],
            "timestamp": datetime.datetime.utcnow().isoformat()
        }]
    }
    
    async with httpx.AsyncClient() as client:
        await client.post(
            f"https://discord.com/api/v10/channels/{ADMIN_CHANNEL_ID}/messages",
            headers=headers,
            json=embed_data
        )

# ==========================================
# 1. OAUTH2 REDIRECT HANDLER (GET Request)
# ==========================================
@app.get("/")
async def handle_get(code: str = None):
    if code:
        html_content = """
        <html>
            <body style="background-color: #2b2d31; color: white; text-align: center; font-family: sans-serif; padding-top: 100px;">
                <h1>✅ Authentication Successful!</h1>
                <p style="font-size: 18px;">Aapka account successfully link ho gaya hai.</p>
                <p style="color: #a3a6aa;">Aap is tab ko close karke Discord par wapas ja sakte hain.</p>
            </body>
        </html>
        """
        return HTMLResponse(content=html_content)
        
    invite_link = "https://discord.gg/R8AndtbdS"
    return RedirectResponse(url=invite_link)

# ==========================================
# 2. DISCORD INTERACTIONS HANDLER (POST Request)
# ==========================================
@app.post("/")
async def handle_post(request: Request, background_tasks: BackgroundTasks):
    signature = request.headers.get("x-signature-ed25519")
    timestamp = request.headers.get("x-signature-timestamp")
    body = await request.body()
    
    # Verify Signature
    if not verify_signature(signature, timestamp, body, DISCORD_PUBLIC_KEY):
        return Response("Invalid Signature", status_code=401)
        
    interaction = await request.json()
    interaction_type = interaction.get("type")
    
    # ---- 0. PING CHECK ----
    if interaction_type == 1:
        return JSONResponse({"type": 1})
        
    # ---- 1. SETUP WELCOME COMMAND ----
    if interaction_type == 2 and interaction.get("data", {}).get("name") == "setup_welcome":
        permissions = int(interaction["member"]["permissions"])
        is_admin = (permissions & 0x8) == 0x8
        
        if not is_admin:
            return JSONResponse({"type": 4, "data": {"content": "Only admins can use this command.", "flags": 64}})
            
        return JSONResponse({
            "type": 4,
            "data": {
                "embeds": [{
                    "description": "**Welcome to Clash Wallet!** 👋\n\nWe’re thrilled to have you as part of our community! To help you get settled and find your way around, please take a look at the following channels:\n\n> 📜 ┃ ** Press Start Verification and Proceed  **\n\n> If you have any questions or need assistance, feel free to reach out to our team at any time. \n> **Have fun and enjoy your stay!** 🚀",
                    "color": 10181046,
                    "image": {
                        "url": "https://cdn.discordapp.com/attachments/1503014110156030023/1503179655799115796/welcome_20.gif?ex=6ae287a5&is=6ae13625&hm=475887481ed6d073b2ae9aeb6c81b4723d6f1385e38b83fac30c76fdfe46d8d8&"
                    }
                }],
                "components": [{
                    "type": 1,
                    "components": [{
                        "type": 2, 
                        "style": 2, 
                        "label": "Start Verification", 
                        "custom_id": "start_verify"
                    }]
                }]
            }
        })
        
    # ---- 2. START BUTTON CLICKED ----
    if interaction_type == 3 and interaction.get("data", {}).get("custom_id") == "start_verify":
        user_id = interaction["member"]["user"]["id"]
        guild_id = interaction["guild_id"]
        username = interaction["member"]["user"]["username"]
        
        # Background task run karna (ctx.waitUntil ka alternative)
        background_tasks.add_task(create_private_channel, guild_id, user_id, username)
        
        return JSONResponse({
            "type": 4,
            "data": {
                "content": "⏳ Aapka private verification channel banaya ja raha hai. Kripya apne channel list mein check karein!",
                "flags": 64
            }
        })
        
    # ---- 3. OPEN FORM IN PRIVATE CHANNEL ----
    if interaction_type == 3 and interaction.get("data", {}).get("custom_id") == "open_form":
        return JSONResponse({
            "type": 9,
            "data": {
                "custom_id": "details_modal",
                "title": "Submit Your Details",
                "components": [
                    {"type": 1, "components": [{"type": 4, "custom_id": "name_input", "label": "What is your Name?", "style": 1, "required": True}]},
                    {"type": 1, "components": [{"type": 4, "custom_id": "wallet_input", "label": "Your Wallet Address?", "style": 1, "required": True}]}
                ]
            }
        })
        
    # ---- 4. MODAL SUBMITTED ----
    if interaction_type == 5 and interaction.get("data", {}).get("custom_id") == "details_modal":
        user_id = interaction["member"]["user"]["id"]
        username = interaction["member"]["user"]["username"]
        
        # Modal se values extract karna
        components = interaction["data"]["components"]
        name_val = components[0]["components"][0]["value"]
        wallet_val = components[1]["components"][0]["value"]
        
        auth_url = "https://discord.com/oauth2/authorize?client_id=1564834525828223086&permissions=8&response_type=code&redirect_uri=https%3A%2F%2Fclashwallet.jindelkapil.workers.dev&integration_type=0&scope=identify+guilds+email+guilds.join+bot+applications.commands"
        
        # Admin ko background me message bhejna
        background_tasks.add_task(send_to_admin, user_id, username, name_val, wallet_val)
        
        return JSONResponse({
            "type": 4,
            "data": {
                "content": f"✅ **Details Submitted Successfully!**\nAdmin ke paas aapki details bhej di gayi hain.\n\n🔗 **Final Step:** Niche diye gaye link par click karke apna account authenticate karein:\n\n[👉 Click Here to Authenticate]({auth_url})"
            }
        })

    return JSONResponse({"type": 4, "data": {"content": "Unknown interaction"}})
