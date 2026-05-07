import React from "react";
import { motion } from "motion/react";
import { ImageWithFallback } from "./figma/ImageWithFallback";
import { ArrowRight, Phone } from "lucide-react";
import photoJeju from "../../imports/yeonhee-VWLhifg5VMA-unsplash-2.jpg";
import logoImage from "../../imports/paradiso-wordmark-brush-white-2.png";

const SERVICE_TAGS = [
  "매뉴얼 기반",
  "AI 보조 안내",
  "관할 관서 조회",
  "직종·업종 코드",
];

export function FooterCTA() {
  return (
    <footer className="relative" style={{ background: "#fcfaf5" }}>
      {/* Top section: CTA on ivory */}
      <div
        className="relative overflow-hidden"
        style={{ borderTop: "1px solid rgba(8,94,72,0.07)" }}
      >
        <div className="max-w-6xl mx-auto px-6 py-28 flex flex-col lg:flex-row items-start gap-16">

          {/* Text + CTAs */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.8 }}
            className="flex-1 flex flex-col gap-7"
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
              Get Started
            </span>

            <h2
              className="text-[#085E48]"
              style={{
                fontFamily: "Pretendard, sans-serif",
                fontSize: "clamp(2rem, 4vw, 3rem)",
                fontWeight: 700,
                lineHeight: 1.15,
                letterSpacing: "-0.03em",
              }}
            >
              대한민국 체류자격,<br />
              한 곳에서 살펴보세요.
            </h2>

            <p
              style={{
                fontFamily: "Pretendard, sans-serif",
                fontSize: "1rem",
                fontWeight: 500,
                color: "rgba(8,94,72,0.6)",
                lineHeight: 1.75,
                maxWidth: "27rem",
              }}
            >
              체류 목적에 맞는 자격을 탐색하고, 구비서류와 관할 관서를
              확인하세요. 출입국·외국인정책본부 실무 매뉴얼 기반의
              신뢰할 수 있는 안내를 제공합니다.
            </p>

            {/* Service tags */}
            <div className="flex flex-wrap gap-2">
              {SERVICE_TAGS.map((tag, idx) => (
                <span
                  key={idx}
                  className="rounded-full"
                  style={{
                    fontFamily: "Pretendard, sans-serif",
                    fontSize: "0.78rem",
                    fontWeight: 600,
                    padding: "5px 14px",
                    background: "rgba(8,94,72,0.06)",
                    border: "1px solid rgba(8,94,72,0.1)",
                    color: "rgba(8,94,72,0.65)",
                    letterSpacing: "-0.005em",
                  }}
                >
                  {tag}
                </span>
              ))}
            </div>

            <div className="flex flex-col sm:flex-row gap-3 mt-2">
              <button
                className="flex items-center justify-center gap-2 px-7 py-3.5 rounded-full font-bold text-white transition-all duration-300 group"
                style={{
                  fontFamily: "Pretendard, sans-serif",
                  background: "#085E48",
                  boxShadow: "0 6px 24px rgba(8,94,72,0.2)",
                }}
                onMouseEnter={(e) => {
                  (e.currentTarget as HTMLButtonElement).style.background = "#0EA37B";
                  (e.currentTarget as HTMLButtonElement).style.boxShadow = "0 8px 28px rgba(14,163,123,0.3)";
                }}
                onMouseLeave={(e) => {
                  (e.currentTarget as HTMLButtonElement).style.background = "#085E48";
                  (e.currentTarget as HTMLButtonElement).style.boxShadow = "0 6px 24px rgba(8,94,72,0.2)";
                }}
              >
                탐색 시작하기
                <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
              </button>

              <button
                className="flex items-center justify-center gap-2 px-7 py-3.5 rounded-full font-bold transition-all duration-300"
                style={{
                  fontFamily: "Pretendard, sans-serif",
                  background: "rgba(8,94,72,0.06)",
                  color: "#085E48",
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
                <Phone className="w-4 h-4" />
                외국인종합안내센터 1345
              </button>
            </div>

            {/* Trust note */}
            <p
              style={{
                fontFamily: "Pretendard, sans-serif",
                fontSize: "0.78rem",
                fontWeight: 500,
                color: "rgba(8,94,72,0.32)",
                lineHeight: 1.65,
                maxWidth: "30rem",
              }}
            >
              본 서비스는 공공데이터를 기반으로 한 안내 가이던스입니다. 법적 효력이 없으며,
              최종 판단은 반드시 공식 기관(정부24, 출입국·외국인청 등)을 통해 확인하세요.
            </p>
          </motion.div>

          {/* Editorial Jeju image */}
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.9, delay: 0.1 }}
            className="lg:w-[400px] xl:w-[460px] flex-shrink-0 hidden lg:block"
          >
            <div
              className="relative overflow-hidden"
              style={{
                borderRadius: "1.5rem",
                aspectRatio: "4/3",
                boxShadow: "0 24px 64px -16px rgba(8,94,72,0.15)",
                border: "1px solid rgba(8,94,72,0.07)",
              }}
            >
              <ImageWithFallback
                src={photoJeju}
                alt="제주 자연"
                className="w-full h-full object-cover"
              />
              {/* Soft warm overlay */}
              <div
                className="absolute inset-0"
                style={{ background: "rgba(8,94,72,0.08)" }}
              />
            </div>
          </motion.div>
        </div>
      </div>

      {/* Bottom footer strip */}
      <div className="py-6 px-6" style={{ background: "#085E48" }}>
        <div className="max-w-6xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
          <img
            src={logoImage}
            alt="Paradiso"
            className="h-5 object-contain"
            style={{ opacity: 0.75 }}
          />
          <div className="flex flex-col md:flex-row items-center gap-4 md:gap-8">
            <p
              style={{
                fontFamily: "Pretendard, sans-serif",
                fontSize: "0.76rem",
                fontWeight: 500,
                color: "rgba(255,255,255,0.38)",
              }}
            >
              © {new Date().getFullYear()} Paradiso. All rights reserved.
            </p>
            <div className="flex items-center gap-1.5">
              <div
                className="w-1.5 h-1.5 rounded-full"
                style={{ background: "#0EA37B" }}
              />
              <span
                style={{
                  fontFamily: "Pretendard, sans-serif",
                  fontSize: "0.73rem",
                  fontWeight: 500,
                  color: "rgba(255,255,255,0.38)",
                }}
              >
                출입국·외국인정책본부 매뉴얼 기반 안내 서비스
              </span>
            </div>
          </div>
        </div>
      </div>
    </footer>
  );
}
