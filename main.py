import discord
from discord.ext import commands
import os
import re
import asyncio
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

CANAL_ADMINS = 1502920731372163112
CANAL_GENERAL = 1502889242072842303

def parse_tiempo(texto):
    match = re.match(r"(\d+)(s|seg|segundos?|m|min|h|hora|horas|d|dia|dias|w|semana|semanas|y|year|año|años)$", texto.lower())
    if not match: return None
    num, unidad = int(match[1]), match[2]
    if unidad.startswith('s'): return num
    if unidad.startswith('m'): return num*60
    if unidad.startswith('h'): return num*3600
    if unidad.startswith('d'): return num*86400
    if unidad.startswith('w'): return num*604800
    if unidad.startswith('y') or unidad.startswith('a'): return num*31536000
    return None

@bot.event
async def on_ready():
    print(f"✅ Bot conectado: {bot.user}")

@bot.command()
async def ping(ctx): await ctx.send("Pong!")

@bot.command(name="hola")
async def hola(ctx): await ctx.send(f"¡Hola {ctx.author.mention}! 👋")

# --- MENÚ BONITO PARA USUARIOS ---
@bot.command(name="menu")
async def menu(ctx):
    embed = discord.Embed(
        title="📜 Menú de Comandos",
        description="Aquí tienes todo lo que puedo hacer:",
        color=0x5865F2
    )
    embed.set_thumbnail(url=bot.user.display_avatar.url)
    embed.add_field(name="🏓!ping", value="Comprueba si estoy vivo.", inline=False)
    embed.add_field(name="👋!hola", value="Te saludo personalmente.", inline=False)
    embed.add_field(name="📢!anunciar <texto>", value="Solo admins, en canal admins → publica en #general", inline=False)
    embed.add_field(name="📜!menu", value="Muestra este panel.", inline=False)
    embed.set_footer(text="Bot Pruebas", icon_url=bot.user.display_avatar.url) # <-- AQUÍ
    await ctx.send(embed=embed)

@bot.command(name="anunciar")
@commands.has_permissions(administrator=True)
async def anunciar(ctx, *, mensaje: str):
    if ctx.channel.id!= CANAL_ADMINS: return
    canal = bot.get_channel(CANAL_GENERAL)
    embed = discord.Embed(title="📢 Anuncio Oficial", description=mensaje, color=0xED4245)
    embed.set_footer(text="Enviado por ServerPrueba", icon_url=bot.user.display_avatar.url)
    await canal.send(embed=embed)

@bot.command(name="admi")
@commands.has_permissions(ban_members=True)
async def admi(ctx):
    if ctx.channel.id!= CANAL_ADMINS: return
    embed = discord.Embed(title="🛡️ Panel Admin", description="Solo en canal admins", color=0xFAA61A)
    embed.add_field(name="!ban @usuario motivo tiempo", value="Ej: `!ban @Jairo mal comportamiento 2d`", inline=False)
    embed.add_field(name="!unban ID motivo", value="Ej: `!unban 123456789 volvió`", inline=False)
    embed.add_field(name="Tiempos", value="10s, 5m, 2h, 3d, 1w, 1y", inline=False)
    embed.set_footer(text="ServerPrueba Mod")
    await ctx.send(embed=embed)

@bot.command(name="ban")
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member, *, args=""):
    if ctx.channel.id!= CANAL_ADMINS: return
    partes = args.rsplit(" ", 1)
    tiempo = None; motivo = args
    if len(partes)==2 and parse_tiempo(partes[1]):
        tiempo = parse_tiempo(partes[1]); motivo = partes[0]
    if not motivo: motivo = "Sin motivo"
    await ctx.guild.ban(member, reason=f"{motivo} | por {ctx.author}")
    await ctx.send(f"🔨 {member} baneado. Motivo: {motivo}" + (f" | {partes[1]}" if tiempo else ""))
    if tiempo:
        await asyncio.sleep(tiempo)
        try:
            await ctx.guild.unban(discord.Object(id=member.id))
            await bot.get_channel(CANAL_ADMINS).send(f"⏰ Unban automático: {member}")
        except: pass

@bot.command(name="unban")
@commands.has_permissions(ban_members=True)
async def unban(ctx, user_id: int, *, motivo="Sin motivo"):
    if ctx.channel.id!= CANAL_ADMINS: return
    try:
        await ctx.guild.unban(discord.Object(id=user_id), reason=motivo)
        await ctx.send(f"✅ {user_id} desbaneado.")
    except: await ctx.send("❌ No encontré ese ban.")

bot.run(TOKEN)
