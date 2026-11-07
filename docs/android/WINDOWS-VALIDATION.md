# Windows Android launcher — evidências e limites

## Escopo e composição da PR

Branch `codex/windows-android-launcher`, baseada em `codex/android-health-connect` (#25), não em #24. O diff contra a base contém launcher, testes, documentação e ajustes de CI; nenhuma regra de readiness ou código de autenticação/persistência foi alterado. O workflow de PR automático escolhe essa base somente para esta branch. A dependência #25 precisa ser revisada separadamente; não autoriza merge de nenhuma das duas. Após integração da dependência, revisar/atualizar a base antes de integrar o launcher. A #24 continua preservada, sem cherry-pick de seu launcher.

## Decisão sobre o APK e a API

- APK conhecido: `android-health-connect-debug-apk`, [run 42396895440](https://github.com/giovanimarin/vytal/actions/runs/42396895440), SHA `440a01b` da correção #27 (base #26/#25). Build debug universal ARM64/x86_64, Expo SDK 54.0.37, `com.vytal.app`, Expo development client, Health Connect 4.1.3 e cleartext habilitado apenas em development. Android compatível e compartilhamento Garmin efetivamente disponível continuam necessários.
- O APK de desenvolvimento carrega JS do Metro. `EXPO_PUBLIC_API_URL` no processo Metro atualiza o transporte e `extra.apiUrl`; a API `10.0.2.2` do prebuild CI não fixa a API usada no bundle em development. O launcher anuncia o IPv4 escolhido por `REACT_NATIVE_PACKAGER_HOSTNAME`/`EXPO_PACKAGER_PROXY_URL`. Não foi necessário alterar o app nem recompilar o APK. **Não se aplica a APK release com bundle embarcado.**
- `launcher-metro.test.cjs` inicia Expo/Metro real em loopback, usa IP LAN sintético, consulta o manifesto Android e baixa o bundle completo. Verifica a URL anunciada, `extra.apiUrl`, a leitura de `process.env.EXPO_PUBLIC_API_URL` pelo transporte real e a atribuição concreta dessa variável no polyfill dev do bundle. Encerra somente seu processo/grupo. Não executa APK, Android ou Garmin.
- Download é opcional via `gh` já autorizado; sem CLI usa artefato GitHub no navegador e seleção de arquivo. Artifacts exigem login/permissão e expiram. Expiração requer regeneração pelo mantenedor, nunca fallback para build local/serviço pago. Apenas o `app-debug.apk` exato da raiz é extraído do ZIP, sem extrair caminhos arbitrários. Checagem estrutural e hash local **não** atestam assinatura nem autenticidade: baixar somente do run confiável indicado. Nunca executar/descompactar conteúdo de ZIP como script.

## Preservação e segurança local

- Dois pré-requisitos de execução: Python (3.12 recomendado; 3.11–3.13 suportados pelo verificador) e Node 22. Usa `.venv`, requirements-prod e `npm ci --legacy-peer-deps`; não instala Java/Gradle/SDK. ADB é opcional e pode ser somente platform-tools. O script não instala ferramentas globais nem solicita elevação.
- Reutiliza `backend/data/vytal.db` ou `.local-vytal/data/vytal.db`; se ambos existem e ainda não há escolha, recusa adivinhar. `-DatabasePath` seleciona caminho explícito, sem cópia, remoção ou conversão. Escolha persistida em `.local-vytal/windows-config.json`, provider local. Não edita backend/config.yaml, .env nem configurações GCP. Configurações SQLite personalizadas fora desses caminhos devem ser selecionadas explicitamente com esse parâmetro antes do primeiro uso.
- Chaves locais estáveis em `.local-vytal/keys.json`, mesmo formato uppercase da #24, criadas exclusivamente se ausentes. ACL da pasta privada limita ao usuário Windows atual; não altera ACL de arquivos de produção nem firewall. Não imprime chaves; JSON inválido é recusado com erro genérico. Reiniciar backend mantém JWT e dados; credenciais efêmeras de execuções anteriores por outros meios podem exigir novo login. Nenhum seed/demo é executado.
- Backend vinculado somente ao IPv4 físico RFC1918 selecionado, perfil Windows Private/DomainAuthenticated e gateway. Não vincula a 0.0.0.0/IPv6 público. Metro padrão LAN escuta em outras interfaces também; o launcher recusa outra interface física pública ativa, inclusive sem IPv4. Não cria túnel, regra de firewall, port forwarding nem muda perfil de rede. Uso só em rede confiável, sem VPN; restrição de sub-rede no Firewall Windows deve ser revisada pelo usuário. HTTP local não cifra dados de saúde; não alegar segurança equivalente a produção.
- Portas 8000/8081 testadas antes de abrir serviços; apenas estado PID+instante de criação+IP e saúde confirmados permitem reutilização. Não mata processos desconhecidos nem muda portas silenciosamente. Trocar IP/banco ou repetir install com serviço próprio ativo exige fechar janelas anteriores, antes de qualquer mudança de configuração/dependências. Dois terminais persistem com diagnóstico; o processo pai não precisa ficar aberto. App/SQLite nunca são desinstalados/apagados para corrigir assinatura, porta ou configuração.
- Saúde verificada do PC não prova a rota Samsung→PC. O roteiro exige abrir `/health` no navegador do celular, depois URL/QR no development client. Recusa de rede, porta, RSA/offline/serial ausente, falta de ADB, assinatura/instalação e permissões nativas têm instruções separadas. `start` sem ADB continua operacional pelo caminho manual.

## Testes e comandos reproduzíveis

| Verificação | Evidência local antes da publicação |
| --- | --- |
| PowerShell 7.4.13 no Linux | **82 checks passaram**: IPv4/perfil/seleção, ambiente inseguro, propriedade de PID, portas, ADB, dados/chaves preservados, banco ambíguo, ZIP/APK/traversal, erro de chaves sem exposição, parse AST |
| Ambiente do launcher + FastAPI/SQLite reais | **7 checks passaram**: cadastro/login, perfil, replay HC sintético, isolamento A/B, sessão/dados após restart e novo login |
| Metro/manifest/bundle Android reais | **1 teste passou**: manifesto e bundle completos, somente loopback e IP sintético. Node 24.22.1 local; CI usa Node 22 |
| Windows PowerShell 5.1 e PowerShell 7 | Job `windows-launcher` do CI executa os 82 checks nos dois runtimes e o smoke HTTP/SQLite no Windows. Consultar checks do SHA final; Linux não substitui evidência Windows |
| Regressões existentes | Localmente: **445 testes backend e 73 Android JS passaram**, ESLint/TypeScript passaram. Jobs backend/Android/web preservados; nenhum teste enfraquecido. Novo teste Metro no job Android, sem workflow duplicado |

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File tests/windows-launcher.tests.ps1
pwsh -NoProfile -File tests/windows-launcher.tests.ps1
# Python com requirements-prod instalados; banco temporário, não toca dados pessoais:
powershell -NoProfile -ExecutionPolicy Bypass -File tests/windows-backend-smoke.ps1 -Python .venv\Scripts\python.exe
cd mobile/vytal-app
node --test tests/launcher-metro.test.cjs
```

Nenhum aparelho Samsung/USB/instalador gráfico/firewall real está disponível neste executor. Diálogo de arquivo, RSA, instalação APK, QR/deep link, permissões Health Connect e registro **real** Garmin não foram homologados aqui. ADB/normalização simulados e APK compilado não satisfazem esses aceites. Nenhum dado pessoal, credencial Garmin, recurso GCP ou serviço pago foi usado.

## Homologação pendente no Samsung

1. Windows sem JDK/Android Studio: executar install, selecionar artefato e instalar por ADB ou Meus Arquivos; registrar modelo/SO, versão APK e resultado sem dados pessoais.
2. Start: selecionar rede, abrir `/health` no Samsung, abrir development client na URL; cadastrar/entrar e acessar Fontes de Dados.
3. Confirmar registro Garmin dentro de Health Connect; conceder leituras e importar. Comparar valor/unidade/data/fuso/origem no Vytal, Health Connect e Garmin. Repetir sem duplicar; não publicar PHI/screenshots sensíveis.
4. Fechar serviços e repetir start sem reinstalar. Verificar mesma conta/histórico; testar permissão negada, rede bloqueada, ausência de ADB e porta ocupada.

Até esses passos serem registrados, a entrega é um caminho automatizado testado para execução local, **não homologação física concluída**. Não houve merge, deploy, migração nem provisionamento.
