import "./globals.css"
export const metadata = { title: "Paiva AI Decision Platform" }
export default function RootLayout({ children }) {
  return (
    <html lang="pt-BR">
      <body style={{background:'#030712',color:'white',minHeight:'100vh',fontFamily:'-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif'}}>
        {children}
      </body>
    </html>
  )
}
