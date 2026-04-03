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
│       └── autobook.yml  # GitHub Actions (CD)
├── requirements.txt
└── README.md
```

---

## Configuración en GitHub (Secrets)

Ve a **Settings → Secrets and variables → Actions → New repository secret** y añade:

| Secret | Descripción |
|---|---|
| `AIMHARDER_EMAIL` | Email de tu cuenta AimHarder |
| `AIMHARDER_PASSWORD` | Contraseña |
| `BOX_NAME` | Subdominio de tu box (ej: `crossfit-test`) |
| `BOX_ID` | ID numérico del box (ver abajo) |
| `CLASS_TIME` | Hora de la clase en formato `HHMM` (ej: `0700`) |
| `CLASS_NAME` | Fragmento del nombre de la clase (ej: `CrossFit`) |
| `FAMILY_ID` | (Opcional) ID familiar |
| `PROXY` | (Opcional) `socks5://[IP_ADDRESS]` |

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
```

---

## Desarrollo y Tests

El proyecto usa `pytest` para las pruebas unitarias.

```bash
# Ejecutar todos los tests
python -m pytest tests/
```

---

## Lógica de la Ventana de 72 horas

AimHarder abre reservas exactamente **72h antes** de la clase. El workflow de GitHub está configurado para dispararse en el momento exacto de apertura (ajustado por zona horaria de España) para asegurar el puesto en clases muy demandadas.

El script calcula automáticamente la fecha objetivo sumando las horas configuradas en `TARGET_HOURS` (por defecto 72) a la hora actual.

---

## Anti-Bot y Seguridad

El inicio de sesión utiliza **Playwright (Headless Chrome)**. Esto emula un navegador real, lo que permite:
1. Evitar bloqueos de "Contraseña incorrecta" producidos por detección de scripts.
2. Capturar las cookies de sesión (`amhrdrauth`) de forma segura.
3. Seguir operando a través de la API oficial con la sesión ya establecida.

---

## Licencia

MIT
