import os
import discord
from discord.ext import commands
import instaloader
import asyncio
from datetime import datetime

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
INSTAGRAM_CHANNEL = 1341465591667753060  # Altere para o ID do canal desejado
INSTAGRAM_USERNAME = "seu_usuario"  # Altere para o usuário que deseja monitorar
INSTAGRAM_CHECK_INTERVAL = 300  # Intervalo de verificação em segundos (5 minutos)

intents = discord.Intents.default()

async def check_instagram_posts():
    await bot.wait_until_ready()
    L = instaloader.Instaloader()
    last_post_date = datetime.now()
    
    while not bot.is_closed():
        try:
            profile = instaloader.Profile.from_username(L.context, INSTAGRAM_USERNAME)
            
            # Verifica posts, reels e stories
            for post in profile.get_posts():
                if post.date > last_post_date:
                    channel = bot.get_channel(INSTAGRAM_CHANNEL)
                    
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
                    last_post_date = post.date
                break
            
            # Verifica stories
            for story in profile.get_stories():
                if story.date > last_post_date:
                    channel = bot.get_channel(INSTAGRAM_CHANNEL)
                    
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
                    last_post_date = story.date
                break
                
        except Exception as e:
            print(f"Erro ao verificar Instagram: {e}")
            
        await asyncio.sleep(INSTAGRAM_CHECK_INTERVAL)
intents.guilds = True
intents.guild_messages = True
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="/",
                  intents=intents,
                  application_id=os.getenv("APPLICATION_ID"))

@bot.event
async def on_ready():
    print(f"Bot conectado como: {bot.user}")
    await sync_commands()
    bot.loop.create_task(check_instagram_posts())

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

bot.run(TOKEN)