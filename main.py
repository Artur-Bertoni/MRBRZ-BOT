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
                if child.label != "Definir Template":
                    child.disabled = self.embed_data["template"] is None

        async def update_preview(self, inner_interaction):
            preview_embed = discord.Embed(
                title=self.embed_data["titulo"] or "Título do Embed",
                description=self.embed_data["descricao"] or "Descrição do Embed",
                color=discord.Color.blue(),
            )
            if self.embed_data["imagem"]:
                preview_embed.set_image(url=self.embed_data["imagem"])

            external_info = f"Canal de envio: {self.embed_data['canal_envio'].mention if self.embed_data['canal_envio'] else 'Nenhum'}\n"
            external_info += f"Mensagem de notificação: {self.embed_data['notificacao'] or 'Nenhuma'}"

            await inner_interaction.response.edit_message(
                content=f"Monte seu embed com as características abaixo:\n\n{external_info}",
                embed=preview_embed,
                view=self,
            )

        async def load_template(self, template_name):
            try:
                with open(f"./embed_templates/{template_name}_template.json", "r", encoding="utf-8") as file:
                    self.template_content = json.load(file)

                self.embed_data["titulo"] = None
                self.embed_data["descricao"] = None
                self.embed_data["notificacao"] = None
                self.embed_data["imagem"] = None
                for key in ["template", "canal_envio"]:
                    self.embed_data[key] = None

                self.embed_data["template"] = template_name
            except FileNotFoundError:
                self.template_content = None
                raise Exception("❌ Template não encontrado.")

        async def apply_template(self):
            if not self.template_content:
                return

            embed_template = self.template_content["embeds"][0]
            self.embed_data["titulo"] = embed_template["description"].split("\n\n")[0].replace("# ", "").strip()
            self.embed_data["descricao"] = embed_template["description"].split("\n\n")[1].strip()
            self.embed_data["notificacao"] = self.template_content["content"]

            self.update_buttons()

        @discord.ui.button(label="Definir Template", style=discord.ButtonStyle.primary)
        async def define_template(self, inner_interaction: discord.Interaction, button: Button):
            class TemplateModal(Modal, title="Definir Template"):
                def __init__(self, embed_view):
                    super().__init__()
                    self.embed_view = embed_view

                template_input = TextInput(
                    label="Escolha o Template",
                    placeholder="Opções: event, announcement, championship ou patchnote",
                    required=True,
                )

                async def on_submit(self, modal_interaction: discord.Interaction):
                    template = self.template_input.value.strip().lower()
                    if template not in ["event", "announcement", "championship", "patchnote"]:
                        await modal_interaction.response.send_message(
                            "❌ Template inválido. Escolha: event, announcement, championship ou patchnote.",
                            ephemeral=True,
                        )
                        return

                    try:
                        await self.embed_view.load_template(template)
                        await self.embed_view.apply_template()
                        await self.embed_view.update_preview(modal_interaction)
                        await modal_interaction.response.send_message(
                            f"✅ Template '{template}' carregado com sucesso!", ephemeral=True
                        )
                    except Exception as e:
                        await modal_interaction.response.send_message(str(e), ephemeral=True)

            await inner_interaction.response.send_modal(
                TemplateModal(self)
            )

        @discord.ui.button(label="Definir Mensagem de Notificação", style=discord.ButtonStyle.primary, disabled=True)
        async def define_notificacao(self, inner_interaction: discord.Interaction, button: Button):
            class NotificacaoModal(Modal, title="Definir Mensagem de Notificação"):
                def __init__(self, embed_view):
                    super().__init__()
                    self.embed_data = embed_view.embed_data
                    self.template_content = embed_view.template_content
                    self.update_preview_callback = embed_view.update_preview

                notificacao_input = TextInput(
                    label="Mensagem de Notificação",
                    placeholder="Digite aqui a mensagem de notificação.",
                    required=True,
                )

                async def on_submit(self, modal_interaction: discord.Interaction):
                    self.embed_data["notificacao"] = (
                        self.template_content["content"].replace(
                            "[Notificação]", self.notificacao_input.value
                        )
                        if self.template_content
                        else ""
                    )
                    await self.update_preview_callback(modal_interaction)
                    await modal_interaction.response.send_message(
                        "✅ Mensagem de Notificação definida com sucesso!", ephemeral=True
                    )

            await inner_interaction.response.send_modal(
                NotificacaoModal(self)
            )

        @discord.ui.button(label="Definir Título", style=discord.ButtonStyle.primary, disabled=True)
        async def define_titulo(self, inner_interaction: discord.Interaction, button: Button):
            class TituloModal(Modal, title="Definir Título"):
                def __init__(self, embed_data, update_preview_callback):
                    super().__init__()
                    self.embed_data = embed_data
                    self.update_preview_callback = update_preview_callback

                titulo_input = TextInput(label="Título do Embed", placeholder="Digite o título", required=True)

                async def on_submit(self, modal_interaction: discord.Interaction):
                    self.embed_data["titulo"] = self.titulo_input.value
                    await self.update_preview_callback(modal_interaction)

            await inner_interaction.response.send_modal(
                TituloModal(self.embed_data, self.update_preview)
            )

        @discord.ui.button(label="Definir Descrição", style=discord.ButtonStyle.primary, disabled=True)
        async def define_descricao(self, inner_interaction: discord.Interaction, button: Button):
            class DescricaoModal(Modal, title="Definir Descrição"):
                def __init__(self, embed_data, update_preview_callback):
                    super().__init__()
                    self.embed_data = embed_data
                    self.update_preview_callback = update_preview_callback

                descricao_input = TextInput(
                    label="Descrição do Embed",
                    placeholder="Digite a descrição",
                    required=True,
                    style=discord.TextStyle.long,
                )

                async def on_submit(self, modal_interaction: discord.Interaction):
                    self.embed_data["descricao"] = self.descricao_input.value
                    await self.update_preview_callback(modal_interaction)

            await inner_interaction.response.send_modal(
                DescricaoModal(self.embed_data, self.update_preview)
            )

        @discord.ui.button(label="Definir Canal de Envio", style=discord.ButtonStyle.primary, disabled=True)
        async def define_canal(self, inner_interaction: discord.Interaction, button: Button):
            class CanalModal(Modal, title="Definir Canal de Envio"):
                def __init__(self, embed_data, update_preview_callback):
                    super().__init__()
                    self.embed_data = embed_data
                    self.update_preview_callback = update_preview_callback

                canal_input = TextInput(
                    label="ID do Canal", placeholder="Insira o ID do canal", required=True
                )

                async def on_submit(self, modal_interaction: discord.Interaction):
                    try:
                        canal_id = int(self.canal_input.value)
                        canal = bot.get_channel(canal_id)
                        if not canal:
                            raise ValueError
                        self.embed_data["canal_envio"] = canal
                        await self.update_preview_callback(modal_interaction)
                    except ValueError:
                        await modal_interaction.response.send_message(
                            "❌ ID de canal inválido. Tente novamente.", ephemeral=True
                        )

            await inner_interaction.response.send_modal(
                CanalModal(self.embed_data, self.update_preview)
            )

        @discord.ui.button(label="Enviar", style=discord.ButtonStyle.success, disabled=True)
        async def enviar(self, inner_interaction: discord.Interaction, button: Button):
            if not self.embed_data["titulo"] or not self.embed_data["descricao"] or not self.embed_data["canal_envio"]:
                await inner_interaction.response.send_message(
                    "⚠️ Preencha o Título, Descrição e Canal antes de enviar!", ephemeral=True
                )
                return

            final_embed = discord.Embed(
                title=self.embed_data["titulo"],
                description=self.embed_data["descricao"],
                color=discord.Color.blue(),
            )
            if self.embed_data["imagem"]:
                final_embed.set_image(url=self.embed_data["imagem"])

            canal = self.embed_data["canal_envio"]
            try:
                await canal.send(embed=final_embed)
                await inner_interaction.response.edit_message(
                    content="✅ Embed enviado com sucesso!", embed=None, view=None
                )
            except Exception:
                await inner_interaction.response.send_message(
                    "❌ Não foi possível enviar o embed. Verifique o canal e permissões.", ephemeral=True
                )
            self.stop()

    await interaction.response.send_message(
        content="Monte seu embed com as características abaixo:",
        embed=discord.Embed(
            title="Pré-visualização do Embed",
            description="Aqui você pode pré-visualizar o embed conforme ajusta os campos abaixo.",
            color=discord.Color.blue(),
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
