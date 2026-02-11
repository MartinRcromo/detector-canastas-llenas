import { createAdminSupabaseClient } from "@/lib/supabase/admin";

export const runtime = "nodejs";

async function loadPlaywright() {
  const importer = new Function('return import("playwright")') as () => Promise<any>;
  return importer();
}

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const shouldDownload = searchParams.get("download") === "1";
  searchParams.delete("download");

  const baseUrl = process.env.APP_BASE_URL ?? "http://localhost:3000";
  const printUrl = `${baseUrl}/catalog/print?${searchParams.toString()}`;

  const { chromium } = await loadPlaywright();
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();
  await page.goto(printUrl, { waitUntil: "networkidle" });
  const pdfBuffer = await page.pdf({ format: "A4", printBackground: true, margin: { top: "15mm", right: "10mm", bottom: "15mm", left: "10mm" } });
  await browser.close();

  if (shouldDownload) {
    return new Response(pdfBuffer, {
      headers: {
        "Content-Type": "application/pdf",
        "Content-Disposition": `attachment; filename="catalog-${Date.now()}.pdf"`,
      },
    });
  }

  const supabase = createAdminSupabaseClient();
  const filename = `catalog-${Date.now()}.pdf`;
  const storagePath = `exports/${filename}`;

  const { error } = await supabase.storage.from("catalogs").upload(storagePath, pdfBuffer, {
    contentType: "application/pdf",
    upsert: true,
  });

  if (error) return Response.json({ error: error.message }, { status: 500 });

  const { data } = supabase.storage.from("catalogs").getPublicUrl(storagePath);
  return Response.json({ url: data.publicUrl, storagePath });
}
