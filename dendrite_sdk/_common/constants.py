import os

DENDRITE_API_BASE_URL = (
    "http://localhost:8000/api/v1"
    if os.environ.get("DENDRITE_DEV")
    else "https://dendrite-server.azurewebsites.net/api/v1"
)


STEALTH_ARGS = [
    "--no-pings",
    "--mute-audio",
    "--no-first-run",
    "--no-default-browser-check",
    "--disable-cloud-import",
    "--disable-gesture-typing",
    "--disable-offer-store-unmasked-wallet-cards",
    "--disable-offer-upload-credit-cards",
    "--disable-print-preview",
    "--disable-voice-input",
    "--disable-wake-on-wifi",
    "--disable-cookie-encryption",
    "--ignore-gpu-blocklist",
    "--enable-async-dns",
    "--enable-simple-cache-backend",
    "--enable-tcp-fast-open",
    "--prerender-from-omnibox=disabled",
    "--enable-web-bluetooth",
    "--disable-features=AudioServiceOutOfProcess,IsolateOrigins,site-per-process,TranslateUI,BlinkGenPropertyTrees",
    "--aggressive-cache-discard",
    "--disable-extensions",
    "--disable-ipc-flooding-protection",
    "--disable-blink-features=AutomationControlled",
    "--test-type",
    "--enable-features=NetworkService,NetworkServiceInProcess,TrustTokens,TrustTokensAlwaysAllowIssuance",
    "--disable-component-extensions-with-background-pages",
    "--disable-default-apps",
    "--disable-breakpad",
    "--disable-component-update",
    "--disable-domain-reliability",
    "--disable-sync",
    "--disable-client-side-phishing-detection",
    "--disable-hang-monitor",
    "--disable-popup-blocking",
    "--disable-prompt-on-repost",
    "--metrics-recording-only",
    "--safebrowsing-disable-auto-update",
    "--password-store=basic",
    "--autoplay-policy=no-user-gesture-required",
    "--use-mock-keychain",
    "--force-webrtc-ip-handling-policy=disable_non_proxied_udp",
    "--webrtc-ip-handling-policy=disable_non_proxied_udp",
    "--disable-session-crashed-bubble",
    "--disable-crash-reporter",
    "--disable-dev-shm-usage",
    "--force-color-profile=srgb",
    "--disable-translate",
    "--disable-background-networking",
    "--disable-background-timer-throttling",
    "--disable-backgrounding-occluded-windows",
    "--disable-infobars",
    "--hide-scrollbars",
    "--disable-renderer-backgrounding",
    "--font-render-hinting=none",
    "--disable-logging",
    "--enable-surface-synchronization",
    "--run-all-compositor-stages-before-draw",
    "--disable-threaded-animation",
    "--disable-threaded-scrolling",
    "--disable-checker-imaging",
    "--disable-new-content-rendering-timeout",
    "--disable-image-animation-resync",
    "--disable-partial-raster",
    "--blink-settings=primaryHoverType=2,availableHoverTypes=2,"
    "primaryPointerType=4,availablePointerTypes=4",
    "--disable-layer-tree-host-memory-pressure",
]
