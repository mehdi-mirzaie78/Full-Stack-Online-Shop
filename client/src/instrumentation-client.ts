import { reportError } from "./lib/error-reporting";

window.addEventListener("error", (event) => reportError("browser_error", event.error));
window.addEventListener("unhandledrejection", (event) => reportError("unhandled_rejection", event.reason));
