import { jsx as _jsx } from "react/jsx-runtime";
import { createRoot } from "react-dom/client";
import App from "./App";
import "./styles.css";
const rootElement = document.getElementById("root");
if (!rootElement) {
    throw new Error("Missing root element");
}
Office.onReady(() => {
    const root = createRoot(rootElement);
    root.render(_jsx(App, {}));
});
