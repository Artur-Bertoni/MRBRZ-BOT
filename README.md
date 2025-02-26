
# 🤖 Bot de Gerenciamento de Cargos Discord

Bot desenvolvido para automatizar a gestão de cargos em servidor Discord, com funcionalidades específicas para gerenciamento de membros e cargos especiais.

## 📋 Funcionalidades

- **Gerenciamento Automático de Cargos**
  - Remove automaticamente o cargo "Caos no Multiverso" quando membros recebem cargos específicos
  - Monitora alterações de cargos para Subscribers da Twitch e Membros do YouTube

- **Comandos Administrativos**
  - `/ping`: Exibe a latência do bot (exclusivo para administradores)

## 🛠 Tecnologias Utilizadas

- **Python 3**: Linguagem principal do projeto
- **discord.py**: Framework para interação com a API do Discord
- **Flask**: Servidor web leve para manter o bot online
- **Threading**: Utilizado para gerenciar o servidor web em paralelo

## 🔧 Variáveis de Ambiente Necessárias

- `TOKEN`: Token de autenticação do bot Discord
- `APPLICATION_ID`: ID da aplicação Discord

## 📚 Estrutura do Projeto

```
├── main.py           # Arquivo principal do bot
├── keep_alive.py     # Servidor web para uptime
└── requirements.txt  # Dependências do projeto
```

## ⚙️ Configuração

1. Configure as variáveis de ambiente necessárias
2. Instale as dependências do projeto
3. Execute o arquivo principal

## 🔐 Permissões Necessárias

O bot requer as seguintes permissões Discord:
- Ler mensagens
- Gerenciar cargos
- Enviar mensagens
- Ver canais
- Gerenciar webhooks

## 📝 Logs

O bot mantém um sistema de logs que registra:
- Alterações de cargos
- Sincronização de comandos
- Erros e exceções

---
Desenvolvido com 💜 para gerenciamento eficiente de comunidades Discord
