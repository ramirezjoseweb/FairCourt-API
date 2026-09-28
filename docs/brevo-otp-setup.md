# OTP real con OVHcloud y Brevo

Esta guía activa el envío de códigos desde `FairCourt <acceso@faircourt.es>`.
Las contraseñas, códigos de doble factor y claves SMTP deben introducirse
directamente en cada servicio. No deben pegarse en chats, capturas, incidencias
ni archivos versionados.

## 1. Registrar el dominio

1. Comprueba en OVHcloud que `faircourt.es` está disponible. Si aparece ocupado,
   detén el proceso y elige otro nombre antes de configurar Brevo.
2. Contrata solo el dominio, sin alojamiento, IP dedicada ni complementos de
   marketing.
3. Usa una cuenta propiedad del responsable de FairCourt y activa el doble
   factor.
4. Mantén la renovación manual y comprueba que los avisos de caducidad llegan a
   una dirección que revises habitualmente.
5. Activa DNSSEC. Si el dominio incluye gratuitamente un buzón Starter, crea
   `acceso@faircourt.es`; no es necesario contratar un buzón de pago para enviar
   los OTP.

## 2. Autenticar el dominio en Brevo

1. Crea una cuenta gratuita de Brevo bajo el mismo responsable.
2. En **Configuración > Remitentes, dominios e IP > Dominios**, añade
   `faircourt.es` como dominio raíz.
3. Usa IP compartida y elige registros DNS individuales. No delegues los
   servidores NS del dominio ni autorices una conexión automática con OVH.
4. Copia en la zona DNS de OVH todos los registros que Brevo muestre. Respeta
   exactamente el tipo, nombre y valor de cada registro. Debe existir un único
   registro DMARC.
5. No sustituyas otros registros MX o TXT sin revisar para qué sirven. Un
   registro DNS puede tardar hasta 48 horas en propagarse.
6. Continúa solo cuando Brevo muestre el dominio como autenticado.
7. Crea el remitente `FairCourt <acceso@faircourt.es>`.

Los valores concretos de DKIM y demás registros son únicos para la cuenta. Por
ese motivo no deben copiarse de esta guía ni de otro proyecto.

## 3. Crear las credenciales SMTP

1. Abre **Configuración > SMTP y API > SMTP**.
2. Genera una clave SMTP estándar con un nombre reconocible, por ejemplo
   `FairCourt piloto`.
3. Guarda inmediatamente la clave completa en un gestor de contraseñas. Brevo
   no vuelve a mostrarla y habrá que generar otra si se pierde.
4. Copia también el usuario SMTP que muestra Brevo. No uses una clave API ni la
   contraseña de acceso a Brevo.

## 4. Activar FairCourt

Copia `faircourt-backend/.env.example` como `faircourt-backend/.env`, genera una
`SECRET_KEY` privada y completa únicamente en ese archivo:

```dotenv
OTP_DELIVERY_MODE=smtp
DEV_PRINT_OTP=false
SMTP_HOST=smtp-relay.brevo.com
SMTP_PORT=587
SMTP_USERNAME=<usuario SMTP mostrado por Brevo>
SMTP_PASSWORD=<clave SMTP generada por Brevo>
SMTP_FROM_EMAIL=acceso@faircourt.es
SMTP_FROM_NAME=FairCourt
SMTP_STARTTLS=true
SMTP_USE_SSL=false
SMTP_TIMEOUT_SECONDS=10
```

El archivo `.env` está ignorado por Git. Antes de arrancar el backend, verifica
con `git check-ignore faircourt-backend/.env` que continúa siendo privado.

## 5. Primera prueba

1. Reinicia Uvicorn para cargar el `.env`.
2. Solicita un OTP únicamente para una vivienda de prueba asociada a tu propio
   correo.
3. Comprueba el remitente, la carpeta de spam y el estado de entrega en Brevo.
4. Confirma que el OTP no aparece en la terminal, caduca, solo funciona una vez
   y no puede solicitarse repetidamente durante el cooldown.
5. Prueba un código incorrecto, uno caducado y la reutilización del código ya
   consumido.
6. Cuando todo funcione, repite con una segunda dirección de confianza antes de
   habilitar el envío para residentes reales.

Si el puerto 587 estuviera bloqueado por el futuro proveedor de alojamiento,
comprueba primero su política de red. Solo entonces valora el puerto 2525
admitido por Brevo; no desactives TLS para solucionar un problema de conexión.
