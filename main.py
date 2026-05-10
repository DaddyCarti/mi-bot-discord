"""
SERVERPRUEBA BOT v7.0 PROFESSIONAL
Desarrollado para: daddy_carti
Arquitectura: Modular, asíncrona, production-ready
Fecha: 2026
"""
import discord
from discord.ext import commands, tasks
import os
import json
import re
import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, List
from dotenv import load_dotenv

# =========================================
# CONFIGURACIÓN PROFESIONAL
# =========================================
load_dotenv()

# Logging profesional
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(name)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger('ServerPrueba')

class Config:
    """Configuración centralizada del bot"""
    TOKEN = os.getenv("DISCORD_TOKEN")
    GUILD_ID = 1502889233369534494
    CANAL_ADMINS = 1502920731372163112
    CANAL_GENERAL = 1502889242072842303
    CANAL_TICKETS = 1502942029397753866
    CANAL_AUTOROLES = 1502947801770885120

    COLORS = {
        "success": 0x57F287,
        "warning": 0xFAA61A,
        "error": 0xED4245,
        "info": 0x5865F2,
        "primary": 0x2B2D31
    }

    FOOTER_TEXT = "by: daddy_carti"
    BANNER_FILE = "Banner_de_Tickets.jpg"

# Datos para autoroles
AUTOROLES_DATA = {
    "paises": [
        "🇲🇽 México", "🇨🇴 Colombia", "🇦🇷 Argentina", "🇪🇸 España",
        "🇵🇪 Perú", "🇨🇱 Chile", "🇻🇪 Venezuela", "🇪🇨 Ecuador",
        "🇧🇴 Bolivia", "🇺🇾 Uruguay", "🇵🇾 Paraguay", "🇬🇹 Guatemala",
        "🇭🇳 Honduras", "🇸🇻 El Salvador", "🇳🇮 Nicaragua", "🇨🇷 Costa Rica",
        "🇵🇦 Panamá", "🇩🇴 Rep. Dominicana", "🇨🇺 Cuba", "🇺🇸 USA", "🇧🇷 Brasil"
    ],
    "edades": ["13-15", "16-18", "19-21", "22-25", "26+"],
    "plataformas": ["💻 PC", "📱 Móvil", "🎮 PlayStation", "🎮 Xbox", "🎮 Nintendo"]
}

# =========================================
# SISTEMA DE BASE DE DATOS PROFESIONAL
# =========================================
class DatabaseManager:
    """Manejador de bases de datos JSON con cache"""

    def __init__(self):
        self.cache: Dict[str, dict] = {}
        self.files = {
            "warnings": "warnings.json",
            "antilink": "antilink.json",
            "stats": "stats.json",
            "tempbans": "tempbans.json",
            "panels": "panel.json"
        }
        self._load_all()

    def _load_all(self):
        for key, filename in self.files.items():
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    self.cache[key] = json.load(f)
            except FileNotFoundError:
                self.cache[key] = self._get_default(key)
                self.save(key)
            except Exception as e:
                logger.error(f"Error cargando {filename}: {e}")
                self.cache[key] = self._get_default(key)

    def _get_default(self, key: str) -> dict:
        defaults = {
            "warnings": {},
            "antilink": {"enabled": True, "whitelist": []},
            "stats": {},
            "tempbans": {},
            "panels": {}
        }
        return defaults.get(key, {})

    def get(self, key: str) -> dict:
        return self.cache.get(key, {})

    def set(self, key: str, data: dict):
        self.cache[key] = data
        self.save(key)

    def save(self, key: str):
        try:
            filename = self.files.get(key)
            if filename:
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(self.cache[key], f, indent=4, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error guardando {key}: {e}")

db = DatabaseManager()

# =========================================
# UTILIDADES
# =========================================
class Utils:
    @staticmethod
    def admin_only():
        async def predicate(ctx):
            if ctx.channel.id!= Config.CANAL_ADMINS:
                embed = discord.Embed(
                    title="❌ Acceso Denegado",
                    description=f"Usa este comando en <#{Config.CANAL_ADMINS}>",
                    color=Config.COLORS["error"]
                )
                embed.set_footer(text=Config.FOOTER_TEXT)
                await ctx.send(embed=embed, delete_after=5)
                return False
            return True
        return commands.check(predicate)

    @staticmethod
    def parse_duration(text: str) -> Optional[int]:
        match = re.match(r"^(\d+)(s|m|h|d|w)$", text.lower())
        if not match:
            return None
        value, unit = int(match[1]), match[2]
        multipliers = {"s": 1, "m": 60, "h": 3600, "d": 86400, "w": 604800}
        return value * multipliers[unit]

    @staticmethod
    async def send_log(guild: discord.Guild, title: str, description: str, color: int):
        channel = discord.utils.get(guild.text_channels, name="📜-logs")
        if not channel:
            return

        embed = discord.Embed(
            title=title,
            description=description,
            color=color,
            timestamp=datetime.now(timezone.utc)
        )
        embed.set_footer(text=Config.FOOTER_TEXT, icon_url=guild.me.display_avatar.url)

        try:
            await channel.send(embed=embed)
        except Exception as e:
            logger.error(f"Error enviando log: {e}")

    @staticmethod
    def create_embed(title: str, description: str = None, color: str = "info") -> discord.Embed:
        embed = discord.Embed(
            title=title,
            description=description,
            color=Config.COLORS.get(color, Config.COLORS["info"]),
            timestamp=datetime.now(timezone.utc)
        )
        embed.set_footer(text=Config.FOOTER_TEXT)
        return embed

# =========================================
# VISTAS PERSISTENTES
# =========================================
class AutoroleView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.select(
        custom_id="autorole_pais_v2",
        placeholder="🌎 Selecciona tu país",
        options=[
            discord.SelectOption(
                label=p.split(" ")[1],
                emoji=p.split(" ")[0],
                value=p.split(" ")[1]
            ) for p in AUTOROLES_DATA["paises"]
        ]
    )
    async def pais_select(self, interaction: discord.Interaction, select: discord.ui.Select):
        await interaction.response.defer(ephemeral=True)

        try:
            user = interaction.user
            guild = interaction.guild
            selected = select.values[0]

            # Remover países anteriores
            paises_nombres = [p.split(" ")[1] for p in AUTOROLES_DATA["paises"]]
            roles_a_quitar = [r for r in user.roles if r.name in paises_nombres]

            if roles_a_quitar:
                await user.remove_roles(*roles_a_quitar, reason="Cambio de país")

            # Añadir nuevo rol
            role = discord.utils.get(guild.roles, name=selected)
            if role:
                await user.add_roles(role, reason="Autorol: País")
                embed = Utils.create_embed("✅ País Actualizado", f"Ahora eres de **{selected}**", "success")
                await interaction.followup.send(embed=embed, ephemeral=True)
                await Utils.send_log(guild, "🌎 Autorol País", f"{user.mention} → {selected}", Config.COLORS["info"])
            else:
                await interaction.followup.send("❌ Rol no encontrado. Contacta a un admin.", ephemeral=True)

        except Exception as e:
            logger.error(f"Error en autorol país: {e}")
            await interaction.followup.send("❌ Error al asignar rol", ephemeral=True)

    @discord.ui.select(
        custom_id="autorole_edad_v2",
        placeholder="🎂 Selecciona tu edad",
        options=[discord.SelectOption(label=e, value=e) for e in AUTOROLES_DATA["edades"]]
    )
    async def edad_select(self, interaction: discord.Interaction, select: discord.ui.Select):
        await interaction.response.defer(ephemeral=True)

        try:
            user = interaction.user
            guild = interaction.guild
            selected = select.values[0]

            # Remover edades anteriores
            roles_a_quitar = [r for r in user.roles if r.name in AUTOROLES_DATA["edades"]]
            if roles_a_quitar:
                await user.remove_roles(*roles_a_quitar, reason="Cambio de edad")

            role = discord.utils.get(guild.roles, name=selected)
            if role:
                await user.add_roles(role, reason="Autorol: Edad")
                embed = Utils.create_embed("✅ Edad Actualizada", f"Tu rango: **{selected}**", "success")
                await interaction.followup.send(embed=embed, ephemeral=True)
        except Exception as e:
            logger.error(f"Error en autorol edad: {e}")

    @discord.ui.select(
        custom_id="autorole_plataforma_v2",
        placeholder="🎮 Selecciona tus plataformas",
        min_values=1,
        max_values=3,
        options=[
            discord.SelectOption(
                label=p.split(" ")[1],
                emoji=p.split(" ")[0],
                value=p.split(" ")[1]
            ) for p in AUTOROLES_DATA["plataformas"]
        ]
    )
    async def plataforma_select(self, interaction: discord.Interaction, select: discord.ui.Select):
        await interaction.response.defer(ephemeral=True)

        try:
            user = interaction.user
            guild = interaction.guild

            # Remover plataformas anteriores
            plat_nombres = [p.split(" ")[1] for p in AUTOROLES_DATA["plataformas"]]
            roles_a_quitar = [r for r in user.roles if r.name in plat_nombres]

            if roles_a_quitar:
                await user.remove_roles(*roles_a_quitar, reason="Cambio de plataforma")

            # Añadir nuevas
            roles_a_añadir = []
            for value in select.values:
                role = discord.utils.get(guild.roles, name=value)
                if role:
                    roles_a_añadir.append(role)

            if roles_a_añadir:
                await user.add_roles(*roles_a_añadir, reason="Autorol: Plataformas")
                embed = Utils.create_embed("✅ Plataformas Actualizadas", f"Juegas en: **{', '.join(select.values)}**", "success")
                await interaction.followup.send(embed=embed, ephemeral=True)
        except Exception as e:
            logger.error(f"Error en autorol plataforma: {e}")

class TicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.select(
        custom_id="ticket_select_v2",
        placeholder="🎫 Selecciona el tipo de ticket",
        options=[
            discord.SelectOption(label="Soporte General", value="soporte", description="Ayuda con el servidor", emoji="🛠️"),
            discord.SelectOption(label="Compras y VIP", value="compras", description="Información de pagos", emoji="💰"),
            discord.SelectOption(label="Reportar Usuario", value="reporte", description="Reportar mal comportamiento", emoji="🚨"),
            discord.SelectOption(label="Apelación", value="apelacion", description="Apelar una sanción", emoji="⚖️"),
            discord.SelectOption(label="Bug Report", value="bug", description="Reportar error del bot", emoji="🐛")
        ]
    )
    async def ticket_select(self, interaction: discord.Interaction, select: discord.ui.Select):
        await interaction.response.defer(ephemeral=True)

        try:
            guild = interaction.guild
            user = interaction.user

            # Verificar ticket existente
            category = discord.utils.get(guild.categories, name="🎫 TICKETS")
            if not category:
                category = await guild.create_category("🎫 TICKETS")

            existing = discord.utils.get(category.text_channels, name=f"ticket-{user.name.lower()}")
            if existing:
                embed = Utils.create_embed("⚠️ Ticket Existente", f"Ya tienes un ticket: {existing.mention}", "warning")
                return await interaction.followup.send(embed=embed, ephemeral=True)

            # Crear permisos
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(view_channel=False),
                user: discord.PermissionOverwrite(
                    view_channel=True, send_messages=True, read_message_history=True,
                    attach_files=True, embed_links=True, use_application_commands=True
                ),
                guild.me: discord.PermissionOverwrite(view_channel=True, manage_channels=True, manage_messages=True)
            }

            # Añadir rol de staff
            for role in guild.roles:
                if role.permissions.manage_messages or role.permissions.administrator:
                    overwrites[role] = discord.PermissionOverwrite(view_channel=True, send_messages=True)

            # Crear canal
            channel = await guild.create_text_channel(
                name=f"ticket-{user.name}",
                category=category,
                overwrites=overwrites,
                topic=f"Usuario: {user.id} | Tipo: {select.values[0]} | Creado: {datetime.now().isoformat()}"
            )

            embed = discord.Embed(
                title=f"🎫 Ticket - {select.values[0].title()}",
                description=(
                    f"¡Hola {user.mention}!\n\n"
                    f"**Tipo:** {select.values[0].title()}\n"
                    f"**Creado:** <t:{int(datetime.now().timestamp())}:F>\n\n"
                    f"**📋 Por favor describe:**\n"
                    f"• Tu problema con detalles\n"
                    f"• Capturas si es necesario\n"
                    f"• Qué esperas que hagamos\n\n"
                    f"Un miembro del staff te atenderá pronto.\n"
                    f"Usa `!close` para cerrar cuando termines."
                ),
                color=Config.COLORS["info"],
                timestamp=datetime.now(timezone.utc)
            )
            embed.set_footer(text=Config.FOOTER_TEXT)

            await channel.send(content=f"{user.mention}", embed=embed)

            success_embed = Utils.create_embed("✅ Ticket Creado", f"Tu ticket: {channel.mention}", "success")
            await interaction.followup.send(embed=success_embed, ephemeral=True)

            await Utils.send_log(guild, "🎫 Ticket Abierto", f"{user.mention} abrió ticket de **{select.values[0]}**", Config.COLORS["info"])

        except Exception as e:
            logger.error(f"Error creando ticket: {e}")
            await interaction.followup.send("❌ Error al crear ticket. Contacta a un admin.", ephemeral=True)

# =========================================
# BOT SETUP
# =========================================
class ServerPruebaBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix="!",
            intents=intents,
            help_command=None,
            case_insensitive=True,
            strip_after_prefix=True,
            activity=discord.Activity(type=discord.ActivityType.watching, name="ServerPrueba |!menu")
        )

    async def setup_hook(self):
        self.add_view(TicketView())
        self.add_view(AutoroleView())
        logger.info("Vistas persistentes registradas")

bot = ServerPruebaBot()

# =========================================
# EVENTOS
# =========================================
@bot.event
async def on_ready():
    logger.info(f"{'='*60}")
    logger.info(f"BOT CONECTADO: {bot.user} (ID: {bot.user.id})")
    logger.info(f"SERVIDORES: {len(bot.guilds)}")
    logger.info(f"USUARIOS: {sum(g.member_count for g in bot.guilds)}")
    logger.info(f"LATENCIA: {round(bot.latency * 1000)}ms")
    logger.info(f"{'='*60}")

    # Crear canal de logs si no existe
    for guild in bot.guilds:
        if not discord.utils.get(guild.text_channels, name="📜-logs"):
            try:
                await guild.create_text_channel("📜-logs")
                logger.info(f"Canal de logs creado en {guild.name}")
            except:
                pass

    if not update_stats.is_running():
        update_stats.start()
    if not check_tempbans.is_running():
        check_tempbans.start()

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    # Anti-link
    if message.guild and db.get("antilink").get("enabled"):
        if re.search(r"discord(?:\.gg|com/invite|app\.com/invite)/\w+", message.content.lower()):
            if not message.author.guild_permissions.manage_messages:
                try:
                    await message.delete()
                    embed = Utils.create_embed("🔗 Enlace Bloqueado", f"{message.author.mention}, los invites no están permitidos", "error")
                    await message.channel.send(embed=embed, delete_after=5)
                    await Utils.send_log(message.guild, "🛡️ Anti-Link", f"{message.author} intentó enviar invite", Config.COLORS["error"])
                except:
                    pass
                return

    await bot.process_commands(message)

@bot.event
async def on_member_join(member):
    await Utils.send_log(
        member.guild,
        "📥 Nuevo Miembro",
        f"{member.mention} se unió al servidor\n**Cuenta creada:** <t:{int(member.created_at.timestamp())}:R>\n**ID:** {member.id}",
        Config.COLORS["success"]
    )

@bot.event
async def on_member_remove(member):
    await Utils.send_log(
        member.guild,
        "📤 Miembro Salió",
        f"**{member}** ({member.id}) abandonó el servidor",
        Config.COLORS["warning"]
    )

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        return
    elif isinstance(error, commands.MissingPermissions):
        embed = Utils.create_embed("❌ Sin Permisos", "No tienes permisos para usar este comando", "error")
        await ctx.send(embed=embed, delete_after=5)
    elif isinstance(error, commands.CheckFailure):
        return
    else:
        logger.error(f"Error en comando {ctx.command}: {error}")
        embed = Utils.create_embed("❌ Error", "Ocurrió un error ejecutando el comando", "error")
        await ctx.send(embed=embed, delete_after=5)

# =========================================
# COMANDOS DE USUARIO
# =========================================
@bot.command(name="ping", aliases=["latencia"])
async def ping_cmd(ctx):
    """Muestra la latencia del bot"""
    latency = round(bot.latency * 1000)
    embed = Utils.create_embed("🏓 Pong!", f"**Latencia:** `{latency}ms`\n**Uptime:** <t:{int(bot.user.created_at.timestamp())}:R>", "success")
    await ctx.send(embed=embed)

@bot.command(name="hola", aliases=["hi", "hello"])
async def hola_cmd(ctx):
    """Saludo del bot"""
    responses = [
        f"👋 ¡Hola {ctx.author.mention}!",
        f"¡Hey {ctx.author.mention}! ¿Cómo estás?",
        f"¡Saludos {ctx.author.mention}! Usa `!menu`"
    ]
    await ctx.send(responses[hash(ctx.author.id) % len(responses)])

@bot.command(name="menu", aliases=["help", "ayuda"])
async def menu_cmd(ctx):
    """Menú principal de comandos"""
    embed = discord.Embed(
        title="📜 MENÚ PRINCIPAL",
        description=f"¡Hola {ctx.author.mention}!\n\nBienvenido a **ServerPrueba**",
        color=Config.COLORS["info"],
        timestamp=datetime.now(timezone.utc)
    )

    embed.add_field(
        name="🔹 Comandos Básicos",
        value="`!ping` - Ver latencia\n`!hola` - Saludo\n`!menu` - Este menú",
        inline=False
    )

    embed.add_field(
        name="🎫 Soporte",
        value="`!close` - Cerrar ticket\nUsa el panel de tickets para abrir uno",
        inline=False
    )

    embed.add_field(
        name="🎭 Personalización",
        value="Ve al canal de roles para personalizar tu perfil",
        inline=False
    )

    embed.set_thumbnail(url=bot.user.display_avatar.url)
    embed.set_footer(text=Config.FOOTER_TEXT, icon_url=bot.user.display_avatar.url)

    await ctx.send(embed=embed)

# =========================================
# COMANDOS DE ADMINISTRACIÓN
# =========================================
@bot.command(name="admi", aliases=["admin", "panel"])
@commands.has_permissions(manage_messages=True)
@Utils.admin_only()
async def admin_panel(ctx):
    """Panel de administración"""
    embed = discord.Embed(
        title="🛡️ PANEL DE ADMINISTRACIÓN",
        description=f"**Servidor:** {ctx.guild.name}\n**Admin:** {ctx.author.mention}",
        color=Config.COLORS["warning"],
        timestamp=datetime.now(timezone.utc)
    )

    embed.add_field(
        name="🔨 Moderación",
        value="`!kick @user razón`\n`!ban @user razón`\n`!unban ID`\n`!mute @user 10m`\n`!unmute @user`\n`!warn @user razón`\n`!clear 10`",
        inline=True
    )

    embed.add_field(
        name="🔒 Canales",
        value="`!lock`\n`!unlock`\n`!slowmode 5`",
        inline=True
    )

    embed.add_field(
        name="⚙️ Sistemas",
        value="`!setup-tickets`\n`!setup-autoroles`\n`!create-roles-paises`",
        inline=True
    )

    embed.add_field(
        name="📊 Información",
        value="`!userinfo [@user]`\n`!infoserver`\n`!anunciar texto`",
        inline=True
    )

    embed.add_field(
        name="🛠️ Utilidades",
        value="`!stats`\n`!linkS` / `!linkN`",
        inline=True
    )

    embed.set_footer(text=Config.FOOTER_TEXT)
    await ctx.send(embed=embed)

@bot.command(name="create-roles-paises")
@Utils.admin_only()
@commands.has_permissions(manage_roles=True)
async def create_roles_paises(ctx):
    """Crea todos los roles de autoroles"""
    msg = await ctx.send("⏳ Creando roles de autoroles...")

    todos_roles = []
    todos_roles.extend([p.split(" ")[1] for p in AUTOROLES_DATA["paises"]])
    todos_roles.extend(AUTOROLES_DATA["edades"])
    todos_roles.extend([p.split(" ")[1] for p in AUTOROLES_DATA["plataformas"]])

    creados = 0
    existentes = 0

    for nombre in todos_roles:
        if not discord.utils.get(ctx.guild.roles, name=nombre):
            try:
                await ctx.guild.create_role(name=nombre, reason="Sistema de autoroles")
                creados += 1
                await asyncio.sleep(0.3)
            except Exception as e:
                logger.error(f"Error creando rol {nombre}: {e}")
        else:
            existentes += 1

    embed = Utils.create_embed(
        "✅ Roles Creados",
        f"**Nuevos:** {creados}\n**Ya existían:** {existentes}\n**Total:** {len(todos_roles)}",
        "success"
    )
    await msg.edit(content=None, embed=embed)

@bot.command(name="setup-autoroles")
@Utils.admin_only()
@commands.has_permissions(administrator=True)
async def setup_autoroles(ctx):
    """Configura el panel de autoroles"""
    channel = bot.get_channel(Config.CANAL_AUTOROLES)
    if not channel:
        return await ctx.send("❌ Canal no encontrado")

    embed = discord.Embed(
        title="🎭 PERSONALIZA TU PERFIL",
        description=(
            "**Usa los menús de abajo para obtener tus roles**\n\n"
            "🌎 **País** → Muestra de dónde eres\n"
            "🎂 **Edad** → Tu rango de edad\n"
            "🎮 **Plataforma** → Dónde juegas (máx. 3)\n\n"
            "*Los roles se asignan automáticamente*"
        ),
        color=Config.COLORS["info"]
    )
    embed.set_footer(text=Config.FOOTER_TEXT)

    try:
        file = discord.File(Config.BANNER_FILE, filename="banner.jpg")
        embed.set_image(url="attachment://banner.jpg")
    except:
        file = None
        logger.warning("Banner no encontrado para autoroles")

    panels = db.get("panels")
    if msg_id := panels.get("autoroles"):
        try:
            msg = await channel.fetch_message(msg_id)
            await msg.edit(embed=embed, attachments=[file] if file else [], view=AutoroleView())
            embed_success = Utils.create_embed("✅ Panel Actualizado", "El panel de autoroles se actualizó correctamente", "success")
            return await ctx.send(embed=embed_success)
        except Exception as e:
            logger.error(f"Error editando panel autoroles: {e}")

    try:
        if file:
            msg = await channel.send(file=file, embed=embed, view=AutoroleView())
        else:
            msg = await channel.send(embed=embed, view=AutoroleView())

        panels["autoroles"] = msg.id
        db.set("panels", panels)

        embed_success = Utils.create_embed("✅ Panel Creado", f"Panel creado en {channel.mention}", "success")
        await ctx.send(embed=embed_success)
    except Exception as e:
        logger.error(f"Error creando panel autoroles: {e}")
        await ctx.send("❌ Error al crear panel")

@bot.command(name="setup-tickets")
@Utils.admin_only()
@commands.has_permissions(administrator=True)
async def setup_tickets(ctx):
    """Configura el panel de tickets"""
    channel = bot.get_channel(Config.CANAL_TICKETS)
    if not channel:
        return await ctx.send("❌ Canal no encontrado")

    embed = discord.Embed(
        title="📩 CENTRO DE SOPORTE",
        description=(
            "**Bienvenido al sistema de tickets de ServerPrueba**\n\n"
            "**📋 REGLAS IMPORTANTES:**\n"
            "1️⃣ Abre solo UN ticket por problema\n"
            "2️⃣ Describe tu situación con detalles\n"
            "3️⃣ No hagas spam ni menciones innecesarias\n"
            "4️⃣ Sé respetuoso con el staff\n"
            "5️⃣ No abras tickets por diversión\n\n"
            "**Selecciona una categoría abajo para comenzar:**"
        ),
        color=Config.COLORS["info"]
    )
    embed.set_footer(text=Config.FOOTER_TEXT)

    try:
        file = discord.File(Config.BANNER_FILE, filename="banner.jpg")
        embed.set_image(url="attachment://banner.jpg")
    except:
        file = None

    panels = db.get("panels")
    if msg_id := panels.get("tickets"):
        try:
            msg = await channel.fetch_message(msg_id)
            await msg.edit(embed=embed, attachments=[file] if file else [], view=TicketView())
            embed_success = Utils.create_embed("✅ Panel Actualizado", "Panel de tickets actualizado", "success")
            return await ctx.send(embed=embed_success)
        except:
            pass

    try:
        if file:
            msg = await channel.send(file=file, embed=embed, view=TicketView())
        else:
            msg = await channel.send(embed=embed, view=TicketView())

        panels["tickets"] = msg.id
        db.set("panels", panels)

        embed_success = Utils.create_embed("✅ Panel Creado", f"Panel creado en {channel.mention}", "success")
        await ctx.send(embed=embed_success)
    except Exception as e:
        logger.error(f"Error creando panel tickets: {e}")

@bot.command(name="close", aliases=["cerrar"])
async def close_ticket(ctx):
    """Cierra un ticket"""
    if "ticket-" not in ctx.channel.name.lower():
        embed = Utils.create_embed("❌ Error", "Este comando solo funciona en canales de tickets", "error")
        return await ctx.send(embed=embed, delete_after=5)

    embed = Utils.create_embed("🔒 Cerrando Ticket", "Este canal se eliminará en 5 segundos...", "warning")
    await ctx.send(embed=embed)

    await Utils.send_log(ctx.guild, "🎫 Ticket Cerrado", f"{ctx.channel.name} cerrado por {ctx.author.mention}", Config.COLORS["warning"])

    await asyncio.sleep(5)
    try:
        await ctx.channel.delete(reason=f"Cerrado por {ctx.author}")
    except:
        pass

# Comandos de moderación completos
@bot.command(name="kick")
@Utils.admin_only()
@commands.has_permissions(kick_members=True)
async def kick_cmd(ctx, member: discord.Member, *, reason: str = "Sin razón especificada"):
    """Expulsa a un usuario"""
    try:
        await member.kick(reason=f"{reason} | Por: {ctx.author}")
        embed = Utils.create_embed("👢 Usuario Expulsado", f"**Usuario:** {member.mention}\n**Razón:** {reason}\n**Moderador:** {ctx.author.mention}", "warning")
        await ctx.send(embed=embed)
        await Utils.send_log(ctx.guild, "👢 Kick", f"{member} expulsado por {ctx.author}", Config.COLORS["warning"])
    except Exception as e:
        await ctx.send(f"❌ Error: {e}")

@bot.command(name="ban")
@Utils.admin_only()
@commands.has_permissions(ban_members=True)
async def ban_cmd(ctx, member: discord.Member, *, reason: str = "Sin razón especificada"):
    """Banea a un usuario"""
    try:
        await ctx.guild.ban(member, reason=f"{reason} | Por: {ctx.author}", delete_message_days=0)
        embed = Utils.create_embed("🔨 Usuario Baneado", f"**Usuario:** {member.mention}\n**Razón:** {reason}", "error")
        await ctx.send(embed=embed)
        await Utils.send_log(ctx.guild, "🔨 Ban", f"{member} baneado por {ctx.author}", Config.COLORS["error"])
    except Exception as e:
        await ctx.send(f"❌ Error: {e}")

@bot.command(name="unban")
@Utils.admin_only()
@commands.has_permissions(ban_members=True)
async def unban_cmd(ctx, user_id: int):
    """Desbanea a un usuario"""
    try:
        user = await bot.fetch_user(user_id)
        await ctx.guild.unban(discord.Object(id=user_id), reason=f"Desbaneado por {ctx.author}")
        embed = Utils.create_embed("✅ Usuario Desbaneado", f"{user.mention} ha sido desbaneado", "success")
        await ctx.send(embed=embed)
    except Exception as e:
        await ctx.send(f"❌ Error: {e}")

@bot.command(name="mute", aliases=["silenciar"])
@Utils.admin_only()
@commands.has_permissions(moderate_members=True)
async def mute_cmd(ctx, member: discord.Member, duration: str, *, reason: str = "Sin razón"):
    """Silencia a un usuario temporalmente"""
    seconds = Utils.parse_duration(duration)
    if not seconds:
        return await ctx.send("❌ Formato inválido. Usa: 10m, 1h, 1d")

    try:
        await member.timeout(datetime.now(timezone.utc) + timedelta(seconds=seconds), reason=reason)
        embed = Utils.create_embed("🔇 Usuario Silenciado", f"**Usuario:** {member.mention}\n**Duración:** {duration}\n**Razón:** {reason}", "warning")
        await ctx.send(embed=embed)
    except Exception as e:
        await ctx.send(f"❌ Error: {e}")

@bot.command(name="unmute")
@Utils.admin_only()
@commands.has_permissions(moderate_members=True)
async def unmute_cmd(ctx, member: discord.Member):
    """Quita el silencio a un usuario"""
    try:
        await member.timeout(None, reason=f"Unmute por {ctx.author}")
        embed = Utils.create_embed("🔊 Usuario Desilenciado", f"{member.mention} puede hablar de nuevo", "success")
        await ctx.send(embed=embed)
    except Exception as e:
        await ctx.send(f"❌ Error: {e}")

@bot.command(name="clear", aliases=["purge", "limpiar"])
@Utils.admin_only()
@commands.has_permissions(manage_messages=True)
async def clear_cmd(ctx, amount: int = 5):
    """Elimina mensajes"""
    amount = max(1, min(100, amount))
    try:
        deleted = await ctx.channel.purge(limit=amount + 1)
        embed = Utils.create_embed("🧹 Mensajes Eliminados", f"Se eliminaron {len(deleted) - 1} mensajes", "success")
        await ctx.send(embed=embed, delete_after=3)
    except Exception as e:
        await ctx.send(f"❌ Error: {e}")

@bot.command(name="lock", aliases=["bloquear"])
@Utils.admin_only()
@commands.has_permissions(manage_channels=True)
async def lock_cmd(ctx, channel: discord.TextChannel = None):
    """Bloquea un canal"""
    ch = channel or ctx.channel
    await ch.set_permissions(ctx.guild.default_role, send_messages=False)
    embed = Utils.create_embed("🔒 Canal Bloqueado", f"{ch.mention} ha sido bloqueado", "error")
    await ctx.send(embed=embed)

@bot.command(name="unlock", aliases=["desbloquear"])
@Utils.admin_only()
@commands.has_permissions(manage_channels=True)
async def unlock_cmd(ctx, channel: discord.TextChannel = None):
    """Desbloquea un canal"""
    ch = channel or ctx.channel
    await ch.set_permissions(ctx.guild.default_role, send_messages=None)
    embed = Utils.create_embed("🔓 Canal Desbloqueado", f"{ch.mention} ha sido desbloqueado", "success")
    await ctx.send(embed=embed)

@bot.command(name="userinfo", aliases=["ui", "user"])
@Utils.admin_only()
async def userinfo_cmd(ctx, member: discord.Member = None):
    """Muestra información de un usuario"""
    m = member or ctx.author
    embed = discord.Embed(title=f"Información de {m}", color=m.color or Config.COLORS["info"])
    embed.set_thumbnail(url=m.display_avatar.url)
    embed.add_field(name="ID", value=m.id, inline=True)
    embed.add_field(name="Bot", value="Sí" if m.bot else "No", inline=True)
    embed.add_field(name="Cuenta creada", value=f"<t:{int(m.created_at.timestamp())}:F>", inline=False)
    if m.joined_at:
        embed.add_field(name="Se unió", value=f"<t:{int(m.joined_at.timestamp())}:F>", inline=False)
    embed.add_field(name="Roles", value=len(m.roles) - 1, inline=True)
    embed.set_footer(text=Config.FOOTER_TEXT)
    await ctx.send(embed=embed)

@bot.command(name="infoserver", aliases=["serverinfo", "si"])
@Utils.admin_only()
async def infoserver_cmd(ctx):
    """Muestra información del servidor"""
    g = ctx.guild
    embed = discord.Embed(title=g.name, color=Config.COLORS["info"])
    if g.icon:
        embed.set_thumbnail(url=g.icon.url)
    embed.add_field(name="ID", value=g.id, inline=True)
    embed.add_field(name="Dueño", value=g.owner.mention if g.owner else "Desconocido", inline=True)
    embed.add_field(name="Miembros", value=f"{g.member_count} total\n{len([m for m in g.members if not m.bot])} humanos", inline=True)
    embed.add_field(name="Canales", value=f"{len(g.text_channels)} texto\n{len(g.voice_channels)} voz", inline=True)
    embed.add_field(name="Roles", value=len(g.roles), inline=True)
    embed.add_field(name="Creado", value=f"<t:{int(g.created_at.timestamp())}:D>", inline=True)
    embed.set_footer(text=Config.FOOTER_TEXT)
    await ctx.send(embed=embed)

# =========================================
# TAREAS AUTOMÁTICAS
# =========================================
@tasks.loop(minutes=5)
async def update_stats():
    """Actualiza estadísticas de voz"""
    try:
        stats = db.get("stats")
        if not stats:
            return

        for guild_id, data in stats.items():
            guild = bot.get_guild(int(guild_id))
            if not guild:
                continue

            if "activos" in data:
                activos = len([m for m in guild.members if not m.bot and m.status!= discord.Status.offline])
                channel = bot.get_channel(data["activos"])
                if channel:
                    try:
                        await channel.edit(name=f"🟢 Activos: {activos}")
                    except:
                        pass
    except Exception as e:
        logger.error(f"Error en update_stats: {e}")

@tasks.loop(minutes=1)
async def check_tempbans():
    """Revisa bans temporales"""
    try:
        tempbans = db.get("tempbans")
        now = datetime.now(timezone.utc)
        to_remove = []

        for user_id, data in tempbans.items():
            unban_time = datetime.fromisoformat(data["unban"])
            if now >= unban_time:
                try:
                    guild = bot.get_guild(data["guild"])
                    if guild:
                        await guild.unban(discord.Object(id=int(user_id)), reason="Ban temporal expirado")
                        await Utils.send_log(guild, "⏰ Tempban Expirado", f"<@{user_id}> desbaneado automáticamente", Config.COLORS["success"])
                except:
                    pass
                to_remove.append(user_id)

        for uid in to_remove:
            del tempbans[uid]

        if to_remove:
            db.set("tempbans", tempbans)
    except Exception as e:
        logger.error(f"Error en check_tempbans: {e}")

# =========================================
# INICIO
# =========================================
if __name__ == "__main__":
    if not Config.TOKEN:
        logger.critical("❌ TOKEN no encontrado en.env")
        exit(1)

    try:
        bot.run(Config.TOKEN, log_handler=None)
    except Exception as e:
        logger.critical(f"Error fatal: {e}")
