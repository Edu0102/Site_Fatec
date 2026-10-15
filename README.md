# Site Fatec

## Login local com ASP.NET e SQLite

O portal também pode ser executado como uma aplicação ASP.NET Core, que protege as páginas existentes com uma sessão por cookie e valida o login em um banco SQLite local. Execute:

```powershell
cd database
dotnet run
```

Abra o endereço mostrado no terminal (normalmente `http://localhost:5293`). Na primeira execução, o arquivo local `portal.db` é criado e recebe o usuário inicial `admin@teste.com` com a senha `Senha123`. Altere ou remova essa conta de demonstração antes de publicar o sistema.

Portal interno desenvolvido com HTML, CSS e JavaScript para reunir ferramentas e materiais de consulta da equipe.

## Sumário

- [Visão geral](#visão-geral)
- [Estrutura do projeto](#estrutura-do-projeto)
- [Funcionalidades](#funcionalidades)
- [Como executar](#como-executar)
- [Armazenamento e limitações](#armazenamento-e-limitações)
- [Tecnologias](#tecnologias)

## Visão geral

O ponto de entrada é `index.html`, que apresenta atalhos para as páginas do portal. As páginas de conteúdo ficam em `html/`; os estilos ficam em `css/`; e os scripts de interação ficam em `js/`.

## Estrutura do projeto

```text
Site_Fatec/
├── index.html                 # Hub inicial com atalhos para as áreas
├── login.html                 # Demonstração independente de login
├── README.md                  # Documentação do projeto
├── css/
│   ├── centrallink.css         # Estilos da Central de Links
│   ├── centralpop.css          # Estilos da Central de POPs
│   ├── checklist.css           # Estilos do Checklist
│   ├── feedback.css            # Estilos do formulário de feedback
│   ├── guia.css                # Estilos da página de guias
│   ├── header.css              # Estilos do cabeçalho compartilhado
│   └── index.css               # Estilos do hub inicial
├── html/
│   ├── centrallink.html        # Pesquisa e cadastro de links
│   ├── centralpop.html         # Consulta e gerenciamento local de documentos
│   ├── checklist.html          # Lista de tarefas e acompanhamento de progresso
│   ├── feedback.html           # Formulário de sugestões
│   └── guia.html               # Consulta e cadastro local de guias
└── js/
    ├── centrallink.js          # Filtros e cadastro temporário de links
    ├── centralpop.js           # Persistência e ações dos documentos
    ├── checklist.js            # Tarefas, resumo e alternância de perfil de teste
    ├── guia.js                 # Cadastro e exibição de guias
    └── header.js               # Montagem do cabeçalho compartilhado
```

## Funcionalidades

### Hub inicial

`index.html` direciona para Checklist, Central de Links, Central de POPs, Guia e Feedback. Os ícones do hub usam Bootstrap Icons carregado por CDN.

### Checklist

Em `html/checklist.html`, é possível criar, concluir, remover e desmarcar tarefas, além de acompanhar totais e percentual concluído. O JavaScript cria tarefas iniciais para o funcionário de demonstração. A página também oferece uma alternância temporária entre funcionário e administrador para testar a visualização de consulta.

### Central de Links

Em `html/centrallink.html`, é possível pesquisar links por título, descrição, assunto ou tags, combinar filtros por tags e cadastrar novos links. Os links cadastrados durante o uso não são persistidos após recarregar ou fechar a página.

### Central de POPs

Em `html/centralpop.html`, os documentos são organizados por departamento (Fiscal, Pessoal, Financeiro, Contábil e Regularização). A página permite pesquisar documentos e, ao ativar o modo de gerenciamento, cadastrar arquivos, baixá-los ou removê-los. O armazenamento usa IndexedDB no navegador atual.

### Guia

Em `html/guia.html`, o modo temporário de administrador permite cadastrar e excluir guias com título e conteúdo. Os guias ficam salvos no `localStorage` do navegador atual.

### Feedback

Em `html/feedback.html`, há campos obrigatórios para assunto e descrição da sugestão. Atualmente, o formulário ainda não possui integração para enviar ou salvar as respostas.

### Login de demonstração

`login.html` é uma página independente do hub. Ela demonstra validação local de credenciais, exibição da senha, manutenção de sessão na aba e opção para lembrar o e-mail. As credenciais estão definidas no próprio código da página:

- E-mail: `admin@teste.com`
- Senha: `Senha123`

Esse login é apenas ilustrativo: não autentica em servidor e não deve ser usado para proteger dados ou funcionalidades reais.

## Como executar

O projeto é estático e não exige instalação de dependências ou etapa de compilação.

1. Abra a pasta do projeto no VS Code.
2. Inicie um servidor estático local, por exemplo, com a extensão **Live Server**.
3. Abra `index.html` pelo servidor. As páginas internas dependem dos caminhos relativos entre `index.html`, `html/`, `css/` e `js/`.

Também é possível abrir `index.html` diretamente no navegador. Um servidor local costuma oferecer uma experiência mais consistente para recursos do navegador, como IndexedDB. É necessário acesso à internet para carregar Bootstrap Icons no hub.

## Armazenamento e limitações

- Checklist: usa `localStorage` com a chave `frcont-checklist-v1`.
- Guias: usam `localStorage` com a chave `frcont-guias-v1`.
- POPs: usam IndexedDB, no banco `CentralPOPsFatec`.
- Central de Links: os links adicionados são mantidos apenas na memória da página.
- Feedback: ainda não há envio ou persistência implementados.
- Login e alternâncias de perfil: são demonstrações locais, sem autenticação ou autorização reais.

Os dados armazenados no navegador não são compartilhados automaticamente entre pessoas, dispositivos ou navegadores. Para uso colaborativo, controle de acesso e armazenamento centralizado, será necessário implementar um backend com autenticação e persistência em servidor.

## Tecnologias

- HTML5
- CSS3
- JavaScript sem framework
- `localStorage` e IndexedDB para persistência local
- Bootstrap Icons via CDN no hub inicial
