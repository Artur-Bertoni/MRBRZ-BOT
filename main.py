#######################
# Imports
#######################
import os
import discord
from discord.ext import commands
import instaloader
import asyncio
from datetime import datetime

#######################
# Configurações e Variáveis
#######################

TOKEN = os.getenv("TOKEN")
if not TOKEN:
    print("Error: TOKEN not found in secrets.")
    exit()

GUILD_ID = 1336381520977596518
CARGO_SUBS_TWITCH = 1336425874177790012
CARGO_MEMBROS_YOUTUBE = 1336425799359791174
CARGO_CAOS_NO_MULTIVERSO = 1342108534350811206
CARGO_TESTE = 1343947583260983338
LOG_CHANNEL = 1341465591667753060
INSTAGRAM_CHECK_INTERVAL = 10  # Intervalo de verificação em segundos

#######################
# Classes
#######################
class InstagramAccount:
    def __init__(self, username, channel_id):
        self.username = username
        self.channel_id = channel_id
        self.last_post_date = datetime.now()

instagram_accounts = {}
intents = discord.Intents.default()

#######################
# Funções de Background
#######################
async def check_instagram_posts():
    await bot.wait_until_ready()
    L = instaloader.Instaloader(max_connection_attempts=1)
    try:
        L.load_session_from_file("instagram_bot")
    except FileNotFoundError:
        # Primeira vez executando, fazer login se necessário
        pass
    
    L.context.sleep = True  # Adiciona delays entre requisições
    L.context.quiet = False  # Mostra logs detalhados
    
    while not bot.is_closed():
        for account in instagram_accounts.values():
            try:
                profile = instaloader.Profile.from_username(L.context, account.username)
    
    while not bot.is_closed():
        try:
            profile = instaloader.Profile.from_username(L.context, INSTAGRAM_USERNAME)
            
            # Verifica posts, reels e stories
            for post in profile.get_posts():
                if post.date > account.last_post_date:
                    channel = bot.get_channel(account.channel_id)
                    
                    post_type = "Reels" if post.is_video else "Post"
                    embed = discord.Embed(
                        title=f"Novo {post_type} de @{INSTAGRAM_USERNAME}",
                        description=post.caption[:4096] if post.caption else "Sem legenda",
                        color=0xE1306C,
                        url=f"https://instagram.com/p/{post.shortcode}"
                    )
                    
                    if post.is_video:
                        embed.set_image(url=post.thumbnail_url)
                        embed.add_field(name="Visualizações", value=str(post.video_view_count))
                    else:
                        embed.set_image(url=post.url)
                        embed.add_field(name="Likes", value=str(post.likes))
                    
                    embed.set_footer(text=post.date.strftime("%d/%m/%Y %H:%M"))
                    await channel.send(embed=embed)
                    account.last_post_date = post.date
                break
            
            # Verifica stories
            for story in profile.get_stories():
                if story.date > account.last_post_date:
                    channel = bot.get_channel(account.channel_id)
                    
                    embed = discord.Embed(
                        title=f"Novo Story de @{INSTAGRAM_USERNAME}",
                        color=0xE1306C
                    )
                    
                    if story.is_video:
                        embed.set_image(url=story.thumbnail_url)
                    else:
                        embed.set_image(url=story.url)
                    
                    embed.set_footer(text=story.date.strftime("%d/%m/%Y %H:%M"))
                    await channel.send(embed=embed)
                    account.last_post_date = story.date
                break
                
        except Exception as e:
            print(f"Erro ao verificar Instagram: {e}")
            
        await asyncio.sleep(INSTAGRAM_CHECK_INTERVAL)
intents.guilds = True
intents.guild_messages = True
intents.message_content = True


#######################
# Comandos
#######################
@bot.tree.command(
    name="instagram",
    description="Configura uma conta do Instagram para monitoramento",
    guild=discord.Object(id=GUILD_ID))
async def instagram(
    interaction: discord.Interaction,
    acao: str,
    username: str = None,
    canal: discord.TextChannel = None
):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("Você não tem permissão para usar este comando.", ephemeral=True)
        return

    if acao.lower() == "adicionar":
        if not username or not canal:
            await interaction.response.send_message("Você precisa especificar um username e um canal!", ephemeral=True)
            return
        
        instagram_accounts[username] = InstagramAccount(username, canal.id)
        await interaction.response.send_message(f"Conta @{username} configurada para postar no canal {canal.mention}")
    
    elif acao.lower() == "remover":
        if not username:
            await interaction.response.send_message("Você precisa especificar um username!", ephemeral=True)
            return
        
        if username in instagram_accounts:
            del instagram_accounts[username]
            await interaction.response.send_message(f"Conta @{username} removida do monitoramento")
        else:
            await interaction.response.send_message(f"Conta @{username} não estava sendo monitorada", ephemeral=True)
    
    elif acao.lower() == "listar":
        if not instagram_accounts:
            await interaction.response.send_message("Nenhuma conta está sendo monitorada", ephemeral=True)
            return
        
        accounts_list = "\n".join([f"@{username} -> <#{account.channel_id}>" 
                                 for username, account in instagram_accounts.items()])
        await interaction.response.send_message(f"Contas monitoradas:\n{accounts_list}")
    
    else:
        await interaction.response.send_message(
            "Ação inválida! Use:\n"
            "`/instagram adicionar [username] [#canal]` - Adiciona uma conta para monitorar\n"
            "`/instagram remover [username]` - Remove uma conta do monitoramento\n"
            "`/instagram listar` - Lista todas as contas monitoradas",
            ephemeral=True
        )

intents.members = True

bot = commands.Bot(command_prefix="/",
                  intents=intents,
                  application_id=os.getenv("APPLICATION_ID"))

#######################
# Eventos
#######################
@bot.event
async def on_ready():
    print(f"Bot conectado como: {bot.user}")
    await sync_commands()
    bot.loop.create_task(check_instagram_posts())

#######################
# Funções Utilitárias
#######################
async def send_embed(channel, title, description, thumbnail=None, color=0xFFF200):
    if isinstance(channel, discord.TextChannel):
        embed = discord.Embed(title=title, description=description, color=color)
        if thumbnail:
            embed.set_thumbnail(url=thumbnail)
        await channel.send(embed=embed)

async def send_role_change_embed(member, role_added):
    channel = bot.get_channel(LOG_CHANNEL)
    await send_embed(
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

        current_commands = [cmd.name for cmd in commands]
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
            print(f"Erro ao remover o cargo: {e}")

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

#######################
# Inicialização do Bot
#######################
bot.run(TOKEN)