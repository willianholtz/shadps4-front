# shadps4-front

![shadps4-front](icon.png)

Frontend gráfico em **PySide6** para o emulador [shadPS4](https://github.com/shadps4-emu/shadPS4) no Linux:
biblioteca de jogos com capas, launcher e um editor **seguro** do `config.toml` do emulador.

> O frontend **nunca altera os arquivos dos jogos**. Ele só lê a biblioteca e, quando você manda,
> edita o `config.toml` do shadPS4 (sempre com backup).

---

## Recursos

### Biblioteca
- Varre as pastas de jogos configuradas no próprio shadPS4 e monta a lista automaticamente
- Lê o nome real do jogo do `sce_sys/param.sfo` e a capa do `sce_sys/icon0.png`
- Busca por nome, visão em **ícones** ou **lista**, tamanho dos ícones ajustável
- Ignora pastas `*-patch` e jogos sem `eboot.bin` válido

### Jogar
- Duplo clique (ou menu de contexto) inicia o jogo
- **gamemoderun** opcional (quando instalado) para prioridade/performance
- Botão parar, status de execução e volta automática da janela ao fechar o jogo
- Impede abrir dois jogos ao mesmo tempo

### Instalação de PKG
- Instala `.pkg` direto pela interface, usando o `tools/pkginstall-cli`
- Instala vários arquivos em sequência, com progresso e opção de cancelar
- Mostra a pasta de destino ao final

### Configurações do shadPS4
- Lista **todas** as seções e chaves do `config.toml` com widgets adequados
  (checkbox, número, texto, pasta, lista, combos com valores fixos)
- Descrição em português/inglês de cada opção
- **Backup automático** em `config.toml.backup-front` antes de qualquer escrita
- Merge linha a linha: preserva comentários e o que ele não entende
- Pastas de jogos gerenciadas pela interface (sincroniza `installDirs`/`installDirsEnabled`)

### Ajustes rápidos (menu de contexto)
- Resolução interna: **720p / 1080p / 1440p / 4K**
- Liga/desliga **FSR** e emulação de **PS4 Pro**
- *São ajustes globais — valem para todos os jogos*

### Utilidades
- **Verificar integridade**: acha arquivos zerados (download/instalação corrompida)
- Abrir pasta do jogo e pasta de addons
- **Apagar ROM** manda para a lixeira (com `.trashinfo`, dá para restaurar)

### Interface
- Tema escuro, PT-BR e English (troca na hora)
- Layout responsivo com lista lateral de seções nas configurações

---

## Requisitos

- **Linux** (usa `gamemoderun` e a lixeira XDG)
- **Python 3.11+** (usa `tomllib`; testado no 3.14)
- **PySide6 6.x**
- **shadPS4** instalado e acessível no `PATH` (ou aponte o binário em `config/front.json`)
- Opcional: `gamemode` para o `gamemoderun`

```bash
# Arch
sudo pacman -S python pyside6
# Debian/Ubuntu
sudo apt install python3 python3-pyside6.qtwidgets
```

## Instalação e execução

```bash
git clone https://github.com/willianholtz/shadps4-front.git
cd shadps4-front

python3 -m venv .venv
source .venv/bin/activate
pip install PySide6

python app.py
```

Na primeira execução o app importa as pastas de jogos já configuradas no shadPS4.
Se não houver nenhuma, adicione em **Configurações → Pastas de jogos**.

---

## Como funciona

| Arquivo | Papel |
|---|---|
| `app.py` | Aplicação inteira (biblioteca, launcher, editor de config) |
| `strings.py` | Textos PT-BR/EN da interface + descrição de cada chave do `config.toml` |
| `config/front.json` | Preferências do frontend (pastas, binário, idioma, visual) — **não vai pro Git**; existe o modelo em `config/front.example.json` |
| `tools/pkginstall-cli` | Instalador de PKG usado pela interface |
| `icon.png` | Ícone do app |

**Caminhos usados:**

- Config do emulador: `~/.local/share/shadPS4/config.toml`
- Config do frontend: `config/front.json` (na pasta do projeto)
- Config antiga (migrada automaticamente): `~/.config/shadps4-front/config.json`
- Backup do emulador: `~/.local/share/shadPS4/config.toml.backup-front`

**Contrato do instalador de PKG** (caso queira trocar o binário):

```bash
tools/pkginstall-cli jogo.pkg --out /pasta/destino
# imprime "OUTDIR=/pasta/..." na saída e "OK" no final em caso de sucesso
```

---

## Segurança

- Os jogos são tratados como **somente leitura**
- Toda escrita no `config.toml` faz backup antes
- Apagar ROM usa a lixeira do sistema, nunca `rm -rf`
- Antes de aplicar, o app mostra quantos ajustes foram alterados

## Limitações conhecidas

- Linux apenas
- Resolução interna, FSR e PS4 Pro são **globais** (o `config.toml` do shadPS4 não separa por jogo)
- O título exibido vem do `param.sfo`; jogos sem esse arquivo usam o nome da pasta
- O `tools/PKGInstall.AppImage` (~30 MB) é um utilitário externo e pode ser removido do repositório

## Aviso legal

Este projeto **não inclui jogos, firmware ou dados de jogo**. Você precisa da sua própria cópia
legal dos títulos. O shadPS4 é um projeto separado; este repositório é apenas uma interface.

## Licença

A definir.

---

## English (short)

**shadps4-front** is a PySide6 GUI frontend for the shadPS4 emulator on Linux: game library with
covers, game launcher (optional `gamemoderun`), PKG installer and a safe editor for the emulator's
`config.toml` (automatic backup, line-by-line merge that preserves comments). Also offers quick
tweaks (internal resolution, FSR, PS4 Pro), integrity check, open folder and delete-to-trash.

Requirements: Linux, Python 3.11+, PySide6, shadPS4 in `PATH`. Run with `python app.py`.
No game data is included.
