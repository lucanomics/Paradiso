import React, { useState, useEffect } from "react";
import { HeroGateway } from "./components/HeroGateway";
import { StatBridge } from "./components/StatBridge";
import { FeatureTrust } from "./components/FeatureTrust";
import { AnagramBrandStory } from "./components/AnagramBrandStory";
import { StartSection } from "./components/StartSection";
import { ValuesSection } from "./components/ValuesSection";
import { RoadmapSection } from "./components/RoadmapSection";
import { FooterCTA } from "./components/FooterCTA";
import { Globe } from "lucide-react";
import logoImage from "../imports/paradiso-wordmark-brush-white-2.png";

export default function App() {
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    const handleScroll = () => setScrolled(window.scrollY > 60);
    window.addEventListener("scroll", handleScroll, { passive: true });
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  return (
    <div
      className="min-h-screen overflow-x-hidden relative"
      style={{
        background: "#fcfaf5",
        color: "#085E48",
        fontFamily: "Pretendard, -apple-system, BlinkMacSystemFont, sans-serif",
      }}
    >
      {/* Navigation */}
      <nav
        className="fixed top-0 left-0 right-0 z-50 transition-all duration-500"
        style={{
          padding: scrolled ? "14px 24px" : "20px 24px",
          background: scrolled
            ? "rgba(252,250,245,0.88)"
            : "transparent",
          backdropFilter: scrolled ? "blur(16px)" : "none",
          WebkitBackdropFilter: scrolled ? "blur(16px)" : "none",
          borderBottom: scrolled
            ? "1px solid rgba(8,94,72,0.07)"
            : "none",
        }}
      >
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          {/* Logo: white on hero, dark-inverted on scroll */}
          <img
            src={logoImage}
            alt="Paradiso"
            className="object-contain transition-all duration-500"
            style={{
              height: scrolled ? "24px" : "28px",
              filter: scrolled ? "invert(1) sepia(1) saturate(5) hue-rotate(110deg)" : "none",
              opacity: scrolled ? 1 : 0.95,
            }}
          />

          {/* Nav links — visible when scrolled */}
          <div
            className="hidden md:flex items-center gap-8 transition-all duration-500"
            style={{ opacity: scrolled ? 1 : 0, pointerEvents: scrolled ? "auto" : "none" }}
          >
            {["체류자격 탐색", "안내 흐름", "서비스 소개"].map((item) => (
              <button
                key={item}
                className="text-sm font-medium transition-colors"
                style={{
                  fontFamily: "Pretendard, sans-serif",
                  color: "rgba(8,94,72,0.65)",
                }}
                onMouseEnter={(e) => {
                  (e.currentTarget as HTMLButtonElement).style.color = "#085E48";
                }}
                onMouseLeave={(e) => {
                  (e.currentTarget as HTMLButtonElement).style.color = "rgba(8,94,72,0.65)";
                }}
              >
                {item}
              </button>
            ))}
          </div>

          {/* CTA button — 언어 설정 (future language switcher) */}
          <button
            className="flex items-center gap-1.5 px-5 py-2 rounded-full font-bold text-sm transition-all duration-300"
            style={{
              fontFamily: "Pretendard, sans-serif",
              background: scrolled ? "rgba(8,94,72,0.08)" : "rgba(255,255,255,0.15)",
              color: scrolled ? "#085E48" : "#fff",
              border: scrolled ? "1px solid rgba(8,94,72,0.14)" : "1px solid rgba(255,255,255,0.3)",
              backdropFilter: scrolled ? "none" : "blur(8px)",
            }}
            onMouseEnter={(e) => {
              const el = e.currentTarget as HTMLButtonElement;
              el.style.background = scrolled ? "rgba(8,94,72,0.14)" : "rgba(255,255,255,0.24)";
            }}
            onMouseLeave={(e) => {
              const el = e.currentTarget as HTMLButtonElement;
              el.style.background = scrolled ? "rgba(8,94,72,0.08)" : "rgba(255,255,255,0.15)";
            }}
          >
            <Globe style={{ width: "14px", height: "14px" }} />
            언어 설정
          </button>
        </div>
      </nav>

      <main>
        <HeroGateway />
        <StatBridge />
        <FeatureTrust />
        <AnagramBrandStory />
        <StartSection />
        <ValuesSection />
        <RoadmapSection />
      </main>

      <FooterCTA />
    </div>
  );
}