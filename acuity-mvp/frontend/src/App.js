import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useEffect, useState } from "react";
import CellTagger from "./components/CellTagger";
import ResultsDashboard from "./components/ResultsDashboard";
import { fetchMacroFactors, runSimulation } from "./api/client";
const defaultRequest = {
    deal_name: "Project Atlas",
    firm_name: "North Peak Capital",
    base_interest_rate: 0.055,
    base_exit_multiple: 10.5,
    base_exit_ebitda: 18,
    entry_ebitda: 12,
    entry_multiple: 10,
    initial_debt: 60,
    hold_period_years: 5,
    iterations: 10000,
    tagged_inputs: []
};
export default function App() {
    const [request, setRequest] = useState(defaultRequest);
    const [result, setResult] = useState(null);
    const [macroFactors, setMacroFactors] = useState([]);
    const [loading, setLoading] = useState(false);
    useEffect(() => {
        let active = true;
        fetchMacroFactors()
            .then((response) => {
            if (active)
                setMacroFactors(response.factors);
        })
            .catch(() => {
            if (active)
                setMacroFactors([]);
        });
        return () => {
            active = false;
        };
    }, []);
    const handleTaggedCell = (cell) => {
        setRequest((current) => {
            const remaining = current.tagged_inputs.filter((item) => item.tag !== cell.tag);
            const tagged_inputs = [...remaining, cell];
            const next = { ...current, tagged_inputs };
            if (cell.tag === "base_interest_rate")
                next.base_interest_rate = cell.value;
            if (cell.tag === "base_exit_multiple")
                next.base_exit_multiple = cell.value;
            if (cell.tag === "base_exit_ebitda")
                next.base_exit_ebitda = cell.value;
            return next;
        });
    };
    const handleRun = async () => {
        setLoading(true);
        try {
            const response = await runSimulation(request);
            setResult(response);
            setMacroFactors(response.macro_factors);
        }
        finally {
            setLoading(false);
        }
    };
    return (_jsx("main", { className: "min-h-screen bg-slate-950 p-6 text-slate-100", children: _jsxs("div", { className: "mx-auto max-w-5xl space-y-6", children: [_jsxs("header", { className: "rounded-3xl border border-cyan-500/30 bg-slate-900/80 p-6", children: [_jsx("p", { className: "text-sm uppercase tracking-[0.35em] text-cyan-300", children: "Acuity" }), _jsx("h1", { className: "mt-2 text-4xl font-semibold", children: "Probabilistic Risk Infrastructure" }), _jsx("p", { className: "mt-3 max-w-3xl text-slate-300", children: "Tag model drivers in Excel, push them into the simulation engine, and measure the probability of sub-10% IRR and covenant breach before IC." })] }), _jsxs("section", { className: "grid gap-6 lg:grid-cols-[1.1fr_0.9fr]", children: [_jsxs("div", { className: "rounded-3xl border border-slate-800 bg-slate-900 p-6", children: [_jsx("h2", { className: "text-xl font-medium", children: "Excel Input Mapping" }), _jsx("p", { className: "mt-2 text-sm text-slate-400", children: "Capture the active cell in Excel and map it to the key drivers used by the backend." }), _jsxs("div", { className: "mt-6 space-y-4", children: [_jsx(CellTagger, { label: "Base Interest Rate", tag: "base_interest_rate", onTagged: handleTaggedCell }), _jsx(CellTagger, { label: "Base Exit Multiple", tag: "base_exit_multiple", onTagged: handleTaggedCell }), _jsx(CellTagger, { label: "Base Exit EBITDA", tag: "base_exit_ebitda", onTagged: handleTaggedCell })] }), _jsx("button", { className: "mt-6 rounded-full bg-cyan-400 px-5 py-3 font-medium text-slate-950 disabled:opacity-50", disabled: loading, onClick: handleRun, children: loading ? "Running 10,000 sims..." : "Run Simulation" })] }), _jsx(ResultsDashboard, { result: result, macroFactors: macroFactors })] })] }) }));
}
