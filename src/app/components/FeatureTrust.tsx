import React from "react";
import { motion } from "motion/react";
import { CheckCircle2, Search, FileText, Building2, Briefcase } from "lucide-react";

const FEATURES = [
  {
    icon: Search,
    ko: "39개 체류자격 통합 검색",
    en: "Search across 39 visa types",
    accent: "#0EA37B",
  },
  {
    icon: FileText,
    ko: "자격별 구비서류 자동 생성",
    en: "Auto-generated document checklist",
    accent: "#7DD8B8",
  },
  {
    icon: Building2,
    ko: "관할 출입국관서 즉시 조회",
    en: "Find your jurisdiction office",
    accent: "#0EA37B",
  },
  {
    icon: Briefcase,
    ko: "취업신고 직종·업종 코드",
    en: "Employment notification codes",
    accent: "#FF8C7A",
  },
];

export function FeatureTrust() {
  return (
    <section className="py-28 px-6 relative overflow-hidden" style={{ background: "#fcfaf5" }}>
      {/* Subtle top divider */}
      <div
        className="max-w-7xl mx-auto mb-20"
        style={{ borderTop: "1px solid rgba(8,94,72,0.07)" }}
      />

      <div className="max-w-7xl mx-auto">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-16 lg:gap-24 items-center">

          {/* Left: heading + legal basis */}
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.8 }}
            className="flex flex-col gap-7"
          >
            <span
              className="uppercase text-[#0EA37B]"
              style={{
                fontFamily: "Pretendard, sans-serif",
                fontSize: "0.78rem",
                fontWeight: 600,
                letterSpacing: "0.2em",
              }}
            >
              Information Coverage
            </span>

            <h2
              className="text-[#085E48]"
              style={{
                fontFamily: "Pretendard, sans-serif",
                fontSize: "clamp(1.9rem, 3.8vw, 3rem)",
                fontWeight: 700,
                lineHeight: 1.15,
                letterSpacing: "-0.03em",
              }}
            >
              법무부 매뉴얼 기반,<br />
              <span style={{ color: "#0EA37B" }}>구조화된 안내</span>
            </h2>

            <p
              style={{
                fontFamily: "Pretendard, sans-serif",
                fontSize: "1rem",
                fontWeight: 500,
                color: "rgba(8,94,72,0.62)",
                lineHeight: 1.75,
                maxWidth: "28rem",
              }}
            >
              2026년 현행 출입국관리법 시행규칙과{" "}
              <strong className="text-[#085E48]/75">법무부 출입국·외국인정책본부</strong>{" "}
              실무 매뉴얼을 1차 출처로 체류 정보를 정규화합니다.
              다만 최종 판단은 관할 출입국·외국인관서에 귀속됩니다.
            </p>

            {/* Contact CTA */}
            <button
              className="self-start flex items-center gap-2 px-5 py-2.5 rounded-full transition-all duration-300"
              style={{
                fontFamily: "Pretendard, sans-serif",
                fontSize: "0.85rem",
                fontWeight: 700,
                color: "#085E48",
                background: "rgba(8,94,72,0.06)",
                border: "1px solid rgba(8,94,72,0.1)",
              }}
              onMouseEnter={(e) => {
                (e.currentTarget as HTMLButtonElement).style.background = "rgba(8,94,72,0.1)";
                (e.currentTarget as HTMLButtonElement).style.borderColor = "rgba(8,94,72,0.18)";
              }}
              onMouseLeave={(e) => {
                (e.currentTarget as HTMLButtonElement).style.background = "rgba(8,94,72,0.06)";
                (e.currentTarget as HTMLButtonElement).style.borderColor = "rgba(8,94,72,0.1)";
              }}
            >
              📞 1345 외국인종합안내센터
            </button>
          </motion.div>

          {/* Right: feature checklist */}
          <div className="flex flex-col gap-4">
            {FEATURES.map((feat, idx) => {
              const Icon = feat.icon;
              return (
                <motion.div
                  key={idx}
                  initial={{ opacity: 0, x: 20 }}
                  whileInView={{ opacity: 1, x: 0 }}
                  viewport={{ once: true }}
                  transition={{ duration: 0.6, delay: idx * 0.1 }}
                  className="flex items-center gap-4 p-5 rounded-2xl transition-all duration-300 group"
                  style={{
                    background: "rgba(255,255,255,0.72)",
                    backdropFilter: "blur(14px)",
                    WebkitBackdropFilter: "blur(14px)",
                    border: "1px solid rgba(8,94,72,0.07)",
                    boxShadow: "0 6px 24px -8px rgba(8,94,72,0.04)",
                  }}
                  onMouseEnter={(e) => {
                    const el = e.currentTarget as HTMLDivElement;
                    el.style.transform = "translateY(-2px)";
                    el.style.borderColor = `${feat.accent}30`;
                    el.style.boxShadow = "0 12px 36px -8px rgba(8,94,72,0.08)";
                  }}
                  onMouseLeave={(e) => {
                    const el = e.currentTarget as HTMLDivElement;
                    el.style.transform = "translateY(0)";
                    el.style.borderColor = "rgba(8,94,72,0.07)";
                    el.style.boxShadow = "0 6px 24px -8px rgba(8,94,72,0.04)";
                  }}
                >
                  {/* Icon */}
                  <div
                    className="w-11 h-11 rounded-xl flex items-center justify-center flex-shrink-0 transition-all duration-300"
                    style={{
                      background: `${feat.accent}12`,
                      border: `1px solid ${feat.accent}22`,
                    }}
                  >
                    <Icon className="w-5 h-5" style={{ color: feat.accent }} />
                  </div>

                  {/* Text */}
                  <div className="flex-1">
                    <p
                      className="text-[#085E48]"
                      style={{
                        fontFamily: "Pretendard, sans-serif",
                        fontSize: "0.98rem",
                        fontWeight: 700,
                        letterSpacing: "-0.01em",
                      }}
                    >
                      {feat.ko}
                    </p>
                    <p
                      style={{
                        fontFamily: "Pretendard, sans-serif",
                        fontSize: "0.75rem",
                        fontWeight: 500,
                        color: "rgba(8,94,72,0.4)",
                        letterSpacing: "0.02em",
                        marginTop: "2px",
                      }}
                    >
                      {feat.en}
                    </p>
                  </div>

                  {/* Check */}
                  <CheckCircle2
                    className="w-5 h-5 flex-shrink-0 opacity-30 group-hover:opacity-70 transition-opacity"
                    style={{ color: feat.accent }}
                  />
                </motion.div>
              );
            })}
          </div>
        </div>
      </div>
    </section>
  );
}