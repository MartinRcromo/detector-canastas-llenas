import { createClient } from "@supabase/supabase-js";

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
const serviceRole = process.env.SUPABASE_SERVICE_ROLE_KEY;

if (!supabaseUrl || !serviceRole) {
  throw new Error("Missing NEXT_PUBLIC_SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY");
}

const supabase = createClient(supabaseUrl, serviceRole, { auth: { persistSession: false } });

const templates = [
  {
    category: "PARAGOLPES",
    title: "Paragolpes Delantero",
    position: "DELANTERO",
    side: null,
    variant: "con agujeros PDC",
  },
  {
    category: "FARO TRASERO",
    title: "Faro Trasero",
    position: "TRASERO",
    side: "DER",
    variant: "sin lavafaros",
  },
  {
    category: "OPTICA",
    title: "Óptica Delantera",
    position: "DELANTERO",
    side: "IZQ",
    variant: "halógena",
  },
  {
    category: "RADIADOR",
    title: "Radiador Motor",
    position: "DELANTERO",
    side: null,
    variant: "alto rendimiento",
  },
];

const vehicles = [
  { make: "FORD", model: "RANGER", yearFrom: 2016, yearTo: 2020, engine: "3.2 TDCi", engineCode: "P5AT" },
  { make: "TOYOTA", model: "HILUX", yearFrom: 2017, yearTo: 2022, engine: "2.8 D4D", engineCode: "1GD-FTV" },
  { make: "VW", model: "AMAROK", yearFrom: 2015, yearTo: 2021, engine: "2.0 TDI", engineCode: "EA189" },
  { make: "CHEVROLET", model: "S10", yearFrom: 2018, yearTo: 2023, engine: "2.8 Duramax", engineCode: "LWN" },
  { make: "NISSAN", model: "FRONTIER", yearFrom: 2019, yearTo: 2023, engine: "2.3 TwinTurbo", engineCode: "YS23" },
  { make: "FORD", model: "RANGER", yearFrom: 2012, yearTo: 2015, engine: "2.2 TDCi", engineCode: "P4AT" },
];

async function run() {
  await supabase.from("product_images").delete().neq("id", "00000000-0000-0000-0000-000000000000");
  await supabase.from("product_fitments").delete().neq("id", "00000000-0000-0000-0000-000000000000");
  await supabase.from("products").delete().neq("id", "00000000-0000-0000-0000-000000000000");

  const products = Array.from({ length: 24 }, (_, index) => {
    const template = templates[index % templates.length];
    const vehicle = vehicles[index % vehicles.length];
    const sku = `AP-${template.category.slice(0, 3)}-${String(index + 1).padStart(4, "0")}`;

    return {
      sku,
      title: `${template.title} ${vehicle.make} ${vehicle.model} ${vehicle.yearFrom}-${vehicle.yearTo}`,
      part_category: template.category,
      brand_vehicle: vehicle.make,
      part_position: template.position,
      part_side: template.side,
      oem_codes: [`OEM-${index + 1000}`, `OEM-${index + 2000}`],
      aftermarket_codes: [`ALT-${index + 3000}`],
      specs: {
        variant: template.variant,
        material: index % 2 === 0 ? "Plástico ABS" : "Aluminio",
        finish: index % 3 === 0 ? "Negro texturado" : "Primer",
        warranty_months: 6,
      },
    };
  });

  const { data: insertedProducts, error: productsError } = await supabase.from("products").insert(products).select("id, sku, brand_vehicle, title");
  if (productsError) throw productsError;

  const fitments = insertedProducts.flatMap((product, index) => {
    const vehicle = vehicles[index % vehicles.length];
    return [
      {
        product_id: product.id,
        make: vehicle.make,
        model: vehicle.model,
        year_from: vehicle.yearFrom,
        year_to: vehicle.yearTo,
        trim: index % 2 === 0 ? "XLT" : "SRV",
        engine: vehicle.engine,
        engine_code: vehicle.engineCode,
        transmission: index % 2 === 0 ? "AT" : "MT",
        body_style: "PICKUP",
        notes: index % 2 === 0 ? "con agujeros PDC" : "sin faro antiniebla",
      },
    ];
  });

  const { error: fitmentError } = await supabase.from("product_fitments").insert(fitments);
  if (fitmentError) throw fitmentError;

  console.log(`Seed completado. Productos: ${insertedProducts.length}, Fitments: ${fitments.length}`);
}

run().catch((error) => {
  console.error(error);
  process.exit(1);
});
