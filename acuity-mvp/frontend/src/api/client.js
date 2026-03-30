const API_BASE_URL = "http://localhost:8000";
export async function runSimulation(payload) {
    const response = await fetch(`${API_BASE_URL}/simulate`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify(payload)
    });
    if (!response.ok) {
        throw new Error(`Simulation failed with status ${response.status}`);
    }
    return response.json();
}
export async function fetchMacroFactors() {
    const response = await fetch(`${API_BASE_URL}/macro/factors`);
    if (!response.ok) {
        throw new Error(`Macro factor fetch failed with status ${response.status}`);
    }
    return response.json();
}
