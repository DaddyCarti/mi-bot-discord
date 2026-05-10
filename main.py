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

# ==================== CONFIGURACIÓN ====================
CANAL_ADMINS = 1502920731372163112
CANAL_TICKETS = 1502942029397753866
CANAL_AUTOROLES = 1502947801770885120
CREADOR = "daddy_oofo"
FOOTER = f"Creador: {CREADOR} | Bot Premium"

COLORS = {
    "azul": 0x5865F2,
    "verde": 0x57F287,
    "rojo": 0xED4245,
    "oro": 0xF1C40F,
    "morado": 0x9B59B6
}

PAISES = ["México","Colombia","Argentina","España","Perú","Chile","Venezuela","Ecuador","Bolivia","Uruguay","Paraguay","Guatemala","Honduras","El Salvador","Nicaragua","Costa Rica","Panamá","Rep. Dominicana","Cuba","USA","Brasil"]
EMOJIS = {"México":"🇲🇽","Colombia":"🇨🇴","Argentina":"🇦🇷","España":"🇪🇸","Perú":"🇵🇪","Chile":"🇨🇱","Venezuela":"🇻🇪","Ecuador":"🇪🇨","Bolivia":"🇧🇴","Uruguay":"🇺🇾","Paraguay":"🇵🇾","Guatemala":"🇬🇹","Honduras":"🇭🇳","El Salvador":"🇸🇻","Nicaragua":"🇳🇮","Costa Rica":"🇨🇷","Panamá":"🇵🇦","Rep. Dominicana":"🇩🇴","Cuba":"🇨🇺","USA":"🇺🇸","Brasil":"🇧🇷"}
EDADES = ["13-15","16-18","19-21","22-25","26+"]
PLAT = {"PC":"💻","Móvil":"📱","PlayStation":"🎮","Xbox":"🎮","Nintendo":"🎮"}

# ==================== BASE DE DATOS ====================
def load_db(file, default={}):
    try:
        with open(file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return default

def save_db(file, data):
    with open(file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)

levels = load_db("levels.json")
economy = load_db("economy.json")
warns = load_db("warns.json")

# ==================== VISTAS PERSISTENTES ====================
class ViewAutoroles(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.select(custom_id="pais_menu", placeholder="🌎 Selecciona tu país", options=[discord.SelectOption(label=p, emoji=EMOJIS.get(p), value=p, description=f"Obtén el rol de {p}") for p in PAISES])
    async def pais(self, interaction: discord.Interaction, select: discord.ui.Select):
        await interaction.response.defer(ephemeral=True)
        guild = interaction.guild
        user = interaction.user
        pais = select.values[0]

        role = discord.utils.get(guild.roles, name=pais) or await guild.create_role(name=pais, reason="Autorol país")
        for r in user.roles:
            if r.name in PAISES:
                await user.remove_roles(r)
        await user.add_roles(role)

        embed = discord.Embed(title="✅ País Actualizado", description=f"Ahora eres de {EMOJIS.get(pais)} **{pais}**", color=COLORS["verde"])
        embed.set_footer(text=FOOTER)
        await interaction.followup.send(embed=embed, ephemeral=True)

    @discord.ui.select(custom_id="edad_menu", placeholder="🎂 Selecciona tu edad", options=[discord.SelectOption(label=e, value=e, description=f"Rango {e} años") for e in EDADES])
    async def edad(self, interaction: discord.Interaction, select: discord.ui.Select):
        await interaction.response.defer(ephemeral=True)
        guild = interaction.guild
        user = interaction.user
        edad = select.values[0]

        role = discord.utils.get(guild.roles, name=edad) or await guild.create_role(name=edad, reason="Autorol edad")
        for r in user.roles:
            if r.name in EDADES:
                await user.remove_roles(r)
        await user.add_roles(role)

        embed = discord.Embed(title="✅ Edad Actualizada", description=f"Tu rango: **{edad}**", color=COLORS["verde"])
        embed.set_footer(text=FOOTER)
        await interaction.followup.send(embed=embed, ephemeral=True)

    @discord.ui.select(custom_id="plat_menu", placeholder="🎮 Elige tus plataformas", min_values=1, max_values=3, options=[discord.SelectOption(label=k, emoji=v, value=k, description=f"Juegas en {k}") for k,v in PLAT.items()])
    async def plataforma(self, interaction: discord.Interaction, select: discord.ui.Select):
        await interaction.response.defer(ephemeral=True)
        guild = interaction.guild
        user = interaction.user

        for r in user.roles:
            if r.name in PLAT:
                await user.remove_roles(r)

        for plataforma in select.values:
            role = discord.utils.get(guild.roles, name=plataforma) or await guild.create_role(name=plataforma, reason="Autorol plataforma")
            await user.add_roles(role)

        embed = discord.Embed(title="✅ Plataformas Actualizadas", description=f"Juegas en: **{', '.join(select.values)}**", color=COLORS["verde"])
        embed.set_footer(text=FOOTER)
        await interaction.followup.send(embed=embed, ephemeral=True)

class ViewTickets(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.select(custom_id="ticket_menu", placeholder="🎫 Selecciona tipo de ayuda", options=[
        discord.SelectOption(label="Soporte General", value="soporte", emoji="🛠️", description="Ayuda con el servidor"),
        discord.SelectOption(label="Compras y VIP", value="compras", emoji="💰", description="Información de pagos"),
        discord.SelectOption(label="Reportar Usuario", value="reporte", emoji="🚨", description="Reportar mal comportamiento"),
        discord.SelectOption(label="Apelación", value="apelacion", emoji="⚖️", description="Apelar sanción")
    ])
    async def ticket(self, interaction: discord.Interaction, select: discord.ui.Select):
        await interaction.response.defer(ephemeral=True)
        guild = interaction.guild
        user = interaction.user
        tipo = select.values[0]

        category = discord.utils.get(guild.categories, name="🎫 TICKETS") or await guild.create_category("🎫 TICKETS")

        # Verificar si ya tiene ticket
        existing = discord.utils.get(category.text_channels, name=f"ticket-{user.name.lower()}")
        if existing:
            return await interaction.followup.send(f"❌ Ya tienes un ticket abierto: {existing.mention}", ephemeral=True)

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            user: discord.PermissionOverwrite(view_channel=True, send_messages=True, attach_files=True),
            guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True)
        }

        channel = await guild.create_text_channel(f"ticket-{user.name}", category=category, overwrites=overwrites)

        embed = discord.Embed(
            title=f"🎫 Ticket de {tipo.title()}",
            description=f"Hola {user.mention}\n\n**Tipo:** {tipo.title()}\n\nDescribe tu problema detalladamente y un miembro del staff te ayudará pronto.\n\nUsa `!close` para cerrar este ticket.",
            color=COLORS["azul"],
            timestamp=datetime.now(timezone.utc)
        )
        embed.set_footer(text=FOOTER)

        await channel.send(content=f"{user.mention} <@&{discord.utils.get(guild.roles, name='🛡️ Admin').id if discord.utils.get(guild.roles, name='🛡️ Admin') else ''}>", embed=embed)
        await interaction.followup.send(f"✅ Ticket creado: {channel.mention}", ephemeral=True)

# ==================== EVENTOS ====================
@bot.event
async def on_ready():
    print(f"✅ Bot conectado: {bot.user}")
    print(f"📊 Servidores: {len(bot.guilds)}")
    bot.add_view(ViewAutoroles())
    bot.add_view(ViewTickets())

@bot.event
async def on_message(message):
    if message.author.bot or not message.guild:
        return

    # Sistema de niveles
    uid = str(message.author.id)
    if uid not in levels:
        levels[uid] = {"xp": 0, "lvl": 0}

    levels[uid]["xp"] += random.randint(10, 20)

    if levels[uid]["xp"] >= 100:
        levels[uid]["lvl"] += 1
        levels[uid]["xp"] = 0
        save_db("levels.json", levels)

        embed = discord.Embed(
            title="🎉 ¡Subiste de nivel!",
            description=f"{message.author.mention} ahora es nivel **{levels[uid]['lvl']}**",
            color=COLORS["oro"]
        )
        embed.set_footer(text=FOOTER)
        await message.channel.send(embed=embed, delete_after=10)
    else:
        save_db("levels.json", levels)

    # Anti-links
    if re.search(r"discord(?:\.gg|com/invite)/", message.content.lower()):
        if not message.author.guild_permissions.manage_messages:
            try:
                await message.delete()
                await message.channel.send(f"{message.author.mention} ❌ No se permiten invitaciones", delete_after=5)
            except:
                pass
            return

    await bot.process_commands(message)

# ==================== COMANDOS BÁSICOS ====================
@bot.command()
async def ping(ctx):
    await ctx.send(f"🏓 Pong! {round(bot.latency * 1000)}ms")

@bot.command()
async def hola(ctx):
    embed = discord.Embed(title=f"👋 Hola {ctx.author.display_name}!", description="¿En qué puedo ayudarte?", color=COLORS["azul"])
    embed.set_footer(text=FOOTER)
    await ctx.send(embed=embed)

@bot.command(name="help", aliases=["ayuda"])
async def help_cmd(ctx):
    embed = discord.Embed(
        title="📖 COMANDOS DEL BOT",
        description=f"Bot premium desarrollado por **{CREADOR}**",
        color=COLORS["azul"]
    )
    embed.add_field(name="🔹 Básicos", value="`!ping` `!hola` `!help` `!paybot`", inline=False)
    embed.add_field(name="📊 Información", value="`!serverinfo` `!userinfo [@user]` `!rank [@user]` `!top`", inline=False)
    embed.add_field(name="🎮 Economía", value="`!balance` `!daily` `!work`", inline=False)
    embed.add_field(name="🎲 Diversión", value="`!8ball <pregunta>` `!coinflip` `!dice`", inline=False)
    embed.add_field(name="🔨 Moderación", value="`!ban @user` `!kick @user` `!mute @user 10m` `!clear 5`", inline=False)
    embed.add_field(name="⚙️ Setup", value="`!setup-tickets` `!setup-autoroles` `!create-roles`", inline=False)
    embed.set_footer(text=FOOTER)
    await ctx.send(embed=embed)

# ==================== COMANDO PAYBOT ====================
@bot.command()
async def paybot(ctx):
    embed = discord.Embed(
        title="💎 SERVERPRUEBA BOT - VENTA OFICIAL",
        description=f"**El bot más completo de Discord**\n\n✨ Desarrollado por **{CREADOR}**",
        color=COLORS["oro"]
    )
    embed.add_field(
        name="💰 PLANES Y PRECIOS",
        value="**🥉 BÁSICO - $15 USD**\n• Comandos básicos\n• Sistema de moderación\n• Tickets y autoroles\n• Soporte básico\n\n**🥈 PREMIUM - $25 USD**\n• Todo lo básico\n• Sistema de niveles\n• Economía completa\n• Logs automáticos\n• Comandos divertidos\n\n**🥇 PRO - $40 USD**\n• Todo lo premium\n• Código fuente completo\n• Personalización total\n• Soporte 24/7\n• Actualizaciones de por vida",
        inline=False
    )
    embed.add_field(
        name="✅ ¿QUÉ INCLUYE?",
        value="• Instalación en tu servidor\n• Configuración completa\n• Tutorial personalizado\n• Hosting en Railway\n• Soporte por Discord",
        inline=True
    )
    embed.add_field(
        name="📩 CONTACTO",
        value=f"**Discord:** `{CREADOR}`\n**Respuesta:** Inmediata\n**Pagos:** PayPal, Nequi, Binance, Zinli",
        inline=True
    )
    embed.set_thumbnail(url=bot.user.display_avatar.url)
    embed.set_image(url="https://i.imgur.com/3ZQ3Z3Z.png")
    embed.set_footer(text=FOOTER)
    await ctx.send(embed=embed)

# ==================== INFORMACIÓN ====================
@bot.command(aliases=["server"])
async def serverinfo(ctx):
    g = ctx.guild
    embed = discord.Embed(title=f"📊 {g.name}", color=COLORS["azul"])
    embed.add_field(name="👥 Miembros", value=f"Total: {g.member_count}\nUsuarios: {len([m for m in g.members if not m.bot])}\nBots: {len([m for m in g.members if m.bot])}", inline=True)
    embed.add_field(name="📅 Creado", value=f"<t:{int(g.created_at.timestamp())}:D>\n<t:{int(g.created_at.timestamp())}:R>", inline=True)
    embed.add_field(name="👑 Dueño", value=g.owner.mention, inline=True)
    embed.add_field(name="💬 Canales", value=f"Texto: {len(g.text_channels)}\nVoz: {len(g.voice_channels)}", inline=True)
    embed.add_field(name="🎭 Roles", value=len(g.roles), inline=True)
    embed.add_field(name="😀 Emojis", value=len(g.emojis), inline=True)
    if g.icon:
        embed.set_thumbnail(url=g.icon.url)
    embed.set_footer(text=FOOTER)
    await ctx.send(embed=embed)

@bot.command(aliases=["ui", "user"])
async def userinfo(ctx, member: discord.Member = None):
    m = member or ctx.author
    embed = discord.Embed(title=f"👤 {m}", color=m.color)
    embed.add_field(name="📋 Información", value=f"**ID:** {m.id}\n**Apodo:** {m.display_name}\n**Bot:** {'Sí' if m.bot else 'No'}", inline=True)
    embed.add_field(name="📅 Fechas", value=f"**Cuenta:** <t:{int(m.created_at.timestamp())}:R>\n**Se unió:** <t:{int(m.joined_at.timestamp())}:R>", inline=True)
    embed.add_field(name="🎭 Roles", value=len(m.roles) - 1, inline=True)
    embed.set_thumbnail(url=m.display_avatar.url)
    embed.set_footer(text=FOOTER)
    await ctx.send(embed=embed)

@bot.command()
async def rank(ctx, member: discord.Member = None):
    m = member or ctx.author
    data = levels.get(str(m.id), {"xp": 0, "lvl": 0})
    embed = discord.Embed(title=f"📈 Nivel de {m.display_name}", color=m.color)
    embed.add_field(name="Nivel", value=f"**{data['lvl']}**", inline=True)
    embed.add_field(name="XP", value=f"**{data['xp']}/100**", inline=True)
    embed.add_field(name="XP Total", value=f"**{data['lvl'] * 100 + data['xp']}**", inline=True)
    embed.set_thumbnail(url=m.display_avatar.url)
    embed.set_footer(text=FOOTER)
    await ctx.send(embed=embed)

@bot.command(aliases=["leaderboard"])
async def top(ctx):
    sorted_users = sorted(levels.items(), key=lambda x: x[1]["lvl"], reverse=True)[:10]
    desc = ""
    for i, (uid, data) in enumerate(sorted_users, 1):
        try:
            user = await bot.fetch_user(int(uid))
            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"`{i}.`"
            desc += f"{medal} **{user.name}** - Nivel {data['lvl']} ({data['xp']} XP)\n"
        except:
            continue

    embed = discord.Embed(title="🏆 Top 10 Niveles", description=desc or "No hay datos aún", color=COLORS["oro"])
    embed.set_footer(text=FOOTER)
    await ctx.send(embed=embed)

# ==================== ECONOMÍA ====================
@bot.command(aliases=["bal", "dinero"])
async def balance(ctx, member: discord.Member = None):
    m = member or ctx.author
    bal = economy.get(str(m.id), 1000)
    embed = discord.Embed(title=f"💰 Balance de {m.display_name}", description=f"**${bal:,}**", color=COLORS["oro"])
    embed.set_footer(text=FOOTER)
    await ctx.send(embed=embed)

@bot.command()
async def daily(ctx):
    uid = str(ctx.author.id)
    amount = random.randint(200, 500)
    economy[uid] = economy.get(uid, 1000) + amount
    save_db("economy.json", economy)

    embed = discord.Embed(title="💵 Recompensa Diaria", description=f"Has reclamado **${amount}**", color=COLORS["verde"])
    embed.set_footer(text=FOOTER)
    await ctx.send(embed=embed)

@bot.command()
async def work(ctx):
    uid = str(ctx.author.id)
    amount = random.randint(100, 300)
    jobs = ["programador", "diseñador", "streamer", "youtuber", "moderador"]
    job = random.choice(jobs)

    economy[uid] = economy.get(uid, 1000) + amount
    save_db("economy.json", economy)

    embed = discord.Embed(title="💼 Trabajo Completado", description=f"Trabajaste como **{job}** y ganaste **${amount}**", color=COLORS["verde"])
    embed.set_footer(text=FOOTER)
    await ctx.send(embed=embed)

# ==================== DIVERSIÓN ====================
@bot.command(name="8ball")
async def eightball(ctx, *, pregunta=None):
    if not pregunta:
        return await ctx.send("❌ Escribe una pregunta. Ej: `!8ball ¿soy pro?`")

    respuestas = ["Sí, definitivamente", "Es cierto", "Sin duda", "Sí", "Puedes confiar en ello", "Muy probable", "No", "No cuentes con ello", "Muy dudoso", "Pregunta luego"]
    embed = discord.Embed(title="🎱 Bola 8 Mágica", color=COLORS["morado"])
    embed.add_field(name="Pregunta", value=pregunta, inline=False)
    embed.add_field(name="Respuesta", value=random.choice(respuestas), inline=False)
    embed.set_footer(text=FOOTER)
    await ctx.send(embed=embed)

@bot.command()
async def coinflip(ctx):
    result = random.choice(["Cara", "Cruz"])
    await ctx.send(f"🪙 **{result}**")

@bot.command()
async def dice(ctx):
    await ctx.send(f"🎲 Sacaste **{random.randint(1, 6)}**")

# ==================== MODERACIÓN ====================
def admin_only():
    async def predicate(ctx):
        if ctx.channel.id!= CANAL_ADMINS:
            await ctx.send(f"❌ Usa <#{CANAL_ADMINS}>", delete_after=5)
            return False
        return True
    return commands.check(predicate)

@bot.command()
@admin_only()
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member, *, razon="Sin razón"):
    await member.ban(reason=razon)
    embed = discord.Embed(title="🔨 Usuario Baneado", description=f"{member.mention} fue baneado\n**Razón:** {razon}", color=COLORS["rojo"])
    embed.set_footer(text=FOOTER)
    await ctx.send(embed=embed)

@bot.command()
@admin_only()
@commands.has_permissions(kick_members=True)
async def kick(ctx, member: discord.Member, *, razon="Sin razón"):
    await member.kick(reason=razon)
    await ctx.send(f"👢 {member.mention} expulsado")

@bot.command()
@admin_only()
@commands.has_permissions(moderate_members=True)
async def mute(ctx, member: discord.Member, tiempo: str, *, razon="Sin razón"):
    match = re.match(r"(\d+)([smhd])", tiempo)
    if not match:
        return await ctx.send("❌ Usa formato: 10m, 1h, 1d")

    cantidad = int(match.group(1))
    unidad = match.group(2)
    segundos = cantidad * {"s": 1, "m": 60, "h": 3600, "d": 86400}[unidad]

    await member.timeout(datetime.now(timezone.utc) + timedelta(seconds=segundos), reason=razon)
    await ctx.send(f"🔇 {member.mention} muteado por {tiempo}")

@bot.command()
@admin_only()
@commands.has_permissions(moderate_members=True)
async def unmute(ctx, member: discord.Member):
    await member.timeout(None)
    await ctx.send(f"🔊 {member.mention} desmuteado")

@bot.command()
@admin_only()
@commands.has_permissions(manage_messages=True)
async def clear(ctx, cantidad: int = 5):
    await ctx.channel.purge(limit=cantidad + 1)
    await ctx.send(f"✅ {cantidad} mensajes eliminados", delete_after=3)

# ==================== SETUP ====================
@bot.command()
@admin_only()
@commands.has_permissions(administrator=True)
async def setup_autoroles(ctx):
    ch = bot.get_channel(CANAL_AUTOROLES)
    await ch.purge(limit=10)

    embed = discord.Embed(
        title="🎭 PERSONALIZA TU PERFIL",
        description="**¡Bienvenido al sistema de autoroles!**\n\nSelecciona las opciones de abajo para obtener tus roles personalizados y acceder a canales exclusivos.\n\n**¿Cómo funciona?**\n1️⃣ Elige tu país\n2️⃣ Selecciona tu edad\n3️⃣ Marca tus plataformas",
        color=COLORS["azul"]
    )
    embed.add_field(name="🌎 Países", value=f"{len(PAISES)} disponibles", inline=True)
    embed.add_field(name="🎂 Edades", value="5 rangos", inline=True)
    embed.add_field(name="🎮 Plataformas", value="5 opciones", inline=True)
    embed.set_footer(text=FOOTER)

    await ch.send(embed=embed, view=ViewAutoroles())
    await ctx.send("✅ Panel de autoroles instalado")

@bot.command()
@admin_only()
@commands.has_permissions(administrator=True)
async def setup_tickets(ctx):
    ch = bot.get_channel(CANAL_TICKETS)
    await ch.purge(limit=10)

    embed = discord.Embed(
        title="📩 CENTRO DE AYUDA",
        description="**¿Necesitas ayuda?**\n\nNuestro equipo está listo para ayudarte. Selecciona el tipo de ticket que necesitas.",
        color=COLORS["azul"]
    )
    embed.add_field(name="🛠️ Soporte", value="Dudas generales", inline=True)
    embed.add_field(name="💰 Compras", value="Información VIP", inline=True)
    embed.add_field(name="🚨 Reportes", value="Reportar usuarios", inline=True)
    embed.add_field(name="⚖️ Apelaciones", value="Apelar sanciones", inline=True)
    embed.set_footer(text=FOOTER)

    await ch.send(embed=embed, view=ViewTickets())
    await ctx.send("✅ Panel de tickets instalado")

@bot.command(name="create-roles")
@admin_only()
@commands.has_permissions(manage_roles=True)
async def create_roles(ctx):
    msg = await ctx.send("⏳ Creando roles...")
    todos = PAISES + EDADES + list(PLAT.keys())
    creados = 0

    for nombre in todos:
        if not discord.utils.get(ctx.guild.roles, name=nombre):
            await ctx.guild.create_role(name=nombre)
            creados += 1
            await asyncio.sleep(0.2)

    await msg.edit(content=f"✅ {creados} roles creados")

@bot.command()
async def close(ctx):
    if "ticket-" in ctx.channel.name.lower():
        await ctx.send("🔒 Cerrando ticket en 3 segundos...")
        await asyncio.sleep(3)
        await ctx.channel.delete()

@bot.command()
@admin_only()
async def admi(ctx):
    embed = discord.Embed(title="🛡️ Panel Admin", description=f"Servidor: {ctx.guild.name}", color=COLORS["morado"])
    embed.add_field(name="Comandos", value="`!ban` `!kick` `!mute` `!clear` `!setup-tickets` `!setup-autoroles`", inline=False)
    embed.set_footer(text=FOOTER)
    await ctx.send(embed=embed)

bot.run(TOKEN)
