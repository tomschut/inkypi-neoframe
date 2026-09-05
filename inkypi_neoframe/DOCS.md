# Install on Home Assistant OS

This add-on currently supports **amd64 (x86-64)** HAOS. It builds InkyPi locally on your HAOS machine, so the first installation needs internet access and can take several minutes.

1. Extract `inkypi-neoframe-haos.tar.gz` on your computer.
2. Use Home Assistant's Samba share to copy the extracted `inkypi_neoframe` folder into the `addons` share. The resulting path must be `/addons/inkypi_neoframe/config.yaml`. Copy the entire folder, including Dockerfile, scripts and src.
3. In Home Assistant, open **Settings → Apps → App store** (called **Add-ons → Add-on store** on older versions). Use the menu to **Check for updates**; reload the page if necessary.
4. Find **InkyPi NeoFrame** under **Local apps**, choose **Install**, then **Start**. Enable **Start on boot** and, optionally, **Watchdog**.
5. Select **Open Web UI**, or visit `http://<HAOS-IP>:8084/`. Create your image content and playlists in InkyPi.
6. Set the Project 1 firmware's `image_url` to `http://<HAOS-IP>:8084/api/current_frame`.

The firmware must support the packed Spectra-6 format. The first successful render makes a 960000-byte frame available. `/api/current_image` remains a PNG. If port 8084 is already used on HAOS, change the host port in the app's Network settings and use that port in the firmware URL.

## Storage and updates

Device settings, playlists, uploaded images, the current PNG/BIN and API keys live in Supervisor's persistent `/data` volume. They survive container replacement and are included in app backups. Configuration is managed in the InkyPi UI; there are no extra YAML options. Back up the app before uninstalling it.

To update a local installation, replace the add-on folder and use **Rebuild** from its menu. Builds preserve `/data`. The startup script seeds defaults only when a persistent file or image directory does not yet exist.

The web UI and firmware endpoint are directly available on the configured LAN port and have no Home Assistant login protection. Keep the port on your trusted LAN. Ingress is not enabled because upstream uses root-relative URLs.

## Scope and verification

The add-on needs no hardware devices, privileged mode, host networking, Docker socket or Supervisor API access. It uses the default protection settings. It renders remotely for the ESP32; no display attaches to the HAOS host.

The amd64 container is tested locally with Podman, including persistent data after replacement. Actual installation under Supervisor and the physical panel remain environment-specific checks. ARM64 is not advertised or tested in this release.

Reference: https://developers.home-assistant.io/docs/apps/tutorial/
