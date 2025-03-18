
# 🤖 Bot de Gerenciamento de Cargos Discord

Este bot foi desenvolvido para automatizar a gestão de cargos em um servidor Discord. Ele monitora alterações de cargos, gerencia atribuições e remoções automáticas, além de permitir a criação de mensagens interativas e embeds personalizados com templates.

---

## 📋 Funcionalidades

### 🔧 Gerenciamento Automático de Cargos
- Monitora cargos como "@Subs Twitch", "@Membros YouTube" e "@Beyonders", realizando alterações automáticas conforme regras específicas.
- Remove automaticamente cargos ou adiciona o cargo especial "@Beyonders" com base na combinação de permissões atribuídas a cada membro.
- Registra todas as alterações de cargos em um canal de logs designado.

### 🎮 Comandos Administrativos
- **`/ping`**:
  - Comando simples para verificar a latência do bot (exclusivo para administradores).
- **`/atualizar_cargos`**:
  - Executa manualmente uma verificação e atualização de cargos para todos os membros do servidor.
  - Garante que o cargo especial "@Beyonders" seja atribuído ou removido corretamente.
- **`/embed`**:
  - Comando interativo para construir e personalizar mensagens `embed` com botões e modais, com as seguintes possibilidades:
    - Seleção de templates predefinidos (`event`, `announcement`, `championship`, `patchnote`).
    - Personalização de título, descrição, imagem e mensagem de notificação.
    - Pré-visualização do embed.
    - Envio automático para canais específicos dependendo do template escolhido.

### 📚 Sintonia para Atualizações
- O bot mantém seus comandos sincronizados, permitindo que sejam facilmente disponíveis e atualizados sem reinício manual do servidor.

---

## 🛠 Tecnologias Utilizadas

- **Python 3**: Linguagem principal do projeto.
- **discord.py**: Framework para interagir com a API do Discord.
- **JSON**: Para suportar templates reutilizáveis para mensagens `embed`.
- **Sistema de Modais e Componentes**: Criação interativa de mensagens customizadas.

---

## 📂 Estrutura do Projeto

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
   - `TOKEN`: Token do bot fornecido pelo Discord Developer Portal.
   - `APPLICATION_ID`: ID da aplicação criada no Discord.

2. **Instalação**:
   - Instale as dependências do projeto:
     ```bash
     pip install -r requirements.txt
     ```
   - Configure os IDs de cargos e canais diretamente no código (`main.py`).

3. **Execução**:
   - Inicialize o bot com:
     ```bash
     python main.py
     ```

---

## 📢 Observação Sobre Templates
O comando `/embed` utiliza os seguintes templates predefinidos:
- **`event`**: Enviado automaticamente para o canal de eventos.
- **`championship`**: Associado ao canal de campeonatos do servidor.
- **`announcement`**: Voltado para anúncios gerais do servidor.
- **`patchnote`**: Destinado para patch notes e notificações.

IDs de canais personalizados podem ser ajustados diretamente.

---

## 🔐 Permissões Necessárias

Antes de adicionar o bot ao seu servidor, certifique-se de conceder as permissões adequadas:
- Gerenciar Cargos.
- Ler Mensagens.
- Enviar Mensagens e Embeds.
- Gerenciar Webhooks (para notificações automáticas).

---

## 📝 Registro de Logs

Todas as atividades de alteração de cargo e notificações geradas pelo bot são registradas no canal de logs designado. Essas mensagens incluem:
- Ações realizadas no cargo "@Beyonders".
- Motivo e atribuição/remanejamento de cargos.
- Relatórios de sincronização de comandos.

---

Projeto desenvolvido com 💜 para tornar a administração de servidores Discord mais prática e eficiente.
