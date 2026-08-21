# MULTIVERSE Companion — v1.80 RC1

PWA estática preparada para GitHub Pages.

La aplicación guarda el estado localmente en el dispositivo y ofrece respaldos JSON desde **⚙ Datos y respaldo**.

## Publicar la RC1

1. Sube a la raíz del repositorio el archivo `MULTIVERSE-v1.80-RC1-PWA.zip` sin cambiarle el nombre.
2. En **Settings → Pages → Build and deployment → Source**, selecciona **GitHub Actions**.
3. El workflow `Deploy MULTIVERSE PWA` descomprime y publica automáticamente la aplicación.

La fuente de Pages ya fue configurada. Este commit vuelve a disparar el deployment después de esa configuración.

Cuando termine el deployment, la PWA quedará disponible en GitHub Pages y podrá instalarse desde Safari/Chrome.