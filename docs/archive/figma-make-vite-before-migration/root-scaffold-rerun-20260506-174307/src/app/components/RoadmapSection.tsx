import React, { useRef } from "react";
import { motion, useScroll, useTransform } from "motion/react";

const MILESTONES = [
  {
    q: "2025 Q4",
    badge: "완료",
    badgeType: "done" as const,
    title: "공공데이터 활용 공모전 출품 및 MVP 검증",
    desc: "39개 체류자격 데이터 정규화, 핵심 검색 흐름 구현 및 초기 사용자 피드백 수집.",
  },
  {
    q: "2026 Q1",
    badge: "진행 중",
    badgeType: "active" as const,
    title: "AI 기반 질의응답과 안내 품질 고도화",
    desc: "자연어 질의 응답 기능 도입, 직종 코드 매핑 정확도 향상 및 안내 콘텐츠 보강.",
  },
  {
    q: "2026 Q3",
    badge: "예정",
    badgeType: "planned" as const,
    title: "다국어 UI와 사용자 접근성 확대",
    desc: "영어·중국어·베트남어 지원 추가, 모바일 접근성 개선, 더 넓은 사용자층으로 확장.",
  },
];

const BADGE_STYLES = {
  done: { bg: "rgba(14,163,123,0.1)", text: "#0EA37B", border: "rgba(14,163,123,0.2)" },
  active: { bg: "rgba(8,94,72,0.08)", text: "#085E48", border: "rgba(8,94,72,0.15)" },
  planned: { bg: "rgba(8,94,72,0.04)", text: "rgba(8,94,72,0.5)", border: "rgba(8,94,72,0.08)" },
};

function TimelineProgressLine({ containerRef }: { containerRef: React.RefObject<HTMLDivElement> }) {
  const { scrollYProgress } = useScroll({
    target: containerRef,
    offset: ["start 80%", "end 20%"],
  });
  const scaleY = useTransform(scrollYProgress, [0, 1], [0, 1]);

  return (
    <div className="absolute top-6 bottom-6 left-[23px] w-px hidden md:block">
      {/* Base track */}
      <div
        className="absolute inset-0"
        style={{ background: "rgba(8,94,72,0.08)" }}
      />
      {/* Animated fill */}
      <motion.div
        className="absolute top-0 left-0 w-full"
        style={{
          scaleY,
          transformOrigin: "top",
          height: "100%",
          background: "linear-gradient(to bottom, #0EA37B, rgba(14,163,123,0.3))",
        }}
      />
    </div>
  );
}

export function RoadmapSection() {
  const timelineRef = useRef<HTMLDivElement>(null);

  return (
    <section className="py-28 px-6 relative" style={{ background: "#fcfaf5", position: "relative" }}>
      {/* Hairline separator */}
      <div
        className="max-w-6xl mx-auto mb-24"
        style={{ borderTop: "1px solid rgba(8,94,72,0.07)" }}
      />

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
            Project Roadmap
          </span>
          <h2
            className="text-[#085E48] max-w-md"
            style={{
              fontFamily: "Pretendard, sans-serif",
              fontSize: "clamp(1.8rem, 3.5vw, 2.5rem)",
              fontWeight: 700,
              lineHeight: 1.2,
              letterSpacing: "-0.025em",
            }}
          >
            프로젝트 로드맵
          </h2>
          <p
            className="mt-4 max-w-xl"
            style={{
              fontFamily: "Pretendard, sans-serif",
              fontSize: "1rem",
              fontWeight: 500,
              color: "rgba(8,94,72,0.55)",
              lineHeight: 1.65,
            }}
          >
            Paradiso는 더 나은 안내를 위한 방향을 모색하며 꾸준히 발전해 나갈
            계획입니다. 본 로드맵은 개발 목표를 나타냅니다.
          </p>
        </motion.div>

        {/* Timeline */}
        <div ref={timelineRef} className="relative" style={{ position: "relative" }}>
          {/* Animated vertical connector line */}
          <TimelineProgressLine containerRef={timelineRef} />

          <div className="space-y-6">
            {MILESTONES.map((item, idx) => {
              const badge = BADGE_STYLES[item.badgeType];
              return (
                <motion.div
                  key={idx}
                  initial={{ opacity: 0, y: 20 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true }}
                  transition={{ duration: 0.6, delay: idx * 0.12 }}
                  className="flex items-start gap-6 md:gap-10"
                >
                  {/* Timeline node */}
                  <div className="relative flex-shrink-0 mt-1 hidden md:flex">
                    <div
                      className="w-12 h-12 rounded-full flex items-center justify-center z-10 relative"
                      style={{
                        background:
                          item.badgeType === "done"
                            ? "rgba(14,163,123,0.1)"
                            : item.badgeType === "active"
                            ? "rgba(8,94,72,0.08)"
                            : "rgba(8,94,72,0.04)",
                        border:
                          item.badgeType === "done"
                            ? "1.5px solid rgba(14,163,123,0.3)"
                            : item.badgeType === "active"
                            ? "1.5px solid rgba(8,94,72,0.15)"
                            : "1.5px dashed rgba(8,94,72,0.1)",
                      }}
                    >
                      <div
                        className="w-2.5 h-2.5 rounded-full"
                        style={{
                          background:
                            item.badgeType === "done"
                              ? "#0EA37B"
                              : item.badgeType === "active"
                              ? "#085E48"
                              : "rgba(8,94,72,0.2)",
                        }}
                      />
                    </div>
                  </div>

                  {/* Card */}
                  <div
                    className="flex-1 p-7 rounded-[1.25rem] transition-all duration-300 group"
                    style={{
                      background: "rgba(255,255,255,0.72)",
                      backdropFilter: "blur(14px)",
                      WebkitBackdropFilter: "blur(14px)",
                      border: "1px solid rgba(8,94,72,0.07)",
                      boxShadow: "0 8px 32px -10px rgba(8,94,72,0.04)",
                    }}
                    onMouseEnter={(e) => {
                      (e.currentTarget as HTMLDivElement).style.transform = "translateY(-2px)";
                      (e.currentTarget as HTMLDivElement).style.boxShadow = "0 14px 44px -10px rgba(8,94,72,0.08)";
                      (e.currentTarget as HTMLDivElement).style.borderColor = "rgba(8,94,72,0.12)";
                    }}
                    onMouseLeave={(e) => {
                      (e.currentTarget as HTMLDivElement).style.transform = "translateY(0)";
                      (e.currentTarget as HTMLDivElement).style.boxShadow = "0 8px 32px -10px rgba(8,94,72,0.04)";
                      (e.currentTarget as HTMLDivElement).style.borderColor = "rgba(8,94,72,0.07)";
                    }}
                  >
                    <div className="flex flex-wrap items-center gap-3 mb-3">
                      {/* Quarter label */}
                      <span
                        style={{
                          fontFamily: "Pretendard, sans-serif",
                          fontSize: "0.88rem",
                          fontWeight: 700,
                          color: "#085E48",
                          letterSpacing: "0.04em",
                        }}
                      >
                        {item.q}
                      </span>

                      {/* Status badge */}
                      <span
                        className="px-2.5 py-0.5 rounded-full"
                        style={{
                          fontFamily: "Pretendard, sans-serif",
                          fontSize: "0.72rem",
                          fontWeight: 600,
                          background: badge.bg,
                          color: badge.text,
                          border: `1px solid ${badge.border}`,
                          letterSpacing: "0.04em",
                        }}
                      >
                        {item.badge}
                      </span>
                    </div>

                    <h3
                      className="text-[#085E48] mb-2"
                      style={{
                        fontFamily: "Pretendard, sans-serif",
                        fontSize: "1.05rem",
                        fontWeight: 700,
                        letterSpacing: "-0.01em",
                      }}
                    >
                      {item.title}
                    </h3>

                    <p
                      style={{
                        fontFamily: "Pretendard, sans-serif",
                        fontSize: "0.9rem",
                        fontWeight: 500,
                        color: "rgba(8,94,72,0.55)",
                        lineHeight: 1.65,
                      }}
                    >
                      {item.desc}
                    </p>
                  </div>
                </motion.div>
              );
            })}
          </div>
        </div>
      </div>
    </section>
  );
}