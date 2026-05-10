import discord
from discord.ext import commands
import os
import json
import asyncio
import random
import re
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

# Configuración de intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.presences = True
intents.guilds = True

# Crear bot
bot = commands.Bot(
    command_prefix="!",
    intents=intents,
    help_command=None,
    case_insensitive=True
)

# ==================== CONFIGURACIÓN DEL SERVIDOR ====================
CANAL_ADMINS = 1502920731372163112
CANAL_TICKETS = 1502942029397753866
CANAL_AUTOROLES = 1502947801770885120
CREADOR = "daddy_oofo"
FOOTER_TEXT = f"Bot desarrollado por {CREADOR} | Sistema Premium"

# Colores para embeds
COLORS = {
    "azul": 0x5865F2,
    "verde": 0x57F287,
    "rojo": 0xED4245,
    "oro": 0xF1C40F,
    "morado": 0x9B59B6,
    "naranja": 0xE67E22
}

# Datos para autoroles
PAISES = ["México", "Colombia", "Argentina", "España", "Perú", "Chile", "Venezuela", "Ecuador", "Bolivia", "Uruguay", "Paraguay", "Guatemala", "Honduras", "El Salvador", "Nicaragua", "Costa Rica", "Panamá", "Rep. Dominicana", "Cuba", "USA", "Brasil"]
EMOJIS_PAISES = {"México":"🇲🇽","Colombia":"🇨🇴","Argentina":"🇦🇷","España":"🇪🇸","Perú":"🇵🇪","Chile":"🇨🇱","Venezuela":"🇻🇪","Ecuador":"🇪🇨","Bolivia":"🇧🇴","Uruguay":"🇺🇾","Paraguay":"🇵🇾","Guatemala":"🇬🇹","Honduras":"🇭🇳","El Salvador":"🇸🇻","Nicaragua":"🇳🇮","Costa Rica":"🇨🇷","Panamá":"🇵🇦","Rep. Dominicana":"🇩🇴","Cuba":"🇨🇺","USA":"🇺🇸","Brasil":"🇧🇷"}
EDADES = ["13-15", "16-18", "19-21", "22-25", "26+"]
PLATAFORMAS = {"PC":"💻","Móvil":"📱","PlayStation":"🎮","Xbox":"🎮","Nintendo":"🎮"}

# ==================== SISTEMA DE BASE DE DATOS ====================
def cargar_base_datos(archivo, valor_por_defecto={}):
    try:
        with open(archivo, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return valor_por_defecto
    except Exception as e:
        print(f"Error cargando {archivo}: {e}")
        return valor_por_defecto

def guardar_base_datos(archivo, datos):
    try:
        with open(archivo, 'w', encoding='utf-8') as f:
            json.dump(datos, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"Error guardando {archivo}: {e}")

# Cargar datos
niveles_data = cargar_base_datos("levels.json")
economia_data = cargar_base_datos("economy.json")
daily_data = cargar_base_datos("daily.json")
advertencias_data = cargar_base_datos("warns.json")

# ==================== FUNCIÓN PARA PARSEAR TIEMPOS ====================
def parsear_tiempo(tiempo_str):
    """
    Convierte strings como 10s, 10min, 1h, 1d, 1w, 1y a segundos
    """
    if not tiempo_str:
        return None

    tiempo_str = tiempo_str.lower().strip()
    patron = r"^(\d+)(s|sec|second|seconds|min|m|minute|minutes|h|hour|hours|d|day|days|w|week|weeks|y|year|years)$"
    match = re.match(patron, tiempo_str)

    if not match:
        return None

    cantidad = int(match.group(1))
    unidad = match.group(2)

    multiplicadores = {
        "s": 1, "sec": 1, "second": 1, "seconds": 1,
        "m": 60, "min": 60, "minute": 60, "minutes": 60,
        "h": 3600, "hour": 3600, "hours": 3600,
        "d": 86400, "day": 86400, "days": 86400,
        "w": 604800, "week": 604800, "weeks": 604800,
        "y": 31536000, "year": 31536000, "years": 31536000
    }

    return cantidad * multiplicadores.get(unidad, 0)

# ==================== SISTEMA DE LOGS ====================
async def enviar_log(guild, titulo, descripcion, color):
    try:
        canal_logs = discord.utils.get(guild.text_channels, name="📜-logs")
        if not canal_logs:
            canal_logs = await guild.create_text_channel("📜-logs")

        embed = discord.Embed(
            title=titulo,
            description=descripcion,
            color=color,
            timestamp=datetime.now(timezone.utc)
        )
        embed.set_footer(text=FOOTER_TEXT)
        await canal_logs.send(embed=embed)
    except Exception as e:
        print(f"Error enviando log: {e}")

# ==================== VISTA DE AUTOROLES ====================
class VistaAutoroles(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.select(
        custom_id="select_pais",
        placeholder="🌎 Selecciona tu país de origen",
        min_values=1,
        max_values=1,
        options=[
            discord.SelectOption(
                label=pais,
                emoji=EMOJIS_PAISES.get(pais, "🌎"),
                value=pais,
                description=f"Obtén acceso al rol de {pais}"
            ) for pais in PAISES
        ]
    )
    async def seleccionar_pais(self, interaction: discord.Interaction, select: discord.ui.Select):
        await interaction.response.defer(ephemeral=True)
        pais_seleccionado = select.values[0]
        guild = interaction.guild
        miembro = interaction.user

        try:
            # Buscar o crear rol
            rol = discord.utils.get(guild.roles, name=pais_seleccionado)
            if not rol:
                rol = await guild.create_role(
                    name=pais_seleccionado,
                    reason="Autorol - País"
                )

            # Quitar otros roles de países
            for rol_actual in miembro.roles:
                if rol_actual.name in PAISES:
                    await miembro.remove_roles(rol_actual)

            # Asignar nuevo rol
            await miembro.add_roles(rol)

            embed = discord.Embed(
                title="✅ País Actualizado Correctamente",
                description=f"Has seleccionado **{EMOJIS_PAISES.get(pais_seleccionado)} {pais_seleccionado}** como tu país.\n\nAhora tienes acceso a canales exclusivos para tu región.",
                color=COLORS["verde"]
            )
            embed.set_thumbnail(url="https://i.imgur.com/8Km9tLL.png")
            embed.set_footer(text=FOOTER_TEXT)
            await interaction.followup.send(embed=embed, ephemeral=True)

        except Exception as e:
            await interaction.followup.send("❌ Error al asignar el rol. Contacta a un administrador.", ephemeral=True)

    @discord.ui.select(
        custom_id="select_edad",
        placeholder="🎂 Selecciona tu rango de edad",
        min_values=1,
        max_values=1,
        options=[
            discord.SelectOption(
                label=edad,
                value=edad,
                description=f"Rango de edad: {edad} años",
                emoji="🎂"
            ) for edad in EDADES
        ]
    )
    async def seleccionar_edad(self, interaction: discord.Interaction, select: discord.ui.Select):
        await interaction.response.defer(ephemeral=True)
        edad_seleccionada = select.values[0]
        guild = interaction.guild
        miembro = interaction.user

        try:
            rol = discord.utils.get(guild.roles, name=edad_seleccionada)
            if not rol:
                rol = await guild.create_role(name=edad_seleccionada, reason="Autorol - Edad")

            for rol_actual in miembro.roles:
                if rol_actual.name in EDADES:
                    await miembro.remove_roles(rol_actual)

            await miembro.add_roles(rol)

            embed = discord.Embed(
                title="✅ Edad Actualizada",
                description=f"Tu rango de edad ha sido establecido en **{edad_seleccionada}**",
                color=COLORS["verde"]
            )
            embed.set_footer(text=FOOTER_TEXT)
            await interaction.followup.send(embed=embed, ephemeral=True)

        except:
            await interaction.followup.send("❌ Error al asignar rol", ephemeral=True)

    @discord.ui.select(
        custom_id="select_plataforma",
        placeholder="🎮 Selecciona tus plataformas de juego",
        min_values=1,
        max_values=5,
        options=[
            discord.SelectOption(
                label=nombre,
                emoji=emoji,
                value=nombre,
                description=f"Juegas en {nombre}"
            ) for nombre, emoji in PLATAFORMAS.items()
        ]
    )
    async def seleccionar_plataforma(self, interaction: discord.Interaction, select: discord.ui.Select):
        await interaction.response.defer(ephemeral=True)
        guild = interaction.guild
        miembro = interaction.user
        plataformas_seleccionadas = select.values

        try:
            for rol_actual in miembro.roles:
                if rol_actual.name in PLATAFORMAS.keys():
                    await miembro.remove_roles(rol_actual)

            for plataforma in plataformas_seleccionadas:
                rol = discord.utils.get(guild.roles, name=plataforma)
                if not rol:
                    rol = await guild.create_role(name=plataforma, reason="Autorol - Plataforma")
                await miembro.add_roles(rol)

            embed = discord.Embed(
                title="✅ Plataformas Actualizadas",
                description=f"Has seleccionado: **{', '.join(plataformas_seleccionadas)}**",
                color=COLORS["verde"]
            )
            embed.set_footer(text=FOOTER_TEXT)
            await interaction.followup.send(embed=embed, ephemeral=True)

        except:
            await interaction.followup.send("❌ Error al asignar roles", ephemeral=True)

# ==================== VISTA DE TICKETS ====================
class VistaTickets(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.select(
        custom_id="ticket_selector",
        placeholder="🎫 Selecciona el tipo de soporte que necesitas",
        min_values=1,
        max_values=1,
        options=[
            discord.SelectOption(
                label="Soporte General",
                value="soporte",
                emoji="🛠️",
                description="Ayuda general con el servidor o bot"
            ),
            discord.SelectOption(
                label="Compras y Pagos",
                value="compras",
                emoji="💰",
                description="Información sobre VIP, compras y pagos"
            ),
            discord.SelectOption(
                label="Reportar Usuario",
                value="reporte",
                emoji="🚨",
                description="Reportar comportamiento inapropiado"
            ),
            discord.SelectOption(
                label="Apelación de Sanción",
                value="apelacion",
                emoji="⚖️",
                description="Apelar un ban, mute o advertencia"
            )
        ]
    )
    async def crear_ticket(self, interaction: discord.Interaction, select: discord.ui.Select):
        await interaction.response.defer(ephemeral=True)
        guild = interaction.guild
        usuario = interaction.user
        tipo_ticket = select.values[0]

        try:
            categoria = discord.utils.get(guild.categories, name="🎫 TICKETS")
            if not categoria:
                categoria = await guild.create_category("🎫 TICKETS")

            # Verificar ticket existente
            for canal in categoria.text_channels:
                if canal.topic and str(usuario.id) in canal.topic:
                    embed_error = discord.Embed(
                        title="❌ Ya tienes un ticket abierto",
                        description=f"Ya tienes un ticket activo: {canal.mention}\n\nCierra ese ticket antes de abrir uno nuevo.",
                        color=COLORS["rojo"]
                    )
                    return await interaction.followup.send(embed=embed_error, ephemeral=True)

            # Crear canal de ticket
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(view_channel=False),
                usuario: discord.PermissionOverwrite(view_channel=True, send_messages=True, attach_files=True, read_message_history=True),
                guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True, manage_channels=True)
            }

            canal_ticket = await guild.create_text_channel(
                name=f"ticket-{usuario.name}",
                category=categoria,
                overwrites=overwrites,
                topic=f"Ticket de {usuario.id} | Tipo: {tipo_ticket} | Creado: {datetime.now().isoformat()}"
            )

            # Embed de bienvenida
            embed_bienvenida = discord.Embed(
                title=f"🎫 Ticket de {tipo_ticket.title()}",
                description=f"¡Hola {usuario.mention}!\n\n**Tipo de ticket:** {tipo_ticket.title()}\n**Creado:** <t:{int(datetime.now().timestamp())}:R>\n\nPor favor describe detalladamente tu problema o consulta. Un miembro del equipo de soporte te atenderá lo antes posible.\n\n**Para cerrar este ticket, escribe:** `!close`",
                color=COLORS["azul"],
                timestamp=datetime.now(timezone.utc)
            )
            embed_bienvenida.set_thumbnail(url=usuario.display_avatar.url)
            embed_bienvenida.set_footer(text=FOOTER_TEXT)

            await canal_ticket.send(content=f"{usuario.mention}", embed=embed_bienvenida)

            embed_confirmacion = discord.Embed(
                title="✅ Ticket Creado Exitosamente",
                description=f"Tu ticket ha sido creado: {canal_ticket.mention}\n\nUn miembro del staff te atenderá pronto.",
                color=COLORS["verde"]
            )
            embed_confirmacion.set_footer(text=FOOTER_TEXT)
            await interaction.followup.send(embed=embed_confirmacion, ephemeral=True)

            await enviar_log(guild, "🎫 Nuevo Ticket", f"{usuario.mention} creó un ticket de tipo: {tipo_ticket}", COLORS["verde"])

        except Exception as e:
            await interaction.followup.send("❌ Error al crear el ticket. Por favor contacta a un administrador.", ephemeral=True)

# ==================== EVENTOS DEL BOT ====================
@bot.event
async def on_ready():
    print(f"✅ Bot conectado exitosamente como {bot.user}")
    print(f"📊 Conectado a {len(bot.guilds)} servidores")

    # Registrar vistas persistentes
    bot.add_view(VistaAutoroles())
    bot.add_view(VistaTickets())
    print("✅ Vistas persistentes registradas correctamente")

@bot.event
async def on_message(message):
    if message.author.bot or not message.guild:
        return

    # Sistema de niveles
    user_id = str(message.author.id)
    if user_id not in niveles_data:
        niveles_data[user_id] = {"xp": 0, "lvl": 0}

    # Otorgar XP
    xp_ganado = random.randint(15, 25)
    niveles_data[user_id]["xp"] += xp_ganado

    # Verificar subida de nivel
    if niveles_data[user_id]["xp"] >= 100:
        niveles_data[user_id]["lvl"] += 1
        niveles_data[user_id]["xp"] = 0

        embed_nivel = discord.Embed(
            title="🎉 ¡FELICIDADES!",
            description=f"{message.author.mention} ha alcanzado el **Nivel {niveles_data[user_id]['lvl']}**",
            color=COLORS["oro"]
        )
        embed_nivel.set_thumbnail(url=message.author.display_avatar.url)
        embed_nivel.set_footer(text=FOOTER_TEXT)
        await message.channel.send(embed=embed_nivel, delete_after=15)

    guardar_base_datos("levels.json", niveles_data)
    await bot.process_commands(message)

# ==================== COMANDOS BÁSICOS ====================
@bot.command(name="ping")
async def comando_ping(ctx):
    latencia = round(bot.latency * 1000)
    embed = discord.Embed(
        title="🏓 ¡Pong!",
        description=f"Latencia del bot: **{latencia}ms**",
        color=COLORS["verde"]
    )
    embed.set_footer(text=FOOTER_TEXT)
    await ctx.send(embed=embed)

@bot.command(name="help", aliases=["ayuda", "comandos"])
async def comando_help(ctx):
    embed = discord.Embed(
        title="📖 CENTRO DE AYUDA - LISTA DE COMANDOS",
        description=f"Bot premium desarrollado por **{CREADOR}**\nPrefijo del bot: `!`",
        color=COLORS["azul"]
    )

    embed.add_field(
        name="🔹 Comandos Básicos",
        value="`ping` - Ver latencia del bot\n`help` - Mostrar esta ayuda\n`paybot` - Información de compra",
        inline=False
    )

    embed.add_field(
        name="📊 Comandos de Información",
        value="`serverinfo` - Info del servidor\n`userinfo [@usuario]` - Info de usuario\n`avatar [@usuario]` - Ver avatar\n`rank [@usuario]` - Ver nivel\n`top` - Top 10 niveles",
        inline=False
    )

    embed.add_field(
        name="💰 Sistema de Economía",
        value="`balance` - Ver tu dinero\n`daily` - Recompensa diaria\n`work` - Trabajar por dinero",
        inline=False
    )

    embed.add_field(
        name="🎲 Comandos de Diversión",
        value="`8ball <pregunta>` - Bola mágica\n`coinflip` - Lanzar moneda\n`dado` - Tirar dado",
        inline=False
    )

    embed.add_field(
        name="🔨 Comandos de Moderación",
        value="`ban` `unban` `kick` `mute` `unmute` `clear` `warn`",
        inline=False
    )

    embed.set_thumbnail(url=bot.user.display_avatar.url)
    embed.set_footer(text=FOOTER_TEXT)
    await ctx.send(embed=embed)

# ==================== COMANDO PAYBOT ====================
@bot.command(name="paybot")
async def comando_paybot(ctx):
    embed = discord.Embed(
        title="💎 SERVERPRUEBA BOT - VENTA OFICIAL",
        description="**El bot más completo y avanzado de Discord**\n\nDesarrollado 100% por **daddy_oofo**\nMás de 6 meses de desarrollo y mejoras continuas",
        color=COLORS["oro"]
    )

    embed.add_field(
        name="💰 PLANES Y PRECIOS DISPONIBLES",
        value="**🥉 PLAN BÁSICO - $15 USD**\n✓ Todos los comandos básicos\n✓ Sistema de moderación completo\n✓ Sistema de tickets avanzado\n✓ Sistema de autoroles\n✓ Soporte técnico por 1 mes\n✓ Instalación y configuración incluida\n\n**🥈 PLAN PREMIUM - $25 USD**\n✓ Todo lo del plan básico\n✓ Sistema de niveles y XP\n✓ Economía completa (balance, daily, work)\n✓ Sistema de advertencias\n✓ Logs automáticos detallados\n✓ Comandos de diversión\n✓ Soporte por 3 meses\n✓ 1 personalización gratuita\n\n**🥇 PLAN PRO - $40 USD**\n✓ Todo lo del plan premium\n✓ Código fuente completo\n✓ Personalización ilimitada\n✓ Soporte 24/7 de por vida\n✓ Actualizaciones gratuitas para siempre\n✓ Hosting incluido por 3 meses\n✓ Tutorial personalizado 1 a 1",
        inline=False
    )

    embed.add_field(
        name="✅ ¿QUÉ INCLUYE TU COMPRA?",
        value="• Instalación completa en tu servidor\n• Configuración de todos los canales\n• Creación automática de roles\n• Tutorial de uso detallado\n• Soporte técnico por Discord\n• Garantía de funcionamiento 100%",
        inline=True
    )

    embed.add_field(
        name="💳 MÉTODOS DE PAGO ACEPTADOS",
        value="• PayPal\n• Nequi\n• Bancolombia\n• Binance (USDT)\n• Zinli\n• Pago Móvil",
        inline=True
    )

    embed.add_field(
        name="📩 CONTACTO DIRECTO",
        value=f"**Discord:** `{CREADOR}`\n**Tiempo de respuesta:** Inmediato (5-10 min)\n**Entrega:** 5-10 minutos después del pago\n**Garantía:** Devolución si no funciona",
        inline=False
    )

    embed.set_thumbnail(url=bot.user.display_avatar.url)
    embed.set_image(url="https://i.imgur.com/8Km9tLL.png")
    embed.set_footer(text=f"{FOOTER_TEXT} | Más de 50 servidores confían en nosotros")

    await ctx.send(embed=embed)

# ==================== COMANDOS DE INFORMACIÓN ====================
@bot.command(name="serverinfo", aliases=["server"])
async def comando_serverinfo(ctx):
    guild = ctx.guild

    embed = discord.Embed(
        title=f"📊 Información Detallada de {guild.name}",
        description=guild.description or "Este servidor no tiene descripción",
        color=COLORS["azul"],
        timestamp=datetime.now(timezone.utc)
    )

    # Información básica
    embed.add_field(name="👑 Propietario", value=guild.owner.mention if guild.owner else "Desconocido", inline=True)
    embed.add_field(name="🆔 ID del Servidor", value=f"`{guild.id}`", inline=True)
    embed.add_field(name="📅 Fecha de Creación", value=f"<t:{int(guild.created_at.timestamp())}:D>\n<t:{int(guild.created_at.timestamp())}:R>", inline=True)

    # Miembros
    total_miembros = guild.member_count
    bots = len([m for m in guild.members if m.bot])
    humanos = total_miembros - bots
    en_linea = len([m for m in guild.members if m.status!= discord.Status.offline])

    embed.add_field(name="👥 Estadísticas de Miembros", value=f"**Total:** {total_miembros}\n**Usuarios:** {humanos}\n**Bots:** {bots}\n**En línea:** {en_linea}", inline=True)

    # Canales
    embed.add_field(name="💬 Canales", value=f"**Texto:** {len(guild.text_channels)}\n**Voz:** {len(guild.voice_channels)}\n**Categorías:** {len(guild.categories)}\n**Total:** {len(guild.channels)}", inline=True)

    # Otros
    embed.add_field(name="🎭 Roles", value=f"{len(guild.roles)} roles creados", inline=True)
    embed.add_field(name="😀 Emojis", value=f"{len(guild.emojis)}/{guild.emoji_limit}", inline=True)
    embed.add_field(name="🚀 Nivel de Boost", value=f"Nivel {guild.premium_tier}\n{guild.premium_subscription_count} boosts", inline=True)

    if guild.icon:
        embed.set_thumbnail(url=guild.icon.url)
    if guild.banner:
        embed.set_image(url=guild.banner.url)

    embed.set_footer(text=f"{FOOTER_TEXT} | Solicitado por {ctx.author}")
    await ctx.send(embed=embed)

@bot.command(name="userinfo", aliases=["ui", "user"])
async def comando_userinfo(ctx, miembro: discord.Member = None):
    usuario = miembro or ctx.author

    embed = discord.Embed(
        title=f"👤 Información de Usuario",
        description=f"Información detallada de {usuario.mention}",
        color=usuario.color,
        timestamp=datetime.now(timezone.utc)
    )

    embed.add_field(name="📛 Nombre de Usuario", value=f"{usuario}", inline=True)
    embed.add_field(name="🆔 ID", value=f"`{usuario.id}`", inline=True)
    embed.add_field(name="🤖 ¿Es Bot?", value="Sí" if usuario.bot else "No", inline=True)

    embed.add_field(name="📅 Cuenta Creada", value=f"<t:{int(usuario.created_at.timestamp())}:D>\n<t:{int(usuario.created_at.timestamp())}:R>", inline=True)
    embed.add_field(name="📥 Se Unió al Servidor", value=f"<t:{int(usuario.joined_at.timestamp())}:D>\n<t:{int(usuario.joined_at.timestamp())}:R>", inline=True)
    embed.add_field(name="🎭 Roles", value=f"{len(usuario.roles) - 1} roles", inline=True)

    embed.add_field(name="🔝 Rol Más Alto", value=usuario.top_role.mention, inline=False)

    embed.set_thumbnail(url=usuario.display_avatar.url)
    embed.set_footer(text=FOOTER_TEXT)

    await ctx.send(embed=embed)

@bot.command(name="avatar")
async def comando_avatar(ctx, miembro: discord.Member = None):
    usuario = miembro or ctx.author
    embed = discord.Embed(title=f"Avatar de {usuario.display_name}", color=usuario.color)
    embed.set_image(url=usuario.display_avatar.url)
    embed.set_footer(text=FOOTER_TEXT)
    await ctx.send(embed=embed)

# ==================== SISTEMA DE ECONOMÍA ====================
@bot.command(name="balance", aliases=["bal", "dinero"])
async def comando_balance(ctx, miembro: discord.Member = None):
    usuario = miembro or ctx.author
    user_id = str(usuario.id)

    # ARREGLO: Inicializar si no existe
    if user_id not in economia_data:
        economia_data[user_id] = 1000
        guardar_base_datos("economy.json", economia_data)

    balance_actual = economia_data[user_id]

    embed = discord.Embed(
        title=f"💰 Balance de {usuario.display_name}",
        description=f"**${balance_actual:,}** monedas",
        color=COLORS["oro"]
    )
    embed.set_thumbnail(url=usuario.display_avatar.url)
    embed.add_field(name="💵 Estado", value="Rico" if balance_actual > 5000 else "Clase media" if balance_actual > 2000 else "Necesita trabajar", inline=False)
    embed.set_footer(text=FOOTER_TEXT)
    await ctx.send(embed=embed)

@bot.command(name="daily")
async def comando_daily(ctx):
    user_id = str(ctx.author.id)
    ahora = datetime.now().timestamp()

    # ARREGLO: Verificar cooldown
    if user_id in daily_data:
        ultimo_reclamo = daily_data[user_id]
        tiempo_transcurrido = ahora - ultimo_reclamo

        if tiempo_transcurrido < 86400: # 24 horas
            tiempo_restante = 86400 - tiempo_transcurrido
            horas = int(tiempo_restante // 3600)
            minutos = int((tiempo_restante % 3600) // 60)

            embed_error = discord.Embed(
                title="⏰ Daily en Cooldown",
                description=f"Ya has reclamado tu recompensa diaria.\n\n**Tiempo restante:** {horas}h {minutos}m",
                color=COLORS["rojo"]
            )
            embed_error.set_footer(text=FOOTER_TEXT)
            return await ctx.send(embed=embed_error)

    # Inicializar economía si no existe
    if user_id not in economia_data:
        economia_data[user_id] = 1000

    # Dar recompensa
    cantidad = random.randint(500, 800)
    economia_data[user_id] += cantidad
    daily_data[user_id] = ahora

    # Guardar datos
    guardar_base_datos("economy.json", economia_data)
    guardar_base_datos("daily.json", daily_data)

    embed = discord.Embed(
        title="💵 Recompensa Diaria Reclamada",
        description=f"Has recibido **${cantidad}** monedas\n\n**Nuevo balance:** ${economia_data[user_id]:,}",
        color=COLORS["verde"]
    )
    embed.set_thumbnail(url=ctx.author.display_avatar.url)
    embed.set_footer(text=f"{FOOTER_TEXT} | Vuelve en 24 horas")
    await ctx.send(embed=embed)

@bot.command(name="work")
async def comando_work(ctx):
    user_id = str(ctx.author.id)

    if user_id not in economia_data:
        economia_data[user_id] = 1000

    trabajos = ["Programador", "Diseñador", "Streamer", "Youtuber", "Moderador", "Vendedor", "Cocinero"]
    trabajo = random.choice(trabajos)
    cantidad = random.randint(200, 400)

    economia_data[user_id] += cantidad
    guardar_base_datos("economy.json", economia_data)

    embed = discord.Embed(
        title="💼 Trabajo Completado",
        description=f"Trabajaste como **{trabajo}**\n\n**Ganancia:** ${cantidad}\n**Balance total:** ${economia_data[user_id]:,}",
        color=COLORS["verde"]
    )
    embed.set_footer(text=FOOTER_TEXT)
    await ctx.send(embed=embed)

# ==================== SISTEMA DE NIVELES ====================
@bot.command(name="rank")
async def comando_rank(ctx, miembro: discord.Member = None):
    usuario = miembro or ctx.author
    user_id = str(usuario.id)
    datos = niveles_data.get(user_id, {"xp": 0, "lvl": 0})

    embed = discord.Embed(
        title=f"📈 Nivel de {usuario.display_name}",
        color=usuario.color
    )
    embed.add_field(name="🏆 Nivel Actual", value=f"**{datos['lvl']}**", inline=True)
    embed.add_field(name="⭐ XP Actual", value=f"**{datos['xp']}/100**", inline=True)
    embed.add_field(name="💫 XP Total", value=f"**{datos['lvl'] * 100 + datos['xp']}**", inline=True)

    # Barra de progreso
    progreso = int((datos['xp'] / 100) * 10)
    barra = "█" * progreso + "░" * (10 - progreso)
    embed.add_field(name="📊 Progreso", value=f"`{barra}` {datos['xp']}%", inline=False)

    embed.set_thumbnail(url=usuario.display_avatar.url)
    embed.set_footer(text=FOOTER_TEXT)
    await ctx.send(embed=embed)

@bot.command(name="top", aliases=["leaderboard"])
async def comando_top(ctx):
    top_usuarios = sorted(niveles_data.items(), key=lambda x: x[1]["lvl"] * 100 + x[1]["xp"], reverse=True)[:10]

    descripcion = ""
    for i, (user_id, datos) in enumerate(top_usuarios, 1):
        try:
            usuario = await bot.fetch_user(int(user_id))
            medalla = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"**{i}.**"
            descripcion += f"{medalla} {usuario.name} - **Nivel {datos['lvl']}** ({datos['xp']} XP)\n"
        except:
            continue

    embed = discord.Embed(
        title="🏆 TOP 10 - Mejores Usuarios por Nivel",
        description=descripcion or "No hay datos disponibles",
        color=COLORS["oro"]
    )
    embed.set_thumbnail(url=ctx.guild.icon.url if ctx.guild.icon else None)
    embed.set_footer(text=FOOTER_TEXT)
    await ctx.send(embed=embed)

# ==================== COMANDOS DE DIVERSIÓN ====================
@bot.command(name="8ball")
async def comando_8ball(ctx, *, pregunta: str = None):
    if not pregunta:
        return await ctx.send("❌ Debes hacer una pregunta. Ejemplo: `!8ball ¿Voy a ser rico?`")

    respuestas = [
        "Sí, definitivamente", "Es cierto", "Sin duda alguna", "Sí", "Puedes confiar en ello",
        "Muy probable", "Las perspectivas son buenas", "Sí, en mi opinión",
        "No", "No cuentes con ello", "Muy dudoso", "Mis fuentes dicen que no",
        "Pregunta de nuevo más tarde", "No puedo predecir ahora", "Concéntrate y pregunta otra vez"
    ]

    embed = discord.Embed(title="🎱 Bola 8 Mágica", color=COLORS["morado"])
    embed.add_field(name="❓ Pregunta", value=pregunta, inline=False)
    embed.add_field(name="💬 Respuesta", value=random.choice(respuestas), inline=False)
    embed.set_footer(text=FOOTER_TEXT)
    await ctx.send(embed=embed)

@bot.command(name="coinflip")
async def comando_coinflip(ctx):
    resultado = random.choice(["Cara", "Cruz"])
    emoji = "🪙" if resultado == "Cara" else "🥈"

    embed = discord.Embed(title=f"{emoji} Lanzamiento de Moneda", description=f"**{resultado}**", color=COLORS["oro"])
    embed.set_footer(text=FOOTER_TEXT)
    await ctx.send(embed=embed)

@bot.command(name="dado")
async def comando_dado(ctx):
    numero = random.randint(1, 6)
    embed = discord.Embed(title="🎲 Tirada de Dado", description=f"Has sacado un **{numero}**", color=COLORS["azul"])
    embed.set_footer(text=FOOTER_TEXT)
    await ctx.send(embed=embed)

# ==================== MODERACIÓN ====================
def solo_admins():
    async def predicado(ctx):
        if ctx.channel.id!= CANAL_ADMINS:
            embed = discord.Embed(title="❌ Canal Incorrecto", description=f"Usa este comando en <#{CANAL_ADMINS}>", color=COLORS["rojo"])
            await ctx.send(embed=embed, delete_after=5)
            return False
        return True
    return commands.check(predicado)

@bot.command(name="ban")
@solo_admins()
@commands.has_permissions(ban_members=True)
async def comando_ban(ctx, miembro: discord.Member, tiempo: str = None, *, razon: str = "Sin razón especificada"):
    segundos = parsear_tiempo(tiempo) if tiempo else None

    if segundos is None and tiempo:
        razon = f"{tiempo} {razon}"
        tiempo = None

    try:
        await ctx.guild.ban(miembro, reason=f"{razon} | Moderador: {ctx.author}", delete_message_days=0)

        embed = discord.Embed(title="🔨 Usuario Baneado", color=COLORS["rojo"], timestamp=datetime.now(timezone.utc))
        embed.add_field(name="👤 Usuario", value=f"{miembro.mention}\n`{miembro}`", inline=True)
        embed.add_field(name="👮 Moderador", value=ctx.author.mention, inline=True)
        embed.add_field(name="📝 Razón", value=razon, inline=False)
        if tiempo:
            embed.add_field(name="⏰ Duración", value=f"{tiempo} (desbaneo automático)", inline=False)
        embed.set_thumbnail(url=miembro.display_avatar.url)
        embed.set_footer(text=FOOTER_TEXT)

        await ctx.send(embed=embed)
        await enviar_log(ctx.guild, "🔨 Ban", f"{miembro} baneado por {ctx.author}\nRazón: {razon}", COLORS["rojo"])

        if segundos:
            await asyncio.sleep(segundos)
            try:
                await ctx.guild.unban(miembro, reason="Ban temporal expirado")
                await enviar_log(ctx.guild, "✅ Unban Automático", f"{miembro} desbaneado automáticamente", COLORS["verde"])
            except:
                pass
    except Exception as e:
        await ctx.send(f"❌ Error al banear: {e}")

@bot.command(name="unban")
@solo_admins()
@commands.has_permissions(ban_members=True)
async def comando_unban(ctx, *, user_id: str):
    try:
        user_id = int(user_id.strip())
        usuario = await bot.fetch_user(user_id)
        await ctx.guild.unban(usuario, reason=f"Desbaneado por {ctx.author}")

        embed = discord.Embed(title="✅ Usuario Desbaneado", description=f"{usuario.mention} (`{usuario}`) ha sido desbaneado exitosamente", color=COLORS["verde"])
        embed.set_footer(text=FOOTER_TEXT)
        await ctx.send(embed=embed)
        await enviar_log(ctx.guild, "✅ Unban", f"{usuario} desbaneado por {ctx.author}", COLORS["verde"])
    except ValueError:
        await ctx.send("❌ ID inválido. Usa el ID numérico del usuario.")
    except Exception as e:
        await ctx.send(f"❌ Error: Usuario no encontrado o no está baneado")

@bot.command(name="kick")
@solo_admins()
@commands.has_permissions(kick_members=True)
async def comando_kick(ctx, miembro: discord.Member, *, razon: str = "Sin razón"):
    await miembro.kick(reason=razon)
    embed = discord.Embed(title="👢 Usuario Expulsado", description=f"{miembro.mention} ha sido expulsado\n**Razón:** {razon}", color=COLORS["naranja"])
    embed.set_footer(text=FOOTER_TEXT)
    await ctx.send(embed=embed)
    await enviar_log(ctx.guild, "👢 Kick", f"{miembro} expulsado por {ctx.author}", COLORS["naranja"])

@bot.command(name="mute")
@solo_admins()
@commands.has_permissions(moderate_members=True)
async def comando_mute(ctx, miembro: discord.Member, tiempo: str, *, razon: str = "Sin razón"):
    segundos = parsear_tiempo(tiempo)
    if not segundos:
        embed = discord.Embed(title="❌ Formato Incorrecto", description="Usa: `10s`, `10min`, `1h`, `1d`, `1w`, `1y`", color=COLORS["rojo"])
        return await ctx.send(embed=embed)

    duracion = datetime.now(timezone.utc) + timedelta(seconds=segundos)
    await miembro.timeout(duracion, reason=razon)

    embed = discord.Embed(title="🔇 Usuario Silenciado", color=COLORS["rojo"])
    embed.add_field(name="Usuario", value=miembro.mention, inline=True)
    embed.add_field(name="Duración", value=tiempo, inline=True)
    embed.add_field(name="Razón", value=razon, inline=False)
    embed.set_footer(text=FOOTER_TEXT)
    await ctx.send(embed=embed)
    await enviar_log(ctx.guild, "🔇 Mute", f"{miembro} muteado por {tiempo}", COLORS["rojo"])

@bot.command(name="unmute")
@solo_admins()
@commands.has_permissions(moderate_members=True)
async def comando_unmute(ctx, miembro: discord.Member):
    await miembro.timeout(None, reason=f"Desmuteado por {ctx.author}")
    embed = discord.Embed(title="🔊 Usuario Desmuteado", description=f"{miembro.mention} ha sido desmuteado", color=COLORS["verde"])
    embed.set_footer(text=FOOTER_TEXT)
    await ctx.send(embed=embed)

@bot.command(name="clear")
@solo_admins()
@commands.has_permissions(manage_messages=True)
async def comando_clear(ctx, cantidad: int = 5):
    if cantidad > 100:
        return await ctx.send("❌ No puedes borrar más de 100 mensajes")

    eliminados = await ctx.channel.purge(limit=cantidad + 1)
    embed = discord.Embed(title="🧹 Mensajes Eliminados", description=f"Se eliminaron **{len(eliminados) - 1}** mensajes", color=COLORS["verde"])
    msg = await ctx.send(embed=embed)
    await asyncio.sleep(3)
    await msg.delete()

# ==================== SETUP ====================
@bot.command(name="setup-autoroles")
@solo_admins()
@commands.has_permissions(administrator=True)
async def setup_autoroles(ctx):
    canal = bot.get_channel(CANAL_AUTOROLES)
    if not canal:
        return await ctx.send("❌ Canal de autoroles no encontrado")

    await canal.purge(limit=10)

    embed = discord.Embed(
        title="🎭 SISTEMA DE AUTOROLES PREMIUM",
        description="**¡Bienvenido al sistema de personalización de perfil!**\n\nPersonaliza tu experiencia en el servidor seleccionando tus preferencias. Los roles se asignan automáticamente al instante.\n\n**📌 INSTRUCCIONES DETALLADAS:**\n1️⃣ **País:** Selecciona tu país de origen para acceder a canales regionales\n2️⃣ **Edad:** Elige tu rango de edad para contenido apropiado\n3️⃣ **Plataformas:** Marca todas las plataformas donde juegas",
        color=COLORS["azul"]
    )
    embed.add_field(name="🌎 Países Disponibles", value=f"**{len(PAISES)} países** diferentes con banderas oficiales", inline=True)
    embed.add_field(name="🎂 Rangos de Edad", value="5 categorías: 13-15, 16-18, 19-21, 22-25, 26+", inline=True)
    embed.add_field(name="🎮 Plataformas", value="PC, Móvil, PlayStation, Xbox, Nintendo", inline=True)
    embed.set_image(url="https://i.imgur.com/3Q3Z3ZQ.png")
    embed.set_footer(text=FOOTER_TEXT)

    await canal.send(embed=embed, view=VistaAutoroles())

    embed_confirm = discord.Embed(title="✅ Panel Instalado", description=f"Panel de autoroles instalado en {canal.mention}", color=COLORS["verde"])
    await ctx.send(embed=embed_confirm)

@bot.command(name="setup-tickets")
@solo_admins()
@commands.has_permissions(administrator=True)
async def setup_tickets(ctx):
    canal = bot.get_channel(CANAL_TICKETS)
    if not canal:
        return await ctx.send("❌ Canal de tickets no encontrado")

    await canal.purge(limit=10)

    embed = discord.Embed(
        title="📩 CENTRO DE SOPORTE Y AYUDA",
        description="**¿Necesitas ayuda? ¡Estamos aquí para ayudarte 24/7!**\n\nNuestro equipo de soporte profesional está listo para resolver cualquier duda o problema que tengas.\n\n**⏰ Tiempo de respuesta promedio:** 5-15 minutos\n**📅 Horario de atención:** 24 horas, 7 días a la semana\n**👥 Equipo:** Moderadores y administradores capacitados",
        color=COLORS["azul"]
    )
    embed.add_field(name="🛠️ Soporte General", value="Ayuda con el servidor, bot, roles, canales y funciones generales", inline=True)
    embed.add_field(name="💰 Compras y Pagos", value="Información sobre VIP, beneficios premium, métodos de pago", inline=True)
    embed.add_field(name="🚨 Reportar Usuarios", value="Reportar comportamiento inapropiado, spam, toxicidad", inline=True)
    embed.add_field(name="⚖️ Apelaciones", value="Apelar sanciones, baneos, mutes o advertencias injustas", inline=True)
    embed.set_thumbnail(url=bot.user.display_avatar.url)
    embed.set_footer(text=FOOTER_TEXT)

    await canal.send(embed=embed, view=VistaTickets())

    embed_confirm = discord.Embed(title="✅ Panel Instalado", description=f"Panel de tickets instalado en {canal.mention}", color=COLORS["verde"])
    await ctx.send(embed=embed_confirm)

@bot.command(name="close")
async def comando_close(ctx):
    if "ticket-" in ctx.channel.name.lower():
        embed = discord.Embed(title="🔒 Cerrando Ticket", description="Este canal se eliminará en 5 segundos...\n\n¡Gracias por contactarnos!", color=COLORS["rojo"])
        embed.set_footer(text=FOOTER_TEXT)
        await ctx.send(embed=embed)
        await enviar_log(ctx.guild, "🔒 Ticket Cerrado", f"{ctx.channel.name} cerrado por {ctx.author}", COLORS["azul"])
        await asyncio.sleep(5)
        await ctx.channel.delete()
    else:
        await ctx.send("❌ Este comando solo funciona en canales de tickets")

@bot.command(name="admi")
@solo_admins()
async def comando_admi(ctx):
    embed = discord.Embed(title="🛡️ PANEL DE ADMINISTRACIÓN AVANZADO", description="Guía completa de comandos de moderación", color=COLORS["rojo"])
    embed.add_field(name="🔨 BAN", value="**Uso:** `!ban @usuario [tiempo] [razón]`\n**Tiempos:** 10s, 10min, 1h, 1d, 1w, 1y\n**Ejemplo:** `!ban @troll 7d spam`", inline=False)
    embed.add_field(name="✅ UNBAN", value="**Uso:** `!unban ID`**\n**Ejemplo:** `!unban 123456789`", inline=False)
    embed.add_field(name="👢 KICK", value="**Uso:** `!kick @usuario [razón]`", inline=False)
    embed.add_field(name="🔇 MUTE", value="**Uso:** `!mute @usuario [tiempo] [razón]`", inline=False)
    embed.add_field(name="🧹 CLEAR", value="**Uso:** `!clear [cantidad]`", inline=False)
    embed.set_footer(text=FOOTER_TEXT)
    await ctx.send(embed=embed)

# Ejecutar bot
bot.run(TOKEN)
