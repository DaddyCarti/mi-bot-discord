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
CREADOR = "daddy_oofo"
FOOTER = f"Bot creado por {CREADOR}"

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
def load_db(filename, default={}):
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return default

def save_db(filename, data):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)

levels = load_db("levels.json")
economy = load_db("economy.json")
daily_data = load_db("daily.json")

# ==================== LOGS ====================
async def log_action(guild, titulo, descripcion, color):
    try:
        canal = discord.utils.get(guild.text_channels, name="📜-logs")
        if not canal:
            canal = await guild.create_text_channel("📜-logs")
        embed = discord.Embed(title=titulo, description=descripcion, color=color, timestamp=datetime.now(timezone.utc))
        embed.set_footer(text=FOOTER)
        await canal.send(embed=embed)
    except:
        pass

# ==================== VISTAS AUTOROLES ====================
class ViewAutoroles(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.select(
        custom_id="autorol_pais",
        placeholder="🌎 Selecciona tu país",
        min_values=1,
        max_values=1,
        options=[discord.SelectOption(label=p, emoji=EMOJIS.get(p, "🌎"), value=p, description=f"Obtén el rol de {p}") for p in PAISES]
    )
    async def select_pais(self, interaction: discord.Interaction, select: discord.ui.Select):
        await interaction.response.defer(ephemeral=True)
        pais = select.values[0]
        guild = interaction.guild
        member = interaction.user

        try:
            role = discord.utils.get(guild.roles, name=pais)
            if not role:
                role = await guild.create_role(name=pais, reason="Autorol país")

            # Quitar otros países
            for r in member.roles:
                if r.name in PAISES:
                    await member.remove_roles(r)

            await member.add_roles(role)

            embed = discord.Embed(
                title="✅ País Actualizado",
                description=f"Has seleccionado {EMOJIS.get(pais)} **{pais}**\n\nAhora tienes acceso a canales exclusivos de tu país.",
                color=COLORS["verde"]
            )
            embed.set_footer(text=FOOTER)
            await interaction.followup.send(embed=embed, ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"❌ Error: No tengo permisos para darte el rol. Contacta a un admin.", ephemeral=True)

    @discord.ui.select(
        custom_id="autorol_edad",
        placeholder="🎂 Selecciona tu edad",
        options=[discord.SelectOption(label=e, value=e, description=f"Rango de edad {e} años") for e in EDADES]
    )
    async def select_edad(self, interaction: discord.Interaction, select: discord.ui.Select):
        await interaction.response.defer(ephemeral=True)
        edad = select.values[0]
        guild = interaction.guild
        member = interaction.user

        try:
            role = discord.utils.get(guild.roles, name=edad)
            if not role:
                role = await guild.create_role(name=edad, reason="Autorol edad")

            for r in member.roles:
                if r.name in EDADES:
                    await member.remove_roles(r)

            await member.add_roles(role)

            embed = discord.Embed(title="✅ Edad Actualizada", description=f"Tu rango de edad: **{edad}**", color=COLORS["verde"])
            embed.set_footer(text=FOOTER)
            await interaction.followup.send(embed=embed, ephemeral=True)
        except:
            await interaction.followup.send("❌ Error al asignar rol", ephemeral=True)

    @discord.ui.select(
        custom_id="autorol_plataforma",
        placeholder="🎮 Selecciona tus plataformas",
        min_values=1,
        max_values=5,
        options=[discord.SelectOption(label=k, emoji=v, value=k, description=f"Juegas en {k}") for k,v in PLAT.items()]
    )
    async def select_plataforma(self, interaction: discord.Interaction, select: discord.ui.Select):
        await interaction.response.defer(ephemeral=True)
        guild = interaction.guild
        member = interaction.user

        try:
            for r in member.roles:
                if r.name in PLAT.keys():
                    await member.remove_roles(r)

            for plataforma in select.values:
                role = discord.utils.get(guild.roles, name=plataforma)
                if not role:
                    role = await guild.create_role(name=plataforma, reason="Autorol plataforma")
                await member.add_roles(role)

            embed = discord.Embed(title="✅ Plataformas Actualizadas", description=f"Juegas en: **{', '.join(select.values)}**", color=COLORS["verde"])
            embed.set_footer(text=FOOTER)
            await interaction.followup.send(embed=embed, ephemeral=True)
        except:
            await interaction.followup.send("❌ Error al asignar roles", ephemeral=True)

# ==================== VISTAS TICKETS ====================
class ViewTickets(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.select(
        custom_id="ticket_selector",
        placeholder="🎫 Selecciona el tipo de ticket",
        options=[
            discord.SelectOption(label="Soporte General", value="soporte", emoji="🛠️", description="Ayuda con el servidor o bot"),
            discord.SelectOption(label="Compras y Pagos", value="compras", emoji="💰", description="Información sobre VIP y compras"),
            discord.SelectOption(label="Reportar Usuario", value="reporte", emoji="🚨", description="Reportar mal comportamiento"),
            discord.SelectOption(label="Apelación", value="apelacion", emoji="⚖️", description="Apelar una sanción")
        ]
    )
    async def create_ticket(self, interaction: discord.Interaction, select: discord.ui.Select):
        await interaction.response.defer(ephemeral=True)
        guild = interaction.guild
        user = interaction.user
        tipo = select.values[0]

        try:
            category = discord.utils.get(guild.categories, name="🎫 TICKETS")
            if not category:
                category = await guild.create_category("🎫 TICKETS")

            # Verificar si ya tiene ticket
            for channel in category.text_channels:
                if channel.name == f"ticket-{user.name.lower().replace(' ', '-')}" or channel.topic and str(user.id) in channel.topic:
                    return await interaction.followup.send(f"❌ Ya tienes un ticket abierto: {channel.mention}", ephemeral=True)

            overwrites = {
                guild.default_role: discord.PermissionOverwrite(view_channel=False),
                user: discord.PermissionOverwrite(view_channel=True, send_messages=True, attach_files=True, read_message_history=True),
                guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True, manage_messages=True)
            }

            channel = await guild.create_text_channel(
                f"ticket-{user.name}",
                category=category,
                overwrites=overwrites,
                topic=f"Ticket de {user.id} | Tipo: {tipo}"
            )

            embed = discord.Embed(
                title=f"🎫 Ticket de {tipo.title()}",
                description=f"Hola {user.mention}!\n\n**Tipo de ticket:** {tipo.title()}\n**Creado:** <t:{int(datetime.now().timestamp())}:R>\n\nPor favor describe tu problema detalladamente. Un miembro del staff te atenderá pronto.\n\n**Para cerrar este ticket escribe:** `!close`",
                color=COLORS["azul"],
                timestamp=datetime.now(timezone.utc)
            )
            embed.set_footer(text=FOOTER)

            await channel.send(content=f"{user.mention}", embed=embed)
            await interaction.followup.send(f"✅ Tu ticket ha sido creado: {channel.mention}", ephemeral=True)
            await log_action(guild, "🎫 Ticket Creado", f"{user.mention} creó un ticket de {tipo}", COLORS["verde"])
        except Exception as e:
            await interaction.followup.send(f"❌ Error al crear ticket. Contacta a un administrador.", ephemeral=True)

# ==================== EVENTOS ====================
@bot.event
async def on_ready():
    print(f"✅ Bot conectado como {bot.user}")
    bot.add_view(ViewAutoroles())
    bot.add_view(ViewTickets())
    print("✅ Vistas persistentes cargadas")

@bot.event
async def on_message(message):
    if message.author.bot or not message.guild:
        return

    # Sistema de niveles
    uid = str(message.author.id)
    if uid not in levels:
        levels[uid] = {"xp": 0, "lvl": 0}

    levels[uid]["xp"] += random.randint(15, 25)

    if levels[uid]["xp"] >= 100:
        levels[uid]["lvl"] += 1
        levels[uid]["xp"] = 0
        embed = discord.Embed(
            title="🎉 ¡NIVEL SUPERIOR!",
            description=f"{message.author.mention} ha alcanzado el **nivel {levels[uid]['lvl']}**",
            color=COLORS["oro"]
        )
        embed.set_footer(text=FOOTER)
        await message.channel.send(embed=embed, delete_after=15)

    save_db("levels.json", levels)
    await bot.process_commands(message)

# ==================== COMANDOS BÁSICOS ====================
@bot.command()
async def ping(ctx):
    latency = round(bot.latency * 1000)
    embed = discord.Embed(title="🏓 Pong!", description=f"Latencia: **{latency}ms**", color=COLORS["verde"])
    embed.set_footer(text=FOOTER)
    await ctx.send(embed=embed)

@bot.command(name="help", aliases=["ayuda", "comandos"])
async def help_command(ctx):
    embed = discord.Embed(
        title="📖 LISTA DE COMANDOS",
        description=f"Bot desarrollado por **{CREADOR}**\nPrefijo: `!`",
        color=COLORS["azul"]
    )
    embed.add_field(name="🔹 Básicos", value="`ping` `help` `paybot`", inline=False)
    embed.add_field(name="📊 Información", value="`serverinfo` `userinfo` `rank` `top`", inline=False)
    embed.add_field(name="💰 Economía", value="`balance` `daily` `work`", inline=False)
    embed.add_field(name="🎲 Diversión", value="`8ball` `coinflip` `dado` `avatar`", inline=False)
    embed.add_field(name="🔨 Moderación", value="`ban` `kick` `mute` `unmute` `clear` `warn`", inline=False)
    embed.add_field(name="⚙️ Setup", value="`setup-tickets` `setup-autoroles` `create-roles`", inline=False)
    embed.set_footer(text=FOOTER)
    await ctx.send(embed=embed)

# ==================== PAYBOT DETALLADO ====================
@bot.command()
async def paybot(ctx):
    embed = discord.Embed(
        title="💎 SERVERPRUEBA BOT - VENTA OFICIAL",
        description=f"**El bot más completo y avanzado de Discord**\n\nDesarrollado 100% por **{CREADOR}**\nMás de 6 meses de desarrollo",
        color=COLORS["oro"]
    )
    embed.add_field(
        name="💰 PLANES DISPONIBLES",
        value="**🥉 PLAN BÁSICO - $15 USD**\n✓ Comandos básicos (ping, help, etc.)\n✓ Sistema de moderación completo\n✓ Sistema de tickets\n✓ Sistema de autoroles\n✓ Soporte por 1 mes\n✓ Instalación incluida\n\n**🥈 PLAN PREMIUM - $25 USD**\n✓ Todo lo del plan básico\n✓ Sistema de niveles y XP\n✓ Economía completa (balance, daily, work)\n✓ Sistema de advertencias\n✓ Logs automáticos\n✓ Comandos de diversión\n✓ Soporte por 3 meses\n✓ 1 personalización gratis\n\n**🥇 PLAN PRO - $40 USD**\n✓ Todo lo del plan premium\n✓ Código fuente completo\n✓ Personalización ilimitada\n✓ Soporte 24/7 de por vida\n✓ Actualizaciones gratis para siempre\n✓ Hosting incluido 3 meses\n✓ Tutorial personalizado 1 a 1",
        inline=False
    )
    embed.add_field(
        name="✅ ¿QUÉ INCLUYE LA COMPRA?",
        value="• Instalación completa en tu servidor\n• Configuración de todos los canales\n• Creación de roles automática\n• Tutorial de uso detallado\n• Soporte técnico por Discord\n• Garantía de funcionamiento",
        inline=True
    )
    embed.add_field(
        name="💳 MÉTODOS DE PAGO",
        value="• PayPal\n• Nequi\n• Bancolombia\n• Binance (USDT)\n• Zinli\n• Pago móvil",
        inline=True
    )
    embed.add_field(
        name="📩 CONTACTO DIRECTO",
        value=f"**Discord:** `{CREADOR}`\n**Tiempo de respuesta:** Inmediato\n**Entrega:** 5-10 minutos después del pago",
        inline=False
    )
    embed.set_thumbnail(url=bot.user.display_avatar.url)
    embed.set_image(url="https://i.imgur.com/8Km9tLL.png")
    embed.set_footer(text=f"{FOOTER} | Más de 50 servidores usando este bot")
    await ctx.send(embed=embed)

# ==================== SERVERINFO DETALLADO ====================
@bot.command(aliases=["server"])
async def serverinfo(ctx):
    guild = ctx.guild
    embed = discord.Embed(
        title=f"📊 Información de {guild.name}",
        description=guild.description or "Sin descripción",
        color=COLORS["azul"],
        timestamp=datetime.now(timezone.utc)
    )

    # Información general
    embed.add_field(
        name="👑 Propietario",
        value=guild.owner.mention if guild.owner else "Desconocido",
        inline=True
    )
    embed.add_field(
        name="🆔 ID del Servidor",
        value=f"`{guild.id}`",
        inline=True
    )
    embed.add_field(
        name="📅 Creación",
        value=f"<t:{int(guild.created_at.timestamp())}:D>\n<t:{int(guild.created_at.timestamp())}:R>",
        inline=True
    )

    # Miembros
    total = guild.member_count
    bots = len([m for m in guild.members if m.bot])
    humans = total - bots
    online = len([m for m in guild.members if m.status!= discord.Status.offline])

    embed.add_field(
        name="👥 Miembros",
        value=f"**Total:** {total}\n**Usuarios:** {humans}\n**Bots:** {bots}\n**En línea:** {online}",
        inline=True
    )

    # Canales
    embed.add_field(
        name="💬 Canales",
        value=f"**Texto:** {len(guild.text_channels)}\n**Voz:** {len(guild.voice_channels)}\n**Categorías:** {len(guild.categories)}",
        inline=True
    )

    # Otros
    embed.add_field(
        name="🎭 Roles",
        value=f"{len(guild.roles)} roles",
        inline=True
    )
    embed.add_field(
        name="😀 Emojis",
        value=f"{len(guild.emojis)}/{guild.emoji_limit}",
        inline=True
    )
    embed.add_field(
        name="🚀 Boosts",
        value=f"Nivel {guild.premium_tier} ({guild.premium_subscription_count} boosts)",
        inline=True
    )
    embed.add_field(
        name="🔒 Verificación",
        value=str(guild.verification_level).title(),
        inline=True
    )

    if guild.icon:
        embed.set_thumbnail(url=guild.icon.url)
    if guild.banner:
        embed.set_image(url=guild.banner.url)

    embed.set_footer(text=f"{FOOTER} | Solicitado por {ctx.author}")
    await ctx.send(embed=embed)

@bot.command(aliases=["ui", "user"])
async def userinfo(ctx, member: discord.Member = None):
    m = member or ctx.author
    embed = discord.Embed(title=f"👤 Información de {m}", color=m.color, timestamp=datetime.now(timezone.utc))
    embed.add_field(name="🆔 ID", value=m.id, inline=True)
    embed.add_field(name="📛 Apodo", value=m.display_name, inline=True)
    embed.add_field(name="🤖 Bot", value="Sí" if m.bot else "No", inline=True)
    embed.add_field(name="📅 Cuenta creada", value=f"<t:{int(m.created_at.timestamp())}:D>", inline=True)
    embed.add_field(name="📥 Se unió", value=f"<t:{int(m.joined_at.timestamp())}:D>", inline=True)
    embed.add_field(name="🎭 Roles", value=len(m.roles)-1, inline=True)
    embed.set_thumbnail(url=m.display_avatar.url)
    embed.set_footer(text=FOOTER)
    await ctx.send(embed=embed)

# ==================== ECONOMÍA CON COOLDOWN ====================
@bot.command(aliases=["bal", "dinero"])
async def balance(ctx, member: discord.Member = None):
    user = member or ctx.author
    uid = str(user.id)
    if uid not in economy:
        economy[uid] = 1000
        save_db("economy.json", economy)

    embed = discord.Embed(
        title=f"💰 Balance de {user.display_name}",
        description=f"**${economy[uid]:,}** monedas",
        color=COLORS["oro"]
    )
    embed.set_thumbnail(url=user.display_avatar.url)
    embed.set_footer(text=FOOTER)
    await ctx.send(embed=embed)

@bot.command()
async def daily(ctx):
    uid = str(ctx.author.id)
    now = datetime.now().timestamp()

    # Cooldown de 24 horas
    if uid in daily_data:
        last_claim = daily_data[uid]
        if now - last_claim < 86400: # 24 horas
            remaining = 86400 - (now - last_claim)
            hours = int(remaining // 3600)
            minutes = int((remaining % 3600) // 60)
            embed = discord.Embed(
                title="⏰ Daily en cooldown",
                description=f"Ya reclamaste tu daily hoy.\n\nVuelve en **{hours}h {minutes}m**",
                color=COLORS["rojo"]
            )
            embed.set_footer(text=FOOTER)
            return await ctx.send(embed=embed)

    if uid not in economy:
        economy[uid] = 1000

    amount = random.randint(400, 700)
    economy[uid] += amount
    daily_data[uid] = now

    save_db("economy.json", economy)
    save_db("daily.json", daily_data)

    embed = discord.Embed(
        title="💵 Daily Reclamado",
        description=f"Has recibido **${amount}** monedas\n\n**Nuevo balance:** ${economy[uid]:,}",
        color=COLORS["verde"]
    )
    embed.set_footer(text=f"{FOOTER} | Vuelve en 24 horas")
    await ctx.send(embed=embed)

@bot.command()
async def work(ctx):
    uid = str(ctx.author.id)
    if uid not in economy:
        economy[uid] = 1000

    jobs = ["Programador", "Diseñador", "Streamer", "Youtuber", "Moderador", "Vendedor"]
    job = random.choice(jobs)
    amount = random.randint(150, 350)

    economy[uid] += amount
    save_db("economy.json", economy)

    embed = discord.Embed(
        title="💼 Trabajo Completado",
        description=f"Trabajaste como **{job}**\nGanaste **${amount}**",
        color=COLORS["verde"]
    )
    embed.set_footer(text=FOOTER)
    await ctx.send(embed=embed)

# ==================== NIVELES ====================
@bot.command()
async def rank(ctx, member: discord.Member = None):
    user = member or ctx.author
    data = levels.get(str(user.id), {"xp": 0, "lvl": 0})

    embed = discord.Embed(title=f"📈 Nivel de {user.display_name}", color=user.color)
    embed.add_field(name="Nivel", value=f"**{data['lvl']}**", inline=True)
    embed.add_field(name="XP", value=f"**{data['xp']}/100**", inline=True)
    embed.add_field(name="XP Total", value=f"**{data['lvl']*100 + data['xp']}**", inline=True)
    embed.set_thumbnail(url=user.display_avatar.url)
    embed.set_footer(text=FOOTER)
    await ctx.send(embed=embed)

@bot.command(aliases=["leaderboard"])
async def top(ctx):
    sorted_users = sorted(levels.items(), key=lambda x: x[1]["lvl"]*100 + x[1]["xp"], reverse=True)[:10]
    desc = ""
    for i, (uid, data) in enumerate(sorted_users, 1):
        try:
            user = await bot.fetch_user(int(uid))
            medal = "🥇" if i==1 else "🥈" if i==2 else "🥉" if i==3 else f"**{i}.**"
            desc += f"{medal} {user.name} - Nivel {data['lvl']} ({data['xp']} XP)\n"
        except:
            continue

    embed = discord.Embed(title="🏆 Top 10 Niveles", description=desc or "No hay datos", color=COLORS["oro"])
    embed.set_footer(text=FOOTER)
    await ctx.send(embed=embed)

# ==================== DIVERSIÓN ====================
@bot.command(name="8ball")
async def eightball(ctx, *, pregunta):
    respuestas = ["Sí definitivamente", "Es cierto", "Sin duda", "Sí", "Pregunta luego", "No cuentes con ello", "Muy dudoso", "No"]
    embed = discord.Embed(title="🎱 Bola 8 Mágica", color=COLORS["morado"])
    embed.add_field(name="Pregunta", value=pregunta, inline=False)
    embed.add_field(name="Respuesta", value=random.choice(respuestas), inline=False)
    embed.set_footer(text=FOOTER)
    await ctx.send(embed=embed)

@bot.command()
async def coinflip(ctx):
    resultado = random.choice(["Cara", "Cruz"])
    embed = discord.Embed(title="🪙 Lanzamiento de moneda", description=f"**{resultado}**", color=COLORS["oro"])
    embed.set_footer(text=FOOTER)
    await ctx.send(embed=embed)

@bot.command(name="dado")
async def dado(ctx):
    numero = random.randint(1, 6)
    embed = discord.Embed(title="🎲 Dado", description=f"Sacaste un **{numero}**", color=COLORS["azul"])
    embed.set_footer(text=FOOTER)
    await ctx.send(embed=embed)

@bot.command()
async def avatar(ctx, member: discord.Member = None):
    user = member or ctx.author
    embed = discord.Embed(title=f"Avatar de {user.display_name}", color=user.color)
    embed.set_image(url=user.display_avatar.url)
    embed.set_footer(text=FOOTER)
    await ctx.send(embed=embed)

# ==================== MODERACIÓN ====================
def admin_only():
    async def predicate(ctx):
        if ctx.channel.id!= CANAL_ADMINS:
            await ctx.send(f"❌ Usa este comando en <#{CANAL_ADMINS}>", delete_after=5)
            return False
        return True
    return commands.check(predicate)

@bot.command()
@admin_only()
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member, tiempo: str = None, *, razon="Sin razón proporcionada"):
    segundos = None
    if tiempo and re.match(r"^\d+[smhd]$", tiempo):
        cantidad = int(tiempo[:-1])
        unidad = tiempo[-1]
        segundos = cantidad * {"s":1, "m":60, "h":3600, "d":86400}[unidad]
    else:
        if tiempo:
            razon = f"{tiempo} {razon}"

    try:
        await ctx.guild.ban(member, reason=f"{razon} | Por {ctx.author}", delete_message_days=0)
        embed = discord.Embed(title="🔨 Usuario Baneado", description=f"**Usuario:** {member.mention} ({member})\n**Razón:** {razon}\n**Moderador:** {ctx.author.mention}", color=COLORS["rojo"])
        if segundos:
            dias = segundos // 86400
            embed.add_field(name="⏰ Duración", value=f"{dias} días (desbaneo automático)", inline=False)
        embed.set_footer(text=FOOTER)
        await ctx.send(embed=embed)
        await log_action(ctx.guild, "🔨 Ban", f"{member} baneado por {ctx.author}\nRazón: {razon}", COLORS["rojo"])

        if segundos:
            await asyncio.sleep(segundos)
            try:
                await ctx.guild.unban(member, reason="Ban temporal expirado")
                await log_action(ctx.guild, "✅ Unban Automático", f"{member} desbaneado automáticamente", COLORS["verde"])
            except:
                pass
    except:
        await ctx.send("❌ No pude banear al usuario")

@bot.command()
@admin_only()
@commands.has_permissions(kick_members=True)
async def kick(ctx, member: discord.Member, *, razon="Sin razón"):
    await member.kick(reason=razon)
    embed = discord.Embed(title="👢 Usuario Expulsado", description=f"{member.mention}\nRazón: {razon}", color=COLORS["rojo"])
    embed.set_footer(text=FOOTER)
    await ctx.send(embed=embed)
    await log_action(ctx.guild, "👢 Kick", f"{member} expulsado por {ctx.author}", COLORS["rojo"])

@bot.command()
@admin_only()
@commands.has_permissions(moderate_members=True)
async def mute(ctx, member: discord.Member, tiempo: str, *, razon="Sin razón"):
    match = re.match(r"(\d+)([smhd])", tiempo)
    if not match:
        return await ctx.send("❌ Formato: 10m, 1h, 2d")

    segundos = int(match.group(1)) * {"s":1,"m":60,"h":3600,"d":86400}[match.group(2)]
    await member.timeout(datetime.now(timezone.utc) + timedelta(seconds=segundos), reason=razon)

    embed = discord.Embed(title="🔇 Usuario Silenciado", description=f"{member.mention}\nTiempo: {tiempo}\nRazón: {razon}", color=COLORS["rojo"])
    embed.set_footer(text=FOOTER)
    await ctx.send(embed=embed)
    await log_action(ctx.guild, "🔇 Mute", f"{member} muteado {tiempo} por {ctx.author}", COLORS["rojo"])

@bot.command()
@admin_only()
@commands.has_permissions(moderate_members=True)
async def unmute(ctx, member: discord.Member):
    await member.timeout(None)
    await ctx.send(f"🔊 {member.mention} desmuteado")
    await log_action(ctx.guild, "🔊 Unmute", f"{member} desmuteado por {ctx.author}", COLORS["verde"])

@bot.command()
@admin_only()
@commands.has_permissions(manage_messages=True)
async def clear(ctx, cantidad: int):
    deleted = await ctx.channel.purge(limit=cantidad+1)
    msg = await ctx.send(f"✅ {len(deleted)-1} mensajes eliminados")
    await asyncio.sleep(3)
    await msg.delete()
    await log_action(ctx.guild, "🧹 Clear", f"{ctx.author} borró {len(deleted)-1} mensajes en {ctx.channel.mention}", COLORS["azul"])

# ==================== SETUP ====================
@bot.command()
@admin_only()
@commands.has_permissions(administrator=True)
async def setup_autoroles(ctx):
    channel = bot.get_channel(CANAL_AUTOROLES)
    if not channel:
        return await ctx.send("❌ Canal no encontrado")

    await channel.purge(limit=10)

    embed = discord.Embed(
        title="🎭 SISTEMA DE AUTOROLES",
        description="**¡Personaliza tu perfil en el servidor!**\n\nSelecciona las opciones de abajo para obtener roles automáticamente y acceder a contenido exclusivo.\n\n**📌 INSTRUCCIONES:**\n1️⃣ Elige tu país de origen\n2️⃣ Selecciona tu rango de edad\n3️⃣ Marca las plataformas donde juegas\n\n¡Los roles se asignan instantáneamente!",
        color=COLORS["azul"]
    )
    embed.add_field(name="🌎 Países Disponibles", value=f"**{len(PAISES)} países** con su bandera oficial", inline=True)
    embed.add_field(name="🎂 Rangos de Edad", value="5 categorías diferentes", inline=True)
    embed.add_field(name="🎮 Plataformas", value="PC, Móvil, PlayStation, Xbox, Nintendo", inline=True)
    embed.set_image(url="https://i.imgur.com/3Q3Z3ZQ.png")
    embed.set_footer(text=FOOTER)

    await channel.send(embed=embed, view=ViewAutoroles())
    await ctx.send("✅ Panel de autoroles instalado correctamente")

@bot.command()
@admin_only()
@commands.has_permissions(administrator=True)
async def setup_tickets(ctx):
    channel = bot.get_channel(CANAL_TICKETS)
    if not channel:
        return await ctx.send("❌ Canal no encontrado")

    await channel.purge(limit=10)

    embed = discord.Embed(
        title="📩 CENTRO DE SOPORTE",
        description="**¿Necesitas ayuda? ¡Estamos aquí para ti!**\n\nNuestro equipo de soporte está disponible para resolver tus dudas y problemas.\n\n**⏰ Tiempo de respuesta promedio:** 5-15 minutos\n**📅 Horario:** 24/7",
        color=COLORS["azul"]
    )
    embed.add_field(name="🛠️ Soporte General", value="Dudas sobre el servidor, bot o funciones", inline=True)
    embed.add_field(name="💰 Compras y VIP", value="Información sobre pagos y beneficios", inline=True)
    embed.add_field(name="🚨 Reportes", value="Reportar usuarios o problemas", inline=True)
    embed.add_field(name="⚖️ Apelaciones", value="Apelar sanciones o baneos", inline=True)
    embed.set_thumbnail(url=bot.user.display_avatar.url)
    embed.set_footer(text=FOOTER)

    await channel.send(embed=embed, view=ViewTickets())
    await ctx.send("✅ Panel de tickets instalado correctamente")

@bot.command(name="create-roles")
@admin_only()
@commands.has_permissions(manage_roles=True)
async def create_roles(ctx):
    msg = await ctx.send("⏳ Creando roles... Esto puede tardar un momento")
    todos = PAISES + EDADES + list(PLAT.keys())
    creados = 0

    for nombre in todos:
        if not discord.utils.get(ctx.guild.roles, name=nombre):
            await ctx.guild.create_role(name=nombre, reason="Setup inicial de autoroles")
            creados += 1
            await asyncio.sleep(0.3)

    await msg.edit(content=f"✅ Proceso completado. **{creados}** roles nuevos creados.")

@bot.command()
async def close(ctx):
    if "ticket-" in ctx.channel.name.lower():
        embed = discord.Embed(title="🔒 Cerrando Ticket", description="Este canal se eliminará en 5 segundos...", color=COLORS["rojo"])
        embed.set_footer(text=FOOTER)
        await ctx.send(embed=embed)
        await log_action(ctx.guild, "🔒 Ticket Cerrado", f"{ctx.channel.name} cerrado por {ctx.author}", COLORS["azul"])
        await asyncio.sleep(5)
        await ctx.channel.delete()
    else:
        await ctx.send("❌ Este comando solo funciona en tickets")

@bot.command()
@admin_only()
async def admi(ctx):
    embed = discord.Embed(
        title="🛡️ PANEL DE ADMINISTRACIÓN",
        description="Guía completa de comandos de moderación",
        color=COLORS["rojo"]
    )
    embed.add_field(
        name="🔨 BAN - Banear usuario",
        value="**Uso:** `!ban @usuario [tiempo] [razón]`\n**Ejemplo:** `!ban @troll 7d spam constante`\n**Qué hace:** Expulsa permanentemente (o temporal si pones tiempo)\n**Tiempo:** 1m, 1h, 1d, 7d, 30d",
        inline=False
    )
    embed.add_field(
        name="👢 KICK - Expulsar usuario",
        value="**Uso:** `!kick @usuario [razón]`\n**Ejemplo:** `!kick @usuario molestar`\n**Qué hace:** Expulsa pero puede volver con invitación",
        inline=False
    )
    embed.add_field(
        name="🔇 MUTE - Silenciar usuario",
        value="**Uso:** `!mute @usuario [tiempo] [razón]`\n**Ejemplo:** `!mute @toxico 2h insultos`\n**Qué hace:** No puede escribir ni hablar en voz",
        inline=False
    )
    embed.add_field(
        name="🔊 UNMUTE - Quitar silencio",
        value="**Uso:** `!unmute @usuario`\n**Qué hace:** Restaura permisos de habla",
        inline=False
    )
    embed.add_field(
        name="🧹 CLEAR - Borrar mensajes",
        value="**Uso:** `!clear [número]`\n**Ejemplo:** `!clear 20`\n**Qué hace:** Elimina mensajes del canal",
        inline=False
    )
    embed.set_footer(text=FOOTER)
    await ctx.send(embed=embed)

bot.run(TOKEN)
