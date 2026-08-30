# MIATSUNO-Lab

Um laboratório público para ferramentas pequenas, úteis e sem frescura. Reúne automação, segurança defensiva, utilitários de programação, experiências geek e projetos legados.

Cada entrada abaixo liga ao código e ao README correspondente. Os caminhos dos READMEs seguem o nome do projeto: `categoria/ferramenta/README.md`.

## Automação

- [`automation/file_sift.py`](automation/file_sift.py) — organiza arquivos com simulação, manifesto e opção de desfazer. [Guia](automation/file_sift/README.md)
- [`automation/site_watch.py`](automation/site_watch.py) — acompanha páginas HTTP(S), guarda estado e detecta mudanças. [Guia](automation/site_watch/README.md)
- [`automation/backup_buddy.py`](automation/backup_buddy.py) — cria backups ZIP incrementais e verifica os arquivos. [Guia](automation/backup_buddy/README.md)

## Segurança defensiva

- [`security/header_guard.py`](security/header_guard.py) — confere cabeçalhos, cookies e redirecionamentos HTTP. [Guia](security/header_guard/README.md)
- [`security/dependency_lens.py`](security/dependency_lens.py) — consulta o OSV para dependências locais. [Guia](security/dependency_lens/README.md)
- [`security/pyroom.py`](security/pyroom.py) — executa 45 verificações HTTP somente de leitura, incluindo cabeçalhos, DNS, RDAP, certificados e documentos públicos. [Guia](security/pyroom/README.md)

Use as ferramentas de segurança apenas em sistemas e domínios próprios ou autorizados. Elas não fazem brute force, exploração, invasão, coleta de credenciais ou escrita de dados.

## Utilitários para quem programa

- [`practical/env_doctor.py`](practical/env_doctor.py) — inspeciona o ambiente de desenvolvimento. [Guia](practical/env_doctor/README.md)
- [`practical/git_scribe.py`](practical/git_scribe.py) — transforma o estado e o histórico Git em um relatório factual. [Guia](practical/git_scribe/README.md)
- [`practical/snippet_box.py`](practical/snippet_box.py) — guarda, busca, importa e exporta snippets localmente. [Guia](practical/snippet_box/README.md)

## Geek

- [`geek/solar_ledger.py`](geek/solar_ledger.py) — consulta dados astronômicos e monta efemérides. [Guia](geek/solar_ledger/README.md)
- [`geek/curiosity_terminal.py`](geek/curiosity_terminal.py) — busca fatos, piadas, números, citações e curiosidades em APIs públicas. [Guia](geek/curiosity_terminal/README.md)

## Legado

Os projetos mantidos por compatibilidade ficam em `legacy/`, cada um em seu próprio diretório:

- [`legacy/pulse_assistant/pulse_assistant.py`](legacy/pulse_assistant/pulse_assistant.py) — assistente local com clima e definições obtidos de APIs públicas. [Guia](legacy/pulse_assistant/README.md)
- [`legacy/secure_passphrase/secure_passphrase.py`](legacy/secure_passphrase/secure_passphrase.py) — gerador local de senhas e frases usando `secrets`. [Guia](legacy/secure_passphrase/README.md)
- [`legacy/host_diagnostics/host_diagnostics.py`](legacy/host_diagnostics/host_diagnostics.py) — diagnóstico de DNS e portas TCP de um único host. [Guia](legacy/host_diagnostics/README.md)
- [`legacy/column_fall/column_fall.py`](legacy/column_fall/column_fall.py) — jogo de combinações jogável no terminal. [Guia](legacy/column_fall/README.md)
- [`legacy/local_toolbox/local_toolbox.py`](legacy/local_toolbox/local_toolbox.py) — hashes, estatísticas de arquivos, árvores de diretórios e JSON local. [Guia](legacy/local_toolbox/README.md)

## Plataformas públicas relacionadas

### Kachey — Music Vault

Para quem estuda, toca, consulta ou organiza referências musicais no navegador.

Tutorial rápido em [kachey.neocities.org](https://kachey.neocities.org):

1. Abra o Music Vault e escolha um álbum.
2. Entre em uma música para ler os acordes e as notas disponíveis.
3. Use o chord viewer para visualizar os acordes e o metronome para praticar o andamento.
4. Aplique templates quando precisar de uma estrutura pronta.
5. Exporte o material em `.txt` quando quiser guardar uma cópia simples.

### Kayepad — BETA

Para quem escreve, revisa e consulta textos em uma interface leve de navegador.

Tutorial rápido em [kayepad.neocities.org](https://kayepad.neocities.org):

1. Abra a entrada de escrita em [load.html](https://kayepad.neocities.org/load.html).
2. Use Explore para navegar pelas entradas; a busca e os filtros ajudam a encontrar um texto.
3. Consulte as anotações em [Kaynotes](https://kayepad.neocities.org/sc/notes).

## Como usar

Cada ferramenta explica o próprio uso. Rode:

```bash
python3 caminho/do/programa.py --help
```

Os programas usam a biblioteca padrão sempre que possível. A suíte de segurança lista suas dependências em [`security/requirements.txt`](security/requirements.txt).
