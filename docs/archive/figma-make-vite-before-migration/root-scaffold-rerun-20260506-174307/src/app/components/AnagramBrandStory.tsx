import React, { useState, useEffect, useRef } from "react";
import { motion } from "motion/react";

// DIASPORA → PARADISO (exact anagram)
const SOURCE = ["D", "I", "A", "S", "P", "O", "R", "A"];
const TARGET = ["P", "A", "R", "A", "D", "I", "S", "O"];

// Which source index maps to which target index
const MAPPING = [
  { s: 0, t: 4 }, // D→D
  { s: 1, t: 5 }, // I→I
  { s: 2, t: 1 }, // A→A (first)
  { s: 3, t: 6 }, // S→S
  { s: 4, t: 0 }, // P→P
  { s: 5, t: 7 }, // O→O
  { s: 6, t: 2 }, // R→R
  { s: 7, t: 3 }, // A→A (second)
];

const LETTER_STEP = 87;
const START_X = 96;

const getX = (i: number) => START_X + i * LETTER_STEP;

export function AnagramBrandStory() {
  // prefers-reduced-motion guard
  const prefersReducedMotion = useRef(false);
  useEffect(() => {
    const mq = window.matchMedia("(prefers-reduced-motion: reduce)");
    prefersReducedMotion.current = mq.matches;
  }, []);

  const [activeIndex, setActiveIndex] = useState(0);
  const [phase, setPhase] = useState<"cycling" | "complete">("cycling");

  useEffect(() => {
    // Skip animation if user prefers reduced motion
    if (prefersReducedMotion.current) {
      setPhase("complete");
      setActiveIndex(MAPPING.length - 1);
      return;
    }

    if (phase === "cycling") {
      const timer = setInterval(() => {
        setActiveIndex((prev) => {
          const next = prev + 1;
          if (next >= MAPPING.length) {
            setPhase("complete");
            return prev;
          }
          return next;
        });
      }, 1600);
      return () => clearInterval(timer);
    } else {
      // brief pause on "complete" then restart (skip if reduced motion)
      if (prefersReducedMotion.current) return;
      const reset = setTimeout(() => {
        setActiveIndex(0);
        setPhase("cycling");
      }, 2400);
      return () => clearTimeout(reset);
    }
  }, [phase]);

  const isComplete = phase === "complete";

  return (
    <section
      className="py-28 px-6 relative overflow-hidden"
      style={{ background: "#fcfaf5" }}
    >
      {/* Subtle warm radial gradient */}
      <div
        className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[700px] h-[400px] rounded-full pointer-events-none"
        style={{
          background:
            "radial-gradient(ellipse, rgba(14,163,123,0.05) 0%, transparent 70%)",
        }}
      />

      <div className="max-w-4xl mx-auto flex flex-col items-center relative z-10">
        {/* Section label */}
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.7 }}
          className="flex flex-col items-center text-center mb-14 gap-4"
        >
          <span
            className="tracking-[0.2em] uppercase text-[#0EA37B]"
            style={{
              fontFamily: "Pretendard, sans-serif",
              fontSize: "0.78rem",
              fontWeight: 600,
            }}
          >
            Brand Story
          </span>
          <h2
            className="text-[#085E48] max-w-xl"
            style={{
              fontFamily: "Pretendard, sans-serif",
              fontSize: "clamp(1.6rem, 3.5vw, 2.2rem)",
              fontWeight: 700,
              lineHeight: 1.25,
              letterSpacing: "-0.025em",
            }}
          >
            디아스포라에서, 파라디소로.
          </h2>
          <p
            className="text-[#085E48]/60 max-w-md"
            style={{
              fontFamily: "Pretendard, sans-serif",
              fontSize: "1rem",
              fontWeight: 500,
              lineHeight: 1.65,
            }}
          >
            <strong style={{ color: "#FF8C7A", fontWeight: 800 }}>Paradiso</strong>는 이주민을 뜻하는{" "}
            <strong className="text-[#085E48]/80">Diaspora</strong>의 알파벳 8개를
            재배열(Anagram)한 이름입니다.{" "}
            <span className="italic">이탈리아어로 '낙원(Paradise)'</span>을 의미합니다.
          </p>
        </motion.div>

        {/* Anagram SVG canvas */}
        <motion.div
          initial={{ opacity: 0, y: 24 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.9, delay: 0.15 }}
          className="w-full"
        >
          <svg
            viewBox="0 0 800 380"
            className="w-full max-w-3xl mx-auto"
            aria-label="DIASPORA에서 PARADISO로의 애너그램 변환"
          >
            {/* Row labels */}
            <text
              x="18"
              y="108"
              textAnchor="start"
              fill="rgba(8,94,72,0.25)"
              fontSize="10"
              fontWeight="600"
              fontFamily="Pretendard, -apple-system, sans-serif"
              letterSpacing="2"
              style={{ textTransform: "uppercase" }}
            >
              FROM
            </text>
            <text
              x="18"
              y="278"
              textAnchor="start"
              fill="rgba(8,94,72,0.25)"
              fontSize="10"
              fontWeight="600"
              fontFamily="Pretendard, -apple-system, sans-serif"
              letterSpacing="2"
              style={{ textTransform: "uppercase" }}
            >
              TO
            </text>

            {/* Hairline separators */}
            <line
              x1="60"
              y1="145"
              x2="740"
              y2="145"
              stroke="rgba(8,94,72,0.06)"
              strokeWidth="1"
            />
            <line
              x1="60"
              y1="235"
              x2="740"
              y2="235"
              stroke="rgba(8,94,72,0.06)"
              strokeWidth="1"
            />

            {/* Connecting curves — all at once, active highlighted */}
            {MAPPING.map((map, i) => {
              const x1 = getX(map.s);
              const x2 = getX(map.t);
              const isActive = !isComplete && i === activeIndex;
              const isPast = !isComplete && i < activeIndex;
              const strokeColor = isComplete
                ? "rgba(14,163,123,0.18)"
                : isActive
                ? "rgba(14,163,123,0.7)"
                : isPast
                ? "rgba(14,163,123,0.1)"
                : "rgba(14,163,123,0.06)";
              const strokeWidth = isActive ? 2 : 1;

              return (
                <path
                  key={i}
                  d={`M ${x1} 146 C ${x1} 192, ${x2} 192, ${x2} 234`}
                  fill="none"
                  stroke={strokeColor}
                  strokeWidth={strokeWidth}
                  style={{ transition: "stroke 0.5s ease, stroke-width 0.3s ease" }}
                />
              );
            })}

            {/* DIASPORA letters — source row */}
            {SOURCE.map((letter, i) => {
              const x = getX(i);
              const mappingIdx = MAPPING.findIndex((m) => m.s === i);
              const isActive = !isComplete && mappingIdx === activeIndex;
              const isPast = !isComplete && mappingIdx < activeIndex;

              const fillColor = isComplete
                ? "rgba(8,94,72,0.22)"
                : isActive
                ? "#0EA37B"
                : isPast
                ? "rgba(8,94,72,0.15)"
                : "rgba(8,94,72,0.28)";

              return (
                <g key={`s-${i}`}>
                  {isActive && (
                    <circle
                      cx={x}
                      cy={108}
                      r={30}
                      fill="rgba(14,163,123,0.08)"
                      style={{ transition: "opacity 0.4s ease" }}
                    />
                  )}
                  <text
                    x={x}
                    y={108}
                    textAnchor="middle"
                    dominantBaseline="central"
                    fontSize={56}
                    fontWeight={700}
                    fontFamily="Pretendard, -apple-system, sans-serif"
                    fill={fillColor}
                    style={{
                      transition: "fill 0.55s ease",
                      letterSpacing: "-1px",
                    }}
                  >
                    {letter}
                  </text>
                </g>
              );
            })}

            {/* PARADISO letters — target row */}
            {TARGET.map((letter, i) => {
              const x = getX(i);
              const mappingIdx = MAPPING.findIndex((m) => m.t === i);
              const isActive = !isComplete && mappingIdx === activeIndex;
              const isPast = !isComplete && mappingIdx < activeIndex;

              const fillColor = isComplete
                ? "#FF8C7A"
                : isActive
                ? "#085E48"
                : isPast
                ? "rgba(8,94,72,0.55)"
                : "rgba(8,94,72,0.22)";

              return (
                <g key={`t-${i}`}>
                  {isActive && (
                    <circle
                      cx={x}
                      cy={274}
                      r={30}
                      fill="rgba(8,94,72,0.05)"
                      style={{ transition: "opacity 0.4s ease" }}
                    />
                  )}
                  <text
                    x={x}
                    y={274}
                    textAnchor="middle"
                    dominantBaseline="central"
                    fontSize={56}
                    fontWeight={800}
                    fontFamily="Pretendard, -apple-system, sans-serif"
                    fill={fillColor}
                    style={{
                      transition: "fill 0.55s ease",
                      letterSpacing: "-1px",
                    }}
                  >
                    {letter}
                  </text>
                </g>
              );
            })}

            {/* Progress dots */}
            {MAPPING.map((_, i) => (
              <circle
                key={`dot-${i}`}
                cx={getX(i)}
                cy={355}
                r={3}
                fill={
                  isComplete || i < activeIndex
                    ? "rgba(14,163,123,0.6)"
                    : i === activeIndex
                    ? "#0EA37B"
                    : "rgba(8,94,72,0.12)"
                }
                style={{ transition: "fill 0.4s ease" }}
              />
            ))}
          </svg>
        </motion.div>

        {/* Brand meaning block */}
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.8, delay: 0.4 }}
          className="mt-10 w-full max-w-2xl"
        >
          <div
            className="flex flex-col sm:flex-row gap-6 p-7 rounded-2xl"
            style={{
              background: "rgba(255,255,255,0.65)",
              backdropFilter: "blur(12px)",
              WebkitBackdropFilter: "blur(12px)",
              border: "1px solid rgba(8,94,72,0.07)",
              boxShadow: "0 8px 32px -12px rgba(8,94,72,0.06)",
            }}
          >
            <div className="flex-1">
              <p
                style={{
                  fontFamily: "Pretendard, sans-serif",
                  fontSize: "0.88rem",
                  fontWeight: 600,
                  color: "#085E48",
                  lineHeight: 1.7,
                  marginBottom: "0.5rem",
                }}
              >
                고국을 떠나온 이주민들이 대한민국에서 안정적인 정주 환경을 영위할 수 있도록 지원한다는 지향점을 담았습니다.
              </p>
              <p
                style={{
                  fontFamily: "Pretendard, sans-serif",
                  fontSize: "0.82rem",
                  fontWeight: 500,
                  color: "rgba(8,94,72,0.5)",
                  lineHeight: 1.65,
                }}
              >
                300만 체류 외국인 시대를 위한 공공 정보 인프라를 지향합니다.
              </p>
            </div>
            <div
              className="flex-shrink-0 self-center hidden sm:block w-px h-16"
              style={{ background: "rgba(8,94,72,0.07)" }}
            />
            <div className="flex-shrink-0 sm:self-center text-center sm:text-left">
              <p
                style={{
                  fontFamily: "Pretendard, sans-serif",
                  fontSize: "0.72rem",
                  fontWeight: 600,
                  color: "rgba(8,94,72,0.35)",
                  letterSpacing: "0.12em",
                  textTransform: "uppercase",
                  marginBottom: "4px",
                }}
              >
                Exact anagram
              </p>
              <p
                style={{
                  fontFamily: "Pretendard, sans-serif",
                  fontSize: "0.85rem",
                  fontWeight: 600,
                  color: "rgba(8,94,72,0.45)",
                  letterSpacing: "0.02em",
                }}
              >
                DIASPORA = PARADISO
              </p>
            </div>
          </div>
        </motion.div>
      </div>
    </section>
  );
}