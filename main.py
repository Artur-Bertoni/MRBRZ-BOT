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
    await bot.tree.sync()
    added_commands = []
    removed_commands = []
    original_commands = bot.tree.get_commands()
    await bot.tree.sync()
    updated_commands = bot.tree.get_commands()

    # Compare commands based on their IDs
    for updated_command in updated_commands:
        if updated_command.extras.get('id') not in [
                c.extras.get('id') for c in original_commands
        ]:
            added_commands.append(updated_command.name)

    for original_command in original_commands:
        if original_command.extras.get('id') not in [
                c.extras.get('id') for c in updated_commands
        ]:
            removed_commands.append(original_command.name)

    log_message = "Comandos sincronizados com sucesso!\n"
    if added_commands:
        log_message += f"Comandos adicionados: {', '.join(added_commands)}\n"
    if removed_commands:
        log_message += f"Comandos removidos: {', '.join(removed_commands)}\n"

    channel = bot.get_channel(LOG_CHANNEL)
    await send_embed(channel,
                     title="**Comandos Sincronizados**",
                     description=log_message)


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


# Test Command
@bot.tree.command(name="teste",
                  description="Comando de teste para validar o bot",
                  extras={"id": "teste_command"})
async def teste(interaction):
    if interaction.user.guild_permissions.administrator:
        await interaction.response.send_message(
            "Este comando é um comando de teste!")
    else:
        await interaction.response.send_message(
            "Você não tem permissão para usar este comando.")


# Run Discord Bot
bot.run(TOKEN)
