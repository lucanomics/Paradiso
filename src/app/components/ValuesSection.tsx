import React from "react";
import { motion } from "motion/react";
import { Database, Users, Sparkles } from "lucide-react";

const VALUES = [
  {
    icon: Database,
    accentColor: "#0EA37B",
    title: "Data Integrity",
    titleKo: "데이터 무결성",
    desc: "신뢰할 수 있는 출처를 바탕으로 체류 규정 데이터를 꼼꼼히 정리합니다. 지속적인 업데이트를 통해 정보의 무결성을 유지하고자 노력합니다.",
  },
  {
    icon: Users,
    accentColor: "#FF8C7A",
    title: "User Centric",
    titleKo: "사용자 중심",
    desc: "복잡한 법률 용어 대신, 실사용자가 이해하기 쉬운 언어와 탐색 흐름으로 정보 격차를 해소합니다.",
  },
  {
    icon: Sparkles,
    accentColor: "#7DD8B8",
    title: "AI Assisted",
    titleKo: "AI 보조 안내",
    desc: "AI 기술을 활용해 검색과 안내의 편의를 돕습니다. 다만, 최종적인 행정 절차와 결정은 항상 공식 기관의 지침을 우선해야 합니다.",
  },
];

export function ValuesSection() {
  return (
    <section className="py-28 px-6" style={{ background: "#fcfaf5" }}>
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.7 }}
          className="mb-16"
        >
          <span
            className="uppercase text-[#0EA37B] mb-4 block"
            style={{
              fontFamily: "Pretendard, sans-serif",
              fontSize: "0.78rem",
              fontWeight: 600,
              letterSpacing: "0.2em",
            }}
          >
            Operating Principles
          </span>
          <h2
            className="text-[#085E48]"
            style={{
              fontFamily: "Pretendard, sans-serif",
              fontSize: "clamp(1.8rem, 3.5vw, 2.5rem)",
              fontWeight: 700,
              lineHeight: 1.2,
              letterSpacing: "-0.025em",
            }}
          >
            Paradiso의 운영 원칙
          </h2>
        </motion.div>

        {/* Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {VALUES.map((val, idx) => {
            const Icon = val.icon;
            return (
              <motion.div
                key={idx}
                initial={{ opacity: 0, y: 24 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.65, delay: idx * 0.12 }}
                className="group relative p-8 rounded-[1.5rem] transition-all duration-400 cursor-default"
                style={{
                  background: "rgba(255,255,255,0.72)",
                  backdropFilter: "blur(16px)",
                  WebkitBackdropFilter: "blur(16px)",
                  border: "1px solid rgba(8,94,72,0.07)",
                  boxShadow: "0 10px 40px -12px rgba(8,94,72,0.04)",
                }}
                onMouseEnter={(e) => {
                  (e.currentTarget as HTMLDivElement).style.transform = "translateY(-3px)";
                  (e.currentTarget as HTMLDivElement).style.boxShadow = "0 16px 50px -10px rgba(8,94,72,0.09)";
                  (e.currentTarget as HTMLDivElement).style.borderColor = `rgba(${val.accentColor === "#0EA37B" ? "14,163,123" : val.accentColor === "#FF8C7A" ? "255,140,122" : "125,216,184"},0.25)`;
                }}
                onMouseLeave={(e) => {
                  (e.currentTarget as HTMLDivElement).style.transform = "translateY(0)";
                  (e.currentTarget as HTMLDivElement).style.boxShadow = "0 10px 40px -12px rgba(8,94,72,0.04)";
                  (e.currentTarget as HTMLDivElement).style.borderColor = "rgba(8,94,72,0.07)";
                }}
              >
                {/* Icon container */}
                <div
                  className="w-14 h-14 rounded-2xl flex items-center justify-center mb-6"
                  style={{
                    background: `${val.accentColor}0f`,
                    border: `1px solid ${val.accentColor}20`,
                  }}
                >
                  <Icon className="w-6 h-6" style={{ color: val.accentColor }} />
                </div>

                {/* Title */}
                <div className="mb-1">
                  <h3
                    className="text-[#085E48]"
                    style={{
                      fontFamily: "Pretendard, sans-serif",
                      fontSize: "1.15rem",
                      fontWeight: 700,
                      letterSpacing: "-0.01em",
                    }}
                  >
                    {val.title}
                  </h3>
                  <span
                    style={{
                      fontFamily: "Pretendard, sans-serif",
                      fontSize: "0.8rem",
                      fontWeight: 500,
                      color: val.accentColor,
                      opacity: 0.8,
                    }}
                  >
                    {val.titleKo}
                  </span>
                </div>

                {/* Description */}
                <p
                  className="mt-4"
                  style={{
                    fontFamily: "Pretendard, sans-serif",
                    fontSize: "0.92rem",
                    fontWeight: 500,
                    color: "rgba(8,94,72,0.62)",
                    lineHeight: 1.7,
                  }}
                >
                  {val.desc}
                </p>

                {/* Subtle corner accent */}
                <div
                  className="absolute bottom-0 right-0 w-24 h-24 rounded-full pointer-events-none opacity-40"
                  style={{
                    background: `radial-gradient(circle, ${val.accentColor}18 0%, transparent 70%)`,
                  }}
                />
              </motion.div>
            );
          })}
        </div>

        {/* Footer note */}
        <motion.p
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
          transition={{ duration: 0.8, delay: 0.4 }}
          className="mt-8"
          style={{
            fontFamily: "Pretendard, sans-serif",
            fontSize: "0.82rem",
            fontWeight: 500,
            color: "rgba(8,94,72,0.38)",
            textAlign: "center",
          }}
        >
          모두가 평등하게 정보를 누릴 수 있는 체류 환경을 만듭니다.
        </motion.p>
      </div>
    </section>
  );
}
