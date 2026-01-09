import "./globals.css";

export const metadata = {
  title: "Análisis de Rentabilidad",
  description: "Dashboard de subrubros para análisis de rentabilidad",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="es">
      <body className="min-h-screen bg-slate-950 text-slate-100">
        {children}
      </body>
    </html>
  );
}
