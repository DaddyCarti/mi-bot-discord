# =========================================
# CONFIGURACIÓN
# =========================================
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

# IDs DE TUS CANALES
CANAL_ADMINS = 1502920731372163112
CANAL_GENERAL = 1502889242072842303

# NOMBRES AUTOMÁTICOS
TICKETS_CAT = "🎫 TICKETS"
LOGS_NAME = "📜-logs"

# COLORES
COLOR_OK = 0x57F287
COLOR_WARN = 0xFAA61A
COLOR_ERROR = 0xED4245
COLOR_INFO = 0x5865F2
COLOR_MUTE = 0x9B59B6

# =========================================
# UTILIDADES Y DATOS
# =========================================
def parse_tiempo(txt):
    m = re.match(r"(\d+)(s|seg|m|min|h|d|w|y)$", txt.lower())
    if not m: return None
    n,u = int(m[1]), m[2]
    return {'s':1,'seg':1,'m':60,'min':60,'h':3600,'d':86400,'w':604800,'y':31536000}[u]*n

try: warnings = json.load(open("warnings.json"))
except: warnings = {}
def save_warn(): json.dump(warnings, open("warnings.json","w"))

try: antilink = json.load(open("antilink.json"))
except: antilink = {"enabled": True}
def save_antilink(): json.dump(antilink, open("antilink.json","w"))

STATS_FILE = "stats.json"

def admin_check(ctx):
    return ctx.channel.id == CANAL_ADMINS

async def send_log(embed):
    for g in bot.guilds:
        ch = discord.utils.get(g.text_channels, name=LOGS_NAME)
        if ch:
            embed.timestamp = datetime.utcnow()
            embed.set_footer(text="Logs", icon_url=bot.user.display_avatar.url)
            await ch.send(embed=embed)

# =========================================
# EVENTOS
# =========================================
@bot.event
async def on_ready():
    print(f"✅ Conectado como {bot.user}")
    for g in bot.guilds:
        if not discord.utils.get(g.text_channels, name=LOGS_NAME):
            await g.create_text_channel(LOGS_NAME)
        if not discord.utils.get(g.categories, name=TICKETS_CAT):
            await g.create_category(TICKETS_CAT)
    actualizar_stats.start()

@bot.event
async def on_message(message):
    if message.author.bot or not message.guild:
        await bot.process_commands(message); return
    # ANTI-LINKS
    if antilink["enabled"] and re.search(r"(discord\.gg/|discord\.com/invite/)", message.content.lower()):
        if not message.author.guild_permissions.manage_messages:
            await message.delete()
            e = discord.Embed(title="🔗 Invite bloqueado", color=COLOR_ERROR)
            await message.channel.send(embed=e, delete_after=4)
            return
    await bot.process_commands(message)

@bot.event
async def on_member_join(m):
    await send_log(discord.Embed(title="📥 Entró", description=f"{m.mention}", color=COLOR_OK))

@bot.event
async def on_member_remove(m):
    await send_log(discord.Embed(title="📤 Salió", description=f"{m}", color=COLOR_WARN))

@bot.event
async def on_message_delete(m):
    if not m.author.bot:
        await send_log(discord.Embed(title="🗑️ Mensaje borrado", description=f"{m.author} en {m.channel.mention}: {m.content[:300]}", color=COLOR_ERROR))

# =========================================
# COMANDOS PARA USUARIOS NORMALES
# =========================================
@bot.command()
async def ping(ctx):
    await ctx.send(embed=discord.Embed(title="🏓 Pong", description=f"{round(bot.latency*1000)}ms", color=COLOR_OK))

@bot.command()
async def hola(ctx):
    await ctx.send(f"Hola {ctx.author.mention} 👋")

@bot.command(name="menu")
async def menu(ctx):
    e = discord.Embed(title="📜 Menú de Usuario", color=COLOR_INFO)
    e.add_field(name="!ping", value="Ver latencia", inline=False)
    e.add_field(name="!hola", value="Saludo", inline=False)
    e.add_field(name="!ticket [motivo]", value="Abrir ticket de soporte", inline=False)
    await ctx.send(embed=e)

@bot.command()
async def ticket(ctx, *, motivo="Soporte"):
    """Cualquier usuario puede abrir ticket"""
    cat = discord.utils.get(ctx.guild.categories, name=TICKETS_CAT)
    overw = {
        ctx.guild.default_role: discord.PermissionOverwrite(view_channel=False),
        ctx.author: discord.PermissionOverwrite(view_channel=True, send_messages=True)
    }
    for r in ctx.guild.roles:
        if r.permissions.manage_messages:
            overw[r] = discord.PermissionOverwrite(view_channel=True)
    ch = await ctx.guild.create_text_channel(f"ticket-{ctx.author.name}", category=cat, overwrites=overw)
    await ch.send(f"{ctx.author.mention}", embed=discord.Embed(title="🎫 Ticket", description=motivo, color=COLOR_INFO))
    await ctx.send(f"Ticket creado: {ch.mention}", delete_after=5)
    await send_log(discord.Embed(title="Ticket abierto", description=f"{ctx.author} → {ch.name}", color=COLOR_INFO))

@bot.command()
async def close(ctx):
    """Cierra tu ticket"""
    if "ticket-" in ctx.channel.name:
        await send_log(discord.Embed(title="Ticket cerrado", description=f"{ctx.channel.name}", color=COLOR_WARN))
        await ctx.send("Cerrando..."); await asyncio.sleep(2); await ctx.channel.delete()

# =========================================
# COMANDOS STAFF (solo en #admins)
# =========================================
@bot.command(name="admi")
@commands.has_permissions(manage_messages=True)
async def admi(ctx):
    if not admin_check(ctx): return
    status = "🟢 ON" if antilink["enabled"] else "🔴 OFF"
    e = discord.Embed(title="🛡️ Panel Staff", color=COLOR_WARN, timestamp=datetime.utcnow())
    e.add_field(name="Mod", value="`!kick!ban!unban!mute!unmute!warn!warnings`", inline=False)
    e.add_field(name="Canales", value="`!clear!lock!unlock!slowmode`", inline=False)
    e.add_field(name="Stats", value="`!stats` `!delstats`", inline=False)
    e.add_field(name="Anti-Links", value=f"{status} `!linkS` `!linkN`", inline=False)
    e.add_field(name="Info", value="`!userinfo!infoserver!anunciar`", inline=False)
    await ctx.send(embed=e)

@bot.command(name="anunciar")
@commands.has_permissions(administrator=True)
async def anunciar(ctx, *, msg):
    if not admin_check(ctx): return
    e = discord.Embed(title="📢 ANUNCIO", description=msg, color=COLOR_ERROR)
    await bot.get_channel(CANAL_GENERAL).send(embed=e)

# --- Moderación ---
@bot.command()
@commands.has_permissions(kick_members=True)
async def kick(ctx, m:discord.Member, *, r="Sin motivo"):
    if not admin_check(ctx): return
    await m.kick(reason=r); await send_log(discord.Embed(title="Kick", description=f"{m} | {r}", color=COLOR_WARN))
    await ctx.send("✅ Kick")

@bot.command()
@commands.has_permissions(ban_members=True)
async def ban(ctx, m:discord.Member, *, args=""):
    if not admin_check(ctx): return
    await ctx.guild.ban(m, reason=args); await send_log(discord.Embed(title="Ban", description=f"{m}", color=COLOR_ERROR))
    await ctx.send("✅ Ban")

@bot.command()
@commands.has_permissions(ban_members=True)
async def unban(ctx, uid:int):
    if not admin_check(ctx): return
    await ctx.guild.unban(discord.Object(id=uid)); await ctx.send("✅ Unban")

@bot.command()
@commands.has_permissions(moderate_members=True)
async def mute(ctx, m:discord.Member, t:str, *, r=""):
    if not admin_check(ctx): return
    s=parse_tiempo(t) or 60; await m.timeout(datetime.utcnow()+timedelta(seconds=s)); await ctx.send("🔇 Mute")

@bot.command()
@commands.has_permissions(moderate_members=True)
async def unmute(ctx, m:discord.Member):
    if not admin_check(ctx): return
    await m.timeout(None); await ctx.send("🔊 Unmute")

@bot.command()
async def warn(ctx, m:discord.Member, *, r):
    if not admin_check(ctx): return
    warnings.setdefault(str(m.id), []).append({"r":r}); save_warn(); await ctx.send("⚠️ Warn")

@bot.command()
async def warnings(ctx, m:discord.Member):
    if not admin_check(ctx): return
    await ctx.send(f"Warns: {len(warnings.get(str(m.id), []))}")

# --- Gestión canales ---
@bot.command()
@commands.has_permissions(manage_messages=True)
async def clear(ctx, n:int=10):
    if not admin_check(ctx): return
    await ctx.channel.purge(limit=n+1); await ctx.send(f"🧹 {n}", delete_after=2)

@bot.command()
@commands.has_permissions(manage_channels=True)
async def lock(ctx, c:discord.TextChannel=None):
    if not admin_check(ctx): return
    t=c or ctx.channel; await t.set_permissions(ctx.guild.default_role, send_messages=False); await ctx.send("🔒")

@bot.command()
@commands.has_permissions(manage_channels=True)
async def unlock(ctx, c:discord.TextChannel=None):
    if not admin_check(ctx): return
    t=c or ctx.channel; await t.set_permissions(ctx.guild.default_role, send_messages=None); await ctx.send("🔓")

@bot.command()
@commands.has_permissions(manage_channels=True)
async def slowmode(ctx, s:int):
    if not admin_check(ctx): return
    await ctx.channel.edit(slowmode_delay=s); await ctx.send(f"🐢 {s}s")

# --- Info ---
@bot.command()
async def userinfo(ctx, m:discord.Member=None):
    if not admin_check(ctx): return
    m=m or ctx.author; await ctx.send(embed=discord.Embed(title=m.display_name, description=f"ID: {m.id}", color=COLOR_INFO))

@bot.command()
async def infoserver(ctx):
    if not admin_check(ctx): return
    g=ctx.guild; await ctx.send(embed=discord.Embed(title=g.name, description=f"Miembros: {g.member_count}", color=COLOR_INFO))

# =========================================
# STATS Y ANTI-LINKS
# =========================================
@tasks.loop(minutes=5)
async def actualizar_stats():
    try: data=json.load(open(STATS_FILE))
    except: return
    g=bot.get_guild(data["guild"]); a=len([m for m in g.members if not m.bot and m.status!=discord.Status.offline])
    await bot.get_channel(data["a"]).edit(name=f"🟢 Activos: {a}")

@bot.command(name="stats")
@commands.has_permissions(administrator=True)
async def stats(ctx):
    if not admin_check(ctx): return
    g=ctx.guild; cat=await g.create_category("📊 ESTADÍSTICAS", position=0)
    c1=await g.create_voice_channel("🟢 Activos: 0", category=cat)
    for c in : await c.set_permissions(g.default_role, connect=False)
    json.dump({"guild":g.id,"a":c1.id}, open(STATS_FILE,"w")); await ctx.send("✅ Stats")

@bot.command(name="delstats")
@commands.has_permissions(administrator=True)
async def delstats(ctx):
    if not admin_check(ctx): return
    try: os.remove(STATS_FILE)
    except: pass
    await ctx.send("🗑️ Borrado")

@bot.command(name="linkS")
@commands.has_permissions(administrator=True)
async def links_on(ctx):
    if not admin_check(ctx): return
    antilink["enabled"]=True; save_antilink(); await ctx.send("✅ Anti-links ON")

@bot.command(name="linkN")
@commands.has_permissions(administrator=True)
async def links_off(ctx):
    if not admin_check(ctx): return
    antilink["enabled"]=False; save_antilink(); await ctx.send("❌ Anti-links OFF")

bot.run(TOKEN)
