# Issue #27 — runtime Android / Expo SDK 54

PR draft contra `codex/windows-android-launcher` (#26), dependente de `codex/android-health-connect` (#25). Sem merge, deploy, provisionamento ou alteração de dados existentes.

## Correção

O APK com falha combinava SDK 54 com WebBrowser 14, Linking 7, SecureStore 14, Router 5 e Babel preset 13. O `package.json` e o lockfile agora usam SDK 54.0.37, dev-client 6.0.21, WebBrowser 15, Linking 8, SecureStore 15, Router 6 e Babel preset 54. Constants e Font, exigidos pelo Router, estão explícitos. Google Fit e Health Connect continuam disponíveis.

O workflow **Android APK runtime smoke** valida `expo install --check`, `expo-doctor`, autolinking, classes compiladas no DEX, assinatura, arquiteturas ARM64/x86_64 e permissões somente de leitura do APK. A verificação inclui o listener Expo responsável pelo consentimento do Health Connect. O APK é publicado após a compilação; a aprovação do runtime depende também do smoke verde no mesmo workflow.

## Ubuntu + Samsung: instalar por cima e abrir Metro

Execute a partir do checkout deste PR, para servir o JavaScript e as dependências do SDK corrigido. Use o IPv4 privado do PC e o ID do workflow validado, indicado na entrega:

```bash
gh pr checkout 28 && bash scripts/android/run-local.sh 192.168.1.10 RUN_ID
```

Pré-requisitos: Node 22, Python 3.12, `gh` autenticado, `adb` e celular autorizado por USB. PC e celular devem compartilhar uma rede Wi-Fi confiável. O comando baixa o artifact **android-health-connect-debug-apk**, instala com `adb install -r`, inicia FastAPI/SQLite e Metro na LAN e abre o development client no telefone. O APK contém código nativo de desenvolvimento e usa o bundle servido pelo Metro. O launcher usa o parâmetro de onboarding do Dev Client para abrir diretamente o Vytal; cadastro e permissões do app seguem o fluxo normal.

O launcher reutiliza SQLite, chaves de autenticação e `.env` existentes. Se houver bancos ambíguos, informe `VYTAL_DATABASE_PATH`. Ctrl+C encerra os serviços e mantém os dados. A instalação usa a identidade de assinatura debug do template anterior; se o Android rejeitar a atualização por certificado diferente, preserve o app instalado e confira a origem do APK.

Download pelo navegador: abra o workflow verde desta branch, baixe **Artifacts → android-health-connect-debug-apk** e extraia `app-debug.apk`. A instalação equivalente é `adb install -r app-debug.apk`. Preserve o armazenamento do app, o SQLite e as chaves locais; desinstalação e reset não fazem parte do procedimento.

## Reproduzir build e smoke

Ubuntu, Node 22, Python 3.12, JDK 17, Android SDK 36/build-tools 36 e um emulador Android 14/API 34 Google APIs dedicado, com `adb` disponível. Defina `ANDROID_HOME` para o SDK:

```bash
python3.12 -m venv .venv
.venv/bin/pip install -r backend/requirements-prod.txt
bash scripts/android/build.sh && .venv/bin/python scripts/android/smoke.py
```

O build recria o projeto Android e compila o APK universal debug para Samsung ARM64 e emulador x86_64. O smoke recusa dispositivos físicos. O APK auxiliar `org.vytal.smokefixture` grava 123 passos sintéticos no serviço Health Connect real do emulador, com sua própria origem; ele é separado do APK Vytal.

O smoke inicia o APK com Metro e FastAPI/SQLite local, acessado pelo Android em `10.0.2.2`. O manifest e o bundle usam esse endereço. O fluxo cobre:

- Boot sem red screen; cadastro, login e dashboard.
- Rota Google Fit abrindo o Chrome pela ponte nativa WebBrowser.
- Fontes de dados e consentimento nativo Health Connect negado.
- Permissões concedidas e leitura nativa sem registros.
- Importação de passos da origem sintética, releitura e deduplicação.
- Erro de rede e reinício do backend preservando o mesmo SQLite.
- Isolamento A/B, retorno à conta A e reinstalação `-r` preservando a sessão.

No AVD, a negação usa a UI nativa; a concessão para leitura é aplicada por `pm grant`, seguida de chamadas reais ao SDK Health Connect. O SQLite do smoke é temporário, com contas e chaves exclusivamente de teste. A execução publica screenshots, árvores de UI, logcat, logs de Metro/backend e `checks.json`, inclusive em caso de falha. O CI encerra os compiladores antes do emulador, exige KVM e limita CPU/RAM do AVD. Erros de UI transitórios recebem tentativas limitadas; red screens e ANRs do Vytal falham o teste.

## Evidências e limites

Os workflows vinculados ao PR registram os resultados por commit. O artifact `android-runtime-evidence` contém a lista exata das etapas concluídas e as telas correspondentes. Os testes locais do backend passaram: **445 testes**, cobertura **84,24%**. Também passaram os **73 testes unitários do app**, integração cliente/API/SQLite, teste de manifest/bundle Metro com Node 22, TypeScript, lint e **4 testes de persistência do launcher Linux**.

As primeiras execuções publicaram APKs que passaram build, inspeção nativa e `expo-doctor`, mas o smoke detectou ANR do Pixel Launcher do AVD antes de alcançar o login. Esses resultados permanecem no histórico. A validação de entrega deve usar o workflow de runtime verde, com seus artifacts correspondentes.

Permissões e dados históricos reais do Samsung/Garmin permanecem como homologação em dispositivo físico. Os passos sintéticos do emulador têm origem própria e não certificam a integração Garmin real. Google Fit é exercitado até a abertura do browser; o smoke usa credenciais locais sintéticas e não executa login OAuth real.
