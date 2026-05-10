import discord
from discord.ext import commands
import os
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"✅ Bot conectado: {bot.user}")

@bot.command()
async def ping(ctx):
    await ctx.send("Pong!")

@bot.command(name="hola")
async def hola(ctx):
    await ctx.send(f"¡Hola {ctx.author.mention}! 👋")

@bot.command(name="menu")
async def menu(ctx):
    embed = discord.Embed(
        title="📜 Menú de Comandos",
        description="Aquí tienes todo lo que puedo hacer:",
        color=0x5865F2
    )
    embed.set_thumbnail(url=bot.user.display_avatar.url)
    embed.add_field(name="🏓 !ping", value="Comprueba si estoy vivo.", inline=False)
    embed.add_field(name="👋 !hola", value="Te saludo personalmente.", inline=False)
    embed.add_field(name="📢 !anunciar <texto>", value="Solo admins, en canal admins → publica en #general", inline=False)
    embed.add_field(name="📜 !menu", value="Muestra este panel.", inline=False)
    embed.set_footer(text=f"Solicitado por {ctx.author}", icon_url=ctx.author.display_avatar.url)
    await ctx.send(embed=embed)

@bot.command(name="anunciar")
@commands.has_permissions(administrator=True)
async def anunciar(ctx, *, mensaje: str):
    CANAL_ADMINS = 1502920731372163112
    CANAL_GENERAL = 1502889242072842303

    # Solo funciona si lo escribes en el canal de admins
    if ctx.channel.id != CANAL_ADMINS:
        return  # no hace nada en otros canales

    canal_general = bot.get_channel(CANAL_GENERAL)
    
    embed = discord.Embed(
        title="📢 Anuncio Oficial",
        description=mensaje,
        color=0xED4245
    )
    embed.set_footer(text=f"Por {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url)
    
    await canal_general.send(embed=embed)
    await ctx.message.add_reaction("✅")

bot.run(TOKEN)
