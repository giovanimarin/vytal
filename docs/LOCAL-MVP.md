# Vytal — executar e validar o MVP local

Backend FastAPI + SQLite, web Next e aplicativo Android oficial em `mobile/vytal-app/`. Sem GCP, PostgreSQL, Docker, EAS, conta de provedor ou serviço pago. **Backend/web tiveram fluxo essencial validado em Chromium automatizado; Android nativo ainda exige validação em dispositivo/emulador. Não considerar o MVP completo das três plataformas homologado.** Evidências em [MVP-LOCAL-REPORT.md](MVP-LOCAL-REPORT.md).

## Pré-requisitos

- Git, **Python 3.12**, **Node 22/npm 10** e terminais locais. No Windows use `python`; Linux/macOS podem exigir `python3`.
- Espaço para dependências locais. Instalação inicial usa registries públicos; a aplicação local e os dados demo não exigem serviço cloud.
- Para Android: Android Studio + emulator/SDK/adb ou dispositivo físico com cliente Expo compatível com **SDK 54**. O aplicativo usa expo-dev-client; o launcher força Expo Go (`--go`) com EXPO_OFFLINE=1. Expo Go de outro SDK pode ser incompatível: obter cliente SDK 54 oficial ou produzir development build **local** com Android SDK/JDK e `npx expo run:android`. Não usar build/EAS pago para este guia.

## Instalar

Na raiz de um checkout que contenha este PR:

```sh
python scripts/local.py setup
```

Instala requirements-prod no `.venv` da raiz, `npm ci` web e `npm ci --legacy-peer-deps` Android. Para desenvolver/testar backend completo, instalar adicionalmente `.venv/bin/python -m pip install -r backend/requirements.txt` (Windows: `.venv\Scripts\python -m pip ...`). O launcher não carrega credenciais de produção nem seleciona GCP.

## Iniciar (terminais separados)

```sh
# Terminal 1: backend
python scripts/local.py backend
# Terminal 2: interface web oficial (Next)
python scripts/local.py web
```

- Web: **http://localhost:3000/login**
- API: **http://localhost:8000/api/v1**
- Swagger: **http://localhost:8000/docs**
- Liveness: **http://localhost:8000/health**

`dev.bat` inicia os mesmos dois componentes no Windows depois do setup; não é um seed nem inicia Expo web em lugar da web Next. Ctrl+C encerra cada terminal. Sem reload automático do backend: reiniciar seu processo após mudar Python; Next/Expo usam recarga de desenvolvimento.

O launcher cria `.local-vytal/` ignorado pelo Git: SQLite em `data/vytal.db`, config local e chaves locais aleatórias privadas em `keys.json`. As chaves são reutilizadas entre reinícios para não invalidar sessões por mudança incidental de assinatura. **Não exibir/commitar/compartilhar essa pasta**. Não apagar enquanto quiser manter dados/sessões; removê-la deliberadamente perde a base local e invalida seus tokens. Nenhuma senha padrão ou conta compartilhada é criada. Não executar o launcher em produção: ele rejeita ENVIRONMENT production/staging/test/desconhecido e K_SERVICE. As variáveis sintéticas de OAuth não são uma integração Google Fit real.

## Cadastro, demonstração e roteiro web

1. Acesse `/login`, clique **Criar conta**, preencha nome, e-mail e senha (mínimo existente: 8 caracteres), clique **Cadastrar**. Usar e-mails sintéticos para demonstração, sem dados de saúde reais. Cadastre-se normalmente: não há bypass de autenticação.
2. Consulte **Perfil**, selecione preferências e salve. Recarregue a página: a conta deve permanecer enquanto o access token é válido. Corrigida a corrida de hidratação que redirecionava ao login. Política existente preservada: o refresh token web permanece em memória; após recarga completa e posterior expiração do access token, é necessário novo login. Não prometer login permanente.
3. Em outro terminal, gere dados na **conta já cadastrada**:

```sh
python scripts/local.py demo --email seu-email-de-teste@example.invalid
```

São 14 dias até hoje UTC: sono, FC, passos, atividade e estresse **inteiramente sintéticos**, identificados como `local_demo`/`local-demo:`. Usa normalização e readiness existentes, sem alterar fórmulas. Pode repetir sem duplicar os mesmos eventos/normalizados; preserva outras contas e recusa misturar com dados não demo no período. Não cadastra/vincula Google Fit, não cria tokens OAuth e não apaga base existente. Use conta nova para este roteiro.

4. Recarregue **Dashboard** e **Dados** para métricas/contribuições, readiness, histórico e insights. Em **Como você se sente hoje?**, salve feedback. Em **Treinos**, registre duração/modalidade/intensidade e notas; consulte **Histórico** e **Body Map** para recuperação. A web passou a expor cadastro/feedback já existentes na API.
5. Saia pelo botão **Sair** e entre novamente. Em janela anônima crie outra conta: ela deve começar sem dados da primeira. Geração demo precisa ser solicitada separadamente para cada conta.

O antigo botão de seed compartilhado não é oferecido por padrão. Seu fluxo legado exige opt-in explícito separado no backend e NEXT_PUBLIC_ENABLE_DEV_SEED=true no desenvolvimento; não é usado neste guia. Não habilitar seed público para viabilizar testes. Em modo demo, não usar “Sincronizar”/Google Fit esperando importação real: os registros já foram gravados localmente; recarregue a consulta. Integração real com provedor fica fora desta validação de custo zero.

## Android: configuração separada

### Emulador Android no mesmo computador

Inicie o emulador no Android Studio e mantenha backend rodando. Em outro terminal:

```sh
python scripts/local.py android
```

API padrão **http://10.0.2.2:8000/api/v1** (localhost do computador visto pelo emulador). Metro padrão **8081**. Com adb/emulador disponíveis, pressione **a** no Expo. Se o Metro localhost não for alcançável, usar `adb reverse tcp:8081 tcp:8081` ou modo LAN. Não usar 127.0.0.1 como API dentro do emulador sem configurar reverse também para 8000.

### Dispositivo físico na mesma rede confiável

```sh
# Terminal backend
python scripts/local.py backend --lan
# Terminal Android: substituir pelo IP LAN do computador
python scripts/local.py android --lan --api-url http://IP-LAN-DO-COMPUTADOR:8000/api/v1
```

Libere somente sua rede privada/firewall para 8000/8081, abra o QR/URL LAN no cliente compatível. Não usar tunnel/serviço cloud, não expor a internet e não usar dados reais: HTTP é permitido apenas em desenvolvimento. Release continua exigindo HTTPS explícito. Android não usa o proxy web: URL precisa terminar em `/api/v1` e EXPO_PUBLIC_API_URL é pública, nunca secret.

Roteiro pendente no dispositivo: cadastrar/login, restaurar sessão pelo SecureStore, consultar/editar perfil, sair/entrar, validar separação de contas e visualizar indicadores/feedback após gerar demo para o mesmo e-mail. **Não foi executado aqui**: não há adb, SDK/emulador, dispositivo ou /dev/kvm. Export Hermes/integrar serviços JS com API não substitui teste nativo. A interface Android atual não expõe uma tela de registro/histórico de treinos equivalente à web; treinos/recuperação foram exercitados na web/API, e a paridade nativa completa permanece pendente, sem criar telas não verificáveis nesta entrega.

## Testes reproduzíveis

```sh
# Backend (dependências completas de desenvolvimento)
cd backend
ENVIRONMENT=test GOOGLE_CLIENT_ID=synthetic GOOGLE_CLIENT_SECRET=synthetic ../.venv/bin/pytest
cd ..
# Clientes
npm test --prefix web
npm test --prefix mobile/vytal-app
# Integração do cliente Android com backend local real
VYTAL_PYTHON="$PWD/.venv/bin/python" npm run test:api --prefix mobile/vytal-app
# E2E browser, sem usar a base manual
cd web
npx playwright install chromium
VYTAL_PYTHON="$PWD/../.venv/bin/python" npm run test:e2e
```

No Windows, usar caminhos `.venv\Scripts\python.exe` e definir env com `$env:VYTAL_PYTHON=...` no PowerShell. No Linux podem ser necessárias bibliotecas do navegador (`npx playwright install --with-deps chromium`); no ambiente desta execução Chromium já existia. Alternativa para browser instalado: VYTAL_CHROMIUM_PATH com caminho local do executável. E2E usa portas **8100/3100**, SQLite/config/segredos sintéticos temporários e dois contextos browser. Não precisa iniciar launcher manual ou acessar endpoints externos. Fecha seus processos, descarta a base e guarda só screenshots/resultado em `.local-vytal/evidence` (ou VYTAL_E2E_ARTIFACTS). Não executa migração. Não usar trace/HAR com tokens sem redação.

Os testes não atualizam os snapshots automaticamente. Mudança deliberada nesta entrega: treino com date null/omitido agora usa o dia atual em vez de 500; data inválida retorna 400 antes de persistir. Schema público e demais snapshots permanecem compatíveis. O histórico T01 de defeitos fica preservado, com esta resolução documentada.

## Problemas comuns

- **Porta ocupada:** encerrar o processo local que a utiliza; o launcher não mata processos de terceiros. E2E exige 8100/3100 livres.
- **403 no seed:** esperado com seed legado desabilitado; usar `demo --email` numa conta existente.
- **Dados demo não aparecem:** confirmar e-mail/conta e usar o launcher, que aponta para `.local-vytal/data/vytal.db`; não misturar com `backend/data`/compose legado. Recarregar tela/queries.
- **Expo fetch failed:** launcher usa `EXPO_OFFLINE=1` e desativa telemetria; não depende da API Expo. Dependências/cliente compatível precisam estar instalados previamente.
- **Emulador não conecta:** 10.0.2.2 é o host; em dispositivo usar IP LAN e backend --lan. CORS não corrige endereço de rede errado.
- **Compose antigo:** não é o caminho validado deste guia; existem portas/variáveis inconsistentes nos arquivos legados. Não foram executados ou promovidos a implantação.
