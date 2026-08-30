# MIATSUNO-Lab

Um laboratório público para ferramentas pequenas, úteis e sem frescura. Tem automação, segurança defensiva, utilitários de programação e umas ideias geek que não cabiam quietas na gaveta.

A regra da casa é simples: se o programa diz que fez alguma coisa, ele faz mesmo. Nada de botão cenográfico, dado inventado ou função com cara de “depois eu termino”.

## automação

- `automation/file_sift.py` organiza arquivos de verdade, começa em modo de simulação segura e permite desfazer com manifesto.
- `automation/site_watch.py` acompanha páginas HTTP(S), guarda estado, detecta mudanças e respeita ETag e Last-Modified.
- `automation/backup_buddy.py` cria backups ZIP incrementais, verifica os arquivos e registra o que mudou.

## segurança defensiva

- `security/header_guard.py` confere cabeçalhos, cookies, redirecionamentos e sinais básicos de configuração HTTP.
- `security/dependency_lens.py` consulta o OSV para procurar vulnerabilidades conhecidas nas dependências locais.
- `security/pychaos_safe.py` é a suíte de diagnóstico estilo PyChaos: 45 funções reais de coleta pública, DNS, HTTP, RDAP, certificados, APIs abertas e checagens de superfície. Use somente em sistemas e domínios que você possui ou tem autorização para testar.

Não tem brute force, exploração, invasão, coleta de credenciais ou varredura irresponsável. Segurança boa não precisa fazer cosplay de vilão de filme ruim.

## utilitários para quem programa

- `practical/env_doctor.py` dá uma olhada honesta no ambiente de desenvolvimento.
- `practical/git_scribe.py` transforma histórico Git em notas de versão.
- `practical/snippet_box.py` guarda, busca, importa e exporta snippets localmente.

## esquina geek

- `geek/solar_ledger.py` consulta dados astronômicos reais e monta efemérides.
- `geek/curiosity_terminal.py` busca fatos, piadas, números, citações e curiosidades em APIs públicas.

## como usar

Cada ferramenta explica o próprio uso. Rode:

```bash
python3 caminho/do/programa.py --help
```

As ferramentas usam a biblioteca padrão sempre que possível. A suíte de segurança lista suas dependências em `security/requirements.txt`.

## status

O laboratório está vivo. Isso quer dizer que os programas funcionam agora e também que podem ganhar melhorias, correções e mais personalidade depois. Código aberto é obra em andamento — só não é desculpa para entregar obra inacabada.

Feito por **MIATSUNO**, com curiosidade, teimosia e café suficiente para assustar um clínico-geral.
