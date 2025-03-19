#######################
# Imports e Setup Inicial
#######################
import json
import os

import discord
from discord.ext import commands
from discord.ui import View, Button, Modal, TextInput

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
CARGO_BOT = 1338657713797857331
CARGO_STAFF = 1336381521111814158
CARGO_BEYONDERS = 1342108534350811206
CARGO_TESTE = 1343947583260983338

TEMPLATES_DIR = "./embed_templates/"

CHANNEL_LOG_APP = 1341465591667753060
CHANNEL_EVENT = 1336666506146349078
CHANNEL_ANNOUNCEMENT = 1336666125257146440
CHANNEL_CHAMPIONSHIP = 1342271005778776064
CHANNEL_PATCHNOTE = 1351534926339506236


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
    description="Monte e personalize um embed com botões interativos.",
    guild=discord.Object(id=GUILD_ID),
)
async def embed(interaction: discord.Interaction):
    class EmbedView(View):
        def __init__(self, *, timeout=300):
            super().__init__(timeout=timeout)
            self.embed_data = {
                "template": None,
                "notificacao": None,
                "titulo": None,
                "descricao": None,
                "canal_envio": None,
                "imagem": None,
            }
            self.template_content = None
            self.update_buttons()

        def update_buttons(self):
            for child in self.children:
                if child.label.__contains__("Mensagem de Notificação"):
                    child.disabled = self.embed_data["template"] == "patchnote" or self.embed_data["template"] is None
                    child.label = "Editar Mensagem de Notificação" if self.embed_data.get(
                        "notificacao") else "Definir Mensagem de Notificação *"
                elif child.label == "Definir Template *":
                    continue
                elif child.label.__contains__("Cancelar"):
                    continue
                elif child.label.__contains__("Enviar"):
                    child.disabled = self.embed_data["template"] is None or self.embed_data["titulo"] is None or \
                                     self.embed_data["descricao"] is None
                elif child.label.__contains__("Imagem"):
                    child.label = "Editar Imagem" if self.embed_data.get("imagem") else "Adicionar Imagem"
                    child.disabled = self.embed_data["template"] is None
                elif child.label.__contains__("Título"):
                    child.label = "Editar Título" if self.embed_data.get("titulo") else "Definir Título *"
                    child.disabled = self.embed_data["template"] is None
                elif child.label.__contains__("Descrição"):
                    child.label = "Editar Descrição" if self.embed_data.get("descricao") else "Definir Descrição *"
                    child.disabled = self.embed_data["template"] is None
                else:
                    key = child.label.split(" ")[-1].lower().strip("*")
                    child.label = f"Editar {key.capitalize()}" if self.embed_data.get(
                        key) else f"Definir {key.capitalize()} *"
                    child.disabled = self.embed_data["template"] is None

        async def update_preview(self, interaction):
            if not self.template_content:
                preview_embed = discord.Embed(
                    title=self.embed_data["titulo"] or "Título do Embed",
                    description=self.embed_data["descricao"] or "Descrição do Embed",
                    color=discord.Color.from_rgb(255, 242, 0),
                )
                if self.embed_data["imagem"]:
                    preview_embed.set_image(url=self.embed_data["imagem"])
            else:
                template_embed = self.template_content["embeds"][0]
                preview_embed = discord.Embed.from_dict(template_embed)

                preview_embed.description = template_embed["description"]
                preview_embed.description = preview_embed.description.replace(
                    "[Título]", self.embed_data["titulo"] or "[Título]"
                )
                preview_embed.description = preview_embed.description.replace(
                    "[Descrição]", self.embed_data["descricao"] or "[Descrição]"
                )
                if self.embed_data["imagem"]:
                    preview_embed.set_image(url=self.embed_data["imagem"])

                if "footer" in template_embed and "text" in template_embed["footer"]:
                    preview_embed.set_footer(text=template_embed["footer"]["text"])
                else:
                    preview_embed.set_footer(text="Atenciosamente, a equipe Marvel Rivals Brazuka")

            external_info = f"**Canal de envio:** {self.embed_data['canal_envio'].mention if self.embed_data['canal_envio'] else 'Nenhum'}\n"
            external_info += f"**Mensagem de notificação:** {self.embed_data['notificacao'] or 'Nenhuma'}"

            await interaction.response.edit_message(
                content=f"Monte seu embed com as características abaixo:\n(Opções marcadas com * são obrigatórias)\n\n{external_info}",
                embed=preview_embed,
                view=self,
            )

        async def load_template(self, template_name):
            try:
                with open(f"{TEMPLATES_DIR}{template_name}_template.json", "r", encoding="utf-8") as file:
                    self.template_content = json.load(file)
                self.embed_data["template"] = template_name
                self.embed_data["titulo"] = None
                self.embed_data["descricao"] = None
                self.embed_data["notificacao"] = None
                self.embed_data["imagem"] = None

                if template_name == "event":
                    self.embed_data["canal_envio"] = bot.get_channel(CHANNEL_EVENT)
                elif template_name == "championship":
                    self.embed_data["canal_envio"] = bot.get_channel(CHANNEL_CHAMPIONSHIP)
                elif template_name == "announcement":
                    self.embed_data["canal_envio"] = bot.get_channel(CHANNEL_ANNOUNCEMENT)
                elif template_name == "patchnote":
                    self.embed_data["canal_envio"] = bot.get_channel(CHANNEL_PATCHNOTE)
                    self.embed_data["notificacao"] = self.template_content["content"]

                self.update_buttons()
            except FileNotFoundError:
                self.template_content = None
                raise Exception("❌ Template não encontrado.")

        @discord.ui.button(label="Definir Template *", style=discord.ButtonStyle.primary, row=0)
        async def define_template(self, interaction: discord.Interaction, button: Button):
            class TemplateModal(Modal, title="Definir Template"):
                def __init__(self, embed_view):
                    super().__init__()
                    self.embed_view = embed_view

                template_input = TextInput(
                    label="Escolha o Template",
                    placeholder="1 (evento), 2 (anúncio), 3 (campeonato) ou 4 (patchnote)",
                    required=True,
                )

                async def on_submit(self, modal_interaction: discord.Interaction):
                    template_map = {
                        "1": "event",
                        "2": "announcement",
                        "3": "championship",
                        "4": "patchnote"
                    }
                    choice = self.template_input.value.strip()
                    template = template_map.get(choice)

                    if not template:
                        await modal_interaction.response.send_message(
                            "❌ Escolha inválida. Digite 1 (evento), 2 (anúncio), 3 (campeonato) ou 4 (patchnote).",
                            ephemeral=True,
                        )
                        return

                    try:
                        await self.embed_view.load_template(template)
                        await self.embed_view.update_preview(modal_interaction)
                    except Exception as e:
                        if not modal_interaction.response.is_done():
                            await modal_interaction.response.send_message(
                                f"❌ Erro ao carregar o template: {str(e)}", ephemeral=True
                            )

            await interaction.response.send_modal(TemplateModal(self))

        @discord.ui.button(label="Definir Mensagem de Notificação *", style=discord.ButtonStyle.primary, row=0)
        async def define_notificacao(self, interaction: discord.Interaction, button: Button):
            class NotificacaoModal(Modal, title="Editar Mensagem de Notificação" if self.embed_data.get(
                "notificacao") else "Definir Mensagem de Notificação"):
                def __init__(self, embed_view):
                    super().__init__()
                    self.embed_view = embed_view

                notificacao_input = TextInput(
                    label="Mensagem de Notificação",
                    placeholder="Digite a mensagem de notificação.",
                    max_length=1900,
                    required=True,
                )

                async def on_submit(self, modal_interaction: discord.Interaction):
                    if self.embed_view.template_content:
                        content_template = self.embed_view.template_content["content"]
                        self.embed_view.embed_data["notificacao"] = content_template.replace(
                            "[Notificação]", self.notificacao_input.value
                        )

                    await self.embed_view.update_preview(modal_interaction)

            modal = NotificacaoModal(self)
            if self.embed_data["notificacao"]:
                modal.notificacao_input.default = self.embed_data["notificacao"]

            await interaction.response.send_modal(modal)

        @discord.ui.button(label="Definir Título *", style=discord.ButtonStyle.primary, row=1)
        async def define_titulo(self, interaction: discord.Interaction, button: Button):
            class TituloModal(Modal, title="Editar Título" if self.embed_data.get("titulo") else "Definir Título"):
                def __init__(self, embed_view):
                    super().__init__()
                    self.embed_view = embed_view

                titulo_input = TextInput(
                    label="Título",
                    placeholder="Digite o título do embed.",
                    max_length=256,
                    required=True,
                )

                async def on_submit(self, modal_interaction: discord.Interaction):
                    self.embed_view.embed_data["titulo"] = self.titulo_input.value

                    await self.embed_view.update_preview(modal_interaction)

            modal = TituloModal(self)
            if self.embed_data.get("titulo"):
                modal.titulo_input.default = self.embed_data["titulo"]

            await interaction.response.send_modal(modal)

        @discord.ui.button(label="Definir Descrição *", style=discord.ButtonStyle.primary, row=1)
        async def define_descricao(self, interaction: discord.Interaction, button: Button):
            class DescricaoModal(Modal,
                                 title="Editar Descrição" if self.embed_data.get("descricao") else "Definir Descrição"):
                def __init__(self, embed_view):
                    super().__init__()
                    self.embed_view = embed_view

                descricao_input = TextInput(
                    label="Descrição",
                    placeholder="Digite a descrição do embed.",
                    style=discord.TextStyle.long,
                    max_length=4000,
                    required=True,
                )

                async def on_submit(self, modal_interaction: discord.Interaction):
                    self.embed_view.embed_data["descricao"] = self.descricao_input.value

                    await self.embed_view.update_preview(modal_interaction)

            modal = DescricaoModal(self)
            if self.embed_data.get("descricao"):
                modal.descricao_input.default = self.embed_data["descricao"]

            await interaction.response.send_modal(modal)

        @discord.ui.button(label="Adicionar Imagem", style=discord.ButtonStyle.primary, row=2)
        async def adiciona_imagem(self, interaction: discord.Interaction, button: Button):
            class ImagemModal(Modal, title="Editar Imagem" if self.embed_data.get("imagem") else "Adicionar Imagem"):
                def __init__(self, embed_view):
                    super().__init__()
                    self.embed_view = embed_view

                imagem_input = TextInput(
                    label="URL da Imagem",
                    placeholder="Digite a URL da imagem.",
                    required=True,
                )

                async def on_submit(self, modal_interaction: discord.Interaction):
                    self.embed_view.embed_data["imagem"] = self.imagem_input.value

                    await self.embed_view.update_preview(modal_interaction)

            modal = ImagemModal(self)
            if self.embed_data.get("imagem"):
                modal.imagem_input.default = self.embed_data["imagem"]

            await interaction.response.send_modal(modal)

        @discord.ui.button(label="Enviar", style=discord.ButtonStyle.success, row=3)
        async def enviar(self, interaction: discord.Interaction, button: Button):
            if not self.embed_data["titulo"] or not self.embed_data["descricao"] or not self.embed_data["canal_envio"]:
                await interaction.response.send_message(
                    "⚠️ Preencha o Título, Descrição e Canal antes de enviar!", ephemeral=True
                )
                return

            combined_description = f"# {self.embed_data['titulo']}\n\n{self.embed_data['descricao']}"

            final_embed = discord.Embed(
                description=combined_description,
                color=discord.Color.from_rgb(255, 242, 0),
            )
            if self.embed_data["imagem"]:
                final_embed.set_image(url=self.embed_data["imagem"])

            content = self.embed_data["notificacao"]
            canal = self.embed_data["canal_envio"]

            try:
                await canal.send(content=content, embed=final_embed)
                await interaction.response.edit_message(
                    content="✅ Embed enviado com sucesso!", embed=None, view=None
                )
            except Exception:
                await interaction.response.send_message(
                    "❌ Não foi possível enviar o embed. Verifique o ID do canal e permissões.", ephemeral=True
                )
            self.stop()

        @discord.ui.button(label="Cancelar", style=discord.ButtonStyle.danger, row=3)
        async def cancelar(self, interaction: discord.Interaction, button: Button):
            await interaction.response.edit_message(
                content="❌ O processo foi cancelado.",
                embed=None,
                view=None,
            )
            self.stop()

    await interaction.response.send_message(
        content="Monte seu embed com as características abaixo:",
        embed=discord.Embed(
            title="Pré-visualização do Embed",
            description="Aqui você pode pré-visualizar o embed conforme ajusta os campos abaixo.",
            color=discord.Color.from_rgb(255, 242, 0),
        ),
        view=EmbedView(),
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
    channel = bot.get_channel(CHANNEL_LOG_APP)

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

        await send_embed(bot.get_channel(CHANNEL_LOG_APP),
                         title="**Comandos Sincronizados**",
                         description=log_message)

    except Exception as e:
        await send_embed(
            bot.get_channel(CHANNEL_LOG_APP),
            title="**Erro na Sincronização**",
            description=f"Ocorreu um erro ao sincronizar os comandos: {str(e)}",
            color=0xFF0000)


async def update_member_roles(member, before_roles=None, after_roles=None):
    monitored_roles = {CARGO_SUBS_TWITCH, CARGO_MEMBROS_YOUTUBE, CARGO_BOT, CARGO_STAFF}
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
    with open(os.path.join(TEMPLATES_DIR, f"{template_name}_template.json"), "r", encoding="utf-8") as file:
        return json.load(file)


#######################
# Inicialização do Bot
#######################
bot.run(TOKEN)
