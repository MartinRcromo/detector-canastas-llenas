"use client";

import { useState } from "react";

interface PdfActionsProps {
  queryString: string;
}

export function PdfActions({ queryString }: PdfActionsProps) {
  const [generatedUrl, setGeneratedUrl] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleGenerate = async () => {
    setLoading(true);
    setGeneratedUrl(null);
    const response = await fetch(`/api/catalog/pdf?${queryString}`);
    const data = await response.json();
    setGeneratedUrl(data.url ?? null);
    setLoading(false);
  };

  return (
    <div className="flex flex-wrap gap-2">
      <a
        href={`/api/catalog/pdf?${queryString}&download=1`}
        className="rounded-md bg-emerald-500 px-4 py-2 text-sm font-semibold text-slate-900 hover:bg-emerald-400"
      >
        Exportar PDF directo
      </a>
      <button
        type="button"
        onClick={handleGenerate}
        className="rounded-md border border-emerald-500 px-4 py-2 text-sm font-semibold text-emerald-300 hover:bg-emerald-950"
      >
        {loading ? "Generando..." : "Generar y guardar en Storage"}
      </button>
      {generatedUrl && (
        <a href={generatedUrl} target="_blank" className="text-sm text-emerald-400 underline" rel="noreferrer">
          Ver PDF guardado
        </a>
      )}
    </div>
  );
}
