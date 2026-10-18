# LOOKAY

LOOKAY leva algumas tarefas da Kayepad para o Termux: consulta obras verificadas na Veristante, permite rascunhar uma obra no terminal e exportá-la no JSON que a Kayepad importa. Também acompanha páginas e avisa quando o conteúdo muda.

## Instalação no Termux

```sh
pkg install python git
git clone https://github.com/MIATSUNO/MIATSUNO-Lab.git
cd MIATSUNO-Lab/automation/lookay
bash install.sh
lookay --help
```

O LOOKAY usa apenas a biblioteca padrão do Python; não precisa instalar pacotes com `pip`.

## Comandos

```sh
lookay login
lookay status
lookay obras
lookay obras --search "autor ou palavra"
lookay obras --json
lookay escrever
lookay acompanhar https://exemplo.org/pagina
lookay logout
```

`lookay login` pede o email e a senha no próprio Termux; a senha não aparece enquanto você digita e não é salva. O comando usa uma conexão HTTPS compatível com o fluxo de login da Kayepad. A sessão fica em `~/.config/lookay/session.json`, protegida pelas permissões locais do arquivo, e pode ser removida com `lookay logout`.

`lookay escrever` pede título, autoria, sinopse, capa e capítulos. Para cada capítulo, use o editor definido em `$EDITOR`; sem ele, digite o texto e encerre com um ponto sozinho em uma linha. O arquivo JSON é salvo localmente e pode ser importado em [Vias › Adicionar uma obra](https://kayepad.neocities.org/site/main). O comando não envia nem publica a obra na conta.

`lookay obras` lê os dados públicos de título, autoria e sinopse disponíveis na [Veristante](https://kayepad.neocities.org/site/veristante). A lista depende do catálogo publicado no site.

`lookay acompanhar` adapta o monitor de páginas do projeto MIATSUNO-Lab. Faz apenas requisições HTTP(S) de leitura (GET), compara o conteúdo e guarda hashes e metadados em `~/.config/lookay/site_watch_state.json`. Com `-i SEGUNDOS`, repete até Ctrl-C. Informe apenas páginas que você tem permissão para consultar.

## Segurança e limites

- O email e a senha são enviados somente ao serviço de login da Kayepad por HTTPS; a senha não é gravada.
- O token de sessão é segredo: não compartilhe `session.json` nem inclua esse arquivo em backups públicos.
- Os textos criados e o JSON ficam no aparelho; LOOKAY não publica, envia nem altera obras na plataforma.
- Os arquivos JSON de obra têm limite de 12 MB, igual ao limite de importação da Kayepad.
- O monitor guarda URLs e resultados de consulta localmente. Não inclua cabeçalhos secretos em arquivos ou comandos que possam ser compartilhados.

A ferramenta é um cliente de terminal, não um navegador completo: para entrar, reproduz a requisição HTTPS usada pelo site e mantém a sessão no dispositivo.