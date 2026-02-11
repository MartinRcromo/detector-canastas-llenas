import { CATEGORIES, MODELS, POSITIONS, SIDES, VEHICLE_MAKES } from "@/lib/catalog/constants";
import { ParsedQueryHints } from "@/lib/catalog/types";

const categoryMap: Record<string, string> = {
  paragolpes: "PARAGOLPES",
  faro: "FARO TRASERO",
  "faro trasero": "FARO TRASERO",
  optica: "OPTICA",
  óptica: "OPTICA",
  radiador: "RADIADOR",
  espejo: "ESPEJO",
};

const makeMap: Record<string, string> = VEHICLE_MAKES.reduce((acc, make) => {
  acc[make.toLowerCase()] = make;
  return acc;
}, {} as Record<string, string>);

const modelMap: Record<string, string> = MODELS.reduce((acc, model) => {
  acc[model.toLowerCase()] = model;
  return acc;
}, {} as Record<string, string>);

export function parseNaturalQuery(q?: string): ParsedQueryHints {
  if (!q) return {};
  const normalized = q.toLowerCase();
  const hints: ParsedQueryHints = {};

  for (const [token, value] of Object.entries(categoryMap)) {
    if (normalized.includes(token)) {
      hints.category = value;
      break;
    }
  }

  for (const make of VEHICLE_MAKES) {
    if (normalized.includes(make.toLowerCase())) {
      hints.make = makeMap[make.toLowerCase()];
      break;
    }
  }

  for (const model of MODELS) {
    if (normalized.includes(model.toLowerCase())) {
      hints.model = modelMap[model.toLowerCase()];
      break;
    }
  }

  if (normalized.includes("delanter")) hints.position = POSITIONS[0];
  if (normalized.includes("traser")) hints.position = POSITIONS[1];
  if (normalized.includes("izq") || normalized.includes("izquier")) hints.side = SIDES[0];
  if (normalized.includes("der") || normalized.includes("derech")) hints.side = SIDES[1];

  const rangeMatch = normalized.match(/(19\d{2}|20\d{2})\s*[-/]\s*(19\d{2}|20\d{2})/);
  if (rangeMatch) {
    hints.year = `${rangeMatch[1]}-${rangeMatch[2]}`;
  } else {
    const yearMatch = normalized.match(/\b(19\d{2}|20\d{2})\b/);
    if (yearMatch) hints.year = yearMatch[1];
  }

  const engineMatch = normalized.match(/\b(\d\.\d|tdci|d4d|tsi|turbodiesel)\b/i);
  if (engineMatch) hints.engine = engineMatch[1];

  return hints;
}
