# =========================================
# SERVERPRUEBA BOT v3.0 - FULL FEATURED
# Discord.py 2.3+ | Python 3.11
# =========================================
import discord
from discord.ext import commands, tasks
import os, json, re, asyncio
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

# ---------- INTENTS ----------
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.presences = True

bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

# ---------- CONFIG ----------
CANAL_ADMINS = 1502920731372163112
CANAL_GENERAL = 1502889242072842303
TICKETS_CAT = "🎫 TICKETS"
LOGS_NAME = "📜-logs"
ROL_TICKET = "ticket"

COLORS = {
    "ok": 0x57F287,
    "warn": 0xFAA61A,
    "error": 0xED4245,
    "info": 0x5865F2,
    "mute": 0x9B59B6
}

# ---------- DATABASE ----------
def load_db(file, default):
    try: return json.load(open(file))
    except: return default
def save_db(file, data): json.dump(data, open(file, "w"), indent=2)

warnings_db = load_db("warnings.json", {})
antilink_db = load_db("antilink.json", {"enabled": True})
stats_db = load_db("stats.json", {})

def is_admin_channel(ctx): return ctx.channel.id == CANAL_ADMINS

async def log(guild, title, desc, color):
    ch = discord.utils.get(guild.text_channels, name=LOGS_NAME)
    if ch:
        e = discord.Embed(title=title, description=desc, color=color, timestamp=datetime.utcnow())
        e.set_footer(text=bot.user.name, icon_url=bot.user.display_avatar.url)
        await ch.send(embed=e)

def parse_time(s):
    if not (m := re.match(r"(\d+)(s|m|h|d|w)", s.lower())): return None
    return int(m[1]) * {"s":1,"m":60,"h":3600,"d":86400,"w":604800}[m[2]]

# =========================================
# TICKETS - PANEL PERSISTENTE
# =========================================
class TicketView(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)

    @discord.ui.select(
        custom_id="ticket_select",
        placeholder="Selecciona el motivo...",
        options=[
            discord.SelectOption(label="Soporte General", value="soporte", emoji="🛠️", description="Dudas, errores, ayuda"),
            discord.SelectOption(label="Compras y Donaciones", value="compras", emoji="💰", description="VIP, rangos, pagos")
        ]
    )
    async def ticket_callback(self, interaction: discord.Interaction, select: discord.ui.Select):
        await interaction.response.defer(ephemeral=True)
        guild = interaction.guild
        cat = discord.utils.get(guild.categories, name=TICKETS_CAT) or await guild.create_category(TICKETS_CAT)

        # Evitar tickets duplicados
        existing = discord.utils.get(cat.text_channels, name=f"ticket-{interaction.user.name.lower()}")
        if existing:
            return await interaction.followup.send(f"Ya tienes un ticket: {existing.mention}", ephemeral=True)

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            interaction.user: discord.PermissionOverwrite(view_channel=True, send_messages=True, attach_files=True, embed_links=True),
            guild.me: discord.PermissionOverwrite(view_channel=True, manage_channels=True)
        }
        if role := discord.utils.get(guild.roles, name=ROL_TICKET):
            overwrites[role] = discord.PermissionOverwrite(view_channel=True, send_messages=True)
        for r in guild.roles:
            if r.permissions.manage_messages:
                overwrites[r] = discord.PermissionOverwrite(view_channel=True, send_messages=True)

        channel = await guild.create_text_channel(
            f"ticket-{interaction.user.name}",
            category=cat,
            overwrites=overwrites,
            topic=f"{interaction.user.id}|{select.values[0]}|{datetime.utcnow().isoformat()}"
        )

        embed = discord.Embed(
            title=f"🎫 Ticket de {select.values[0].title()}",
            description=f"Bienvenido {interaction.user.mention}\n\n**REGLAS**\n• Explica tu problema detalladamente\n• No hagas spam\n• Un ticket por tema\n\nStaff te atenderá pronto.",
            color=COLORS["info"]
        )
        embed.set_footer(text="Usa!close para cerrar el ticket")
        await channel.send(content=f"{interaction.user.mention} {role.mention if role else ''}", embed=embed)
        await interaction.followup.send(f"Ticket creado: {channel.mention}", ephemeral=True)
        await log(guild, "Ticket Abierto", f"{interaction.user.mention} → {select.values[0]}", COLORS["info"])

# =========================================
# EVENTOS
# =========================================
@bot.event
async def on_ready():
    await bot.wait_until_ready()
    bot.add_view(TicketView())
    for guild in bot.guilds:
        if not discord.utils.get(guild.text_channels, name=LOGS_NAME):
            await guild.create_text_channel(LOGS_NAME)
    if not actualizar_stats.is_running(): actualizar_stats.start()
    print(f"✅ {bot.user} - Listo en {len(bot.guilds)} servidores")

@bot.event
async def on_message(message):
    if message.author.bot: return
    if antilink_db["enabled"] and re.search(r"discord(?:\.gg|app\.com/invite)/\w+", message.content, re.I):
        if not message.author.guild_permissions.manage_messages:
            await message.delete()
            e = discord.Embed(title="🔗 Enlace bloqueado", description=f"{message.author.mention}, los invites no están permitidos", color=COLORS["error"])
            await message.channel.send(embed=e, delete_after=5)
            await log(message.guild, "Anti-Link", f"{message.author} intentó enviar invite", COLORS["error"])
            return
    await bot.process_commands(message)

@bot.event
async def on_member_join(member): await log(member.guild, "📥 Miembro Entró", f"{member.mention} ({member.id})", COLORS["ok"])
@bot.event
async def on_member_remove(member): await log(member.guild, "📤 Miembro Salió", f"{member} ({member.id})", COLORS["warn"])
@bot.event
async def on_message_delete(msg):
    if not msg.author.bot and msg.guild:
        await log(msg.guild, "🗑️ Mensaje Eliminado", f"**{msg.author}** en {msg.channel.mention}: {msg.content[:400]}", COLORS["error"])

# =========================================
# COMANDOS USUARIO
# =========================================
@bot.command()
async def ping(ctx):
    e = discord.Embed(title="🏓 Pong!", description=f"Latencia: `{round(bot.latency*1000)}ms`", color=COLORS["ok"], timestamp=datetime.utcnow())
    await ctx.send(embed=e)

@bot.command()
async def hola(ctx):
    await ctx.send(f"👋 Hola {ctx.author.mention}! Usa `!menu` para ver comandos")

@bot.command(name="menu")
async def menu_cmd(ctx):
    e = discord.Embed(title="📜 Menú de Comandos - Usuario", description="Prefijo: `!`", color=COLORS["info"])
    e.add_field(name="🔹 General", value="`ping` - Latencia\n`hola` - Saludo\n`menu` - Este menú", inline=False)
    e.add_field(name="🎫 Tickets", value="`close` - Cierra tu ticket (solo dentro del ticket)", inline=False)
    e.add_field(name="🎭 Roles", value="`rol list` - Ver roles disponibles\n`rol join <nombre>` - Obtener rol\n`rol leave <nombre>` - Quitar rol", inline=False)
    e.set_thumbnail(url=bot.user.display_avatar.url)
    await ctx.send(embed=e)

# =========================================
# SISTEMA DE ROLES
# =========================================
@bot.group(name="rol", invoke_without_command=True)
async def rol_group(ctx):
    e = discord.Embed(title="🎭 Sistema de Roles", color=COLORS["info"])
    e.add_field(name="Para Usuarios", value="`!rol list`\n`!rol join Nombre`\n`!rol leave Nombre`", inline=False)
    e.add_field(name="Para Staff", value="`!rol add @user @rol`\n`!rol remove @user @rol`\n`!rol create Nombre FF0000`\n`!rol delete Nombre`", inline=False)
    await ctx.send(embed=e)

@rol_group.command(name="list")
async def rol_list(ctx):
    roles = [r for r in ctx.guild.roles if not r.managed and r!= ctx.guild.default_role and not r.permissions.administrator and r < ctx.guild.me.top_role]
    desc = "\n".join([f"• {r.name}" for r in sorted(roles, key=lambda x: x.position, reverse=True)[:25]]) or "No hay roles auto-asignables"
    await ctx.send(embed=discord.Embed(title="Roles Disponibles", description=desc, color=COLORS["info"]))

@rol_group.command(name="join")
async def rol_join(ctx, *, nombre: str):
    role = discord.utils.get(ctx.guild.roles, name=nombre)
    if not role: return await ctx.send(embed=discord.Embed(title="❌", description="Rol no encontrado", color=COLORS["error"]))
    if role.permissions.administrator: return await ctx.send(embed=discord.Embed(title="❌", description="No puedes auto-asignarte ese rol", color=COLORS["error"]))
    await ctx.author.add_roles(role)
    await ctx.send(embed=discord.Embed(title="✅ Rol añadido", description=f"Ahora tienes {role.mention}", color=COLORS["ok"]))

@rol_group.command(name="leave")
async def rol_leave(ctx, *, nombre: str):
    role = discord.utils.get(ctx.guild.roles, name=nombre)
    if role and role in ctx.author.roles:
        await ctx.author.remove_roles(role)
        await ctx.send(embed=discord.Embed(title="✅ Rol removido", description=f"Se quitó {role.name}", color=COLORS["ok"]))

@rol_group.command(name="add")
@commands.has_permissions(manage_roles=True)
async def rol_add(ctx, member: discord.Member, role: discord.Role):
    if not is_admin_channel(ctx): return
    await member.add_roles(role)
    await ctx.send(embed=discord.Embed(title="✅ Rol Asignado", description=f"{role.mention} → {member.mention}", color=COLORS["ok"]))
    await log(ctx.guild, "Rol Añadido", f"{ctx.author} dio {role.name} a {member}", COLORS["ok"])

@rol_group.command(name="remove")
@commands.has_permissions(manage_roles=True)
async def rol_remove(ctx, member: discord.Member, role: discord.Role):
    if not is_admin_channel(ctx): return
    await member.remove_roles(role)
    await ctx.send(embed=discord.Embed(title="✅ Rol Quitado", color=COLORS["warn"]))

@rol_group.command(name="create")
@commands.has_permissions(manage_roles=True)
async def rol_create(ctx, nombre: str, color: str = "5865F2"):
    if not is_admin_channel(ctx): return
    try: col = discord.Color(int(color.replace("#",""), 16))
    except: col = COLORS["info"]
    role = await ctx.guild.create_role(name=nombre, color=col, reason=f"Creado por {ctx.author}")
    await ctx.send(embed=discord.Embed(title="✅ Rol Creado", description=f"{role.mention} Color: #{color}", color=col))

@rol_group.command(name="delete")
@commands.has_permissions(manage_roles=True)
async def rol_delete(ctx, *, nombre: str):
    if not is_admin_channel(ctx): return
    if role := discord.utils.get(ctx.guild.roles, name=nombre):
        await role.delete(reason=f"Eliminado por {ctx.author}")
        await ctx.send(embed=discord.Embed(title="🗑️ Rol Eliminado", color=COLORS["error"]))

# =========================================
# STAFF - PANEL COMPLETO
# =========================================
@bot.command(name="admi")
@commands.has_permissions(manage_messages=True)
async def admi_panel(ctx):
    if not is_admin_channel(ctx):
        return await ctx.send(f"Usa este comando en <#{CANAL_ADMINS}>", delete_after=5)

    e = discord.Embed(title="🛡️ PANEL DE ADMINISTRACIÓN", description=f"Servidor: **{ctx.guild.name}**", color=COLORS["warn"], timestamp=datetime.utcnow())
    e.set_thumbnail(url=bot.user.display_avatar.url)
    e.add_field(name="🔨 MODERACIÓN", value="`!kick @user razón`\n`!ban @user [tiempo] razón`\n`!unban ID`\n`!mute @user 10m razón`\n`!unmute @user`\n`!warn @user razón`\n`!warnings @user`", inline=True)
    e.add_field(name="🧹 GESTIÓN", value="`!clear [1-100]`\n`!lock [#canal]`\n`!unlock [#canal]`\n`!slowmode [seg]`", inline=True)
    e.add_field(name="🎭 ROLES", value="`!rol add/remove`\n`!rol create/delete`\n`!rol list`", inline=True)
    e.add_field(name="🎫 TICKETS", value="`!setup-tickets`\n`!close`", inline=True)
    e.add_field(name="📊 UTILIDAD", value="`!userinfo [@user]`\n`!infoserver`\n`!anunciar texto`\n`!stats` / `!delstats`", inline=True)
    e.add_field(name="🔗 ANTI-LINK", value=f"Estado: **{'ON' if antilink_db['enabled'] else 'OFF'}**\n`!linkS` / `!linkN`", inline=True)
    await ctx.send(embed=e)

@bot.command(name="setup-tickets")
@commands.has_permissions(administrator=True)
async def setup_tickets_cmd(ctx):
    if not is_admin_channel(ctx): return
    channel = discord.utils.get(ctx.guild.text_channels, name="ticket") or await ctx.guild.create_text_channel("🎫-abrir-ticket")
    embed = discord.Embed(
        title="📩 Centro de Soporte",
        description="**__REGLAS DE TICKETS__**\n1️⃣ No abras tickets innecesarios\n2️⃣ Describe tu problema claramente\n3️⃣ No menciones al staff, te atenderán\n4️⃣ Prohibido el spam\n\nSelecciona una opción para comenzar:",
        color=COLORS["info"]
    )
    embed.set_image(url="https://i.imgur.com/5lR0X7f.png")
    await channel.send(embed=embed, view=TicketView())
    await ctx.send(embed=discord.Embed(title="✅", description=f"Panel creado en {channel.mention}", color=COLORS["ok"]))

@bot.command()
async def close(ctx):
    if "ticket-" not in ctx.channel.name: return
    await ctx.send(embed=discord.Embed(title="Cerrando...", description="Este canal se eliminará en 3 segundos", color=COLORS["warn"]))
    await asyncio.sleep(3)
    await log(ctx.guild, "Ticket Cerrado", f"{ctx.channel.name} cerrado por {ctx.author}", COLORS["warn"])
    await ctx.channel.delete()

# --- Moderación completa ---
@bot.command()
@commands.has_permissions(kick_members=True)
async def kick(ctx, member: discord.Member, *, reason="Sin razón"):
    if not is_admin_channel(ctx): return
    await member.kick(reason=reason)
    await ctx.send(embed=discord.Embed(title="👢 Kick", description=f"{member} expulsado", color=COLORS["warn"]))
    await log(ctx.guild, "Kick", f"{member} por {ctx.author}: {reason}", COLORS["warn"])

@bot.command()
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member, time: str = None, *, reason="Sin razón"):
    if not is_admin_channel(ctx): return
    seconds = parse_time(time) if time else None
    if seconds: reason = f"{reason} | Duración: {time}"
    await ctx.guild.ban(member, reason=reason, delete_message_days=0)
    e = discord.Embed(title="🔨 Ban", description=f"{member.mention} baneado\n**Razón:** {reason}", color=COLORS["error"])
    await ctx.send(embed=e)
    await log(ctx.guild, "Ban", f"{member} por {ctx.author}", COLORS["error"])
    if seconds:
        await asyncio.sleep(seconds)
        await ctx.guild.unban(discord.Object(id=member.id), reason="Ban temporal expirado")

@bot.command()
@commands.has_permissions(ban_members=True)
async def unban(ctx, user_id: int):
    if not is_admin_channel(ctx): return
    await ctx.guild.unban(discord.Object(id=user_id))
    await ctx.send(embed=discord.Embed(title="✅ Unban", color=COLORS["ok"]))

@bot.command()
@commands.has_permissions(moderate_members=True)
async def mute(ctx, member: discord.Member, duration: str, *, reason="Sin razón"):
    if not is_admin_channel(ctx): return
    seconds = parse_time(duration) or 600
    await member.timeout(datetime.utcnow() + timedelta(seconds=seconds), reason=reason)
    await ctx.send(embed=discord.Embed(title="🔇 Mute", description=f"{member.mention} por {duration}", color=COLORS["mute"]))

@bot.command()
@commands.has_permissions(moderate_members=True)
async def unmute(ctx, member: discord.Member):
    if not is_admin_channel(ctx): return
    await member.timeout(None)
    await ctx.send(embed=discord.Embed(title="🔊 Unmute", color=COLORS["ok"]))

@bot.command()
@commands.has_permissions(kick_members=True)
async def warn(ctx, member: discord.Member, *, reason):
    if not is_admin_channel(ctx): return
    warnings_db.setdefault(str(member.id), []).append({"by": ctx.author.id, "reason": reason, "time": datetime.utcnow().isoformat()})
    save_db("warnings.json", warnings_db)
    await ctx.send(embed=discord.Embed(title="⚠️ Warn", description=f"{member.mention}: {reason}", color=COLORS["warn"]))

@bot.command()
@commands.has_permissions(kick_members=True)
async def warnings(ctx, member: discord.Member):
    if not is_admin_channel(ctx): return
    warns = warnings_db.get(str(member.id), [])
    desc = "\n".join([f"{i+1}. {w['reason']}" for i, w in enumerate(warns)]) or "Sin warns"
    await ctx.send(embed=discord.Embed(title=f"Warns de {member}", description=desc, color=COLORS["warn"]))

@bot.command()
@commands.has_permissions(manage_messages=True)
async def clear(ctx, amount: int = 10):
    if not is_admin_channel(ctx): return
    deleted = await ctx.channel.purge(limit=amount+1)
    await ctx.send(embed=discord.Embed(title=f"🧹 {len(deleted)-1} mensajes borrados", color=COLORS["ok"]), delete_after=3)

@bot.command()
@commands.has_permissions(manage_channels=True)
async def lock(ctx, channel: discord.TextChannel = None):
    if not is_admin_channel(ctx): return
    ch = channel or ctx.channel
    await ch.set_permissions(ctx.guild.default_role, send_messages=False)
    await ctx.send(embed=discord.Embed(title="🔒 Canal bloqueado", color=COLORS["error"]))

@bot.command()
@commands.has_permissions(manage_channels=True)
async def unlock(ctx, channel: discord.TextChannel = None):
    if not is_admin_channel(ctx): return
    ch = channel or ctx.channel
    await ch.set_permissions(ctx.guild.default_role, send_messages=None)
    await ctx.send(embed=discord.Embed(title="🔓 Canal desbloqueado", color=COLORS["ok"]))

@bot.command()
async def userinfo(ctx, member: discord.Member = None):
    if not is_admin_channel(ctx): return
    m = member or ctx.author
    e = discord.Embed(title=str(m), color=m.color)
    e.set_thumbnail(url=m.display_avatar.url)
    e.add_field(name="ID", value=m.id); e.add_field(name="Cuenta creada", value=f"<t:{int(m.created_at.timestamp())}:R>")
    e.add_field(name="Se unió", value=f"<t:{int(m.joined_at.timestamp())}:R>")
    await ctx.send(embed=e)

@bot.command()
async def infoserver(ctx):
    if not is_admin_channel(ctx): return
    g = ctx.guild
    e = discord.Embed(title=g.name, color=COLORS["info"])
    e.add_field(name="Miembros", value=g.member_count); e.add_field(name="Creado", value=f"<t:{int(g.created_at.timestamp())}:D>")
    await ctx.send(embed=e)

@bot.command(name="anunciar")
@commands.has_permissions(administrator=True)
async def anunciar_cmd(ctx, *, mensaje):
    if not is_admin_channel(ctx): return
    ch = bot.get_channel(CANAL_GENERAL)
    e = discord.Embed(title="📢 ANUNCIO OFICIAL", description=mensaje, color=COLORS["error"], timestamp=datetime.utcnow())
    e.set_footer(text=f"Por {ctx.author}", icon_url=ctx.author.display_avatar.url)
    await ch.send(content="@everyone", embed=e)

# ---------- STATS ----------
@tasks.loop(minutes=5)
async def actualizar_stats():
    if not stats_db: return
    for guild_id, data in stats_db.items():
        if guild := bot.get_guild(int(guild_id)):
            activos = len([m for m in guild.members if not m.bot and m.status!= discord.Status.offline])
            if ch := bot.get_channel(data["activos"]): await ch.edit(name=f"🟢 Activos: {activos}")

@bot.command(name="stats")
@commands.has_permissions(administrator=True)
async def stats_cmd(ctx):
    if not is_admin_channel(ctx): return
    cat = await ctx.guild.create_category("📊 ESTADÍSTICAS", position=0)
    v1 = await ctx.guild.create_voice_channel("🟢 Activos: 0", category=cat)
    for c in : await c.set_permissions(ctx.guild.default_role, connect=False)
    stats_db[str(ctx.guild.id)] = {"activos": v1.id}
    save_db("stats.json", stats_db)
    await ctx.send("✅ Stats creadas")

@bot.command(name="linkS")
@commands.has_permissions(administrator=True)
async def links_on(ctx):
    if not is_admin_channel(ctx): return
    antilink_db["enabled"] = True; save_db("antilink.json", antilink_db)
    await ctx.send("✅ Anti-links ACTIVADO")

@bot.command(name="linkN")
@commands.has_permissions(administrator=True)
async def links_off(ctx):
    if not is_admin_channel(ctx): return
    antilink_db["enabled"] = False; save_db("antilink.json", antilink_db)
    await ctx.send("❌ Anti-links DESACTIVADO")

bot.run(TOKEN)
