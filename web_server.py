from aiohttp import web
import os

async def handle_get(request):
    code = request.query.get('code')
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
        return web.Response(text=html_content, content_type='text/html')
    
    invite_link = "https://discord.gg/R8AndtbdS"
    raise web.HTTPFound(invite_link)

async def start_server():
    app = web.Application()
    app.add_routes([web.get('/', handle_get)])
    runner = web.AppRunner(app)
    await runner.setup()
    
    # Railway automatically PORT environment variable provide karta hai
    port = int(os.getenv("PORT", 8080))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    print(f"🌐 Web server started on port {port}")
