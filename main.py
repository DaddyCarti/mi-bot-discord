import discord
from discord.ext import commands
import os, re, asyncio, json
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

CANAL_ADMINS = 1502920731372163112
CANAL_GENERAL = 1502889242072842303

def parse_tiempo(txt):
    m = re.match(r"(\d+)(s|seg|m|min|h|d|w|y)$", txt.lower())
    if not m: return None
    n,u = int(m[1]), m[2]
    return {'s':1,'seg':1,'m':60,'min':60,'h':3600,'d':86400,'w':604800,'y':31536000}[u]*n

try: warnings = json.load(open("warnings.json"))
except: warnings = {}
def save_warn(): json.dump(warnings, open("warnings.json","w"))

# --- ESTILO ---
COLOR_OK = 0x57F287
COLOR_WARN = 0xFAA61A
COLOR_ERROR = 0xED4245
COLOR_INFO = 0x5865F2

@bot.event
async def on_ready(): print(f"✅ {bot.user}")

# PÚBLICOS
@bot.command()
async def ping(ctx):
    e = discord.Embed(title="🏓 Pong!", color=COLOR_OK); e.set_footer(text="Bot Pruebas", icon_url=bot.user.display_avatar.url); await ctx.send(embed=e)

@bot.command(name="menu")
async def menu(ctx):
    e = discord.Embed(title="📜 Menú de Comandos", description="Aquí tienes todo lo que puedo hacer:", color=COLOR_INFO)
    e.set_thumbnail(url=bot.user.display_avatar.url)
    e.add_field(name="🏓!ping", value="Comprueba si estoy vivo.", inline=False)
    e.add_field(name="👋!hola", value="Te saludo.", inline=False)
    e.add_field(name="📜!menu", value="Este panel.", inline=False)
    e.set_footer(text="Bot Pruebas", icon_url=bot.user.display_avatar.url); await ctx.send(embed=e)

# ADMIN
@bot.command(name="admi")
@commands.has_permissions(manage_messages=True)
async def admi(ctx):
    if ctx.channel.id!=CANAL_ADMINS: return
    e = discord.Embed(title="🛡️ Panel Staff", description="**Solo funciona en canal admins**", color=COLOR_WARN)
    e.set_thumbnail(url=bot.user.display_avatar.url)
    e.add_field(name="Moderación", value="`!kick @usuario razón`\n`!ban @usuario razón tiempo`\n`!unban ID`\n`!mute @usuario tiempo razón`\n`!unmute @usuario`\n`!warn @usuario razón`\n`!warnings @usuario`\n`!clear 50`", inline=False)
    e.add_field(name="Canal", value="`!lock` `!unlock` `!slowmode 5` `!nuke`", inline=False)
    e.add_field(name="Info", value="`!userinfo @usuario` `!infoserver`", inline=False)
    e.set_footer(text="ServerPrueba Mod", icon_url=bot.user.display_avatar.url); await ctx.send(embed=e)

@bot.command(name="anunciar")
@commands.has_permissions(administrator=True)
async def anunciar(ctx, *, msg):
    if ctx.channel.id!=CANAL_ADMINS: return
    e = discord.Embed(title="📢 Anuncio Oficial", description=msg, color=COLOR_ERROR); e.set_footer(text="Enviado por ServerPrueba", icon_url=bot.user.display_avatar.url)
    await bot.get_channel(CANAL_GENERAL).send(embed=e)

def admin_check(ctx): return ctx.channel.id==CANAL_ADMINS

@bot.command()
@commands.has_permissions(kick_members=True)
async def kick(ctx, member: discord.Member, *, razon="Sin motivo"):
    if not admin_check(ctx): return
    await member.kick(reason=razon)
    e = discord.Embed(title="👢 Usuario Expulsado", color=COLOR_WARN); e.add_field(name="Usuario", value=member.mention); e.add_field(name="Razón", value=razon); e.set_thumbnail(url=member.display_avatar.url); await ctx.send(embed=e)

@bot.command()
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member, *, args=""):
    if not admin_check(ctx): return
    p=args.rsplit(" ",1); t=None; r=args or "Sin motivo"
    if len(p)==2 and parse_tiempo(p[1]): t=parse_tiempo(p[1]); r=p[0]
    await ctx.guild.ban(member, reason=r)
    e = discord.Embed(title="🔨 Usuario Baneado", color=COLOR_ERROR); e.add_field(name="Usuario", value=member.mention); e.add_field(name="Razón", value=r)
    if t: e.add_field(name="Duración", value=p[1]); e.set_thumbnail(url=member.display_avatar.url); await ctx.send(embed=e)
    if t: await asyncio.sleep(t); await ctx.guild.unban(discord.Object(id=member.id))

@bot.command()
async def mute(ctx, member: discord.Member, tiempo: str, *, razon="Sin motivo"):
    if not admin_check(ctx): return
    s=parse_tiempo(tiempo) or 60
    await member.timeout(datetime.utcnow()+timedelta(seconds=s), reason=razon)
    e = discord.Embed(title="🔇 Usuario Silenciado", color=0x9B59B6); e.add_field(name="Usuario", value=member.mention); e.add_field(name="Tiempo", value=tiempo); e.add_field(name="Razón", value=razon); await ctx.send(embed=e)

@bot.command()
async def unmute(ctx, member: discord.Member):
    if not admin_check(ctx): return
    await member.timeout(None); e=discord.Embed(title="🔊 Silencio Removido", description=f"{member.mention} ya puede hablar", color=COLOR_OK); await ctx.send(embed=e)

@bot.command()
async def warn(ctx, member: discord.Member, *, razon):
    if not admin_check(ctx): return
    warnings.setdefault(str(member.id), []).append({"r":razon,"t":datetime.utcnow().isoformat()}); save_warn()
    e=discord.Embed(title="⚠️ Advertencia", color=COLOR_WARN); e.add_field(name="Usuario", value=member.mention); e.add_field(name="Razón", value=razon); await ctx.send(embed=e)

@bot.command()
async def warnings(ctx, member: discord.Member):
    if not admin_check(ctx): return
    w=warnings.get(str(member.id),[]); e=discord.Embed(title=f"📋 Warns de {member.display_name}", description=f"Total: **{len(w)}**", color=COLOR_INFO); e.set_thumbnail(url=member.display_avatar.url); await ctx.send(embed=e)

@bot.command()
async def clear(ctx, cant:int=10):
    if not admin_check(ctx): return
    await ctx.channel.purge(limit=cant+1); e=discord.Embed(title="🧹 Limpieza", description=f"{cant} mensajes borrados", color=COLOR_OK); await ctx.send(embed=e, delete_after=3)

@bot.command()
async def lock(ctx):
    if not admin_check(ctx): return
    await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=False); e=discord.Embed(title="🔒 Canal Bloqueado", color=COLOR_ERROR); await ctx.send(embed=e)

@bot.command()
async def unlock(ctx):
    if not admin_check(ctx): return
    await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=None); e=discord.Embed(title="🔓 Canal Desbloqueado", color=COLOR_OK); await ctx.send(embed=e)

@bot.command()
async def slowmode(ctx, seg:int):
    if not admin_check(ctx): return
    await ctx.channel.edit(slowmode_delay=seg); e=discord.Embed(title="🐢 Slowmode", description=f"{seg} segundos", color=COLOR_INFO); await ctx.send(embed=e)

@bot.command()
async def userinfo(ctx, member: discord.Member=None):
    if not admin_check(ctx): return
    m=member or ctx.author; e=discord.Embed(title=f"👤 {m.display_name}", color=COLOR_INFO); e.set_thumbnail(url=m.display_avatar.url)
    e.add_field(name="ID", value=m.id); e.add_field(name="Cuenta creada", value=m.created_at.strftime("%d/%m/%Y")); e.add_field(name="Se unió", value=m.joined_at.strftime("%d/%m/%Y")); await ctx.send(embed=e)

@bot.command()
async def infoserver(ctx):
    if not admin_check(ctx): return
    g=ctx.guild; e=discord.Embed(title=f"📊 {g.name}", color=COLOR_INFO); e.set_thumbnail(url=g.icon.url if g.icon else None)
    e.add_field(name="Miembros", value=g.member_count); e.add_field(name="Bots", value=sum(1 for m in g.members if m.bot)); e.add_field(name="Creado", value=g.created_at.strftime("%d/%m/%Y")); await ctx.send(embed=e)

bot.run(TOKEN)
