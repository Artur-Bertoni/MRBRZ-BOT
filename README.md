
# 🤖 Bot de Gerenciamento de Cargos Discord

Bot desenvolvido para automatizar a gestão de cargos em servidor Discord, com funcionalidades específicas para gerenciamento de membros e criação de mensagens personalizadas.

---

## 📋 Funcionalidades

### 🔧 Gerenciamento Automático de Cargos
- Remove automaticamente o cargo "Caos no Multiverso" quando membros recebem cargos específicos.
- Monitora alterações de cargos para Subscribers da Twitch e Membros do YouTube.
- Gerencia automaticamente o cargo especial "@Beyonders" com base nos demais cargos dos membros.

### 🎮 Comandos Administrativos
- **`/ping`**:
  - Comando simples para verificar a latência do bot (exclusivo para administradores).
- **`/atualizar_cargos`**:
  - Permite atualizar manualmente os cargos de todos os membros do servidor, garantindo que cada membro possua o cargo correto.
- **`/embed`**:
  - Comando interativo para construir e personalizar mensagens `embed` com botões e modais, incluindo:
    - **Templates** de mensagens predefinidos (`event`, `announcement`, `championship`, `patchnote`), cada um associado a um canal fixo de envio.
    - Título, descrição, imagem e notificações personalizadas.
    - Os canais de envio são configurados automaticamente com base no template escolhido. O botão de seleção de canal foi desativado para maior consistência.
    - Pré-visualização do embed antes do envio final.

---

## 🛠 Tecnologias Utilizadas

- **Python 3**: Linguagem principal do projeto.
- **discord.py**: Framework para interação com a API do Discord.
- **Flask**: Servidor web leve para manter o bot online.
- **Threading**: Utilizado para gerenciar o servidor web em paralelo.

---

## 📚 Estrutura do Projeto

```
MRBRZ-BOT/
├── main.py                         # Arquivo principal contendo todo o código do bot
├── embed_templates/                # Diretório contendo arquivos de template em JSON para mensagens embed
│   ├── announcement_template.json  # Template para anúncios
│   ├── championship_template.json  # Template para campeonatos
│   ├── event_template.json         # Template para eventos
│   └── patchnote_template.json     # Template para patch notes
├── README.md                       # Arquivo de documentação do projeto
├── keep_alive.py                   # Servidor web para uptime
└── requirements.txt                # Arquivo que lista as dependências instaladas do projeto
```

---

## 🔧 Configuração

1. **Variáveis de Ambiente Necessárias**:
   - `TOKEN`: Token de autenticação do bot Discord.
   - `APPLICATION_ID`: ID da aplicação Discord.

2. **Configuração Local**:
   - Configure o token e as variáveis acima no ambiente.
   - Instale as dependências do projeto usando `pip install -r requirements.txt`.
   - Execute o arquivo principal:
     ```bash
     python main.py
     ```

3. **IDs de Canais Pré-Definidos**:
   Cada template está associado ao envio automático para um canal fixo:
   - `event`: Canal de ID `1336666506146349078`.
   - `championship`: Canal de ID `1342271005778776064`.
   - `announcement`: Canal de ID `1336666125257146440`.
   - `patchnote`: Canal de ID `1351534926339506236`.

---

## 🔐 Permissões Necessárias

O bot precisa das seguintes permissões no Discord:
- Ler mensagens.
- Gerenciar cargos.
- Enviar mensagens.
- Ver canais.
- Gerenciar webhooks.

---

## 📝 Logs

O bot mantém um sistema de logs que registra:
- Alterações de cargos.
- Sincronização de comandos.
- Mensagens de erro ou exceções.

---

Desenvolvido com 💜 para gerenciamento eficiente de comunidades Discord.
