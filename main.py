import discord
from discord.ext import commands, tasks
import os, re, asyncio, json
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.presences = True

bot = commands.Bot(command_prefix="!", intents=intents)

CANAL_ADMINS = 1502920731372163112
CANAL_GENERAL = 1502889242072842303

# --- UTILIDADES ---
def parse_tiempo(txt):
    m = re.match(r"(\d+)(s|seg|m|min|h|d|w|y)$", txt.lower())
    if not m: return None
    n, u = int(m[1]), m[2]
    return {'s':1,'seg':1,'m':60,'min':60,'h':3600,'d':86400,'w':604800,'y':31536000}[u]*n

try: warnings = json.load(open("warnings.json"))
except: warnings = {}
def save_warn(): json.dump(warnings, open("warnings.json","w"))

COLOR_OK = 0x57F287; COLOR_WARN = 0xFAA61A; COLOR_ERROR = 0xED4245; COLOR_INFO = 0x5865F2; COLOR_MUTE = 0x9B59B6

@bot.event
async def on_ready():
    print(f"✅ {bot.user} conectado")
    actualizar_stats.start()

def admin_check(ctx): return ctx.channel.id == CANAL_ADMINS

# --- COMANDOS PÚBLICOS ---
@bot.command()
async def ping(ctx):
    e = discord.Embed(title="🏓 Pong!", description=f"Latencia: {round(bot.latency*1000)}ms", color=COLOR_OK, timestamp=datetime.utcnow())
    e.set_footer(text="ServerPrueba", icon_url=bot.user.display_avatar.url)
    await ctx.send(embed=e)

@bot.command()
async def hola(ctx):
    await ctx.send(f"¡Hola {ctx.author.mention}! 👋")

@bot.command(name="menu")
async def menu(ctx):
    e = discord.Embed(title="📜 Menú Principal", color=COLOR_INFO, timestamp=datetime.utcnow())
    e.set_thumbnail(url=bot.user.display_avatar.url)
    e.add_field(name="🏓!ping", value="Verifica la conexión", inline=False)
    e.add_field(name="👋!hola", value="Saludo del bot", inline=False)
    e.set_footer(text="Usa!admi si eres staff", icon_url=bot.user.display_avatar.url)
    await ctx.send(embed=e)

# --- PANEL STAFF ---
@bot.command(name="admi")
@commands.has_permissions(manage_messages=True)
async def admi(ctx):
    if not admin_check(ctx): return
    e = discord.Embed(title="🛡️ Panel de Staff", description=f"Solo funciona en <#{CANAL_ADMINS}>", color=COLOR_WARN, timestamp=datetime.utcnow())
    e.set_thumbnail(url=bot.user.display_avatar.url)
    e.add_field(name="🔨 Moderación", value="`!kick @u razón` • Expulsa\n`!ban @u razón [tiempo]` • Banea\n`!unban ID` • Desbanea\n`!mute @u 10m razón` • Silencia\n`!unmute @u` • Quita mute\n`!warn @u razón` • Advierte\n`!warnings @u` • Ver warns", inline=False)
    e.add_field(name="🧹 Canales", value="`!clear [n]` • Borra msgs\n`!lock #canal` • Cierra\n`!unlock #canal` • Abre\n`!slowmode [s]` • Lento\n`!stats` • Crea stats arriba\n`!delstats` • Borra stats", inline=False)
    e.add_field(name="ℹ️ Info", value="`!userinfo @u` • Ficha usuario\n`!infoserver` • Info server", inline=False)
    e.add_field(name="📢 Anuncios", value="`!anunciar texto` • Envía a #general", inline=False)
    e.set_footer(text="ServerPrueba Mod", icon_url=bot.user.display_avatar.url)
    await ctx.send(embed=e)

@bot.command(name="anunciar")
@commands.has_permissions(administrator=True)
async def anunciar(ctx, *, msg):
    if not admin_check(ctx): return
    e = discord.Embed(title="📢 ANUNCIO OFICIAL", description=msg, color=COLOR_ERROR, timestamp=datetime.utcnow())
    e.set_footer(text=f"Por {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url)
    await bot.get_channel(CANAL_GENERAL).send(embed=e)
    await ctx.message.add_reaction("✅")

# --- MODERACIÓN ---
@bot.command()
@commands.has_permissions(kick_members=True)
async def kick(ctx, member: discord.Member, *, razon="Sin motivo"):
    if not admin_check(ctx): return
    await member.kick(reason=razon)
    e = discord.Embed(title="👢 Expulsado", color=COLOR_WARN, timestamp=datetime.utcnow())
    e.add_field(name="Usuario", value=member.mention); e.add_field(name="Staff", value=ctx.author.mention)
    e.add_field(name="Razón", value=razon, inline=False); e.set_thumbnail(url=member.display_avatar.url)
    await ctx.send(embed=e)

@bot.command()
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member, *, args=""):
    if not admin_check(ctx): return
    p=args.rsplit(" ",1); r=args or "Sin motivo"; t=None
    if len(p)==2 and parse_tiempo(p[1]): t=parse_tiempo(p[1]); r=p[0]
    await ctx.guild.ban(member, reason=r)
    e = discord.Embed(title="🔨 Baneado", color=COLOR_ERROR, timestamp=datetime.utcnow())
    e.add_field(name="Usuario", value=member.mention); e.add_field(name="Tiempo", value=p[1] if t else "Permanente")
    e.add_field(name="Razón", value=r, inline=False); e.set_thumbnail(url=member.display_avatar.url)
    await ctx.send(embed=e)
    if t: await asyncio.sleep(t); await ctx.guild.unban(discord.Object(id=member.id))

@bot.command()
@commands.has_permissions(ban_members=True)
async def unban(ctx, user_id: int):
    if not admin_check(ctx): return
    await ctx.guild.unban(discord.Object(id=user_id))
    e = discord.Embed(title="✅ Desbaneado", description=f"ID: {user_id}", color=COLOR_OK, timestamp=datetime.utcnow())
    await ctx.send(embed=e)

@bot.command()
@commands.has_permissions(moderate_members=True)
async def mute(ctx, member: discord.Member, tiempo: str, *, razon="Sin motivo"):
    if not admin_check(ctx): return
    s = parse_tiempo(tiempo) or 60
    await member.timeout(datetime.utcnow()+timedelta(seconds=s), reason=razon)
    e = discord.Embed(title="🔇 Silenciado", color=COLOR_MUTE, timestamp=datetime.utcnow())
    e.add_field(name="Usuario", value=member.mention); e.add_field(name="Duración", value=tiempo)
    e.add_field(name="Razón", value=razon, inline=False)
    await ctx.send(embed=e)

@bot.command()
@commands.has_permissions(moderate_members=True)
async def unmute(ctx, member: discord.Member):
    if not admin_check(ctx): return
    await member.timeout(None)
    e = discord.Embed(title="🔊 Voz devuelta", description=f"{member.mention} puede hablar", color=COLOR_OK, timestamp=datetime.utcnow())
    await ctx.send(embed=e)

@bot.command()
async def warn(ctx, member: discord.Member, *, razon):
    if not admin_check(ctx): return
    warnings.setdefault(str(member.id), []).append({"r":razon,"t":datetime.utcnow().isoformat()}); save_warn()
    e = discord.Embed(title="⚠️ Advertencia", color=COLOR_WARN, timestamp=datetime.utcnow())
    e.add_field(name="Usuario", value=member.mention); e.add_field(name="Total warns", value=len(warnings[str(member.id)]))
    e.add_field(name="Razón", value=razon, inline=False)
    await ctx.send(embed=e)

@bot.command()
async def warnings(ctx, member: discord.Member):
    if not admin_check(ctx): return
    w = warnings.get(str(member.id), [])
    e = discord.Embed(title=f"📋 Warns de {member.display_name}", description=f"**{len(w)}** advertencias", color=COLOR_INFO, timestamp=datetime.utcnow())
    e.set_thumbnail(url=member.display_avatar.url)
    await ctx.send(embed=e)

# --- CANALES ---
@bot.command()
@commands.has_permissions(manage_messages=True)
async def clear(ctx, cant:int=10):
    if not admin_check(ctx): return
    await ctx.channel.purge(limit=cant+1)
    e = discord.Embed(title="🧹 Limpieza", description=f"{cant} mensajes eliminados", color=COLOR_OK, timestamp=datetime.utcnow())
    await ctx.send(embed=e, delete_after=4)

@bot.command()
@commands.has_permissions(manage_channels=True)
async def lock(ctx, canal: discord.TextChannel = None):
    if not admin_check(ctx): return
    t = canal or ctx.channel
    await t.set_permissions(ctx.guild.default_role, send_messages=False)
    e = discord.Embed(title="🔒 Cerrado", description=f"{t.mention} bloqueado", color=COLOR_ERROR, timestamp=datetime.utcnow())
    await ctx.send(embed=e)

@bot.command()
@commands.has_permissions(manage_channels=True)
async def unlock(ctx, canal: discord.TextChannel = None):
    if not admin_check(ctx): return
    t = canal or ctx.channel
    await t.set_permissions(ctx.guild.default_role, send_messages=None)
    e = discord.Embed(title="🔓 Abierto", description=f"{t.mention} desbloqueado", color=COLOR_OK, timestamp=datetime.utcnow())
    await ctx.send(embed=e)

@bot.command()
@commands.has_permissions(manage_channels=True)
async def slowmode(ctx, seg:int):
    if not admin_check(ctx): return
    await ctx.channel.edit(slowmode_delay=seg)
    e = discord.Embed(title="🐢 Slowmode", description=f"{seg}s activado", color=COLOR_INFO, timestamp=datetime.utcnow())
    await ctx.send(embed=e)

# --- INFO ---
@bot.command()
async def userinfo(ctx, member: discord.Member=None):
    if not admin_check(ctx): return
    m = member or ctx.author
    e = discord.Embed(title=f"👤 {m.display_name}", color=COLOR_INFO, timestamp=datetime.utcnow())
    e.set_thumbnail(url=m.display_avatar.url)
    e.add_field(name="ID", value=m.id); e.add_field(name="Bot", value="Sí" if m.bot else "No")
    e.add_field(name="Creado", value=m.created_at.strftime("%d/%m/%Y"), inline=False)
    e.add_field(name="Se unió", value=m.joined_at.strftime("%d/%m/%Y"))
    await ctx.send(embed=e)

@bot.command()
async def infoserver(ctx):
    if not admin_check(ctx): return
    g = ctx.guild
    e = discord.Embed(title=g.name, color=COLOR_INFO, timestamp=datetime.utcnow())
    if g.icon: e.set_thumbnail(url=g.icon.url)
    e.add_field(name="Miembros", value=g.member_count); e.add_field(name="Bots", value=sum(1 for m in g.members if m.bot))
    e.add_field(name="Roles", value=len(g.roles)); e.add_field(name="Creado", value=g.created_at.strftime("%d/%m/%Y"))
    await ctx.send(embed=e)

# --- STATS ---
STATS_FILE = "stats.json"

@tasks.loop(minutes=5)
async def actualizar_stats():
    try: data = json.load(open(STATS_FILE))
    except: return
    g = bot.get_guild(data["guild"])
    if not g: return
    activos = len([m for m in g.members if not m.bot and m.status!= discord.Status.offline])
    descon = len([m for m in g.members if not m.bot and m.status == discord.Status.offline])
    bots = len([m for m in g.members if m.bot])
    rol = discord.utils.get(g.roles, name="buyer"); buyers = len(rol.members) if rol else 0
    await bot.get_channel(data["activos"]).edit(name=f"🟢 Activos: {activos}")
    await bot.get_channel(data["desconectados"]).edit(name=f"⚫ Desconectados: {descon}")
    await bot.get_channel(data["bots"]).edit(name=f"🤖 Bots: {bots}")
    await bot.get_channel(data["buyers"]).edit(name=f"🛒 Buyers: {buyers}")

@bot.command(name="stats")
@commands.has_permissions(administrator=True)
async def stats(ctx):
    if not admin_check(ctx): return
    g = ctx.guild
    cat = await g.create_category("📊 ESTADÍSTICAS", position=0)
    c1 = await g.create_voice_channel("🟢 Activos: 0", category=cat)
    c2 = await g.create_voice_channel("⚫ Desconectados: 0", category=cat)
    c3 = await g.create_voice_channel("🤖 Bots: 0", category=cat)
    c4 = await g.create_voice_channel("🛒 Buyers: 0", category=cat)
    for c in [c1,c2,c3,c4]: await c.set_permissions(g.default_role, connect=False)
    json.dump({"guild":g.id,"cat":cat.id,"activos":c1.id,"desconectados":c2.id,"bots":c3.id,"buyers":c4.id}, open(STATS_FILE,"w"))
    e = discord.Embed(title="✅ Stats creadas", description="Arriba del todo, se actualizan cada 5 min", color=COLOR_OK, timestamp=datetime.utcnow())
    await ctx.send(embed=e); await actualizar_stats()

@bot.command(name="delstats")
@commands.has_permissions(administrator=True)
async def delstats(ctx):
    if not admin_check(ctx): return
    try: data = json.load(open(STATS_FILE))
    except: return await ctx.send("No hay stats")
    g = ctx.guild
    for k in ["activos","desconectados","bots","buyers","cat"]:
        ch = g.get_channel(data.get(k))
        if ch: await ch.delete()
    os.remove(STATS_FILE)
    e = discord.Embed(title="🗑️ Stats borradas", color=COLOR_ERROR, timestamp=datetime.utcnow())
    await ctx.send(embed=e)

bot.run(TOKEN)
