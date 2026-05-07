import React, { useState, useEffect, useRef } from "react";
import { motion, AnimatePresence } from "motion/react";
import { Search, ArrowRight, Briefcase, Building2, Plane, ShieldCheck, Sparkles, X, ChevronDown } from "lucide-react";
import { ImageWithFallback } from "./figma/ImageWithFallback";
import photo1 from "../../imports/clary-garcia-QHlGCk9I_lY-unsplash-2.jpg";
import photo2 from "../../imports/ji-seongkwang-CX7fI2LXJgo-unsplash-2.jpg";
import photo3 from "../../imports/ws-chae--jVX4mW1Uac-unsplash-2.jpg";
import photo4 from "../../imports/yeonhee-VWLhifg5VMA-unsplash-2.jpg";
import logoImage from "../../imports/paradiso-wordmark-brush-white-2.png";

const HERO_IMAGES = [photo1, photo2, photo3, photo4];

const KEYWORD_GROUPS = [
  {
    label: "체류자격",
    pills: ["D-2 유학", "D-4 어학연수", "E-7 특정활동", "F-2 거주", "F-4 재외동포", "F-5 영주", "F-6 결혼이민", "H-2 방문취업"],
  },
  {
    label: "서비스",
    pills: ["직종·업종 코드", "관할 관서 찾기", "구비서류 확인", "체류기간 연장", "자격 변경"],
  },
  {
    label: "상황별",
    pills: ["취업 목적 입국", "가족 동반", "유학 후 취업", "점수제 영주"],
  },
];

// Four primary gateway actions — from index.html product spec
const GATEWAY_ACTIONS = [
  {
    icon: Briefcase,
    label: "취업신고용 업종·직종 코드",
    sub: "고용노동부 고시 직종 코드 조회",
    tag: "Tool",
    accentRgb: "14,163,123",
  },
  {
    icon: Building2,
    label: "관할 출입국관서 조회",
    sub: "주소지 기준 담당 관서 즉시 확인",
    tag: "Tool",
    accentRgb: "8,94,72",
  },
  {
    icon: Plane,
    label: "입국 전 — 재외공관 사증 발급",
    sub: "해외 한국 공관 통한 비자 발급 안내",
    tag: "Pathway",
    accentRgb: "255,140,122",
  },
  {
    icon: ShieldCheck,
    label: "입국 후 — 외국인 등록·체류 연장",
    sub: "등록·연장·자격변경 등 국내 체류 서비스",
    tag: "Pathway",
    accentRgb: "125,216,184",
  },
];

function GatewayTile({
  action,
  idx,
}: {
  action: (typeof GATEWAY_ACTIONS)[number];
  idx: number;
}) {
  const [hovered, setHovered] = useState(false);
  const Icon = action.icon;

  return (
    <motion.button
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.55, delay: 0.75 + idx * 0.08, ease: [0.16, 1, 0.3, 1] }}
      className="group relative w-full flex items-center gap-4 text-left rounded-2xl transition-all duration-250 focus-visible:outline-none"
      style={{
        padding: "14px 18px",
        background: hovered
          ? `rgba(${action.accentRgb},0.14)`
          : "rgba(255,255,255,0.10)",
        border: hovered
          ? `1px solid rgba(${action.accentRgb},0.45)`
          : "1px solid rgba(255,255,255,0.16)",
        backdropFilter: "blur(12px)",
        WebkitBackdropFilter: "blur(12px)",
        boxShadow: hovered
          ? `0 8px 24px rgba(0,0,0,0.18), 0 0 0 1px rgba(${action.accentRgb},0.22)`
          : "0 2px 8px rgba(0,0,0,0.12)",
        transform: hovered ? "translateY(-2px)" : "translateY(0)",
        outline: "none",
      }}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      onFocus={() => setHovered(true)}
      onBlur={() => setHovered(false)}
      aria-label={action.label}
    >
      {/* Icon */}
      <div
        className="flex-shrink-0 w-10 h-10 rounded-xl flex items-center justify-center transition-colors duration-250"
        style={{
          background: hovered
            ? `rgba(${action.accentRgb},0.22)`
            : "rgba(255,255,255,0.12)",
          border: `1px solid rgba(${action.accentRgb},${hovered ? "0.4" : "0.18"})`,
        }}
      >
        <Icon
          style={{
            width: "18px",
            height: "18px",
            color: hovered ? `rgba(${action.accentRgb},1)` : "rgba(255,255,255,0.75)",
          }}
        />
      </div>

      {/* Text */}
      <div className="flex-1 min-w-0">
        <p
          className="truncate transition-colors duration-250"
          style={{
            fontFamily: "Pretendard, sans-serif",
            fontSize: "0.82rem",
            fontWeight: 700,
            letterSpacing: "-0.01em",
            color: hovered ? "#fff" : "rgba(255,255,255,0.85)",
            lineHeight: 1.3,
          }}
        >
          {action.label}
        </p>
        <p
          className="truncate mt-0.5 transition-colors duration-250"
          style={{
            fontFamily: "Pretendard, sans-serif",
            fontSize: "0.71rem",
            fontWeight: 500,
            color: hovered ? "rgba(255,255,255,0.72)" : "rgba(255,255,255,0.42)",
            letterSpacing: "-0.005em",
          }}
        >
          {action.sub}
        </p>
      </div>

      {/* Arrow */}
      <ArrowRight
        className="flex-shrink-0 transition-all duration-250"
        style={{
          width: "14px",
          height: "14px",
          color: hovered ? `rgba(${action.accentRgb},0.9)` : "rgba(255,255,255,0.25)",
          transform: hovered ? "translateX(2px)" : "translateX(0)",
        }}
      />
    </motion.button>
  );
}

// Quick Search Popover
function QuickSearchPopover({
  isOpen,
  onClose,
  onSelect,
}: {
  isOpen: boolean;
  onClose: () => void;
  onSelect: (kw: string) => void;
}) {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!isOpen) return;
    const handleClick = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        onClose();
      }
    };
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, [isOpen, onClose]);

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          ref={ref}
          initial={{ opacity: 0, y: -8, scale: 0.97 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          exit={{ opacity: 0, y: -8, scale: 0.97 }}
          transition={{ duration: 0.18, ease: [0.16, 1, 0.3, 1] }}
          className="absolute top-[calc(100%+8px)] right-0 z-50 w-full sm:w-[480px]"
          style={{
            background: "rgba(10,50,40,0.88)",
            backdropFilter: "blur(24px)",
            WebkitBackdropFilter: "blur(24px)",
            border: "1px solid rgba(255,255,255,0.14)",
            borderRadius: "1.25rem",
            boxShadow: "0 24px 56px -8px rgba(0,0,0,0.45)",
            padding: "20px",
          }}
        >
          {/* Header */}
          <div className="flex items-center justify-between mb-4">
            <span
              style={{
                fontFamily: "Pretendard, sans-serif",
                fontSize: "0.72rem",
                fontWeight: 700,
                color: "rgba(255,255,255,0.4)",
                letterSpacing: "0.16em",
                textTransform: "uppercase",
              }}
            >
              자주 찾는 키워드
            </span>
            <button
              onClick={onClose}
              className="w-6 h-6 rounded-full flex items-center justify-center transition-all duration-150"
              style={{
                background: "rgba(255,255,255,0.08)",
                border: "1px solid rgba(255,255,255,0.1)",
              }}
              onMouseEnter={(e) => {
                (e.currentTarget as HTMLButtonElement).style.background = "rgba(255,255,255,0.16)";
              }}
              onMouseLeave={(e) => {
                (e.currentTarget as HTMLButtonElement).style.background = "rgba(255,255,255,0.08)";
              }}
            >
              <X style={{ width: "10px", height: "10px", color: "rgba(255,255,255,0.55)" }} />
            </button>
          </div>

          {/* Keyword groups */}
          <div className="flex flex-col gap-4">
            {KEYWORD_GROUPS.map((group, gi) => (
              <div key={gi}>
                <p
                  className="mb-2"
                  style={{
                    fontFamily: "Pretendard, sans-serif",
                    fontSize: "0.68rem",
                    fontWeight: 700,
                    color: "rgba(255,255,255,0.28)",
                    letterSpacing: "0.1em",
                    textTransform: "uppercase",
                  }}
                >
                  {group.label}
                </p>
                <div className="flex flex-wrap gap-1.5">
                  {group.pills.map((pill, pi) => (
                    <button
                      key={pi}
                      onClick={() => {
                        onSelect(pill);
                        onClose();
                      }}
                      className="rounded-full transition-all duration-150"
                      style={{
                        fontFamily: "Pretendard, sans-serif",
                        fontSize: "0.76rem",
                        fontWeight: 500,
                        padding: "4px 12px",
                        height: "28px",
                        display: "inline-flex",
                        alignItems: "center",
                        background: "rgba(255,255,255,0.08)",
                        border: "1px solid rgba(255,255,255,0.12)",
                        color: "rgba(255,255,255,0.65)",
                        backdropFilter: "blur(6px)",
                      }}
                      onMouseEnter={(e) => {
                        const el = e.currentTarget as HTMLButtonElement;
                        el.style.background = "rgba(14,163,123,0.2)";
                        el.style.borderColor = "rgba(14,163,123,0.4)";
                        el.style.color = "#7DD8B8";
                      }}
                      onMouseLeave={(e) => {
                        const el = e.currentTarget as HTMLButtonElement;
                        el.style.background = "rgba(255,255,255,0.08)";
                        el.style.borderColor = "rgba(255,255,255,0.12)";
                        el.style.color = "rgba(255,255,255,0.65)";
                      }}
                    >
                      {pill}
                    </button>
                  ))}
                </div>
              </div>
            ))}
          </div>

          {/* Footer note */}
          <p
            className="mt-4"
            style={{
              fontFamily: "Pretendard, sans-serif",
              fontSize: "0.68rem",
              fontWeight: 500,
              color: "rgba(255,255,255,0.2)",
            }}
          >
            키워드를 선택하면 검색창에 자동으로 입력됩니다.
          </p>
        </motion.div>
      )}
    </AnimatePresence>
  );
}

export function HeroGateway() {
  const [bgImage, setBgImage] = useState<string>(photo1);
  const [loaded, setLoaded] = useState(false);
  const [searchValue, setSearchValue] = useState("");
  const [popoverOpen, setPopoverOpen] = useState(false);
  const searchContainerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const idx = Math.floor(Math.random() * HERO_IMAGES.length);
    setBgImage(HERO_IMAGES[idx]);
    setLoaded(true);
  }, []);

  return (
    <section className="relative w-full min-h-screen flex flex-col justify-center items-center overflow-hidden">

      {/* ── Background: full-bleed Jeju photo ── */}
      <div className="absolute inset-0 z-0">
        <ImageWithFallback
          src={bgImage}
          alt="제주 풍경"
          className="w-full h-full object-cover"
          style={{ transition: "opacity 1.2s ease", opacity: loaded ? 1 : 0 }}
        />
        {/* Deep green atmospheric tint */}
        <div className="absolute inset-0" style={{ background: "rgba(5,66,52,0.62)" }} />
        {/* Gradient vignette */}
        <div className="absolute inset-0 bg-gradient-to-b from-black/15 via-transparent to-black/60" />
        <div className="absolute inset-0 bg-gradient-to-r from-black/20 via-transparent to-black/20" />
      </div>

      {/* ── Hero content ── */}
      <div className="relative z-10 w-full max-w-2xl px-6 flex flex-col items-center pt-28 pb-16">

        {/* ── Wordmark — primary brand moment ── */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 1.2, ease: [0.16, 1, 0.3, 1] }}
          className="flex flex-col items-center gap-4 mb-8"
        >
          {/* Large brush wordmark — enlarged for brand dominance */}
          <img
            src={logoImage}
            alt="Paradiso"
            style={{
              height: "clamp(100px, 18vw, 200px)",
              objectFit: "contain",
              filter: "drop-shadow(0 6px 40px rgba(0,0,0,0.40))",
              opacity: 0.97,
            }}
          />

          {/* Sub-label */}
          <span
            style={{
              fontFamily: "Pretendard, sans-serif",
              fontSize: "0.72rem",
              fontWeight: 600,
              color: "rgba(255,255,255,0.52)",
              letterSpacing: "0.28em",
              textTransform: "uppercase",
            }}
          >
            비자·체류 정보 안내 플랫폼
          </span>
        </motion.div>

        {/* ── Hero headline ── */}
        <motion.h1
          initial={{ opacity: 0, y: 18 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.95, delay: 0.2, ease: [0.16, 1, 0.3, 1] }}
          className="text-center mb-8"
          style={{
            fontFamily: "Pretendard, sans-serif",
            fontSize: "clamp(1.2rem, 3.2vw, 1.75rem)",
            fontWeight: 500,
            color: "rgba(255,255,255,0.85)",
            lineHeight: 1.6,
            letterSpacing: "-0.01em",
          }}
        >
          대한민국에서 안정적으로 머물기 위한<br className="hidden sm:block" />
          모든 체류 정보를 한 곳에서.
        </motion.h1>

        {/* ── Search + Quick Search toggle ── */}
        <motion.div
          initial={{ opacity: 0, y: 24 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.9, delay: 0.34, ease: [0.16, 1, 0.3, 1] }}
          className="w-full mb-3"
          ref={searchContainerRef}
        >
          <div className="relative">
            <div
              className="flex items-center gap-2 p-2 rounded-2xl"
              style={{
                background: "rgba(255,255,255,0.13)",
                backdropFilter: "blur(20px)",
                WebkitBackdropFilter: "blur(20px)",
                border: "1px solid rgba(255,255,255,0.18)",
                boxShadow: "0 16px 48px -8px rgba(0,0,0,0.28), inset 0 1px 0 rgba(255,255,255,0.1)",
              }}
            >
              {/* Search input area */}
              <div className="flex flex-1 items-center pl-3 pr-1 py-1.5 gap-3 min-w-0">
                <Search className="text-white/45 flex-shrink-0" style={{ width: "18px", height: "18px" }} />
                <input
                  type="text"
                  value={searchValue}
                  onChange={(e) => setSearchValue(e.target.value)}
                  placeholder="체류 목적, 비자 코드 검색 (예: 유학, E-7, F-2)"
                  className="flex-1 min-w-0 bg-transparent border-none outline-none placeholder-white/35"
                  style={{
                    fontFamily: "Pretendard, sans-serif",
                    fontSize: "0.95rem",
                    fontWeight: 500,
                    color: "#fff",
                  }}
                />
              </div>

              {/* Quick search toggle — compact */}
              <div className="relative flex-shrink-0">
                <button
                  onClick={() => setPopoverOpen((v) => !v)}
                  className="flex items-center gap-1.5 px-3 py-2 rounded-xl transition-all duration-200 flex-shrink-0"
                  style={{
                    fontFamily: "Pretendard, sans-serif",
                    fontSize: "0.76rem",
                    fontWeight: 600,
                    color: popoverOpen ? "#7DD8B8" : "rgba(255,255,255,0.55)",
                    background: popoverOpen ? "rgba(14,163,123,0.18)" : "rgba(255,255,255,0.08)",
                    border: `1px solid ${popoverOpen ? "rgba(14,163,123,0.35)" : "rgba(255,255,255,0.12)"}`,
                    letterSpacing: "-0.005em",
                  }}
                  onMouseEnter={(e) => {
                    if (!popoverOpen) {
                      (e.currentTarget as HTMLButtonElement).style.background = "rgba(255,255,255,0.14)";
                      (e.currentTarget as HTMLButtonElement).style.color = "rgba(255,255,255,0.8)";
                    }
                  }}
                  onMouseLeave={(e) => {
                    if (!popoverOpen) {
                      (e.currentTarget as HTMLButtonElement).style.background = "rgba(255,255,255,0.08)";
                      (e.currentTarget as HTMLButtonElement).style.color = "rgba(255,255,255,0.55)";
                    }
                  }}
                  aria-label="자주 찾는 키워드 열기"
                >
                  <Sparkles style={{ width: "12px", height: "12px" }} />
                  <span className="hidden sm:block whitespace-nowrap">자주 찾는</span>
                  <ChevronDown
                    style={{
                      width: "10px",
                      height: "10px",
                      transform: popoverOpen ? "rotate(180deg)" : "rotate(0deg)",
                      transition: "transform 0.2s ease",
                    }}
                  />
                </button>

                {/* Quick Search Popover */}
                <QuickSearchPopover
                  isOpen={popoverOpen}
                  onClose={() => setPopoverOpen(false)}
                  onSelect={(kw) => setSearchValue(kw)}
                />
              </div>

              {/* Search CTA */}
              <button
                className="flex-shrink-0 flex items-center justify-center gap-2 px-5 py-2.5 rounded-xl font-bold text-white transition-all duration-200"
                style={{
                  fontFamily: "Pretendard, sans-serif",
                  fontSize: "0.88rem",
                  background: "#0EA37B",
                  boxShadow: "0 4px 18px rgba(14,163,123,0.4)",
                  whiteSpace: "nowrap",
                }}
                onMouseEnter={(e) => {
                  (e.currentTarget as HTMLButtonElement).style.background = "#0b8c69";
                }}
                onMouseLeave={(e) => {
                  (e.currentTarget as HTMLButtonElement).style.background = "#0EA37B";
                }}
              >
                탐색하기
                <ArrowRight style={{ width: "13px", height: "13px" }} />
              </button>
            </div>
          </div>

          {/* ── Paradiso.ai secondary CTA ── */}
          <motion.div
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.52 }}
            className="flex justify-end mt-2 pr-0.5"
          >
            <button
              className="flex items-center gap-1.5 rounded-full transition-all duration-200"
              style={{
                fontFamily: "Pretendard, sans-serif",
                fontSize: "0.76rem",
                fontWeight: 600,
                padding: "5px 14px",
                background: "rgba(255,140,122,0.12)",
                border: "1px solid rgba(255,140,122,0.28)",
                color: "rgba(255,190,175,0.85)",
                letterSpacing: "-0.005em",
              }}
              onMouseEnter={(e) => {
                const el = e.currentTarget as HTMLButtonElement;
                el.style.background = "rgba(255,140,122,0.22)";
                el.style.borderColor = "rgba(255,140,122,0.45)";
                el.style.color = "rgba(255,210,200,0.95)";
              }}
              onMouseLeave={(e) => {
                const el = e.currentTarget as HTMLButtonElement;
                el.style.background = "rgba(255,140,122,0.12)";
                el.style.borderColor = "rgba(255,140,122,0.28)";
                el.style.color = "rgba(255,190,175,0.85)";
              }}
            >
              <Sparkles style={{ width: "11px", height: "11px" }} />
              Paradiso.ai — 내 상황 AI 분석
            </button>
          </motion.div>
        </motion.div>

        {/* ── Divider ── */}
        <motion.div
          initial={{ opacity: 0, scaleX: 0.6 }}
          animate={{ opacity: 1, scaleX: 1 }}
          transition={{ duration: 0.7, delay: 0.62 }}
          className="w-full mb-4"
          style={{ borderTop: "1px solid rgba(255,255,255,0.1)" }}
        />

        {/* ── Gateway Actions — 4 product entry tiles ── */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.5, delay: 0.7 }}
          className="w-full"
        >
          {/* Group label */}
          <p
            className="mb-3"
            style={{
              fontFamily: "Pretendard, sans-serif",
              fontSize: "0.7rem",
              fontWeight: 600,
              color: "rgba(255,255,255,0.32)",
              letterSpacing: "0.14em",
              textTransform: "uppercase",
            }}
          >
            빠른 서비스
          </p>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
            {GATEWAY_ACTIONS.map((action, idx) => (
              <GatewayTile key={idx} action={action} idx={idx} />
            ))}
          </div>
        </motion.div>
      </div>

      {/* ── Scroll cue ── */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 1.6, duration: 0.8 }}
        className="absolute bottom-7 left-1/2 -translate-x-1/2 flex flex-col items-center gap-2 pointer-events-none"
      >
        <motion.div
          animate={{ y: [0, 6, 0] }}
          transition={{ duration: 2.2, repeat: Infinity, ease: "easeInOut" }}
          className="w-5 h-8 rounded-full flex items-start justify-center pt-1.5"
          style={{ border: "1px solid rgba(255,255,255,0.2)" }}
        >
          <div
            className="w-0.5 h-1.5 rounded-full"
            style={{ background: "rgba(255,255,255,0.35)" }}
          />
        </motion.div>
        <span
          style={{
            fontFamily: "Pretendard, sans-serif",
            fontSize: "9px",
            fontWeight: 500,
            color: "rgba(255,255,255,0.28)",
            letterSpacing: "0.16em",
            textTransform: "uppercase",
          }}
        >
          scroll
        </span>
      </motion.div>
    </section>
  );
}
