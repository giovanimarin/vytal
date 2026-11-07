# Vytal no Samsung — Windows 10/11

Instale **[Node.js 22 LTS](https://nodejs.org)** e **[Python 3.12](https://www.python.org/downloads/windows/)** com Launcher/PATH; reabra o terminal. Use esta branch do projeto e computador/Samsung no mesmo **Wi-Fi privado confiável**, sem convidados/VPN. Não precisa de Java, Android Studio, Gradle, Expo Go ou credenciais Garmin no Vytal.

Na raiz do projeto:

```powershell
.\vytal.ps1 install
.\vytal.ps1 start
```

Se o PowerShell bloquear scripts, use ` .\vytal.bat install` / ` .\vytal.bat start`. O wrapper libera somente aquele processo; não exige administrador nem altera políticas permanentes.

**Install:** prepara dependências e reutiliza o [APK debug do CI](https://github.com/giovanimarin/vytal/actions/runs/42396895440), artefato **android-health-connect-debug-apk**. Com `gh` autorizado, baixa automaticamente; sem ele, abre o GitHub (pode exigir login) e uma janela para selecionar o ZIP/APK baixado. Alternativa: `install -ApkPath C:\Downloads\artefato.zip`. Se expirou, mantenedor deve regenerar no CI; não usar APK desconhecido.

Com ADB/USB autorizado, instala preservando dados. Sem ADB, copie o APK indicado ao Samsung por USB/Transferência de arquivos, abra em **Meus Arquivos** e autorize essa origem se confiar nela. Não desinstale um app existente para contornar erro de assinatura. [ADB standalone](https://developer.android.com/tools/releases/platform-tools) é opcional, sem SDK completo; extraia em `.local-vytal/platform-tools`. Para USB, ative depuração e aceite RSA. Políticas Samsung podem impedir instalação; o script não as modifica.

**Start:** seleciona IPv4 privado (oferece escolha se houver várias interfaces), abre backend/Metro e testa saúde. No navegador do Samsung abra **`http://IP-MOSTRADO:8000/health`**: deve retornar `status: ok`. Abra Vytal → **Enter URL manually** → `http://IP-MOSTRADO:8081`, ou QR do Metro. Por ADB tenta abrir automaticamente. O APK carrega a API correta pelo Metro; trocar IP não exige recompilar/reinstalar.

Entre/cadastre-se → **Fontes de Dados → Conexão Saúde → Conectar / conceder leitura**. Primeiro confirme que o Garmin Connect compartilhou um registro com Health Connect. Importe, compare valor/data/origem e repita para conferir duplicatas. Sem registro disponível na Conexão Saúde, não haverá importação.

**Problemas:** use `start -Address 192.168.x.x` ou `-Device SERIAL` se necessário. Porta ocupada: feche o terminal antigo. Sem `/health` no celular: confira IP, rede/VPN, isolamento do roteador e Firewall Windows para Python/Node **somente na rede privada/sub-rede local**. Nenhuma regra é criada; não abrir portas no roteador. HTTP/Metro são exclusivos de desenvolvimento confiável. Permissão negada: ajuste Health Connect. Feche as duas janelas para parar; reinicie com `start`, sem reinstalar. Feche janelas antigas antes de mudar IP.

**Dados:** preserva SQLite/chaves. Se existem bancos em `backend/data/` e `.local-vytal/data/`, exige `-DatabasePath CAMINHO`; não copia/apaga dados. Não apagar `.local-vytal/`. Esta PR depende da **#25**, sem presumir merge da **#24**. Sem cloud, serviços pagos ou deploy. [Evidências/limitações](WINDOWS-VALIDATION.md); [categorias e histórico](HEALTH-CONNECT.md). **Homologação com registro Garmin no Samsung físico permanece pendente.**
