import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useState } from "react";
export default function CellTagger({ label, tag, onTagged }) {
    const [address, setAddress] = useState("Not tagged");
    const [value, setValue] = useState(0);
    const captureCell = async () => {
        await Excel.run(async (context) => {
            const activeCell = context.workbook.getActiveCell();
            activeCell.load(["address", "values"]);
            await context.sync();
            const cellValue = Number(activeCell.values[0][0]);
            const taggedCell = { tag, address: activeCell.address, value: cellValue };
            setAddress(activeCell.address);
            setValue(cellValue);
            onTagged(taggedCell);
        });
    };
    return (_jsx("div", { className: "rounded-2xl border border-slate-800 bg-slate-950/60 p-4", children: _jsxs("div", { className: "flex items-center justify-between gap-4", children: [_jsxs("div", { children: [_jsx("p", { className: "text-sm text-slate-400", children: label }), _jsx("p", { className: "mt-1 font-mono text-sm text-cyan-300", children: address }), _jsx("p", { className: "mt-1 text-lg font-medium text-slate-100", children: value })] }), _jsx("button", { className: "rounded-full border border-cyan-400 px-4 py-2 text-sm", onClick: captureCell, children: "Tag Active Cell" })] }) }));
}
