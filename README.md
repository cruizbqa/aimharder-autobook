# aimharder-autobook 🏋️

Automatización de reservas en [BOX_NAME.aimharder.com](https://BOX_NAME.aimharder.com)
usando la API interna de AimHarder + GitHub Actions.

El sistema respeta la **ventana de reserva de 72 horas**: el workflow se ejecuta
diariamente y reserva la clase que ocurrirá 3 días después (configurable).

---

## Estructura del proyecto

```
aimharder-autobook/
├── src/
│   ├── aimharder_client.py   # Cliente API reutilizable
│   └── main.py               # Script de entrada (lee env vars)
├── tests/
│   └── test_booking_logic.py # Pytest: ventana 72h, matching, auth
├── .github/
│   └── workflows/
│       └── autobook.yml      # GitHub Actions workflow
├── requirements.txt
└── README.md
```

---

## Configuración en GitHub (Secrets)

Ve a **Settings → Secrets and variables → Actions → New repository secret**
y añade los siguientes secretos:

| Secret | Descripción | Ejemplo |
|---|---|---|
| `AIMHARDER_EMAIL` | Email de tu cuenta AimHarder | `[EMAIL_ADDRESS]` |
| `AIMHARDER_PASSWORD` | Contraseña | `[PASSWORD]` |
| `BOX_NAME` | Subdominio de tu box | `[BOX_NAME]` |
| `BOX_ID` | ID numérico del box *(ver abajo)* | `[BOX_ID]` |
| `BOOKING_GOALS` | JSON con objetivos de reserva | ver abajo |
| `FAMILY_ID` | *(Opcional)* ID familiar | `[FAMILY_ID]` |
| `PROXY` | *(Opcional)* `socks5://[IP_ADDRESS]` | — |

> ⚠️ **NUNCA** pongas credenciales directamente en el código o en el YAML.

### Cómo encontrar el BOX_ID

1. Abre Chrome DevTools (F12) → pestaña **Network**.
2. Accede a `https://[BOX_NAME].aimharder.com/schedule` con tu cuenta.
3. Filtra por `bookings` → inspecciona el payload de la request.
4. El campo `box` es tu `BOX_ID`.

### Formato de BOOKING_GOALS

```json
{
  "0": {"time": "0700", "name": "WOD"},
  "1": {"time": "1200", "name": "WOD"},
  "3": {"time": "0700", "name": "WOD"},
  "4": {"time": "0700", "name": "WOD"}
}
```

- **Clave**: día de la semana como entero, `0` = Lunes … `6` = Domingo.
- **`time`**: hora en formato `HHMM`.
- **`name`**: fragmento del nombre de la clase (case-insensitive).

Para **múltiples clases** el mismo día:

```json
{
  "0": [
    {"time": "0700", "name": "WOD"},
    {"time": "1200", "name": "OPEN BOX"}
  ]
}
```

---

## Ejecución local

```bash
# Instalar dependencias
pip install -r requirements.txt

# Ejecutar (con variables de entorno)
export EMAIL="[EMAIL_ADDRESS]"
export PASSWORD="[PASSWORD]"
export BOX_NAME="[BOX_NAME]"
export BOX_ID="[BOX_ID]"
export BOOKING_GOALS='{"0":{"time":"0700","name":"WOD"}}'
export DAYS_IN_ADVANCE="3"

python src/main.py
```

---

## Tests

```bash
pip install pytest
pytest tests/ -v
```

---

## GitHub Actions workflow

El workflow (`.github/workflows/autobook.yml`) se ejecuta:

- **Automáticamente** cada día a las 00:05 UTC (`cron: "5 0 * * *"`).
- **Manualmente** desde *Actions → AimHarder Auto-Booking → Run workflow*,
  con opción de ajustar `days_in_advance` y activar `dry_run`.

### Lógica de la ventana de 72 horas

```
Hoy (script corre)      +72h                 Clase
─────────────────────────┼────────────────────┼───▶
     00:05 UTC           ventana se abre      clase
```

El script apunta 3 días hacia adelante. Cuando corre el lunes a las 00:05,
reserva la clase del jueves. La ventana de AimHarder abre exactamente 72h
antes, así que el intento de reserva coincide con la apertura.

Si el box tiene un `hours_in_advance` diferente, ajusta la variable
`DAYS_IN_ADVANCE` en el workflow (o pasa el parámetro al trigger manual).

---

## Notas sobre bloqueos de IP

AimHarder puede bloquear IPs fuera de España con un error 403.
Si ejecutas el workflow desde GitHub Actions (servidores en US/EU),
configura el secret `PROXY` con un proxy español (socks5 o https).

> 💡 Usa proxies de confianza: tus credenciales pasan a través de ellos.

---

## Licencia

MIT
