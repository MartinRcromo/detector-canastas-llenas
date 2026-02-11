import { createReadStream } from "fs";
import { basename } from "path";
import { createClient } from "@supabase/supabase-js";

const [,, productId, localFilePath] = process.argv;

if (!productId || !localFilePath) {
  console.error("Uso: npm run upload:image -- <productId> <ruta-local>");
  process.exit(1);
}

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
const serviceRole = process.env.SUPABASE_SERVICE_ROLE_KEY;

if (!supabaseUrl || !serviceRole) {
  throw new Error("Missing NEXT_PUBLIC_SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY");
}

const supabase = createClient(supabaseUrl, serviceRole);

async function main() {
  const fileName = basename(localFilePath);
  const storagePath = `products/${productId}/${fileName}`;
  const file = createReadStream(localFilePath);

  const { error } = await supabase.storage.from("product-images").upload(storagePath, file, {
    upsert: true,
  });

  if (error) throw error;

  const { error: imageError } = await supabase.from("product_images").insert({
    product_id: productId,
    path: storagePath,
    is_primary: true,
    sort_order: 0,
  });

  if (imageError) throw imageError;

  console.log(`Imagen subida en ${storagePath}`);
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
