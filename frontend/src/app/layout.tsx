import type { Metadata } from "next";
import Script from "next/script";
import "./globals.css";
import { pretendard } from "@/lib/fonts";

export const metadata: Metadata = {
  title: "PIXI - AI 공동창업자와 함께 제품을 만들어보세요",
  description: "AI와 함께 아이디어를 연구하고 계획하여 사람들이 정말 원하는 제품을 만드세요",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="ko" suppressHydrationWarning className={pretendard.variable}>
      <body
        className="antialiased"
        suppressHydrationWarning
      >
        {/* hydration 직전에 확장 프로그램이 body에 붙인 속성 제거 */}
        <Script
          id="strip-extension-attrs"
          strategy="beforeInteractive"
          dangerouslySetInnerHTML={{
            __html: `(function(){var b=document.body;if(b){b.removeAttribute('data-new-gr-c-s-check-loaded');b.removeAttribute('data-gr-ext-installed');}})();`,
          }}
        />
        {children}
      </body>
    </html>
  );
}
