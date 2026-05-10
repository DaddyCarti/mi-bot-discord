# =========================================
# SERVERPRUEBA BOT v4.0 PRODUCTION
# Autor: Meta AI para Daniel
# Características: Tickets, Roles, Mod, Logs, Stats, Anti-Link
# Canal Tickets: 1502942029397753866
# =========================================
import discord
from discord.ext import commands, tasks
import os, json, re, asyncio
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

# ---------- CONFIGURACIÓN ----------
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.presences = True

bot = commands.Bot(
    command_prefix="!",
    intents=intents,
    help_command=None,
    case_insensitive=True,
    strip_after_prefix=True
)

# IDs DE TU SERVIDOR
GUILD_ID = 1502889233369534494
CANAL_ADMINS = 1502920731372163112
CANAL_GENERAL = 1502889242072842303
CANAL_TICKET_PANEL = 1502942029397753866
TICKETS_CATEGORY = "🎫 TICKETS"
LOGS_CHANNEL = "📜-logs"
TICKET_ROLE = "ticket"

COLORS = {
    "success": 0x57F287,
    "warning": 0xFAA61A,
    "error": 0xED4245,
    "info": 0x5865F2,
    "primary": 0x2B2D31
}

# ---------- BASE DE DATOS ----------
class Database:
    @staticmethod
    def load(filename, default):
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                return json.load(f)
        except: return default

    @staticmethod
    def save(filename, data):
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

warnings = Database.load("warnings.json", {})
antilink = Database.load("antilink.json", {"enabled": True, "whitelist": []})
stats = Database.load("stats.json", {})
tempbans = Database.load("tempbans.json", {})

# ---------- UTILIDADES ----------
def admin_only():
    async def predicate(ctx):
        if ctx.channel.id!= CANAL_ADMINS:
            embed = discord.Embed(
                title="❌ Comando Restringido",
                description=f"Usa este comando en <#{CANAL_ADMINS}>",
                color=COLORS["error"]
            )
            await ctx.send(embed=embed, delete_after=5)
            return False
        return True
    return commands.check(predicate)

def parse_duration(text: str) -> int:
    """Convierte 10m, 2h, 1d a segundos"""
    match = re.match(r"^(\d+)(s|m|h|d|w)$", text.lower())
    if not match: return None
    value, unit = int(match[1]), match[2]
    multipliers = {"s":1, "m":60, "h":3600, "d":86400, "w":604800}
    return value * multipliers[unit]

async def send_log(guild: discord.Guild, title: str, description: str, color: int):
    channel = discord.utils.get(guild.text_channels, name=LOGS_CHANNEL)
    if channel:
        embed = discord.Embed(title=title, description=description, color=color, timestamp=datetime.now(timezone.utc))
        embed.set_footer(text=bot.user.name, icon_url=bot.user.display_avatar.url)
        await channel.send(embed=embed)

# =========================================
# SISTEMA DE TICKETS - VISTA PERSISTENTE
# =========================================
class TicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.select(
        custom_id="persistent_ticket_select",
        placeholder="🎫 Selecciona el motivo para abrir un ticket",
        min_values=1,
        max_values=1,
        options=[
            discord.SelectOption(
                label="Soporte General",
                value="soporte",
                description="Ayuda con el servidor, bugs o dudas",
                emoji="🛠️"
            ),
            discord.SelectOption(
                label="Compras y Donaciones",
                value="compras",
                description="Información sobre VIP, rangos y pagos",
                emoji="💰"
            ),
            discord.SelectOption(
                label="Reportar Usuario",
                value="reporte",
                description="Reportar mal comportamiento",
                emoji="🚨"
            )
        ]
    )
    async def ticket_select(self, interaction: discord.Interaction, select: discord.ui.Select):
        await interaction.response.defer(ephemeral=True)
        guild = interaction.guild
        user = interaction.user

        # Verificar ticket existente
        category = discord.utils.get(guild.categories, name=TICKETS_CATEGORY)
        if not category:
            category = await guild.create_category(TICKETS_CATEGORY)

        existing = discord.utils.get(category.text_channels, name=f"ticket-{user.name.lower()}")
        if existing:
            return await interaction.followup.send(
                embed=discord.Embed(
                    title="⚠️ Ticket Existente",
                    description=f"Ya tienes un ticket abierto: {existing.mention}",
                    color=COLORS["warning"]
                ),
                ephemeral=True
            )

        # Crear permisos
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            user: discord.PermissionOverwrite(
                view_channel=True, send_messages=True, read_message_history=True,
                attach_files=True, embed_links=True
            ),
            guild.me: discord.PermissionOverwrite(view_channel=True, manage_channels=True, manage_messages=True)
        }

        # Añadir rol de ticket y staff
        if ticket_role := discord.utils.get(guild.roles, name=TICKET_ROLE):
            overwrites[ticket_role] = discord.PermissionOverwrite(view_channel=True, send_messages=True)

        for role in guild.roles:
            if role.permissions.manage_messages or role.permissions.administrator:
                overwrites[role] = discord.PermissionOverwrite(view_channel=True, send_messages=True)

        # Crear canal
        channel = await guild.create_text_channel(
            name=f"ticket-{user.name}",
            category=category,
            overwrites=overwrites,
            topic=f"USER:{user.id}|TYPE:{select.values[0]}|CREATED:{datetime.now().isoformat()}"
        )

        # Mensaje de bienvenida
        embed = discord.Embed(
            title=f"🎫 Ticket de {select.values[0].title()}",
            description=(
                f"¡Hola {user.mention}!\n\n"
                f"**Motivo:** {select.values[0].title()}\n\n"
                f"**📋 REGLAS:**\n"
                f"• Explica tu problema con detalles\n"
                f"• No hagas spam ni menciones innecesarias\n"
                f"• Sé paciente, el staff te atenderá\n"
                f"• Usa `!close` para cerrar cuando termines"
            ),
            color=COLORS["info"],
            timestamp=datetime.now(timezone.utc)
        )
        embed.set_footer(text=f"Ticket ID: {channel.id}")

        await channel.send(content=f"{user.mention} {ticket_role.mention if ticket_role else ''}", embed=embed)
        await interaction.followup.send(
            embed=discord.Embed(
                title="✅ Ticket Creado",
                description=f"Tu ticket ha sido creado: {channel.mention}",
                color=COLORS["success"]
            ),
            ephemeral=True
        )
        await send_log(guild, "🎫 Ticket Abierto", f"{user.mention} abrió ticket de **{select.values[0]}**", COLORS["info"])

# =========================================
# EVENTOS PRINCIPALES
# =========================================
@bot.event
async def on_ready():
    print(f"\n{'='*50}\n✅ BOT CONECTADO: {bot.user}\n📊 Servidores: {len(bot.guilds)}\n👥 Usuarios: {sum(g.member_count for g in bot.guilds)}\n{'='*50}\n")

    # Registrar vista persistente
    bot.add_view(TicketView())

    # Crear canal de logs si no existe
    for guild in bot.guilds:
        if not discord.utils.get(guild.text_channels, name=LOGS_CHANNEL):
            await guild.create_text_channel(LOGS_CHANNEL)

    # Iniciar tareas
    if not update_stats.is_running():
        update_stats.start()
    if not check_tempbans.is_running():
        check_tempbans.start()

@bot.event
async def on_message(message):
    if message.author.bot or not message.guild:
        return await bot.process_commands(message)

    # Anti-link
    if antilink["enabled"] and re.search(r"discord(?:\.gg|com/invite)/[a-zA-Z0-9]+", message.content):
        if not message.author.guild_permissions.manage_messages:
            if message.channel.id not in antilink["whitelist"]:
                await message.delete()
                warn_embed = discord.Embed(
                    title="🔗 Enlace No Permitido",
                    description=f"{message.author.mention}, los invites de Discord no están permitidos aquí.",
                    color=COLORS["error"]
                )
                await message.channel.send(embed=warn_embed, delete_after=5)
                await send_log(message.guild, "Anti-Link", f"{message.author} intentó enviar invite", COLORS["error"])
                return

    await bot.process_commands(message)

@bot.event
async def on_member_join(member):
    await send_log(member.guild, "📥 Miembro Nuevo", f"{member.mention} se unió al servidor\n**Cuenta creada:** <t:{int(member.created_at.timestamp())}:R>", COLORS["success"])

@bot.event
async def on_member_remove(member):
    await send_log(member.guild, "📤 Miembro Salió", f"**{member}** abandonó el servidor", COLORS["warning"])

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        return
    elif isinstance(error, commands.MissingPermissions):
        embed = discord.Embed(title="❌ Sin Permisos", description="No tienes permisos para usar este comando", color=COLORS["error"])
        await ctx.send(embed=embed, delete_after=5)
    elif isinstance(error, commands.CheckFailure):
        return
    else:
        print(f"Error: {error}")

# =========================================
# COMANDOS DE USUARIO
# =========================================
@bot.command(name="ping")
async def ping_cmd(ctx):
    latency = round(bot.latency * 1000)
    embed = discord.Embed(title="🏓 Pong!", description=f"**Latencia:** `{latency}ms`\n**Uptime:** <t:{int(bot.user.created_at.timestamp())}:R>", color=COLORS["success"])
    await ctx.send(embed=embed)

@bot.command(name="hola")
async def hola_cmd(ctx):
    await ctx.send(f"👋 ¡Hola {ctx.author.mention}! Usa `!menu` para ver todos mis comandos.")

@bot.command(name="menu")
async def menu_cmd(ctx):
    embed = discord.Embed(
        title="📜 MENÚ DE COMANDOS",
        description=f"Hola {ctx.author.mention}, estos son mis comandos disponibles:",
        color=COLORS["info"],
        timestamp=datetime.now(timezone.utc)
    )
    embed.add_field(name="🔹 Generales", value="`!ping` - Ver latencia\n`!hola` - Saludo\n`!menu` - Este menú", inline=False)
    embed.add_field(name="🎫 Tickets", value="`!close` - Cerrar tu ticket actual", inline=False)
    embed.add_field(name="🎭 Roles", value="`!rol list` - Ver roles disponibles\n`!rol join <nombre>` - Obtener un rol\n`!rol leave <nombre>` - Quitar un rol", inline=False)
    embed.set_thumbnail(url=bot.user.display_avatar.url)
    embed.set_footer(text="ServerPrueba Bot v4.0")
    await ctx.send(embed=embed)

# =========================================
# SISTEMA DE ROLES
# =========================================
@bot.group(name="rol", invoke_without_command=True)
async def rol_group(ctx):
    embed = discord.Embed(title="🎭 Sistema de Roles", color=COLORS["info"])
    embed.add_field(name="👤 Usuarios", value="`!rol list`\n`!rol join NombreDelRol`\n`!rol leave NombreDelRol`", inline=True)
    embed.add_field(name="🛡️ Staff", value="`!rol add @usuario @rol`\n`!rol remove @usuario @rol`\n`!rol create Nombre Color`\n`!rol delete Nombre`", inline=True)
    await ctx.send(embed=embed)

@rol_group.command(name="list")
async def rol_list(ctx):
    roles = [r for r in ctx.guild.roles if not r.managed and r!= ctx.guild.default_role and not r.permissions.administrator and r < ctx.guild.me.top_role and not r.is_premium_subscriber()]
    roles_sorted = sorted(roles, key=lambda r: r.position, reverse=True)[:30]
    description = "\n".join([f"{r.mention} - `{r.name}`" for r in roles_sorted]) or "No hay roles disponibles"
    embed = discord.Embed(title="🎭 Roles Auto-Asignables", description=description, color=COLORS["info"])
    await ctx.send(embed=embed)

@rol_group.command(name="join")
async def rol_join(ctx, *, nombre: str):
    role = discord.utils.get(ctx.guild.roles, name=nombre)
    if not role:
        return await ctx.send(embed=discord.Embed(title="❌ No encontrado", description=f"No existe el rol `{nombre}`", color=COLORS["error"]))
    if role.permissions.administrator or role >= ctx.guild.me.top_role:
        return await ctx.send(embed=discord.Embed(title="❌ No permitido", description="No puedes obtener ese rol", color=COLORS["error"]))
    await ctx.author.add_roles(role, reason="Auto-rol")
    await ctx.send(embed=discord.Embed(title="✅ Rol Añadido", description=f"Ahora tienes {role.mention}", color=COLORS["success"]))

@rol_group.command(name="leave")
async def rol_leave(ctx, *, nombre: str):
    role = discord.utils.get(ctx.guild.roles, name=nombre)
    if role and role in ctx.author.roles:
        await ctx.author.remove_roles(role, reason="Auto-rol removido")
        await ctx.send(embed=discord.Embed(title="✅ Rol Removido", description=f"Se quitó {role.mention}", color=COLORS["warning"]))

@rol_group.command(name="add")
@admin_only()
@commands.has_permissions(manage_roles=True)
async def rol_add(ctx, member: discord.Member, role: discord.Role):
    await member.add_roles(role, reason=f"Añadido por {ctx.author}")
    await ctx.send(embed=discord.Embed(title="✅ Rol Asignado", description=f"{role.mention} → {member.mention}", color=COLORS["success"]))
    await send_log(ctx.guild, "Rol Añadido", f"{ctx.author.mention} dio {role.mention} a {member.mention}", COLORS["success"])

@rol_group.command(name="remove")
@admin_only()
@commands.has_permissions(manage_roles=True)
async def rol_remove(ctx, member: discord.Member, role: discord.Role):
    await member.remove_roles(role, reason=f"Removido por {ctx.author}")
    await ctx.send(embed=discord.Embed(title="✅ Rol Removido", color=COLORS["warning"]))

@rol_group.command(name="create")
@admin_only()
@commands.has_permissions(manage_roles=True)
async def rol_create(ctx, nombre: str, color: str = "5865F2"):
    try:
        color_int = int(color.replace("#", ""), 16)
        role = await ctx.guild.create_role(name=nombre, color=discord.Color(color_int), reason=f"Creado por {ctx.author}")
        await ctx.send(embed=discord.Embed(title="✅ Rol Creado", description=f"{role.mention} creado con color `#{color}`", color=role.color))
    except: await ctx.send("❌ Color inválido. Usa formato HEX: FF0000")

@rol_group.command(name="delete")
@admin_only()
@commands.has_permissions(manage_roles=True)
async def rol_delete(ctx, *, nombre: str):
    if role := discord.utils.get(ctx.guild.roles, name=nombre):
        await role.delete(reason=f"Eliminado por {ctx.author}")
        await ctx.send(embed=discord.Embed(title="🗑️ Rol Eliminado", color=COLORS["error"]))

# =========================================
# PANEL STAFF Y TICKETS
# =========================================
@bot.command(name="admi")
@commands.has_permissions(manage_messages=True)
@admin_only()
async def admin_panel(ctx):
    embed = discord.Embed(title="🛡️ PANEL DE ADMINISTRACIÓN", description=f"**Servidor:** {ctx.guild.name}", color=COLORS["warning"], timestamp=datetime.now(timezone.utc))
    embed.add_field(name="🔨 MODERACIÓN", value="`!kick @user razón`\n`!ban @user  razón`\n`!unban ID`\n`!mute @user 10m razón`\n`!unmute @user`\n`!warn @user razón`\n`!warnings @user`", inline=True)
    embed.add_field(name="🧹 GESTIÓN", value="`!clear [5-100]`\n`!lock [#canal]`\n`!unlock [#canal]`\n`!slowmode [0-21600]`", inline=True)
    embed.add_field(name="🎭 ROLES", value="`!rol add/remove`\n`!rol create/delete`", inline=True)
    embed.add_field(name="🎫 TICKETS", value="`!setup-tickets`\n`!close`", inline=True)
    embed.add_field(name="📊 INFO", value="`!userinfo [@user]`\n`!infoserver`\n`!anunciar texto`", inline=True)
    embed.add_field(name="⚙️ SISTEMA", value="`!stats`\n`!delstats`\n`!linkS` / `!linkN`", inline=True)
    embed.set_thumbnail(url=bot.user.display_avatar.url)
    await ctx.send(embed=embed)

@bot.command(name="setup-tickets")
@admin_only()
@commands.has_permissions(administrator=True)
async def setup_tickets(ctx):
    channel = bot.get_channel(CANAL_TICKET_PANEL)
    if not channel:
        return await ctx.send("❌ Canal no encontrado")

    # Limpiar mensajes antiguos del bot
    async for msg in channel.history(limit=50):
        if msg.author == bot.user:
            await msg.delete()

    embed = discord.Embed(
        title="📩 CENTRO DE SOPORTE",
        description=(
            "**Bienvenido al sistema de tickets**\n\n"
            "__**REGLAS IMPORTANTES**__\n"
            "1️⃣ Abre un ticket solo si es necesario\n"
            "2️⃣ Describe tu problema detalladamente\n"
            "3️⃣ No hagas spam ni menciones al staff\n"
            "4️⃣ Sé respetuoso en todo momento\n\n"
            "**Selecciona una opción abajo para comenzar:**"
        ),
        color=COLORS["info"]
    )
    embed.set_image(url="https://i.imgur.com/5lR0X7f.png")
    embed.set_footer(text="ServerPrueba • Respuesta promedio: < 1 hora")

    await channel.send(embed=embed, view=TicketView())
    await ctx.send(embed=discord.Embed(title="✅ Panel Instalado", description=f"Panel de tickets instalado en {channel.mention}", color=COLORS["success"]))

@bot.command(name="close")
async def close_ticket(ctx):
    if "ticket-" not in ctx.channel.name.lower():
        return await ctx.send(embed=discord.Embed(title="❌", description="Este comando solo funciona en tickets", color=COLORS["error"]), delete_after=5)

    embed = discord.Embed(title="🔒 Cerrando Ticket", description="Este canal se eliminará en 5 segundos...", color=COLORS["warning"])
    await ctx.send(embed=embed)
    await send_log(ctx.guild, "Ticket Cerrado", f"{ctx.channel.name} cerrado por {ctx.author.mention}", COLORS["warning"])
    await asyncio.sleep(5)
    await ctx.channel.delete(reason=f"Cerrado por {ctx.author}")

# =========================================
# COMANDOS DE MODERACIÓN COMPLETOS
# =========================================
@bot.command()
@admin_only()
@commands.has_permissions(kick_members=True)
async def kick(ctx, member: discord.Member, *, reason: str = "Sin razón especificada"):
    await member.kick(reason=f"{reason} | Por: {ctx.author}")
    embed = discord.Embed(title="👢 Usuario Expulsado", description=f"**Usuario:** {member.mention}\n**Razón:** {reason}\n**Moderador:** {ctx.author.mention}", color=COLORS["warning"])
    await ctx.send(embed=embed)
    await send_log(ctx.guild, "Kick", f"{member} expulsado por {ctx.author}: {reason}", COLORS["warning"])

@bot.command()
@admin_only()
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member, duration: str = None, *, reason: str = "Sin razón"):
    seconds = parse_duration(duration) if duration and parse_duration(duration) else None

    if seconds:
        unban_time = datetime.now(timezone.utc) + timedelta(seconds=seconds)
        tempbans[str(member.id)] = {"guild": ctx.guild.id, "unban": unban_time.isoformat()}
        Database.save("tempbans.json", tempbans)
        reason = f"{reason} | Temporal: {duration}"

    await ctx.guild.ban(member, reason=f"{reason} | Por: {ctx.author}", delete_message_days=0)
    embed = discord.Embed(title="🔨 Usuario Baneado", description=f"**Usuario:** {member.mention}\n**Razón:** {reason}\n**Moderador:** {ctx.author.mention}", color=COLORS["error"])
    await ctx.send(embed=embed)
    await send_log(ctx.guild, "Ban", f"{member} baneado por {ctx.author}", COLORS["error"])

@bot.command()
@admin_only()
@commands.has_permissions(ban_members=True)
async def unban(ctx, user_id: int):
    user = await bot.fetch_user(user_id)
    await ctx.guild.unban(discord.Object(id=user_id), reason=f"Desbaneado por {ctx.author}")
    await ctx.send(embed=discord.Embed(title="✅ Usuario Desbaneado", description=f"{user.mention} ha sido desbaneado", color=COLORS["success"]))

@bot.command()
@admin_only()
@commands.has_permissions(moderate_members=True)
async def mute(ctx, member: discord.Member, duration: str, *, reason: str = "Sin razón"):
    seconds = parse_duration(duration) or 600
    await member.timeout(datetime.now(timezone.utc) + timedelta(seconds=seconds), reason=reason)
    embed = discord.Embed(title="🔇 Usuario Silenciado", description=f"**Usuario:** {member.mention}\n**Duración:** {duration}\n**Razón:** {reason}", color=COLORS["warning"])
    await ctx.send(embed=embed)

@bot.command()
@admin_only()
@commands.has_permissions(moderate_members=True)
async def unmute(ctx, member: discord.Member):
    await member.timeout(None, reason=f"Unmute por {ctx.author}")
    await ctx.send(embed=discord.Embed(title="🔊 Usuario Desilenciado", description=f"{member.mention} puede hablar de nuevo", color=COLORS["success"]))

@bot.command()
@admin_only()
@commands.has_permissions(kick_members=True)
async def warn(ctx, member: discord.Member, *, reason: str):
    user_warns = warnings.get(str(member.id), [])
    user_warns.append({"reason": reason, "mod": ctx.author.id, "date": datetime.now().isoformat()})
    warnings[str(member.id)] = user_warns
    Database.save("warnings.json", warnings)
    embed = discord.Embed(title="⚠️ Advertencia", description=f"{member.mention} ha sido advertido\n**Razón:** {reason}\n**Total warns:** {len(user_warns)}", color=COLORS["warning"])
    await ctx.send(embed=embed)

@bot.command()
@admin_only()
async def warnings(ctx, member: discord.Member):
    user_warns = warnings.get(str(member.id), [])
    if not user_warns:
        return await ctx.send(embed=discord.Embed(title="✅ Sin Advertencias", description=f"{member.mention} no tiene warns", color=COLORS["success"]))
    desc = "\n".join([f"`{i+1}.` {w['reason']} - <t:{int(datetime.fromisoformat(w['date']).timestamp())}:R>" for i, w in enumerate(user_warns[-10:])])
    await ctx.send(embed=discord.Embed(title=f"⚠️ Warns de {member}", description=desc, color=COLORS["warning"]))

@bot.command()
@admin_only()
@commands.has_permissions(manage_messages=True)
async def clear(ctx, amount: int = 10):
    amount = max(1, min(100, amount))
    deleted = await ctx.channel.purge(limit=amount + 1)
    await ctx.send(embed=discord.Embed(title="🧹 Limpieza", description=f"Se eliminaron {len(deleted)-1} mensajes", color=COLORS["success"]), delete_after=3)

@bot.command()
@admin_only()
@commands.has_permissions(manage_channels=True)
async def lock(ctx, channel: discord.TextChannel = None):
    ch = channel or ctx.channel
    await ch.set_permissions(ctx.guild.default_role, send_messages=False)
    await ctx.send(embed=discord.Embed(title="🔒 Canal Bloqueado", description=f"{ch.mention} ha sido bloqueado", color=COLORS["error"]))

@bot.command()
@admin_only()
@commands.has_permissions(manage_channels=True)
async def unlock(ctx, channel: discord.TextChannel = None):
    ch = channel or ctx.channel
    await ch.set_permissions(ctx.guild.default_role, send_messages=None)
    await ctx.send(embed=discord.Embed(title="🔓 Canal Desbloqueado", color=COLORS["success"]))

@bot.command()
@admin_only()
@commands.has_permissions(manage_channels=True)
async def slowmode(ctx, seconds: int = 0):
    await ctx.channel.edit(slowmode_delay=max(0, min(21600, seconds)))
    await ctx.send(embed=discord.Embed(title="⏱️ Slowmode", description=f"Establecido a {seconds}s", color=COLORS["info"]))

@bot.command()
@admin_only()
async def userinfo(ctx, member: discord.Member = None):
    m = member or ctx.author
    embed = discord.Embed(title=f"Información de {m}", color=m.color)
    embed.set_thumbnail(url=m.display_avatar.url)
    embed.add_field(name="ID", value=m.id, inline=True)
    embed.add_field(name="Bot", value="Sí" if m.bot else "No", inline=True)
    embed.add_field(name="Cuenta creada", value=f"<t:{int(m.created_at.timestamp())}:F>", inline=False)
    embed.add_field(name="Se unió", value=f"<t:{int(m.joined_at.timestamp())}:F>", inline=False)
    embed.add_field(name="Roles", value=len(m.roles)-1, inline=True)
    await ctx.send(embed=embed)

@bot.command()
@admin_only()
async def infoserver(ctx):
    g = ctx.guild
    embed = discord.Embed(title=g.name, color=COLORS["info"])
    if g.icon: embed.set_thumbnail(url=g.icon.url)
    embed.add_field(name="ID", value=g.id)
    embed.add_field(name="Dueño", value=g.owner.mention)
    embed.add_field(name="Miembros", value=f"{g.member_count} ({len([m for m in g.members if not m.bot])} humanos)")
    embed.add_field(name="Canales", value=f"{len(g.text_channels)} texto | {len(g.voice_channels)} voz")
    embed.add_field(name="Roles", value=len(g.roles))
    embed.add_field(name="Creado", value=f"<t:{int(g.created_at.timestamp())}:D>")
    await ctx.send(embed=embed)

@bot.command(name="anunciar")
@admin_only()
@commands.has_permissions(administrator=True)
async def anunciar(ctx, *, mensaje: str):
    channel = bot.get_channel(CANAL_GENERAL)
    embed = discord.Embed(title="📢 ANUNCIO OFICIAL", description=mensaje, color=COLORS["error"], timestamp=datetime.now(timezone.utc))
    embed.set_footer(text=f"Anunciado por {ctx.author}", icon_url=ctx.author.display_avatar.url)
    await channel.send(content="@everyone", embed=embed)
    await ctx.send("✅ Anuncio enviado")

# =========================================
# TAREAS AUTOMÁTICAS
# =========================================
@tasks.loop(minutes=5)
async def update_stats():
    if not stats: return
    for guild_id, data in stats.items():
        guild = bot.get_guild(int(guild_id))
        if guild and "activos" in data:
            activos = len([m for m in guild.members if not m.bot and m.status!= discord.Status.offline])
            if channel := bot.get_channel(data["activos"]):
                try: await channel.edit(name=f"🟢 Activos: {activos}")
                except: pass

@tasks.loop(minutes=1)
async def check_tempbans():
    now = datetime.now(timezone.utc)
    to_remove = []
    for user_id, data in tempbans.items():
        unban_time = datetime.fromisoformat(data["unban"])
        if now >= unban_time:
            try:
                guild = bot.get_guild(data["guild"])
                if guild:
                    await guild.unban(discord.Object(id=int(user_id)), reason="Ban temporal expirado")
                    await send_log(guild, "Tempban Expirado", f"<@{user_id}> desbaneado automáticamente", COLORS["success"])
            except: pass
            to_remove.append(user_id)
    for uid in to_remove: del tempbans[uid]
    if to_remove: Database.save("tempbans.json", tempbans)

@bot.command(name="stats")
@admin_only()
@commands.has_permissions(administrator=True)
async def stats_cmd(ctx):
    category = await ctx.guild.create_category("📊 ESTADÍSTICAS", position=0)
    activos = await ctx.guild.create_voice_channel("🟢 Activos: 0", category=category)
    for ch in [activos]:
        await ch.set_permissions(ctx.guild.default_role, connect=False)
    stats[str(ctx.guild.id)] = {"activos": activos.id}
    Database.save("stats.json", stats)
    await ctx.send(embed=discord.Embed(title="✅ Stats Creadas", color=COLORS["success"]))

@bot.command(name="delstats")
@admin_only()
async def delstats_cmd(ctx):
    if data := stats.pop(str(ctx.guild.id), None):
        for ch_id in data.values():
            if ch := bot.get_channel(ch_id):
                await ch.delete()
        Database.save("stats.json", stats)
        await ctx.send("✅ Stats eliminadas")

@bot.command(name="linkS")
@admin_only()
async def link_on(ctx):
    antilink["enabled"] = True
    Database.save("antilink.json", antilink)
    await ctx.send(embed=discord.Embed(title="✅ Anti-Links ACTIVADO", color=COLORS["success"]))

@bot.command(name="linkN")
@admin_only()
async def link_off(ctx):
    antilink["enabled"] = False
    Database.save("antilink.json", antilink)
    await ctx.send(embed=discord.Embed(title="❌ Anti-Links DESACTIVADO", color=COLORS["error"]))

# =========================================
# INICIAR BOT
# =========================================
if __name__ == "__main__":
    bot.run(TOKEN)
