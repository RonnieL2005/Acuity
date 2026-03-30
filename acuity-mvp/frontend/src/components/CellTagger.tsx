import React, { useState } from "react";
import { TaggedCellInput } from "../api/client";

type CellTaggerProps = {
  label: string;
  tag: string;
  onTagged: (cell: TaggedCellInput) => void;
};

export default function CellTagger({ label, tag, onTagged }: CellTaggerProps) {
  const [address, setAddress] = useState<string>("Not tagged");
  const [value, setValue] = useState<number>(0);

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

  return (
    <div className="rounded-2xl border border-slate-800 bg-slate-950/60 p-4">
      <div className="flex items-center justify-between gap-4">
        <div>
          <p className="text-sm text-slate-400">{label}</p>
          <p className="mt-1 font-mono text-sm text-cyan-300">{address}</p>
          <p className="mt-1 text-lg font-medium text-slate-100">{value}</p>
        </div>
        <button className="rounded-full border border-cyan-400 px-4 py-2 text-sm" onClick={captureCell}>
          Tag Active Cell
        </button>
      </div>
    </div>
  );
}
