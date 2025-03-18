#######################
# Imports e Setup Inicial
#######################
import os

import discord
from discord.ext import commands

intents = discord.Intents.default()
intents.guilds = True
intents.guild_messages = True
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="/",
                   intents=intents,
                   application_id=os.getenv("APPLICATION_ID"))

#######################
# Configurações e Variáveis
#######################

TOKEN = os.getenv("TOKEN")
if not TOKEN:
    print("Erro: TOKEN não encontrado nos secrets.")
    exit()

GUILD_ID = 1336381520977596518
CARGO_SUBS_TWITCH = 1336425874177790012
CARGO_MEMBROS_YOUTUBE = 1336425799359791174
CARGO_BEYONDERS = 1342108534350811206
CARGO_TESTE = 1343947583260983338
LOG_CHANNEL = 1341465591667753060


#######################
# Comandos
#######################
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

    await send_embed(
        interaction.channel,
        title="🏓 Pong!",
        description=f"**Gateway (WebSocket):** `{websocket_latency}ms`\n**API:** `{api_latency}ms`"
    )
    await interaction.delete_original_response()


@bot.tree.command(
    name="atualizar_cargos",
    description="Atualiza manualmente os cargos de todos os membros do servidor.",
    guild=discord.Object(id=GUILD_ID))
async def atualizar_cargos(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message(
            "Você não tem permissão para usar este comando.", ephemeral=True
        )
        return

    await interaction.response.send_message(
        "🔄 Iniciando atualização de cargos para todos os membros...",
        ephemeral=True
    )

    guild = interaction.guild
    if not guild:
        await interaction.followup.send("Erro: Servidor não encontrado!")
        return

    updated_count = 0

    for member in guild.members:
        if not member.bot:
            await update_member_roles(member)
            updated_count += 1

    await interaction.followup.send(
        f"✅ Atualização de cargos concluída! Total de membros processados: {updated_count}."
    )


#######################
# Eventos
#######################
@bot.event
async def on_ready():
    print(f"Bot conectado com sucesso como: {bot.user}")
    await sync_commands()


@bot.event
async def on_member_update(before, after):
    if before.guild.id != GUILD_ID:
        return

    await update_member_roles(after)


#######################
# Funções Utilitárias
#######################
async def send_embed(channel, title, description, thumbnail=None, color=0xFFF200):
    if isinstance(channel, discord.TextChannel):
        embed = discord.Embed(title=title, description=description, color=color)
        if thumbnail:
            embed.set_thumbnail(url=thumbnail)
        await channel.send(embed=embed)


async def send_role_change_embed(member, role_changed, is_addition):
    channel = bot.get_channel(LOG_CHANNEL)

    if role_changed is None:
        action = "adicionado ao(à)" if is_addition else "removido do(a)"
        description = (
            f"O cargo <@&{CARGO_BEYONDERS}> foi {action} para o(a) usuário(a) {member.mention}."
        )
    else:
        action = "adicionado ao(à)" if is_addition else "removido do(a)"
        reason = (
            f"após ter o cargo <@&{role_changed.id}> removido"
            if is_addition
            else f"após receber o cargo <@&{role_changed.id}>"
        )
        description = f"Cargo <@&{CARGO_BEYONDERS}> {action} usuário(a) {member.mention} {reason}"

    await send_embed(
        channel=channel,
        title=f"**Cargo alterado para {member.display_name}**",
        description=description,
        thumbnail=member.avatar.url,
    )


async def sync_commands():
    try:
        guild = discord.Object(id=GUILD_ID)
        bot.tree.copy_global_to(guild=guild)
        all_commands = await bot.tree.sync(guild=guild)

        current_commands = [f"`{cmd.name}`" for cmd in all_commands]
        log_message = "Comandos sincronizados com sucesso!\n"
        log_message += f"Comandos ativos: {', '.join(current_commands)}" if current_commands else "Nenhum comando ativo no momento."

        await send_embed(bot.get_channel(LOG_CHANNEL),
                         title="**Comandos Sincronizados**",
                         description=log_message)

    except Exception as e:
        await send_embed(
            bot.get_channel(LOG_CHANNEL),
            title="**Erro na Sincronização**",
            description=f"Ocorreu um erro ao sincronizar os comandos: {str(e)}",
            color=0xFF0000)


async def update_member_roles(member):
    monitored_roles = {CARGO_SUBS_TWITCH, CARGO_MEMBROS_YOUTUBE}
    role_beyonders = member.guild.get_role(CARGO_BEYONDERS)

    if not role_beyonders:
        return

    try:
        if any(role.id in monitored_roles for role in member.roles):
            if role_beyonders in member.roles:
                role_added = next((role for role in member.roles if role.id in monitored_roles), None)
                await member.remove_roles(role_beyonders)
                await send_role_change_embed(member, role_added, is_addition=True)
        else:
            if role_beyonders not in member.roles:
                role_removed = next((role for role in member.roles if role.id in monitored_roles), None)
                await member.add_roles(role_beyonders)
                await send_role_change_embed(member, role_removed, is_addition=False)
    except Exception as e:
        print(f"Erro ao atualizar o cargo de {member.display_name}: {e}")


#######################
# Inicialização do Bot
#######################
bot.run(TOKEN)
