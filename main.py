import json
import io
import os

import discord
from discord.ext import commands
from discord.ui import View, Button, Modal, TextInput

# ======== Setup Inicial ========
intents = discord.Intents.default()
intents.guilds = True
intents.guild_messages = True
intents.message_content = True
intents.members = True

bot = commands.Bot(
    command_prefix="/",
    intents=intents,
    application_id=os.getenv("APPLICATION_ID")
)

# ======== Configurações e Variáveis ========
TOKEN = os.getenv("TOKEN")
if not TOKEN:
    print("Erro: TOKEN não encontrado nos secrets.")
    exit()

GUILD_ID = 1336381520977596518

ROLE_GUARDIOES       = 1336671601864871956
ROLE_SUBS_TWITCH     = 1336425874177790012
ROLE_MEMBROS_YOUTUBE = 1336425799359791174
ROLE_BOT             = 1338657713797857331
ROLE_VINGADORES      = 1336381521111814158
ROLE_EQUIPE          = 1385626621469262026
ROLE_COMMUNITY       = 1384201190270832830
ROLE_BEYONDERS       = 1342108534350811206
ROLE_TEST            = 1343947583260983338

TEMPLATES_DIR        = "./embed_templates/"

CHANNEL_LOG_APP      = 1341465591667753060
CHANNEL_EVENT        = 1336666506146349078
CHANNEL_ANNOUNCEMENT = 1336666125257146440
CHANNEL_CHAMPIONSHIP = 1342271005778776064
CHANNEL_PATCHNOTE    = 1351534926339506236
CHANNEL_RUMOR        = 1384200360054358056
CHANNEL_THEORIES     = 1384504252029993072
CHANNEL_SAVE_EMBEDS  = 1370414840476078092
CHANNEL_THANKS       = 1405149707885481994


# ======== Comandos ========
@bot.tree.command(
    name="ping",
    description="Mostra a latência do bot",
    guild=discord.Object(id=GUILD_ID)
)
async def ping(interaction: discord.Interaction):
    if not any(r.id in (ROLE_GUARDIOES, ROLE_EQUIPE) for r in interaction.user.roles):
        await interaction.response.send_message(
            "🚫 Você não tem permissão para usar este comando.",
            ephemeral=True
        )
        return

    websocket_latency = round(bot.latency * 1000)
    await interaction.response.send_message("Calculando latência...")
    api_latency = round(
        (discord.utils.utcnow() - interaction.created_at).total_seconds() * 1000
    )

    await send_embed(
        interaction.channel,
        title="🏓 Pong!",
        description=(
            f"**Gateway (WebSocket):** `{websocket_latency}ms`\n"
            f"**API:** `{api_latency}ms`"
        )
    )
    await interaction.delete_original_response()


@bot.tree.command(
    name="atualizar_cargos",
    description="Atualiza manualmente os cargos de todos os membros do servidor.",
    guild=discord.Object(id=GUILD_ID)
)
async def atualizar_cargos(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message(
            "🚫 Você não tem permissão para usar este comando.",
            ephemeral=True
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
    if not any(r.id in (ROLE_GUARDIOES, ROLE_COMMUNITY) for r in interaction.user.roles):
        await interaction.response.send_message(
            "🚫 Você não tem permissão para usar este comando.",
            ephemeral=True
        )
        return

    # View de botão único (antes de ter a versão final)
    class DownloadView(View):
        def __init__(self, url: str):
            super().__init__(timeout=None)
            self.add_item(Button(label="Download JSON", style=discord.ButtonStyle.link, url=url))

    # View para dois botões (preview + final)
    class DownloadTwoView(View):
        def __init__(self, preview_url: str, final_url: str):
            super().__init__(timeout=None)
            self.add_item(Button(label="Download Preview", style=discord.ButtonStyle.link, url=preview_url))
            self.add_item(Button(label="Download Final",  style=discord.ButtonStyle.link, url=final_url))

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
            self.json_message = None
            self.update_buttons()

        def update_buttons(self):
            template_set = self.embed_data["template"] is not None
            template_is_patchnote = self.embed_data["template"] == "patchnote"

            for child in self.children:
                if "Mensagem de Notificação" in child.label:
                    child.disabled = template_is_patchnote or not template_set
                    child.label = (
                        "Editar Mensagem de Notificação"
                        if self.embed_data["notificacao"] else
                        "Definir Mensagem de Notificação *"
                    )
                elif "Template" in child.label:
                    child.label = (
                        "Alterar Template"
                        if self.embed_data["template"] else
                        "Definir Template *"
                    )
                elif "Enviar" in child.label:
                    child.disabled = (
                        not template_set
                        or self.embed_data["titulo"] is None
                        or self.embed_data["descricao"] is None
                    )
                elif "Imagem" in child.label:
                    child.label = (
                        "Editar Imagem"
                        if self.embed_data["imagem"] else
                        "Adicionar Imagem"
                    )
                    child.disabled = not template_set
                elif "Título" in child.label:
                    child.label = (
                        "Editar Título"
                        if self.embed_data["titulo"] else
                        "Definir Título *"
                    )
                    child.disabled = not template_set
                elif "Descrição" in child.label:
                    child.label = (
                        "Editar Descrição"
                        if self.embed_data["descricao"] else
                        "Definir Descrição *"
                    )
                    child.disabled = not template_set
                elif "Salvar JSON" in child.label:
                    child.disabled = not template_set
                # cancelar permanece sempre ativo

        # ——— Botões Originais: template / notificação / título / descrição / imagem / cancelar ———
        @discord.ui.button(label="Definir Template *", style=discord.ButtonStyle.primary, row=0)
        async def define_template(self, interaction, button):
            class TemplateModal(Modal, title="Alterar Template" if self.embed_data.get("template") else "Definir Template"):
                def __init__(self, ev):
                    super().__init__()
                    self.embed_view = ev

                template_input = TextInput(
                    label="Escolha o Template (apenas número)",
                    placeholder="1-evento, 2-anúncio, 3-campeonato, 4-rumor, 5-teorias ou 6-patchnote",
                    required=True,
                )
                async def on_submit(self, mi):
                    m = {"1":"event","2":"announcement","3":"championship","4":"rumor","5":"theories","6":"patchnote"}
                    tpl = m.get(self.template_input.value.strip())
                    if not tpl:
                        if not mi.response.is_done():
                            await mi.response.send_message("❌ Escolha inválida.", ephemeral=True)
                        else:
                            await mi.response.send("❌ Escolha inválida.", ephemeral=True)

                        return
                    try:
                        await self.embed_view.load_template(tpl)
                        self.embed_view.update_buttons()
                        await self.embed_view.update_preview(mi)
                    except Exception as e:
                        if not mi.response.is_done():
                            await mi.response.send_message(f"❌ {e}", ephemeral=True)

            await interaction.response.send_modal(TemplateModal(self))

        @discord.ui.button(label="Definir Mensagem de Notificação *", style=discord.ButtonStyle.primary, row=0)
        async def define_notificacao(self, interaction, button):
            class NotifModal(Modal, title="Editar Mensagem de Notificação" if self.embed_data.get("notificacao") else "Definir Mensagem de Notificação"):
                def __init__(self, ev):
                    super().__init__()
                    self.embed_view = ev

                notificacao_input = TextInput(
                    label="Mensagem de Notificação",
                    placeholder="Digite a mensagem de notificação.",
                    max_length=1900,
                    required=True,
                )
                async def on_submit(self, mi):
                    if self.embed_view.template_content:
                        ct = self.embed_view.template_content["content"]
                        self.embed_view.embed_data["notificacao"] = ct.replace("[Notificação]", self.notificacao_input.value)
                    self.embed_view.update_buttons()
                    await self.embed_view.update_preview(mi)

            modal = NotifModal(self)
            if self.embed_data.get("notificacao"):
                modal.notificacao_input.default = self.embed_data["notificacao"]
            await interaction.response.send_modal(modal)

        @discord.ui.button(label="Definir Título *", style=discord.ButtonStyle.primary, row=1)
        async def define_titulo(self, interaction, button):
            class TituloModal(Modal, title="Editar Título" if self.embed_data.get("titulo") else "Definir Título"):
                def __init__(self, ev):
                    super().__init__()
                    self.embed_view = ev

                titulo_input = TextInput(
                    label="Título",
                    placeholder="Digite o título do embed.",
                    max_length=256,
                    required=True,
                )
                async def on_submit(self, mi):
                    self.embed_view.embed_data["titulo"] = self.titulo_input.value
                    self.embed_view.update_buttons()
                    await self.embed_view.update_preview(mi)

            modal = TituloModal(self)
            if self.embed_data.get("titulo"):
                modal.titulo_input.default = self.embed_data["titulo"]
            await interaction.response.send_modal(modal)

        @discord.ui.button(label="Definir Descrição *", style=discord.ButtonStyle.primary, row=1)
        async def define_descricao(self, interaction, button):
            class DescModal(Modal, title="Editar Descrição" if self.embed_data.get("descricao") else "Definir Descrição"):
                def __init__(self, ev):
                    super().__init__()
                    self.embed_view = ev

                descricao_input = TextInput(
                    label="Descrição",
                    placeholder="Digite a descrição do embed.",
                    style=discord.TextStyle.long,
                    max_length=4000,
                    required=True,
                )
                async def on_submit(self, mi):
                    self.embed_view.embed_data["descricao"] = self.descricao_input.value
                    self.embed_view.update_buttons()
                    await self.embed_view.update_preview(mi)

            modal = DescModal(self)
            if self.embed_data.get("descricao"):
                modal.descricao_input.default = self.embed_data["descricao"]
            await interaction.response.send_modal(modal)

        @discord.ui.button(label="Adicionar Imagem", style=discord.ButtonStyle.primary, row=2)
        async def adiciona_imagem(self, interaction, button):
            class ImgModal(Modal, title="Editar Imagem" if self.embed_data.get("imagem") else "Adicionar Imagem"):
                def __init__(self, ev):
                    super().__init__()
                    self.embed_view = ev

                imagem_input = TextInput(
                    label="URL da Imagem",
                    placeholder="Digite a URL da imagem.",
                    required=True,
                )
                async def on_submit(self, mi):
                    self.embed_view.embed_data["imagem"] = self.imagem_input.value
                    self.embed_view.update_buttons()
                    await self.embed_view.update_preview(mi)

            modal = ImgModal(self)
            if self.embed_data.get("imagem"):
                modal.imagem_input.default = self.embed_data["imagem"]
            await interaction.response.send_modal(modal)

        # ——— Novo botão: Salvar JSON ———
        @discord.ui.button(label="Salvar JSON", style=discord.ButtonStyle.secondary, row=2)
        async def salvar_json(self, interaction, button):
            # prepara dict do preview
            if self.template_content:
                base = self.template_content["embeds"][0].copy()
                desc = base.get("description","") \
                    .replace("[Título]", self.embed_data["titulo"] or "") \
                    .replace("[Descrição]", self.embed_data["descricao"] or "")
                base["description"] = desc
                if self.embed_data["imagem"]:
                    base["image"] = {"url": self.embed_data["imagem"]}
                embed_dict = base
            else:
                tmp = discord.Embed(
                    title=self.embed_data["titulo"] or "",
                    description=self.embed_data["descricao"] or "",
                    color=discord.Color.from_rgb(255, 242, 0)
                )
                if self.embed_data["imagem"]:
                    tmp.set_image(url=self.embed_data["imagem"])
                embed_dict = tmp.to_dict()

            json_str = json.dumps(embed_dict, ensure_ascii=False, indent=4)
            title_safe = self.embed_data["titulo"].replace(" ", "_") if self.embed_data["titulo"] else "embed"
            filename = f"{title_safe}_preview.json"
            arquivo = discord.File(io.StringIO(json_str), filename=filename)

            canal = bot.get_channel(CHANNEL_SAVE_EMBEDS)
            if self.json_message:
                await self.json_message.edit(content="Embed JSON atualizado:", attachments=[arquivo])
            else:
                msg = await canal.send(content="Embed JSON salvo:", file=arquivo)
                url = msg.attachments[0].url
                await msg.edit(view=DownloadView(url))
                self.json_message = msg

            await interaction.response.send_message("✅ JSON salvo no canal de destino.", ephemeral=True)

        @discord.ui.button(label="Enviar", style=discord.ButtonStyle.success, row=3)
        async def enviar(self, interaction, button):
            # valida campos
            if (
                not self.embed_data["titulo"]
                or not self.embed_data["descricao"]
                or not self.embed_data["canal_envio"]
            ):
                await interaction.response.send_message(
                    "⚠️ Preencha Título, Descrição e Canal antes de enviar!",
                    ephemeral=True
                )
                return

            # monta embed final
            combined = f"# {self.embed_data['titulo']}\n\n{self.embed_data['descricao']}"
            final = discord.Embed(description=combined, color=discord.Color.from_rgb(255, 242, 0))
            if self.template_content and "footer" in self.template_content["embeds"][0]:
                final.set_footer(text=self.template_content["embeds"][0]["footer"].get("text",""))
            else:
                final.set_footer(text="Atenciosamente, a equipe Marvel Rivals Brazuka")
            if self.embed_data["imagem"]:
                final.set_image(url=self.embed_data["imagem"])

            # envia embed oficial
            sent = await self.embed_data["canal_envio"].send(
                content=self.embed_data["notificacao"],
                embed=final
            )

            # ——— agora atualiza a mensagem de JSON com 2 arquivos + botões ———
            # 1) regenera preview JSON
            if self.template_content:
                base = self.template_content["embeds"][0].copy()
                desc = base.get("description","") \
                    .replace("[Título]", self.embed_data["titulo"]) \
                    .replace("[Descrição]", self.embed_data["descricao"])
                base["description"] = desc
                if self.embed_data["imagem"]:
                    base["image"] = {"url": self.embed_data["imagem"]}
                preview_dict = base
            else:
                tmp2 = discord.Embed(
                    title=self.embed_data["titulo"],
                    description=self.embed_data["descricao"],
                    color=discord.Color.from_rgb(255, 242, 0)
                )
                if self.embed_data["imagem"]:
                    tmp2.set_image(url=self.embed_data["imagem"])
                preview_dict = tmp2.to_dict()

            preview_json = json.dumps(preview_dict, ensure_ascii=False, indent=4)
            final_json   = json.dumps(final.to_dict(), ensure_ascii=False, indent=4)

            safe_title = self.embed_data["titulo"].replace(" ", "_")
            arquivo_pre = discord.File(io.StringIO(preview_json), filename=f"{safe_title}_preview.json")
            arquivo_fin = discord.File(io.StringIO(final_json),   filename=f"{safe_title}_final.json")

            # edita attachments (1ª etapa)
            msg = await self.json_message.edit(
                content=f"JSON do embed: {sent.jump_url}",
                attachments=[arquivo_pre, arquivo_fin]
            )
            # 2ª etapa: pega URLs e adiciona view com 2 botões
            pre_url = msg.attachments[0].url
            fin_url = msg.attachments[1].url
            await msg.edit(view=DownloadTwoView(pre_url, fin_url))
            self.json_message = msg

            # finaliza interação
            await interaction.response.edit_message(
                content="✅ Embed enviado com sucesso!", embed=None, view=None
            )
            self.stop()

        @discord.ui.button(label="Cancelar", style=discord.ButtonStyle.danger, row=3)
        async def cancelar(self, interaction, button):
            await interaction.response.edit_message(
                content="❌ O processo foi cancelado.",
                embed=None,
                view=None,
            )
            self.stop()

        # ——— auxiliares internos: preview e load_template ———
        async def update_preview(self, interaction):
            if not self.template_content:
                pv = discord.Embed(
                    title=self.embed_data["titulo"] or "Título do Embed",
                    description=self.embed_data["descricao"] or "Descrição do Embed",
                    color=discord.Color.from_rgb(255, 242, 0),
                )
                if self.embed_data["imagem"]:
                    pv.set_image(url=self.embed_data["imagem"])
            else:
                tpl = self.template_content["embeds"][0]
                pv = discord.Embed.from_dict(tpl)
                pv.description = tpl["description"] \
                    .replace("[Título]", self.embed_data["titulo"] or "[Título]") \
                    .replace("[Descrição]", self.embed_data["descricao"] or "[Descrição]")
                if self.embed_data["imagem"]:
                    pv.set_image(url=self.embed_data["imagem"])
                if "footer" in tpl and tpl["footer"].get("text"):
                    pv.set_footer(text=tpl["footer"]["text"])
                else:
                    pv.set_footer(text="Atenciosamente, a equipe Marvel Rivals Brazuka")

            info = (
                f"**Canal de envio:** "
                f"{self.embed_data['canal_envio'].mention if self.embed_data['canal_envio'] else 'Nenhum'}\n"
                f"**Mensagem de notificação:** {self.embed_data['notificacao'] or 'Nenhuma'}"
            )
            await interaction.response.edit_message(content=info, embed=pv, view=self)

        async def load_template(self, template_name: str):
            try:
                with open(f"{TEMPLATES_DIR}{template_name}_template.json", "r", encoding="utf-8") as f:
                    self.template_content = json.load(f)
                # limpa campos
                self.embed_data.update({
                    "template": template_name,
                    "titulo": None,
                    "descricao": None,
                    "notificacao": None,
                    "imagem": None
                })
                # canal padrão
                if template_name == "event":
                    self.embed_data["canal_envio"] = bot.get_channel(CHANNEL_EVENT)
                elif template_name == "championship":
                    self.embed_data["canal_envio"] = bot.get_channel(CHANNEL_CHAMPIONSHIP)
                elif template_name == "announcement":
                    self.embed_data["canal_envio"] = bot.get_channel(CHANNEL_ANNOUNCEMENT)
                elif template_name == "rumor":
                    self.embed_data["canal_envio"] = bot.get_channel(CHANNEL_RUMOR)
                elif template_name == "theories":
                    self.embed_data["canal_envio"] = bot.get_channel(CHANNEL_THEORIES)
                elif template_name == "patchnote":
                    self.embed_data["canal_envio"] = bot.get_channel(CHANNEL_PATCHNOTE)
                    self.embed_data["notificacao"] = self.template_content["content"]
                self.update_buttons()
            except FileNotFoundError:
                self.template_content = None
                raise Exception("❌ Template não encontrado.")

    # envia a view inicial
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


# ======== Eventos ========
@bot.event
async def on_ready():
    print(f"Bot conectado como: {bot.user}")
    await sync_commands()

@bot.event
async def on_member_update(before, after):
    if before.guild.id != GUILD_ID:
        return
    await update_member_roles(after, before_roles=before.roles, after_roles=after.roles)


# ======== Utilitários ========
async def send_embed(channel, title, description, thumbnail=None, color=0xFFF200, mention=None):
    if isinstance(channel, discord.TextChannel):
        em = discord.Embed(title=title, description=description, color=color)
        if thumbnail:
            em.set_thumbnail(url=thumbnail)
        await channel.send(
            content= mention,
            embed=em)

async def send_role_change_embed(member, role_changed, is_addition, trigger_to_action):
    ch = bot.get_channel(CHANNEL_LOG_APP)
    if role_changed is None:
        action = "adicionado ao(à)" if is_addition else "removido do(a)"
        desc = f"O cargo <@&{ROLE_BEYONDERS}> foi {action} usuário(a) {member.mention}."
    else:
        action = "adicionado ao(à)" if is_addition else "removido do(a)"
        reason = (
            f"após ter o cargo <@&{role_changed.id}> {trigger_to_action}"
            if is_addition else
            f"após receber o cargo <@&{role_changed.id}>"
        )
        desc = f"Cargo <@&{ROLE_BEYONDERS}> {action} {member.mention} {reason}"

    await send_embed(ch, f"**Cargo alterado para {member.display_name}**", desc, thumbnail=member.avatar.url)

async def send_thanks_embed(member, role_changed, is_addition):
    ch = bot.get_channel(CHANNEL_THANKS)

    action = "adicionado ao(à) usuário(a)" if is_addition else "removido do(a) usuário(a)"
    msg = (
        "Fique mais do que a vontade para usufruir das suas regalias no servidor! \nObrigado pelo seu apoio! 🥳"
        if is_addition else
        "Ficamos tristes em vê-lo(a) partir, mas agradecemos pelo seu apoio até aqui, caso queira voltar, estaremos de braços abertos sempre! 🥰"
    )
    desc = f"Cargo <@&{role_changed.id}> {action} {member.mention}.\n{msg}"

    await send_embed(ch, f"**Cargo alterado para {member.display_name}**", desc, thumbnail=member.avatar.url, mention=f"{member.mention}")

async def sync_commands():
    try:
        g = discord.Object(id=GUILD_ID)
        bot.tree.copy_global_to(guild=g)
        lst = await bot.tree.sync(guild=g)
        names = [f"`/{c.name}`" for c in lst]
        msg = "Comandos sincronizados!\n" + (f"Ativos: {', '.join(names)}" if names else "Nenhum")
        await send_embed(bot.get_channel(CHANNEL_LOG_APP), "**Sincronização**", msg)
    except Exception as e:
        await send_embed(bot.get_channel(CHANNEL_LOG_APP), "**Erro na Sincronização**", str(e), color=0xFF0000)

async def update_member_roles(member, before_roles=None, after_roles=None):
    mon = {ROLE_SUBS_TWITCH, ROLE_MEMBROS_YOUTUBE, ROLE_BOT, ROLE_VINGADORES, ROLE_EQUIPE, ROLE_TEST}
    tksRoles = {ROLE_SUBS_TWITCH, ROLE_MEMBROS_YOUTUBE, ROLE_TEST}
    bey = member.guild.get_role(ROLE_BEYONDERS)
    if not bey: return

    br = before_roles or member.roles
    ar = after_roles  or member.roles
    added   = [r for r in ar if r not in br]
    removed = [r for r in br if r not in ar]

    try:
        if any(r.id in mon for r in ar):
            ra = next((r for r in added if r.id in mon), None)
            if bey in ar:
                await member.remove_roles(bey)
                await send_role_change_embed(member, ra, False, "adicionado")
            print(f"Teste1 - {ra}")
            if ra in tksRoles:
                print("Teste1")
                await send_thanks_embed(member, ra, True)
        else:
            rr = next((r for r in removed if r.id in mon), None)
            if bey not in ar:
                await member.add_roles(bey)
                await send_role_change_embed(member, rr, True, "removido")
            print(f"Teste1 - {rr}")
            if rr in tksRoles:
                print("Teste2")
                await send_thanks_embed(member, rr, False)
    except Exception as e:
        print(f"Erro roles {member.display_name}: {e}")



def load_template(name: str):
    with open(os.path.join(TEMPLATES_DIR, f"{name}_template.json"), "r", encoding="utf-8") as f:
        return json.load(f)

# ======== Inicialização ========
bot.run(TOKEN)
