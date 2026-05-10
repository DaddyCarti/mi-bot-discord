import discord
from discord.ext import commands
import os, json, asyncio, random, re
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.presences = True

bot = commands.Bot(command_prefix="!", intents=intents, help_command=None, case_insensitive=True)

# ==================== CONFIG ====================
CANAL_ADMINS = 1502920731372163112
CANAL_TICKETS = 1502942029397753866
CANAL_AUTOROLES = 1502947801770885120
CANAL_LOGS = None # Se crea automáticamente
CREADOR = "daddy_oofo"
FOOTER = f"Creador: {CREADOR}"

COLORS = {"azul": 0x5865F2, "verde": 0x57F287, "rojo": 0xED4245, "oro": 0xF1C40F}

PAISES = ["México","Colombia","Argentina","España","Perú","Chile","Venezuela","Ecuador","Bolivia","Uruguay","Paraguay","Guatemala","Honduras","El Salvador","Nicaragua","Costa Rica","Panamá","Rep. Dominicana","Cuba","USA","Brasil"]
EMOJIS = {"México":"🇲🇽","Colombia":"🇨🇴","Argentina":"🇦🇷","España":"🇪🇸","Perú":"🇵🇪","Chile":"🇨🇱","Venezuela":"🇻🇪","Ecuador":"🇪🇨","Bolivia":"🇧🇴","Uruguay":"🇺🇾","Paraguay":"🇵🇾","Guatemala":"🇬🇹","Honduras":"🇭🇳","El Salvador":"🇸🇻","Nicaragua":"🇳🇮","Costa Rica":"🇨🇷","Panamá":"🇵🇦","Rep. Dominicana":"🇩🇴","Cuba":"🇨🇺","USA":"🇺🇸","Brasil":"🇧🇷"}
EDADES = ["13-15","16-18","19-21","22-25","26+"]
PLAT = {"PC":"💻","Móvil":"📱","PlayStation":"🎮","Xbox":"🎮","Nintendo":"🎮"}

# DB
def load_db(f):
    try: return json.load(open(f,'r',encoding='utf-8'))
    except: return {}
def save_db(f,d): json.dump(d, open(f,'w',encoding='utf-8'), indent=4)

levels = load_db("levels.json")
economy = load_db("economy.json")

# ==================== LOGS ====================
async def log_action(guild, titulo, descripcion, color):
    canal = discord.utils.get(guild.text_channels, name="📜-logs")
    if not canal:
        canal = await guild.create_text_channel("📜-logs")
    embed = discord.Embed(title=titulo, description=descripcion, color=color, timestamp=datetime.now(timezone.utc))
    embed.set_footer(text=FOOTER)
    await canal.send(embed=embed)

# ==================== VISTAS ====================
class ViewAutoroles(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)

    @discord.ui.select(custom_id="pais_1502947801770885120", placeholder="🌎 Tu país", options=[discord.SelectOption(label=p, emoji=EMOJIS.get(p), value=p) for p in PAISES[:25]])
    async def pais(self, i, s):
        await i.response.defer(ephemeral=True)
        try:
            r = discord.utils.get(i.guild.roles, name=s.values[0]) or await i.guild.create_role(name=s.values[0])
            for x in i.user.roles:
                if x.name in PAISES: await i.user.remove_roles(x)
            await i.user.add_roles(r)
            await i.followup.send(f"✅ País: {EMOJIS.get(s.values[0])} {s.values[0]}", ephemeral=True)
        except Exception as e:
            await i.followup.send(f"❌ Error: {e}", ephemeral=True)

    @discord.ui.select(custom_id="edad_1502947801770885120", placeholder="🎂 Tu edad", options=[discord.SelectOption(label=e, value=e) for e in EDADES])
    async def edad(self, i, s):
        await i.response.defer(ephemeral=True)
        try:
            r = discord.utils.get(i.guild.roles, name=s.values[0]) or await i.guild.create_role(name=s.values[0])
            for x in i.user.roles:
                if x.name in EDADES: await i.user.remove_roles(x)
            await i.user.add_roles(r)
            await i.followup.send(f"✅ Edad: {s.values[0]}", ephemeral=True)
        except Exception as e:
            await i.followup.send(f"❌ Error", ephemeral=True)

    @discord.ui.select(custom_id="plat_1502947801770885120", placeholder="🎮 Plataforma", min_values=1, max_values=3, options=[discord.SelectOption(label=k, emoji=v, value=k) for k,v in PLAT.items()])
    async def plat(self, i, s):
        await i.response.defer(ephemeral=True)
        try:
            for x in i.user.roles:
                if x.name in PLAT: await i.user.remove_roles(x)
            for v in s.values:
                r = discord.utils.get(i.guild.roles, name=v) or await i.guild.create_role(name=v)
                await i.user.add_roles(r)
            await i.followup.send(f"✅ Plataformas: {', '.join(s.values)}", ephemeral=True)
        except:
            await i.followup.send("❌ Error", ephemeral=True)

class ViewTickets(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)

    @discord.ui.select(custom_id="ticket_1502942029397753866", placeholder="🎫 Abrir ticket", options=[
        discord.SelectOption(label="Soporte", value="soporte", emoji="🛠️"),
        discord.SelectOption(label="Compras", value="compras", emoji="💰"),
        discord.SelectOption(label="Reporte", value="reporte", emoji="🚨")
    ])
    async def ticket(self, i, s):
        await i.response.defer(ephemeral=True)
        try:
            guild = i.guild
            cat = discord.utils.get(guild.categories, name="🎫 TICKETS") or await guild.create_category("🎫 TICKETS")

            # Verificar ticket existente
            for ch in cat.text_channels:
                if ch.name == f"ticket-{i.user.name.lower()}":
                    return await i.followup.send(f"Ya tienes ticket: {ch.mention}", ephemeral=True)

            overwrites = {
                guild.default_role: discord.PermissionOverwrite(view_channel=False),
                i.user: discord.PermissionOverwrite(view_channel=True, send_messages=True),
                guild.me: discord.PermissionOverwrite(view_channel=True)
            }

            ch = await guild.create_text_channel(f"ticket-{i.user.name}", category=cat, overwrites=overwrites)
            embed = discord.Embed(title=f"Ticket {s.values[0]}", description=f"{i.user.mention} describe tu problema\n\n!close para cerrar", color=COLORS["azul"])
            embed.set_footer(text=FOOTER)
            await ch.send(embed=embed)
            await i.followup.send(f"✅ {ch.mention}", ephemeral=True)
            await log_action(guild, "🎫 Ticket Creado", f"{i.user} creó ticket {s.values[0]}", COLORS["verde"])
        except Exception as e:
            await i.followup.send(f"❌ Error creando ticket", ephemeral=True)

@bot.event
async def on_ready():
    print(f"Bot: {bot.user}")
    bot.add_view(ViewAutoroles())
    bot.add_view(ViewTickets())

@bot.event
async def on_message(m):
    if m.author.bot or not m.guild: return
    uid = str(m.author.id)
    if uid not in levels: levels[uid] = {"xp":0,"lvl":0}
    levels[uid]["xp"] += 15
    if levels[uid]["xp"] >= 100:
        levels[uid]["lvl"] += 1
        levels[uid]["xp"] = 0
        await m.channel.send(f"🎉 {m.author.mention} nivel {levels[uid]['lvl']}!")
    save_db("levels.json", levels)
    await bot.process_commands(m)

# ==================== COMANDOS ====================
@bot.command()
async def ping(ctx): await ctx.send(f"🏓 {round(bot.latency*1000)}ms")

@bot.command(aliases=["bal", "dinero"])
async def balance(ctx, m: discord.Member = None):
    u = m or ctx.author
    bal = economy.get(str(u.id), 1000)
    if str(u.id) not in economy:
        economy[str(u.id)] = 1000
        save_db("economy.json", economy)
    embed = discord.Embed(title=f"💰 {u.display_name}", description=f"${bal:,}", color=COLORS["oro"])
    embed.set_footer(text=FOOTER)
    await ctx.send(embed=embed)

@bot.command()
async def daily(ctx):
    uid = str(ctx.author.id)
    if uid not in economy: economy[uid] = 1000
    amount = random.randint(300, 600)
    economy[uid] += amount
    save_db("economy.json", economy)
    embed = discord.Embed(title="💵 Daily", description=f"Ganaste ${amount}\nTotal: ${economy[uid]}", color=COLORS["verde"])
    embed.set_footer(text=FOOTER)
    await ctx.send(embed=embed)

@bot.command(name="dado", aliases=["dice"])
async def dado(ctx):
    await ctx.send(f"🎲 {random.randint(1,6)}")

@bot.command()
async def paybot(ctx):
    embed = discord.Embed(title="💎 BOT EN VENTA", description=f"Por {CREADOR}", color=COLORS["oro"])
    embed.add_field(name="Precios", value="Básico $15\nPremium $25\nPro $40", inline=False)
    embed.set_footer(text=FOOTER)
    await ctx.send(embed=embed)

def admin_check():
    async def pred(ctx):
        if ctx.channel.id!= CANAL_ADMINS:
            await ctx.send(f"Usa <#{CANAL_ADMINS}>", delete_after=5)
            return False
        return True
    return commands.check(pred)

@bot.command()
@admin_check()
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member, tiempo: str = None, *, razon="Sin razón"):
    #!ban @user 7d spam o!ban @user spam
    segundos = None
    if tiempo and re.match(r"^\d+[smhd]$", tiempo):
        cant = int(tiempo[:-1])
        unidad = tiempo[-1]
        segundos = cant * {"s":1,"m":60,"h":3600,"d":86400}[unidad]
    else:
        razon = f"{tiempo} {razon}" if tiempo else razon

    await ctx.guild.ban(member, reason=razon, delete_message_days=0)
    await ctx.send(f"🔨 {member} baneado. Razón: {razon}")
    await log_action(ctx.guild, "🔨 Ban", f"{member} baneado por {ctx.author}\nRazón: {razon}", COLORS["rojo"])

    if segundos:
        await asyncio.sleep(segundos)
        try:
            await ctx.guild.unban(member, reason="Ban temporal expirado")
            await log_action(ctx.guild, "✅ Unban Auto", f"{member} desbaneado automáticamente", COLORS["verde"])
        except: pass

@bot.command()
@admin_check()
@commands.has_permissions(kick_members=True)
async def kick(ctx, member: discord.Member, *, razon="Sin razón"):
    await member.kick(reason=razon)
    await ctx.send(f"👢 {member} expulsado")
    await log_action(ctx.guild, "👢 Kick", f"{member} por {ctx.author}", COLORS["rojo"])

@bot.command()
@admin_check()
@commands.has_permissions(moderate_members=True)
async def mute(ctx, member: discord.Member, tiempo: str, *, razon="Sin razón"):
    match = re.match(r"(\d+)([smhd])", tiempo)
    if not match: return await ctx.send("Usa 10m, 1h, 1d")
    seg = int(match[1]) * {"s":1,"m":60,"h":3600,"d":86400}[match[2]]
    await member.timeout(datetime.now(timezone.utc) + timedelta(seconds=seg), reason=razon)
    await ctx.send(f"🔇 {member.mention} muteado {tiempo}")
    await log_action(ctx.guild, "🔇 Mute", f"{member} por {tiempo}\nRazón: {razon}", COLORS["rojo"])

@bot.command()
@admin_check()
async def admi(ctx):
    embed = discord.Embed(title="🛡️ PANEL DE ADMINISTRACIÓN", description="Comandos de moderación explicados", color=COLORS["rojo"])
    embed.add_field(name="🔨!ban @usuario [tiempo] [razón]", value="**¿Qué hace?** Expulsa permanentemente al usuario del servidor.\n**Tiempo:** Opcional. Ej: 7d, 1h, 30m\n**Ejemplo:** `!ban @troll 7d spam`\n**Efecto:** No puede volver a entrar hasta desbaneo", inline=False)
    embed.add_field(name="👢!kick @usuario [razón]", value="**¿Qué hace?** Expulsa al usuario pero PUEDE volver con invitación.\n**Ejemplo:** `!kick @usuario molestar`\n**Efecto:** Expulsión temporal", inline=False)
    embed.add_field(name="🔇!mute @usuario [tiempo] [razón]", value="**¿Qué hace?** Silencia al usuario (no puede escribir ni hablar).\n**Tiempo:** Requerido. Ej: 10m, 2h, 1d\n**Ejemplo:** `!mute @toxico 1h insultos`\n**Efecto:** Timeout de Discord", inline=False)
    embed.add_field(name="🧹!clear [número]", value="**¿Qué hace?** Borra mensajes del canal.\n**Ejemplo:** `!clear 10`\n**Efecto:** Elimina últimos mensajes", inline=False)
    embed.add_field(name="⚙️ Setup", value="`!setup-tickets` - Crea panel tickets\n`!setup-autoroles` - Crea panel roles\n`!create-roles` - Crea todos los roles", inline=False)
    embed.set_footer(text=FOOTER)
    await ctx.send(embed=embed)

@bot.command()
@admin_check()
@commands.has_permissions(administrator=True)
async def setup_autoroles(ctx):
    ch = bot.get_channel(CANAL_AUTOROLES)
    await ch.purge(limit=5)
    embed = discord.Embed(title="🎭 AUTOROLES", description="Elige tu país, edad y plataforma abajo", color=COLORS["azul"])
    embed.set_footer(text=FOOTER)
    await ch.send(embed=embed, view=ViewAutoroles())
    await ctx.send("✅ Autoroles listo")

@bot.command()
@admin_check()
@commands.has_permissions(administrator=True)
async def setup_tickets(ctx):
    ch = bot.get_channel(CANAL_TICKETS)
    await ch.purge(limit=5)
    embed = discord.Embed(title="📩 TICKETS", description="Abre un ticket seleccionando abajo", color=COLORS["azul"])
    embed.set_footer(text=FOOTER)
    await ch.send(embed=embed, view=ViewTickets())
    await ctx.send("✅ Tickets listo")

@bot.command(name="create-roles")
@admin_check()
async def create_roles(ctx):
    todos = PAISES + EDADES + list(PLAT.keys())
    c = 0
    for n in todos:
        if not discord.utils.get(ctx.guild.roles, name=n):
            await ctx.guild.create_role(name=n)
            c += 1
            await asyncio.sleep(0.2)
    await ctx.send(f"✅ {c} roles creados")

@bot.command()
async def close(ctx):
    if "ticket-" in ctx.channel.name:
        await log_action(ctx.guild, "🔒 Ticket Cerrado", f"{ctx.channel.name} cerrado por {ctx.author}", COLORS["azul"])
        await ctx.channel.delete()

@bot.command(aliases=["server"])
async def serverinfo(ctx):
    g = ctx.guild
    e = discord.Embed(title=g.name, color=COLORS["azul"])
    e.add_field(name="Miembros", value=g.member_count)
    e.set_footer(text=FOOTER)
    await ctx.send(embed=e)

@bot.command()
async def top(ctx):
    top10 = sorted(levels.items(), key=lambda x: x[1]["lvl"], reverse=True)[:10]
    desc = "\n".join([f"{i+1}. <@{uid}> - Nvl {d['lvl']}" for i,(uid,d) in enumerate(top10)])
    e = discord.Embed(title="Top", description=desc or "Vacío", color=COLORS["oro"])
    e.set_footer(text=FOOTER)
    await ctx.send(embed=e)

bot.run(TOKEN)
