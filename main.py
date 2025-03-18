#######################
# Imports e Setup Inicial
#######################
import json
import os

import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import Modal, TextInput, View, Button

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

TEMPLATES_DIR = "./embed_templates/"


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


@bot.tree.command(
    name="embed",
    description="Cria e envia um embed baseado em um template.",
    guild=discord.Object(id=GUILD_ID)
)
@app_commands.describe(
    template="Escolha entre: event, announcement, championship ou patchnote",
    notificacao="Mensagem de notificação personalizada",
    titulo="Título que será exibido no embed",
    descricao="Texto descritivo que será exibido no corpo do embed",
    canal="Canal onde o embed será enviado",
    imagem="URL para a imagem no corpo do embed (opcional)",
)
async def embed(
        interaction: discord.Interaction,
        template: str,
        notificacao: str,
        titulo: str,
        descricao: str,
        canal: discord.TextChannel,
        imagem: str = None,
):
    try:
        template_data = load_template(template)
    except FileNotFoundError:
        await interaction.response.send_message(
            f"❌ Template '{template}' não encontrado. Certifique-se de usar: event, announcement, championship, ou patchnote.",
            ephemeral=True,
        )
        return
    except Exception as e:
        await interaction.response.send_message(f"❌ Erro ao carregar o template: {e}", ephemeral=True)
        return

    template_data["content"] = template_data["content"].replace("[Notificação]", notificacao)
    embed_data = template_data["embeds"][0]
    embed_data["description"] = embed_data["description"].replace("[Título]", titulo).replace("[Descrição]", descricao)
    if imagem:
        embed_data["image"] = {"url": imagem}

    embed = discord.Embed.from_dict(embed_data)

    await interaction.response.send_message(
        content=f"**Pré-visualização do Embed:**\nAqui está como ficará sua mensagem no canal {canal.mention}:",
        embed=embed,
        ephemeral=True,
    )

    class ConfirmView(View):
        def __init__(self, *, timeout=30):
            super().__init__(timeout=timeout)
            self.value = None
            self.action = None

        @discord.ui.button(label="Sim", style=discord.ButtonStyle.green)
        async def confirm(self, interaction: discord.Interaction, button: Button):
            self.value = True
            self.action = "confirm"
            await canal.send(embed=embed)
            await interaction.response.edit_message(content="✅ Embed enviado com sucesso!", view=None)
            self.stop()

        @discord.ui.button(label="Não", style=discord.ButtonStyle.red)
        async def cancel(self, interaction: discord.Interaction, button: Button):
            self.value = False
            self.action = "cancel"
            await interaction.response.edit_message(content="❌ Envio do embed foi cancelado.", view=None)
            self.stop()

        @discord.ui.button(label="Editar", style=discord.ButtonStyle.blurple)
        async def edit(self, interaction: discord.Interaction, button: Button):
            self.value = False
            self.action = "edit"
            await interaction.response.send_modal(EditModal(template, notificacao, titulo, descricao, canal, imagem))
            self.stop()

    class EditModal(Modal, title="Editar Informações do Embed"):
        def __init__(self, template, notificacao, titulo, descricao, canal, imagem):
            super().__init__()
            self.template = template
            self.notificacao = notificacao
            self.titulo = titulo
            self.descricao = descricao
            self.canal = canal
            self.imagem = imagem

            self.add_item(TextInput(label="Template", default=template, required=True))
            self.add_item(
                TextInput(label="Notificação", default=notificacao, required=True, style=discord.TextStyle.paragraph))
            self.add_item(TextInput(label="Título", default=titulo, required=True))
            self.add_item(
                TextInput(label="Descrição", default=descricao, required=True, style=discord.TextStyle.paragraph))
            self.add_item(TextInput(label="Canal ID", default=str(canal.id), required=True))

        async def on_submit(self, interaction: discord.Interaction):
            new_template = self.children[0].value
            new_notificacao = self.children[1].value
            new_titulo = self.children[2].value
            new_descricao = self.children[3].value
            new_canal_id = int(self.children[4].value)

            new_canal = interaction.guild.get_channel(new_canal_id)

            class EditImageView(View):
                @discord.ui.button(label="Sim", style=discord.ButtonStyle.green)
                async def edit_image_yes(self, inner_interaction: discord.Interaction, button: Button):
                    await inner_interaction.response.send_modal(EditImageModal(
                        new_template, new_notificacao, new_titulo, new_descricao, new_canal
                    ))
                    self.stop()

                @discord.ui.button(label="Não", style=discord.ButtonStyle.red)
                async def edit_image_no(self, inner_interaction: discord.Interaction, button: Button):
                    await embed(
                        inner_interaction, new_template, new_notificacao, new_titulo, new_descricao, new_canal, None
                    )
                    self.stop()

            view = EditImageView()
            await interaction.response.send_message(
                "Deseja adicionar ou editar uma imagem para este embed?",
                view=view,
                ephemeral=True,
            )

    class EditImageModal(Modal, title="Editar Imagem do Embed"):
        def __init__(self, template, notificacao, titulo, descricao, canal):
            super().__init__()
            self.add_item(TextInput(label="URL da Imagem", required=False, placeholder="Digite a URL da imagem"))
            self.template = template
            self.notificacao = notificacao
            self.titulo = titulo
            self.descricao = descricao
            self.canal = canal

        async def on_submit(self, interaction: discord.Interaction):
            new_imagem = self.children[0].value if self.children[0].value else None

            await embed(
                interaction, self.template, self.notificacao, self.titulo, self.descricao, self.canal, new_imagem
            )

    view = ConfirmView()
    await interaction.followup.send(
        content="Você deseja enviar este embed?",
        view=view,
        ephemeral=True,
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

    await update_member_roles(after, before_roles=before.roles, after_roles=after.roles)


#######################
# Funções Utilitárias
#######################
async def send_embed(channel, title, description, thumbnail=None, color=0xFFF200):
    if isinstance(channel, discord.TextChannel):
        embed = discord.Embed(title=title, description=description, color=color)
        if thumbnail:
            embed.set_thumbnail(url=thumbnail)
        await channel.send(embed=embed)


async def send_role_change_embed(member, role_changed, is_addition, trigger_to_action):
    channel = bot.get_channel(LOG_CHANNEL)

    if role_changed is None:
        action = "adicionado ao(à)" if is_addition else "removido do(a)"
        description = (
            f"O cargo <@&{CARGO_BEYONDERS}> foi {action} usuário(a) {member.mention}."
        )
    else:
        action = "adicionado ao(à)" if is_addition else "removido do(a)"
        reason = (
            f"após ter o cargo <@&{role_changed.id}> {trigger_to_action}"
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


async def update_member_roles(member, before_roles=None, after_roles=None):
    monitored_roles = {CARGO_SUBS_TWITCH, CARGO_MEMBROS_YOUTUBE, CARGO_TESTE}
    role_beyonders = member.guild.get_role(CARGO_BEYONDERS)

    if not role_beyonders:
        return

    if before_roles is None or after_roles is None:
        before_roles = member.roles
        after_roles = member.roles

    added_roles = [role for role in after_roles if role not in before_roles]
    removed_roles = [role for role in before_roles if role not in after_roles]

    try:
        if any(role.id in monitored_roles for role in after_roles):
            if role_beyonders in after_roles:
                role_added = next((role for role in added_roles if role.id in monitored_roles), None)
                await member.remove_roles(role_beyonders)
                await send_role_change_embed(member, role_added, is_addition=False, trigger_to_action="adicionado")
        else:
            if role_beyonders not in after_roles:
                role_removed = next((role for role in removed_roles if role.id in monitored_roles), None)
                await member.add_roles(role_beyonders)
                await send_role_change_embed(
                    member,
                    role_removed,
                    is_addition=True,
                    trigger_to_action="removido"
                )
    except Exception as e:
        print(f"Erro ao atualizar o cargo de {member.display_name}: {e}")


def load_template(template_name: str):
    """Carrega os templates JSON de um arquivo"""
    with open(os.path.join(TEMPLATES_DIR, f"{template_name}_template.json"), "r", encoding="utf-8") as file:
        return json.load(file)


#######################
# Inicialização do Bot
#######################
bot.run(TOKEN)
