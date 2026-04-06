# aimharder-autobook 🏋️

Automatización de reservas en [BOX_NAME.aimharder.com](https://BOX_NAME.aimharder.com) usando la API interna de AimHarder + GitHub Actions.

Este proyecto ha sido refactorizado siguiendo principios **SOLID** y una arquitectura limpia para ser robusto y fácil de mantener. Además, integra **Playwright** para superar bloqueos anti-bot en el inicio de sesión.

---

## Estructura del Proyecto (SOLID)

La lógica se divide en capas de responsabilidad clara:

```
aimharder-autobook/
├── src/
│   ├── config/           # Gestión de settings y .env
│   ├── core/             # Excepciones globales
│   ├── domain/           # Lógica de negocio (API y Reservas)
│   ├── infrastructure/   # Implementaciones técnicas (Auth Playwright, HTTP)
│   └── main.py           # Orquestador (Entry Point)
├── tests/
│   └── unit/             # Tests unitarios organizados por dominio
├── .github/
│   └── workflows/
│       └── autobook.yml  # GitHub Actions (CD - Workflow Dispatch)
├── requirements.txt
└── README.md
```

---

## Configuración en GitHub (Secrets)

Ve a **Settings → Secrets and variables → Actions → New repository secret** y añade:

| `FAMILY_ID` | (Opcional) ID familiar |
| `PROXY` | (Opcional) `socks5://[IP_ADDRESS]` |
| `TELEGRAM_TOKEN` | (Opcional) Token de tu bot de @BotFather |
| `TELEGRAM_CHAT_ID` | (Opcional) Tu ID numérico (de @userinfobot) |

### Cómo encontrar el BOX_ID

1. Abre Chrome DevTools (F12) → pestaña **Network**.
2. Accede a la agenda de tu box en AimHarder.
3. Filtra por `bookings` → inspecciona el payload. El campo `box` es tu `BOX_ID`.

---

## Ejecución Local

Para ejecutar el bot localmente, asegúrate de tener un archivo `.env` en la raíz con las variables mencionadas arriba.

```bash
# 1. Instalar dependencias y navegadores
pip install -r requirements.txt
python -m playwright install chromium

# 2. Ejecutar como módulo
python -m src.main

# 3. Probar Notificaciones de Telegram
python tests/test_telegram.py
```

---

## Desarrollo y Tests

El proyecto usa `pytest` para las pruebas unitarias.

```bash
# Ejecutar todos los tests
python -m pytest tests/
```

---

## Lógica de la Ventana de 72 horas y Scheduling

AimHarder abre reservas exactamente **72h antes** de la clase (normalmente a las 07:00:00). 

Para garantizar la máxima precisión y evitar los retrasos aleatorios del `schedule` nativo de GitHub, este proyecto utiliza un disparador externo:

1. **Scheduler**: Se recomienda usar [cron-job.org](https://cron-job.org) configurado para las **07:00:05 (Europe/Madrid)**.
2. **Trigger**: El scheduler llama a la API de GitHub (`workflow_dispatch`) para arrancar el bot al segundo exacto.
3. **Control en Python**: El script `src/main.py` calcula la fecha objetivo sumando `TARGET_HOURS` (default 72) y, si arranca unos segundos antes, espera al momento preciso para disparar la reserva.

### Manejo de Reservas Duplicadas
El bot detecta si ya tienes una clase reservada en el mismo horario (`NOPUEDESRESERVAMISMAHORA`). En ese caso:
- **Aborta inmediatamente** los reintentos para no bloquear la cuenta.
- Envía una **notificación informativa** por Telegram en lugar de un error de fallo.

---

## Anti-Bot y Seguridad

El inicio de sesión utiliza **Playwright (Headless Chrome)**. Esto emula un navegador real, lo que permite:
1. Evitar bloqueos de "Contraseña incorrecta" producidos por detección de scripts.
2. Gestionar automáticamente el **banner de cookies** y avisos legales.
3. Capturar las cookies de sesión (`amhrdrauth`) de forma segura.
4. Seguir operando a través de la API oficial con la sesión ya establecida.

---

## Licencia

MIT
