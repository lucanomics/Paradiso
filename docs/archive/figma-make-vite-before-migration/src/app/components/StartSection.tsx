import React from "react";
import { motion } from "motion/react";
import { ImageWithFallback } from "./figma/ImageWithFallback";
import photo from "../../imports/ws-chae--jVX4mW1Uac-unsplash-2.jpg";

const KEY_POINTS = [
  "출입국·외국인정책본부 실무 매뉴얼 기반",
  "정보 비대칭 해소, 이용자 친화적 안내",
  "공공데이터 기반 · 비상업적 안내 서비스",
];

export function StartSection() {
  return (
    <section className="py-24 px-6" style={{ background: "#fcfaf5" }}>
      <div className="max-w-6xl mx-auto">
        <div
          className="flex flex-col md:flex-row items-stretch rounded-[2rem] overflow-hidden border"
          style={{
            borderColor: "rgba(8,94,72,0.07)",
            boxShadow: "0 12px 48px -16px rgba(8,94,72,0.1)",
          }}
        >
          {/* Text panel — civic glass */}
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.8 }}
            className="md:w-1/2 p-12 md:p-16 flex flex-col justify-center gap-6 relative overflow-hidden"
            style={{
              background: "rgba(255,255,255,0.82)",
              backdropFilter: "blur(20px)",
            }}
          >
            {/* Subtle corner glow */}
            <div
              className="absolute top-0 right-0 w-56 h-56 rounded-full pointer-events-none"
              style={{
                background: "radial-gradient(circle, rgba(14,163,123,0.07) 0%, transparent 70%)",
              }}
            />

            <span
              className="uppercase text-[#0EA37B] relative z-10"
              style={{
                fontFamily: "Pretendard, sans-serif",
                fontSize: "0.78rem",
                fontWeight: 600,
                letterSpacing: "0.2em",
              }}
            >
              About the Platform
            </span>

            <h2
              className="text-[#085E48] relative z-10"
              style={{
                fontFamily: "Pretendard, sans-serif",
                fontSize: "clamp(1.5rem, 2.8vw, 2.1rem)",
                fontWeight: 700,
                lineHeight: 1.3,
                letterSpacing: "-0.02em",
              }}
            >
              Paradiso의 시작
            </h2>

            <p
              className="text-[#085E48]/65 relative z-10"
              style={{
                fontFamily: "Pretendard, sans-serif",
                fontSize: "0.97rem",
                fontWeight: 500,
                lineHeight: 1.78,
              }}
            >
              대한민국에는 39가지의 체류자격이 존재하지만, 관련 법령과 매뉴얼은
              여러 기관에 파편화되어 있어 진입 장벽이 높습니다.{" "}
              <strong className="text-[#085E48]/80">Paradiso</strong>는
              출입국·외국인정책본부 실무 매뉴얼을 기반으로, 정확한 체류 정보와
              관할 관서를 단일 플랫폼에서 직관적으로 제공하기 위해 기획되었습니다.
            </p>

            {/* Key points */}
            <div className="flex flex-col gap-3 relative z-10 mt-1">
              {KEY_POINTS.map((point, idx) => (
                <div key={idx} className="flex items-center gap-3">
                  <div
                    className="w-1.5 h-1.5 rounded-full flex-shrink-0"
                    style={{ background: "#0EA37B" }}
                  />
                  <span
                    style={{
                      fontFamily: "Pretendard, sans-serif",
                      fontSize: "0.85rem",
                      fontWeight: 600,
                      color: "rgba(8,94,72,0.55)",
                      letterSpacing: "-0.005em",
                    }}
                  >
                    {point}
                  </span>
                </div>
              ))}
            </div>

            {/* Highlight quote */}
            <div
              className="relative z-10 mt-2 p-4 rounded-xl"
              style={{
                background: "rgba(8,94,72,0.04)",
                borderLeft: "2px solid rgba(8,94,72,0.18)",
              }}
            >
              <p
                style={{
                  fontFamily: "Pretendard, sans-serif",
                  fontSize: "0.88rem",
                  fontWeight: 700,
                  color: "#085E48",
                  lineHeight: 1.55,
                }}
              >
                향후 체류 외국인 300만 시대를 대비하는 공공 정보 인프라로 도약하고자 합니다.
              </p>
            </div>
          </motion.div>

          {/* Image panel */}
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.8, delay: 0.1 }}
            className="md:w-1/2 relative min-h-[340px] md:min-h-0"
          >
            <ImageWithFallback
              src={photo}
              alt="제주 자연 풍경"
              className="absolute inset-0 w-full h-full object-cover"
            />
            {/* Warm green tint for coherence */}
            <div
              className="absolute inset-0"
              style={{ background: "rgba(8,94,72,0.12)" }}
            />
          </motion.div>
        </div>
      </div>
    </section>
  );
}
