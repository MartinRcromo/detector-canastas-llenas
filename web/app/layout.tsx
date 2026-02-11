import "./globals.css";

export const metadata = {
  title: "Catálogo Autopartes",
  description: "Búsqueda B2B de autopartes por compatibilidad y códigos",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="es">
      <body className="min-h-screen bg-slate-950 text-slate-100">{children}</body>
    </html>
  );
}
