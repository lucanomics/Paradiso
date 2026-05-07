import React, { useState, useEffect, useRef } from "react";
import { motion, AnimatePresence } from "motion/react";
import { ArrowRight, ChevronDown } from "lucide-react";

const CATEGORIES = [
  {
    span: "md:col-span-2 md:row-span-2",
    label: "Work & Professional",
    title: "취업·전문직",
    sub: "전문 인력, 비전문 취업, 특정활동",
    count: 14,
    style: "featured",
    codes: ["D-7", "D-8", "D-9", "E-1", "E-2", "E-3", "E-4", "E-5", "E-6", "E-7", "E-8", "E-9", "E-10", "H-1"],
    detail: "고용 허가·계약에 따른 국내 취업 및 전문직 체류자격 14개를 포함합니다.",
  },
  {
    span: "md:col-span-1 lg:col-span-2",
    label: "Education",
    title: "유학·연수",
    sub: "학위과정, 어학연수, 구직",
    count: 8,
    style: "light",
    codes: ["D-2", "D-3", "D-4", "D-5", "D-6", "D-10", "G-1-E", "G-1-S"],
    detail: "고등교육기관 학위과정부터 어학연수, 구직비자까지 포함합니다.",
  },
  {
    span: "md:col-span-1 lg:col-span-1",
    label: "Residence",
    title: "거주·결혼",
    sub: "거주, 재외동포, 영주, 결혼이민",
    count: 7,
    style: "warm",
    codes: ["F-1", "F-2", "F-3", "F-4", "F-5", "F-6", "G-1-R"],
    detail: "가족 구성원 및 장기 거주 자격. 영주 경로 포함.",
  },
  {
    span: "md:col-span-1 lg:col-span-1",
    label: "Visit & Other",
    title: "방문·기타",
    sub: "단기방문, 관광, 워킹홀리데이",
    count: 10,
    style: "mint",
    codes: ["B-1", "B-2", "C-1", "C-2", "C-3", "C-4", "H-2", "G-1", "A-1", "A-2"],
    detail: "단기체류·관광·외교 및 특수 목적 방문 자격을 포함합니다.",
  },
];

function useCountUp(target: number, duration = 1400, startOnVisible = true) {
  const [count, setCount] = useState(0);
  const [started, setStarted] = useState(!startOnVisible);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!startOnVisible) return;
    const obs = new IntersectionObserver(
      ([entry]) => { if (entry.isIntersecting) { setStarted(true); obs.disconnect(); } },
      { threshold: 0.4 }
    );
    if (ref.current) obs.observe(ref.current);
    return () => obs.disconnect();
  }, [startOnVisible]);

  useEffect(() => {
    if (!started) return;
    let startTime: number | null = null;
    const step = (ts: number) => {
      if (!startTime) startTime = ts;
      const progress = Math.min((ts - startTime) / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3); // ease-out cubic
      setCount(Math.round(eased * target));
      if (progress < 1) requestAnimationFrame(step);
    };
    requestAnimationFrame(step);
  }, [started, target, duration]);

  return { count, ref };
}

function CategoryCard({
  cat,
  idx,
}: {
  cat: (typeof CATEGORIES)[number];
  idx: number;
}) {
  const [expanded, setExpanded] = useState(false);
  const [hovered, setHovered] = useState(false);
  const { count, ref } = useCountUp(cat.count);

  const isFeatured = cat.style === "featured";

  const baseStyle = isFeatured
    ? { background: "#085E48", boxShadow: "0 16px 48px -12px rgba(8,94,72,0.25)" }
    : cat.style === "warm"
    ? { background: "rgba(255,190,164,0.35)", border: "1px solid rgba(255,140,122,0.2)", boxShadow: "0 8px 24px -8px rgba(255,140,122,0.1)" }
    : cat.style === "mint"
    ? { background: "rgba(14,163,123,0.08)", border: "1px solid rgba(14,163,123,0.15)", boxShadow: "0 8px 24px -8px rgba(14,163,123,0.08)" }
    : { background: "rgba(255,255,255,0.72)", backdropFilter: "blur(16px)", WebkitBackdropFilter: "blur(16px)", border: "1px solid rgba(8,94,72,0.07)", boxShadow: "0 8px 24px -8px rgba(8,94,72,0.05)" };

  return (
    <motion.div
      ref={ref as React.RefObject<HTMLDivElement>}
      key={idx}
      initial={{ opacity: 0, y: 20 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true }}
      transition={{ duration: 0.55, delay: idx * 0.09 }}
      className={`${cat.span} rounded-[1.75rem] p-8 relative overflow-hidden flex flex-col justify-between cursor-pointer`}
      style={{
        ...baseStyle,
        minHeight: isFeatured ? undefined : "220px",
        transition: "transform 0.25s ease, box-shadow 0.25s ease",
        transform: hovered ? "translateY(-3px)" : "translateY(0)",
      }}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      onClick={() => setExpanded((v) => !v)}
    >
      {/* Featured card: radial glow */}
      {isFeatured && (
        <div
          className="absolute top-0 right-0 w-[140%] h-[140%] pointer-events-none transition-opacity duration-700"
          style={{
            opacity: hovered ? 0.65 : 0.35,
            background: "radial-gradient(circle at top right, rgba(14,163,123,0.4) 0%, transparent 60%)",
          }}
        />
      )}

      {/* Top: label + title */}
      <div className="relative z-10">
        <span
          className="inline-block px-3 py-1 rounded-full mb-4"
          style={{
            fontFamily: "Pretendard, sans-serif",
            fontSize: "0.7rem",
            fontWeight: 600,
            letterSpacing: "0.12em",
            textTransform: "uppercase",
            background: isFeatured ? "rgba(255,255,255,0.1)" : "rgba(8,94,72,0.07)",
            color: isFeatured ? "rgba(255,255,255,0.7)" : "rgba(8,94,72,0.5)",
            border: isFeatured ? "1px solid rgba(255,255,255,0.15)" : "1px solid rgba(8,94,72,0.1)",
          }}
        >
          {cat.label}
        </span>
        <h3
          style={{
            fontFamily: "Pretendard, sans-serif",
            fontWeight: 700,
            letterSpacing: "-0.02em",
            color: isFeatured ? "#fff" : "#085E48",
            fontSize: isFeatured ? "clamp(1.8rem, 3vw, 2.8rem)" : "1.4rem",
          }}
        >
          {cat.title}
        </h3>
        <p
          style={{
            fontFamily: "Pretendard, sans-serif",
            fontSize: "0.85rem",
            fontWeight: 500,
            marginTop: "4px",
            color: isFeatured ? "rgba(255,255,255,0.55)" : "rgba(8,94,72,0.45)",
          }}
        >
          {cat.sub}
        </p>
      </div>

      {/* Animated count + code chips */}
      <div className="relative z-10 flex flex-col gap-3 mt-4">
        {/* Stat row */}
        <div className="flex items-end justify-between">
          <div className="flex items-baseline gap-1">
            <span
              style={{
                fontFamily: "Pretendard, sans-serif",
                fontWeight: 900,
                fontSize: isFeatured ? "3.5rem" : "2.5rem",
                lineHeight: 1,
                color: isFeatured ? "rgba(125,216,184,0.85)" : cat.style === "warm" ? "rgba(255,107,91,0.7)" : "rgba(14,163,123,0.7)",
                letterSpacing: "-0.03em",
              }}
            >
              {count}
            </span>
            <span
              style={{
                fontFamily: "Pretendard, sans-serif",
                fontSize: "0.78rem",
                fontWeight: 600,
                color: isFeatured ? "rgba(255,255,255,0.4)" : "rgba(8,94,72,0.35)",
                marginBottom: "4px",
                letterSpacing: "0.04em",
              }}
            >
              개 자격
            </span>
          </div>

          {/* Expand toggle */}
          <button
            className="flex items-center gap-1 px-2.5 py-1 rounded-full transition-all duration-200"
            style={{
              fontFamily: "Pretendard, sans-serif",
              fontSize: "0.68rem",
              fontWeight: 600,
              color: isFeatured ? "rgba(255,255,255,0.5)" : "rgba(8,94,72,0.45)",
              background: isFeatured ? "rgba(255,255,255,0.08)" : "rgba(8,94,72,0.06)",
              border: isFeatured ? "1px solid rgba(255,255,255,0.12)" : "1px solid rgba(8,94,72,0.1)",
              letterSpacing: "0.02em",
            }}
            onClick={(e) => { e.stopPropagation(); setExpanded((v) => !v); }}
          >
            {expanded ? "접기" : "코드 보기"}
            <ChevronDown
              style={{
                width: "10px",
                height: "10px",
                transform: expanded ? "rotate(180deg)" : "rotate(0deg)",
                transition: "transform 0.2s ease",
              }}
            />
          </button>
        </div>

        {/* Expandable visa codes */}
        <AnimatePresence>
          {expanded && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: "auto" }}
              exit={{ opacity: 0, height: 0 }}
              transition={{ duration: 0.25, ease: [0.16, 1, 0.3, 1] }}
              style={{ overflow: "hidden" }}
            >
              <div className="flex flex-wrap gap-1.5 pt-1">
                {cat.codes.map((code) => (
                  <span
                    key={code}
                    className="rounded-full"
                    style={{
                      fontFamily: "Pretendard, sans-serif",
                      fontSize: "0.68rem",
                      fontWeight: 700,
                      padding: "3px 9px",
                      background: isFeatured ? "rgba(255,255,255,0.1)" : "rgba(8,94,72,0.06)",
                      border: isFeatured ? "1px solid rgba(255,255,255,0.18)" : "1px solid rgba(8,94,72,0.1)",
                      color: isFeatured ? "rgba(255,255,255,0.75)" : "rgba(8,94,72,0.6)",
                      letterSpacing: "0.02em",
                    }}
                  >
                    {code}
                  </span>
                ))}
              </div>
              <p
                className="mt-2"
                style={{
                  fontFamily: "Pretendard, sans-serif",
                  fontSize: "0.72rem",
                  fontWeight: 500,
                  color: isFeatured ? "rgba(255,255,255,0.38)" : "rgba(8,94,72,0.35)",
                  lineHeight: 1.5,
                }}
              >
                {cat.detail}
              </p>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Hover prompt (non-expanded) */}
        {!expanded && (
          <div
            className="flex items-center gap-1 transition-opacity duration-300"
            style={{ opacity: hovered ? 0.7 : 0 }}
          >
            <ArrowRight
              style={{
                width: "11px",
                height: "11px",
                color: isFeatured ? "rgba(255,255,255,0.6)" : "rgba(8,94,72,0.5)",
              }}
            />
            <span
              style={{
                fontFamily: "Pretendard, sans-serif",
                fontSize: "0.68rem",
                fontWeight: 500,
                color: isFeatured ? "rgba(255,255,255,0.55)" : "rgba(8,94,72,0.45)",
                letterSpacing: "0.01em",
              }}
            >
              클릭하여 코드 확인
            </span>
          </div>
        )}
      </div>
    </motion.div>
  );
}

export function StatBridge() {
  return (
    <section className="relative w-full px-6 py-24" style={{ background: "#fcfaf5" }}>
      {/* Hairline top divider */}
      <div
        className="max-w-7xl mx-auto mb-20"
        style={{ borderTop: "1px solid rgba(8,94,72,0.07)" }}
      />

      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-16 flex flex-col md:flex-row md:items-end justify-between gap-8">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.7 }}
            className="max-w-xl"
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
              Coverage
            </span>
            <h2
              className="text-[#085E48]"
              style={{
                fontFamily: "Pretendard, sans-serif",
                fontSize: "clamp(2rem, 4vw, 3.2rem)",
                fontWeight: 700,
                lineHeight: 1.15,
                letterSpacing: "-0.03em",
              }}
            >
              39개 체류자격,<br />
              <span style={{ color: "#0EA37B" }}>4가지 카테고리</span>로.
            </h2>
            <p
              className="mt-4"
              style={{
                fontFamily: "Pretendard, sans-serif",
                fontSize: "1.05rem",
                fontWeight: 500,
                color: "rgba(8,94,72,0.55)",
                lineHeight: 1.65,
              }}
            >
              복잡한 체류자격을 목적별로 재구성했습니다. 카드를 클릭해 자격 코드를 확인하세요.
            </p>
          </motion.div>

          {/* Total stat */}
          <motion.div
            initial={{ opacity: 0, y: 12 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6, delay: 0.2 }}
            className="flex-shrink-0"
          >
            <div
              className="px-8 py-5 rounded-2xl flex flex-col items-center"
              style={{
                background: "rgba(14,163,123,0.06)",
                border: "1px solid rgba(14,163,123,0.12)",
              }}
            >
              <span
                style={{
                  fontFamily: "Pretendard, sans-serif",
                  fontSize: "3.5rem",
                  fontWeight: 900,
                  color: "#0EA37B",
                  lineHeight: 1,
                  letterSpacing: "-0.04em",
                }}
              >
                39
              </span>
              <span
                style={{
                  fontFamily: "Pretendard, sans-serif",
                  fontSize: "0.78rem",
                  fontWeight: 600,
                  color: "rgba(8,94,72,0.45)",
                  letterSpacing: "0.1em",
                  textTransform: "uppercase",
                  marginTop: "4px",
                }}
              >
                Total 체류자격
              </span>
            </div>
          </motion.div>
        </div>

        {/* Interactive bento grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-4 auto-rows-[220px] gap-4 md:gap-5">
          {CATEGORIES.map((cat, idx) => (
            <CategoryCard key={idx} cat={cat} idx={idx} />
          ))}
        </div>

        {/* Footnote */}
        <div className="mt-6 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
          <p
            style={{
              fontFamily: "Pretendard, sans-serif",
              fontSize: "0.78rem",
              fontWeight: 500,
              color: "rgba(8,94,72,0.3)",
            }}
          >
            * 시스템 내부 구조화를 위한 분류로, 출입국관리법령상 공식 체계와 상이할 수 있습니다.
          </p>
          <button
            className="flex items-center gap-1.5 rounded-full transition-all duration-200 flex-shrink-0"
            style={{
              fontFamily: "Pretendard, sans-serif",
              fontSize: "0.78rem",
              fontWeight: 600,
              padding: "5px 14px",
              background: "rgba(8,94,72,0.05)",
              border: "1px solid rgba(8,94,72,0.1)",
              color: "rgba(8,94,72,0.5)",
            }}
            onMouseEnter={(e) => {
              const el = e.currentTarget as HTMLButtonElement;
              el.style.background = "rgba(8,94,72,0.1)";
              el.style.color = "#085E48";
            }}
            onMouseLeave={(e) => {
              const el = e.currentTarget as HTMLButtonElement;
              el.style.background = "rgba(8,94,72,0.05)";
              el.style.color = "rgba(8,94,72,0.5)";
            }}
          >
            전체 39개 자격 탐색
            <ArrowRight style={{ width: "12px", height: "12px" }} />
          </button>
        </div>
      </div>
    </section>
  );
}
