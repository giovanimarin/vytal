# Android — Conexão Saúde / Health Connect, backend local

Status: implementação em revisão, **homologação com Garmin/aparelho físico pendente**. Não há registro real de Garmin acessível neste ambiente. Testes com fixtures não satisfazem esse aceite. A solicitação atual inclui Health Connect explicitamente e substitui a exclusão de escopo anterior de D06 para esta entrega; não ativa API Garmin, serviço pago ou GCP.

## Arquitetura e privacidade

- `mobile/vytal-app/src/healthConnect/native.ts`: adaptador Android para react-native-health-connect **4.1.3**. Inicializa SDK, solicita só leitura e lê páginas/changes nativos. Nunca solicita usuário/senha Garmin, não chama Garmin Connect API e não exporta arquivos.
- `normalize.ts`: converte unidades canônicas sem descartar objeto nativo, IDs, origem de pacote, horários/offsets, modification time, clientRecordId/version, device/recordingMethod e estágios/amostras.
- `sync.ts`: coordenador independente de React/HTTP/SDK, histórico inicial limitado e changes token, paginação, batches de 200, retry idempotente, confirmação antes do checkpoint, exclusões e detecção de token expirado. Dados são lidos somente em primeiro plano, após ação do usuário; não há background permission/worker.
- `HealthConnectPanel.tsx`: na tela existente **Fontes de Dados**, conexão, estados, filtros por categoria/origem (Garmin inicialmente), valores/unidades, horários e IDs/origens. Checkpoint no SecureStore, vinculado à conta; instalação tem namespace próprio. Import requests são vinculadas à versão da sessão, impedindo troca de A para B durante leitura/upload.
- Novos endpoints locais autenticados: POST/GET `/api/v1/health-connect/records`. Não aceitam user_id; conta vem do JWT validado. POST restringe instalação/lote, valida timestamps/unidades/números e grava transação SQLite; GET nunca lê outra conta. Fora de local/test/provider SQLite retornam 503. Nenhuma tabela, migração ou infraestrutura é criada além da inicialização SQLite já existente.
- Registros originais no `raw_health_events`, provider `health_connect`. Apps de origem aparecem pelo pacote nativo (Garmin normalmente `com.garmin.android.apps.connectmobile`). O backend conserva o que o SDK reporta; não é uma atestação criptográfica da Garmin nem medição clínica individual.
- GCS/BigQuery não participam. Não são armazenados tokens de Garmin/Google Fit para este caminho. Dados de saúde só seguem para o servidor SQLite configurado pelo usuário; não incluir payloads em logs, reports públicos ou screenshots de homologação com dados pessoais reais.

## Disponibilidade por categoria

Android 14+ costuma incluir Health Connect no sistema; Android 9–13 requer provedor compatível instalado/atualizado. O projeto tem minSdk 26 por dependência, mas API 26/27 não torna Health Connect disponível: o SDK deve retornar disponível e as permissões precisam ser concedidas. Perfis gerenciados/restrições do fabricante podem impedir uso. Android SDK/Health Connect e o **Garmin Connect instalado precisam efetivamente suportar gravação/compartilhamento**; uma permissão Vytal concedida não gera dados.

| Categoria pedida | Tipo Health Connect / permissão READ_* | Valores preservados / limite |
| --- | --- | --- |
| Exercícios | ExerciseSession / EXERCISE | Intervalo, exerciseType, título, segmentos/laps se devolvidos. Não inventa intensidade/modalidade Vytal nem registra treino manual automaticamente |
| Passos | Steps / STEPS | Count e intervalo; passos/hora não são inventados |
| Distância | Distance / DISTANCE | Metros, nativo conserva conversões/unidades disponibilizadas |
| Calorias | ActiveCaloriesBurned e TotalCaloriesBurned / permissões distintas | kcal; **não somar calorias ativas e totais** |
| Frequência cardíaca | HeartRate / HEART_RATE | Série tempo/bpm; UI mostra três amostras iniciais e contagem, objeto integral fica retido no backend |
| FC repouso | RestingHeartRate / RESTING_HEART_RATE | Medida independente em bpm; não inferir repouso da média ou mínimo da série |
| Sono | SleepSession / SLEEP | Sessão/estágios/horários originais; sem inventar sleepScore; somente estágios de sono observados alimentam duração normalizada |
| Peso | Weight / WEIGHT | kg/instante; não modifica perfil/peso manual automaticamente |
| Velocidade | Speed / SPEED | Séries em m/s; não calcular de distância para preencher ausência |
| Elevação | ElevationGained / ELEVATION_GAINED | Ganho de elevação em metros; **não é altitude absoluta nem trilha GPS**. Não pede permissão de localização/rotas |

Registros dessas onze categorias são retidos e consultáveis pelo filtro na tela existente. Não prometer que Garmin fornece todas elas: verificar o registro dentro da Conexão Saúde primeiro. Se a versão do Garmin Connect não escreve para Health Connect, ou a categoria não está publicada, o Vytal não consegue importá-la sem outra fonte; não usa arquivo manual, credenciais Garmin ou ponte paga como fallback.

## Projeções, origem e deduplicação

- Mesma conta + instalação + tipo + pacote de origem + ID nativo = identidade estável de importação. Replay/erro de rede não gera outra linha. Correções atualizam a observação e seu dia anterior/novo; modification timestamps conhecidos impedem replay mais antigo de sobrescrever valor mais novo. Exclusões do changes feed removem registros dessa instalação/conta e suas projeções.
- Espelhamentos com **mesmo tipo, instantes e valores canônicos exatos** têm uma representação de exibição e aliases das origens/IDs; todos os brutos são preservados. Garmin direto tem prioridade sobre espelho Google Fit. Títulos não são usados para deduplicar exercício. Não há tolerância temporal/heurística clínica inventada.
- Para resumo diário, cada categoria escolhe **uma origem**, sem somar Garmin+Fit. Passos da origem escolhida somam somente intervalos não sobrepostos. Intervalos ambíguos da mesma origem ficam brutos e geram aviso; não ratear contagens como se fossem observações.
- A projeção HC em normalized_steps/sleep/heart_rate, quando existe, é prioritária na consulta sobre o dado Google Fit legado do mesmo dia/métrica. O original Fit não é apagado nem adicionado ao total HC. Isso evita dupla contagem, mas pode excluir dados complementares de outra origem do resumo; todos permanecem brutos para conferência. Não alegar resolução universal de duplicatas com intervalos/valores divergentes sem identificador comum.
- Sono: duração somente de união dos intervalos de estágios de sono observados; sem estágios não cria duração artificial. HR só cria projeção de repouso se RestingHeartRate existir. Peso/velocidade/calorias/distância/elevação/exercício ficam na lista com seus valores; não mudam algoritmo de readiness nem fabricam campos obrigatórios de treino.
- Dias operacionais seguem UTC, como as consultas atuais; sono é agrupado pelo término da sessão. A tela mostra instantes locais e o nativo/offset permanece retido. Sessões cruzando meia-noite não são divididas nem reatribuídas silenciosamente. Critério de comparação deve considerar fuso e intervalo, não só o nome do dia no Garmin.
- Entradas efetivamente novas/corrigidas de sono/repouso invalidam os caches derivados desses dias para recálculo pela fórmula existente. Replay idêntico não invalida resultado nem normalized_at. Não muda pesos, categorias ou fórmulas.

## Histórico e limitações de sincronização

A leitura inicial/releitura cobre **30 dias até o início da execução**, condicionada às permissões/janela efetiva do SO. Não solicita permissão especial READ_HEALTH_DATA_HISTORY para histórico irrestrito, nem leitura em background. Não anuncia importação de todo o histórico Garmin. Token é obtido antes do snapshot; alterações capturadas nesse intervalo e páginas seguintes são aplicadas sem perder o checkpoint. Se uma categoria falha, o snapshot fica parcial e o cursor não avança; repetir reimporta idempotentemente.

Alterações posteriores usam getChanges incluindo exclusões. Token expirado é descartado com estado explícito e exige nova sincronização/releitura. **Registros antigos fora da janela e exclusões perdidas durante expiração/revogação não são reconciliados por um snapshot limitado**; histórico retido não deve ser interpretado como presença atual confirmada no Garmin/Health Connect. Reinstalação/novo device também muda IDs/namespace e pode impedir equivalência de registros corrigidos. Isso é limitação declarada, não promessa de exactly-once universal.

Permissões parciais, zero dados, falha de rede/SDK e importação parcial têm estados distintos. O bridge 4.1.3 documenta que revogação pode deixar a lista de permissões em cache até reiniciar o processo; o SO continua impedindo a leitura. Fechar/reabrir e conceder novamente pode ser necessário; não contornar a permissão. Remover acesso nativo não apaga automaticamente o histórico já copiado no SQLite. Não transferir esse histórico a outra conta nem a analytics sem tarefa/aprovação específica.

## Preparar backend SQLite e rede Wi-Fi

Nesta base a PR de MVP local (#24) é separada; **não pressupor que seu launcher está integrado**. Use o backend existente:

```sh
cd backend
python3 -m venv .venv
.venv/bin/pip install -r requirements-prod.txt
cp .env.example .env
# Template tem placeholders locais de OAuth; HC não usa esses serviços.
ENVIRONMENT=local .venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

No Windows, `.venv\Scripts\python.exe` e `$env:ENVIRONMENT='local'` no PowerShell. `CONFIG_PATH` deve selecionar o config.yaml **local**, nunca GCP. Não configurar credenciais reais Garmin/Google. SQLite padrão backend/data/vytal.db persiste localmente; se omitir chaves locais, reiniciar backend invalida tokens (fazer login novamente). Para estabilidade, manter chaves privadas locais fora do Git como já documentado no backend; não colocá-las no app/EXPO_PUBLIC_*.

Computador/celular na mesma rede **privada confiável**. Backend não é publicado na internet; bloquear acesso externo/port forwarding no roteador/firewall. No celular, acessar `http://IP-LAN-DO-COMPUTADOR:8000/health` para confirmar rota; localhost/10.0.2.2 não apontam para o computador de um celular físico. HTTP é exclusivamente desenvolvimento local, não criptografia em trânsito para dados reais: homologar só em rede controlada, ciente desse limite, ou usar TLS local confiável em tarefa específica. O código release exige HTTPS e o plugin só permite cleartext em prebuild development.

## Development build local e instalação no celular

Expo Go **não suporta** este módulo. Não usar EAS/cloud build.

Pré-requisitos no computador: Node 22/npm 10, JDK 17, Android Studio/SDK com platform-tools, plataforma Android 36 e build tools compatíveis (prebuild configura minSdk 26/compile/target 36), ANDROID_HOME e adb no PATH. Aceitar licenças Android SDK localmente; NDK/CMake que Gradle solicitar são ferramentas de build locais gratuitas. Celular Android compatível, depuração USB ligada, cabo para instalar e autorização de adb. Não conectar telefone de terceiros sem autorização.

```sh
cd mobile/vytal-app
npm ci --legacy-peer-deps
# Linux/macOS; substituir IP abaixo pelo computador na rede privada
export NODE_ENV=development
export EXPO_PUBLIC_API_URL=http://IP-LAN-DO-COMPUTADOR:8000/api/v1
export EXPO_NO_TELEMETRY=1
export EXPO_OFFLINE=1
npx expo prebuild --platform android --no-install
adb devices
npx expo run:android --device
```

No PowerShell usar `$env:NODE_ENV='development'` etc. API URL é pública, não incluir tokens. `run:android` compila/instala APK debug e inicia Metro; não é deploy de servidor nem Play Store. Se precisar reiniciar Metro, `npx expo start --dev-client --lan` com as mesmas variáveis. Em offline, cliente/dependências devem estar instalados. Não combinar flag --offline com --lan; usar EXPO_OFFLINE=1. Se instalado por APK de CI, continua sendo necessário Metro local com essa URL da API e conexão ao development client; não abrir no Expo Go.

Compilação alternativa sem dispositivo: `cd android && ./gradlew :app:assembleDebug -PreactNativeArchitectures=arm64-v8a`; no Windows gradlew.bat. Instalação: `adb install -r app/build/outputs/apk/debug/app-debug.apk` para aparelho ARM64 e certificado debug compatível. Não substituir app de produção ou desinstalar apagando dados sem cópia/autorização. O diretório android é gerado/ignorado; nunca executar prebuild --clean sobre alterações nativas manuais não salvas. Para build release futuro, regenerar com NODE_ENV=production/HTTPS; **esta entrega não autoriza release/distribuição**.

## Homologação física obrigatória (pendente)

1. Confirmar no próprio Garmin Connect que a versão oferece compartilhamento com Conexão Saúde; conceder as opções de escrita desejadas **no Garmin**, sem fornecer credenciais ao Vytal. Sincronizar relógio normalmente no app do fabricante (o Vytal não substitui essa operação).
2. Na Conexão Saúde, localizar pelo menos um registro, sua categoria, pacote de origem, valor/unidade e intervalo. Se não existir ali com origem Garmin, registrar ausência e não fabricar evidência.
3. Instalar development build Vytal no Android físico, cadastrar/login na conta do backend local, abrir **Fontes de Dados → Conexão Saúde → Conectar / conceder leitura**.
4. Conceder só as categorias desejadas. Confirmar os prompts nativos; teste negar todas e conceder subconjunto também. Privacy/rationale deve abrir texto estático sem login/dados pessoais.
5. Sincronizar. Filtrar a categoria, registrar origem Garmin, ID, valor/unidade, timestamps/fuso no Vytal. Confirmar resumo das métricas projetáveis/indicadores existentes quando os dados necessários estiverem disponíveis; falta de repouso/estágios não pode virar dado inventado.
6. Comparar com o mesmo registro no Garmin e na Conexão Saúde; redigir evidências com IDs ofuscados, dados autorizados e sem tokens. Não publicar dados de saúde pessoais nos commits.
7. Repetir sincronização e verificar mesmo número/ID/valores, sem duplicar; testar registro novo, correção/exclusão, dois contextos de conta, rede desconectada, permissão negada/revogada, nenhuma observação e token expirado/releitura.
8. Espelhar dado via Google Fit se disponível, confirmar aliases e prioridade sem soma dupla. Intervalos/valores distintos não comprovam espelhamento exato: documentar limite e não apagar brutos.

### Matriz de aceite nesta execução

| Critério | Estado |
| --- | --- |
| 1. Instala Vytal no Android físico | Pendente: sem aparelho/adb/SDK local completo |
| 2. Concede permissões nativas | Prebuild/manifest verificados; diálogo no aparelho pendente |
| 3. Importa um registro REAL Garmin | **Pendente**, não substituído por fixtures |
| 4. Visualiza registro real e origem | UI/contrato implementados; evidência real pendente |
| 5. Repete sem duplicatas | Testes SQLite/JS/replay/concorrência passaram; repetição real pendente |
| 6. Compara com Garmin Connect | **Pendente**, nenhum acesso à conta Garmin do usuário |

## Testes automatizados e evidências locais

- Backend: **445 passed**, 84,24% de cobertura; baseline anterior 418 preservado, 27 casos adicionais. Normalização/unidades, aliases Garmin/Fit, preferência sobre Fit legado, atualização/exclusão por instalação/conta, rollback, concorrência SQLite, timestamps, reimportação sem invalidar resultado e API com JWT real.
- Android JS: **73 passed** (52 anteriores + 21 HC), mais **1 integração Android client→FastAPI/JWT/SQLite**, ampliada para HC/replay e conta B sem dados de A. Reader nativo é simulado apenas nessa automação; backend/normalização/persistência são reais.
- TypeScript, ESLint, Ruff e export **Hermes 2.94 MB** passaram. Prebuild gerou Manifest de leitura, queries, alias Android 14 e activity de rationale; `tests/health-connect-manifest.cjs` verifica a saída real. Isso **não é** instalação nem teste do SDK no telefone.
- Novos endpoints/modelos são aditivos. Verificador OpenAPI permite explicitamente adições, mantendo schemas, required/nullable/status/security anteriores exatos; teste prova que modificar contrato antigo continua falhando. Snapshot atualizado somente com as adições. Estrutura das 16 tabelas permaneceu igual.
- CI existente inclui prebuild/manifest e tentativa de compilar APK debug local no runner (sem EAS, deploy, credenciais ou serviços pagos). Resultado/impedimento de compilação e checks remotos devem ser reportados pelo SHA final, não presumidos por este documento.
- Nenhuma captura nativa/registro real foi criada. Este ambiente não tem adb, Android SDK ou aparelho; JRE não substitui toolchain Android/JDK local. Download de pacote npm e testes não equivalem à homologação nativa.

Comandos de testes: `cd backend && ENVIRONMENT=test GOOGLE_CLIENT_ID=synthetic GOOGLE_CLIENT_SECRET=synthetic ../.venv/bin/pytest`; no app `npm test`, `npm run typecheck`, `npm run lint:pkg01`, `VYTAL_PYTHON=/caminho/python npm run test:api`. Para manifest: prebuild development e `NODE_ENV=development node tests/health-connect-manifest.cjs`. Fixtures são sintéticas e nenhuma usa credencial real.

Referências técnicas: código/tipos/plugin/README de [react-native-health-connect 4.1.3](https://github.com/matinzd/react-native-health-connect), [Health Connect](https://developer.android.com/health-and-fitness/guides/health-connect), [dados e permissões](https://developer.android.com/health-and-fitness/guides/health-connect/plan/data-types). As APIs/tipos da dependência instalada foram inspecionados; disponibilidade real do Garmin/telefone não foi verificada. Não há API Garmin paga, importação por arquivo ou infraestrutura GCP nesta implementação.
