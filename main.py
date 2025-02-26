#######################
# Imports e Setup Inicial
#######################
import os
import discord
import asyncio
from discord.ext import commands
from datetime import datetime
from instagram_manager import InstagramManager

# Configuração inicial do bot
intents = discord.Intents.default()
intents.guilds = True
intents.guild_messages = True
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="/",
                  intents=intents,
                  application_id=os.getenv("APPLICATION_ID"))

# Configuração do Instagram Manager
instagram_manager = None


#######################
# Configurações e Variáveis
#######################

TOKEN = os.getenv("TOKEN")
if not TOKEN:
    print("Erro: TOKEN não encontrado nas variáveis de ambiente.")
    exit()

GUILD_ID = 1336381520977596518
CARGO_SUBS_TWITCH = 1336425874177790012
CARGO_MEMBROS_YOUTUBE = 1336425799359791174
CARGO_CAOS_NO_MULTIVERSO = 1342108534350811206
CARGO_TESTE = 1343947583260983338
LOG_CHANNEL = 1341465591667753060


#######################
# Comandos
#######################

# /ping
@bot.tree.command(
    name="ping",
    description="Mostra a latência do bot",
    guild=discord.Object(id=GUILD_ID))
async def ping(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("Você não tem permissão para usar este comando.", ephemeral=True)
        return

    websocket_latency = round(bot.latency * 1000)
    await interaction.response.send_message("Calculando latência...")
    api_latency = round((discord.utils.utcnow() - interaction.created_at).total_seconds() * 1000)

    send_embed(
        interaction.channel,
        title="🏓 Pong!",
        description=f"**Gateway (WebSocket):** `{websocket_latency}ms`\n**API:** `{api_latency}ms`"
    )
    await interaction.delete_original_response()

# /instagram_add
@bot.tree.command(
    name="instagram_add",
    description="Adiciona uma conta do Instagram para monitoramento",
    guild=discord.Object(id=GUILD_ID))
async def instagram_add(interaction: discord.Interaction, username: str, channel: discord.TextChannel):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("Você não tem permissão para usar este comando.", ephemeral=True)
        return

    success = await instagram_manager.add_account(username, channel.id)
    if success:
        await interaction.response.send_message(f"Conta @{username} adicionada com sucesso para o canal {channel.mention}")
    else:
        await interaction.response.send_message(f"Erro ao adicionar a conta @{username}", ephemeral=True)

# /instagram_remove
@bot.tree.command(
    name="instagram_remove",
    description="Remove uma conta do Instagram do monitoramento",
    guild=discord.Object(id=GUILD_ID))
async def instagram_remove(interaction: discord.Interaction, username: str, channel: discord.TextChannel):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("Você não tem permissão para usar este comando.", ephemeral=True)
        return

    success = await instagram_manager.remove_account(username, channel.id)
    if success:
        await interaction.response.send_message(f"Conta @{username} removida com sucesso do canal {channel.mention}")
    else:
        await interaction.response.send_message(f"Erro ao remover a conta @{username}", ephemeral=True)

# /instagram_check
@bot.tree.command(
    name="instagram_check",
    description="Verifica atualizações manualmente",
    guild=discord.Object(id=GUILD_ID))
async def instagram_check(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("Você não tem permissão para usar este comando.", ephemeral=True)
        return

    await interaction.response.send_message("Verificando atualizações...")
    await instagram_manager.check_all_accounts()
    await interaction.edit_original_response(content="Verificação manual concluída!")

# /instagram_sync
@bot.tree.command(
    name="instagram_sync",
    description="Sincroniza as contas do Instagram",
    guild=discord.Object(id=GUILD_ID))
async def instagram_sync(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("Você não tem permissão para usar este comando.", ephemeral=True)
        return

    instagram_manager.load_accounts()
    await interaction.response.send_message("Contas do Instagram sincronizadas com sucesso!")

#######################
# Eventos
#######################
@bot.event
async def on_ready():
    success_msg = f"Bot conectado com sucesso como: {bot.user}"
    print(success_msg)
    send_embed(title="Bot Conectado", description=success_msg, color=0x00FF00)
    global instagram_manager
    instagram_manager = InstagramManager(bot)
    bot.loop.create_task(check_instagram_updates())
    await sync_commands()

async def check_instagram_updates():
    while True:
        await instagram_manager.check_all_accounts()
        await asyncio.sleep(300)  # Verificar a cada 5 minutos

@bot.event
async def on_member_update(before, after):
    if before.guild.id != GUILD_ID:
        return

    monitored_roles = [CARGO_SUBS_TWITCH, CARGO_MEMBROS_YOUTUBE, CARGO_TESTE]
    if any(role.id in monitored_roles for role in after.roles):
        try:
            role_caos = after.guild.get_role(CARGO_CAOS_NO_MULTIVERSO)
            if role_caos and role_caos in after.roles:
                role_added = next((role for role in after.roles if role not in before.roles), None)
                await after.remove_roles(role_caos)
                await send_role_change_embed(after, role_added)
        except Exception as e:
            error_msg = f"Erro ao tentar remover o cargo: {e}"
    print(error_msg)
    send_embed(title="Erro", description=error_msg, color=0xFF0000)


#######################
# Funções Utilitárias
#######################
def send_embed(channel=None, title=None, description=None, thumbnail=None, color=0xFFF200):
    if channel is None:
        channel = bot.get_channel(LOG_CHANNEL)
    if isinstance(channel, (discord.TextChannel, discord.abc.Messageable)):
        embed = discord.Embed(title=title, description=description, color=color)
        if thumbnail:
            embed.set_thumbnail(url=thumbnail)
        await channel.send(embed=embed)

async def send_role_change_embed(member, role_added):
    channel = bot.get_channel(LOG_CHANNEL)
    send_embed(
        channel,
        title=f"**Cargo alterado para {member.display_name}**",
        description=f"Cargo <@&{CARGO_CAOS_NO_MULTIVERSO}> removido do(a) usuário(a) {member.mention} após receber o cargo <@&{role_added.id}>",
        thumbnail=member.avatar.url,
    )

async def sync_commands():
    try:
        guild = discord.Object(id=GUILD_ID)
        bot.tree.copy_global_to(guild=guild)
        commands = await bot.tree.sync(guild=guild)

        current_commands = [f"`{cmd.name}`" for cmd in commands]
        log_message = "Comandos sincronizados com sucesso!\n"
        log_message += f"Comandos ativos: {', '.join(current_commands)}" if current_commands else "Nenhum comando ativo no momento."

        send_embed(bot.get_channel(LOG_CHANNEL),
                        title="**Comandos Sincronizados**",
                        description=log_message)

    except Exception as e:
        send_embed(
            bot.get_channel(LOG_CHANNEL),
            title="**Erro na Sincronização**",
            description=f"Ocorreu um erro ao sincronizar os comandos: {str(e)}",
            color=0xFF0000)


#######################
# Inicialização do Bot
#######################
bot.run(TOKEN)