import React from "react";
import { motion } from "motion/react";

const KEYWORD_GROUPS = [
  {
    label: "체류자격",
    pills: [
      "D-2 유학",
      "D-4 어학연수",
      "D-10 구직",
      "E-7 특정활동",
      "E-9 비전문취업",
      "F-2 거주",
      "F-4 재외동포",
      "F-5 영주",
      "F-6 결혼이민",
      "H-2 방문취업",
    ],
  },
  {
    label: "서비스 기능",
    pills: [
      "직종·업종 코드 조회",
      "관할 관서 찾기",
      "구비서류 확인",
      "체류기간 연장",
      "자격 변경",
      "영주권 조건",
    ],
  },
  {
    label: "상황별",
    pills: [
      "취업 목적 입국",
      "가족 동반",
      "결혼 이민",
      "유학 후 취업",
      "점수제 영주",
    ],
  },
];

export function KeywordsHints() {
  return (
    <section
      className="relative w-full px-6 py-14 overflow-hidden"
      style={{ background: "#fcfaf5" }}
    >
      {/* Hairline top divider */}
      <div
        className="max-w-7xl mx-auto mb-12"
        style={{ borderTop: "1px solid rgba(8,94,72,0.07)" }}
      />

      <div className="max-w-7xl mx-auto">
        {/* Header row */}
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
          className="mb-9 flex flex-col sm:flex-row sm:items-baseline gap-3"
        >
          <span
            className="text-[#0EA37B]"
            style={{
              fontFamily: "Pretendard, sans-serif",
              fontSize: "0.78rem",
              fontWeight: 600,
              letterSpacing: "0.2em",
              textTransform: "uppercase",
            }}
          >
            Quick Search
          </span>
          <h2
            className="text-[#085E48]"
            style={{
              fontFamily: "Pretendard, sans-serif",
              fontSize: "clamp(1.1rem, 2vw, 1.3rem)",
              fontWeight: 700,
              letterSpacing: "-0.02em",
            }}
          >
            자주 찾는 키워드
          </h2>
        </motion.div>

        {/* Keyword groups */}
        <div className="flex flex-col gap-6">
          {KEYWORD_GROUPS.map((group, groupIdx) => (
            <motion.div
              key={groupIdx}
              initial={{ opacity: 0, y: 10 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.55, delay: groupIdx * 0.08 }}
              className="flex flex-wrap items-center gap-2"
            >
              {/* Group label */}
              <span
                className="mr-1 flex-shrink-0"
                style={{
                  fontFamily: "Pretendard, sans-serif",
                  fontSize: "0.72rem",
                  fontWeight: 700,
                  color: "rgba(8,94,72,0.35)",
                  letterSpacing: "0.08em",
                  textTransform: "uppercase",
                  minWidth: "5rem",
                }}
              >
                {group.label}
              </span>

              {/* Pills */}
              {group.pills.map((pill, pillIdx) => (
                <motion.button
                  key={pillIdx}
                  initial={{ opacity: 0, scale: 0.95 }}
                  whileInView={{ opacity: 1, scale: 1 }}
                  viewport={{ once: true }}
                  transition={{
                    duration: 0.35,
                    delay: groupIdx * 0.08 + pillIdx * 0.04,
                  }}
                  className="rounded-full transition-all duration-250"
                  style={{
                    fontFamily: "Pretendard, sans-serif",
                    fontSize: "0.8rem",
                    fontWeight: 500,
                    padding: "5px 14px",
                    height: "32px",
                    background: "rgba(255,255,255,0.7)",
                    border: "1px solid rgba(8,94,72,0.1)",
                    color: "rgba(8,94,72,0.7)",
                    backdropFilter: "blur(8px)",
                    WebkitBackdropFilter: "blur(8px)",
                    letterSpacing: "-0.005em",
                    display: "inline-flex",
                    alignItems: "center",
                  }}
                  onMouseEnter={(e) => {
                    const el = e.currentTarget as HTMLButtonElement;
                    el.style.background = "rgba(14,163,123,0.08)";
                    el.style.borderColor = "rgba(14,163,123,0.28)";
                    el.style.color = "#0EA37B";
                    el.style.transform = "translateY(-1px)";
                  }}
                  onMouseLeave={(e) => {
                    const el = e.currentTarget as HTMLButtonElement;
                    el.style.background = "rgba(255,255,255,0.7)";
                    el.style.borderColor = "rgba(8,94,72,0.1)";
                    el.style.color = "rgba(8,94,72,0.7)";
                    el.style.transform = "translateY(0)";
                  }}
                >
                  {pill}
                </motion.button>
              ))}
            </motion.div>
          ))}
        </div>

        {/* Footnote */}
        <motion.p
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
          transition={{ duration: 0.7, delay: 0.3 }}
          className="mt-8"
          style={{
            fontFamily: "Pretendard, sans-serif",
            fontSize: "0.75rem",
            fontWeight: 500,
            color: "rgba(8,94,72,0.28)",
            letterSpacing: "0.01em",
          }}
        >
          키워드를 클릭하면 해당 항목 검색 결과로 이동합니다. 총 39개 체류자격 전체 탐색 가능.
        </motion.p>
      </div>
    </section>
  );
}
