import os
import discord
from discord.ext import commands

# Discord Bot Token
TOKEN = os.getenv("TOKEN")
if TOKEN is None:
    print(
        "Error: TOKEN not found in secrets. Configure it in the Secrets tab.")
    exit()

# Guild and Role IDs
GUILD_ID = 1336381520977596518
CARGO_SUBS_TWITCH = 1336425874177790012
CARGO_MEMBROS_YOUTUBE = 1336425799359791174
CARGO_CAOS_NO_MULTIVERSO = 1342108534350811206
CARGO_TESTE = 1343947583260983338
LOG_CHANNEL = 1341465591667753060

# Discord Intents
intents = discord.Intents.default()
intents.guilds = True
intents.guild_messages = True
intents.message_content = True
intents.members = True

# Create Discord Bot
bot = commands.Bot(command_prefix="/",
                   intents=intents,
                   application_id=os.getenv("APPLICATION_ID"))


# Bot On Ready Event
@bot.event
async def on_ready():
    print(f"Bot conectado como: {bot.user}")
    await sync_commands()


# Send Embed Function
async def send_embed(channel,
                     title,
                     description,
                     thumbnail=None,
                     color=0xFFF200):
    if isinstance(channel, discord.TextChannel):
        embed = discord.Embed(title=title,
                              description=description,
                              color=color)
        if thumbnail:
            embed.set_thumbnail(url=thumbnail)
        await channel.send(embed=embed)
    else:
        print("O canal não é um Canal de Texto ou não foi achado!")


# Send Role Change Embed Function
async def send_role_change_embed(member, role_added):
    channel = bot.get_channel(LOG_CHANNEL)
    await send_embed(
        channel,
        title=f"**Cargo alterado para {member.display_name}**",
        description=
        (f"Cargo <@&{CARGO_CAOS_NO_MULTIVERSO}> removido do(a) usuário(a) {member.mention} "
         f"após receber o cargo <@&{role_added.id}>"),
        thumbnail=member.avatar.url,
    )


# Sync Commands Function
async def sync_commands():
    try:
        # Limpa todos os comandos primeiro
        bot.tree.clear_commands(guild=None)
        bot.tree.clear_commands(guild=discord.Object(id=GUILD_ID))
        await bot.tree.sync()
        await bot.tree.sync(guild=discord.Object(id=GUILD_ID))

        # Registra os comandos novamente
        await bot.tree.sync()
        await bot.tree.sync(guild=discord.Object(id=GUILD_ID))

        # Obtém lista de comandos atual
        current_commands = [cmd.name for cmd in bot.tree.get_commands()]

        # Prepara mensagem de log
        log_message = "Comandos sincronizados com sucesso!\n"
        if current_commands:
            log_message += f"Comandos ativos: {', '.join(current_commands)}"
        else:
            log_message += "Nenhum comando ativo."

        channel = bot.get_channel(LOG_CHANNEL)
        await send_embed(channel,
                         title="**Comandos Sincronizados**",
                         description=log_message)
    except Exception as e:
        print(f"Erro ao sincronizar comandos: {e}")
        channel = bot.get_channel(LOG_CHANNEL)
        await send_embed(
            channel,
            title="**Erro na Sincronização**",
            description=f"Ocorreu um erro ao sincronizar os comandos: {str(e)}",
            color=0xFF0000)


# On Member Update Event
@bot.event
async def on_member_update(before, after):
    if before.guild.id != GUILD_ID:
        print("Guild ID diferente, ignorando...")
        return

    monitored_roles = [CARGO_SUBS_TWITCH, CARGO_MEMBROS_YOUTUBE, CARGO_TESTE]
    has_monitored_role = any(role.id in monitored_roles
                             for role in after.roles)

    if has_monitored_role:
        try:
            role_caos = after.guild.get_role(CARGO_CAOS_NO_MULTIVERSO)
            if role_caos and role_caos in after.roles:
                # Find the newly added role
                role_added = next(
                    (role for role in after.roles if role not in before.roles),
                    None)
                await after.remove_roles(role_caos)
                await send_role_change_embed(after, role_added)
        except Exception as e:
            print(f"Erro ao remover o cargo: {e}")


# Ping Command
@bot.tree.command(name="ping",
                  description="Mostra a latência do bot",
                  extras={"id": "ping_command"})
async def ping(interaction):
    # Calcula a latência do WebSocket
    websocket_latency = round(bot.latency * 1000)

    # Envia mensagem inicial
    await interaction.response.send_message("Calculando latência...")

    # Calcula a latência da API
    start_time = interaction.created_at
    end_time = discord.utils.utcnow()
    api_latency = round((end_time - start_time).total_seconds() * 1000)

    # Usa a função send_embed para enviar o resultado
    await send_embed(
        interaction.channel,
        title="🏓 Pong!",
        description=
        f"**Gateway (WebSocket):** `{websocket_latency}ms`\n**API:** `{api_latency}ms`"
    )

    # Remove a mensagem inicial
    await interaction.delete_original_response()


# Run Discord Bot
bot.run(TOKEN)
