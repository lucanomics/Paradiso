#!/usr/bin/env node
/*
 * scripts/check_i18n.js
 *
 * Lightweight validator for the inline UI_TRANSLATIONS object in index.html.
 * Checks:
 *   1. `en` has the same top-level keys as `ko`.
 *   2. Array values shared by `en` and `ko` have the same length.
 *   3. `en` string values contain no Hangul characters.
 *   4. No `en` string value is empty.
 *   5. Known lower-landing/search-result Korean UI regions have explicit
 *      translation keys and apply/render wiring.
 *
 * Designed to be robust to formatting tweaks (object-literal commas, trailing
 * commas, single-quoted strings) without bringing in a full JS parser.
 */

'use strict';

const fs = require('fs');
const path = require('path');

const INDEX_PATH = path.resolve(__dirname, '..', 'index.html');

function fail(msg) {
  console.error(`[check_i18n] ${msg}`);
  process.exitCode = 1;
}

function readIndex() {
  if (!fs.existsSync(INDEX_PATH)) {
    fail(`index.html not found at ${INDEX_PATH}`);
    process.exit(1);
  }
  return fs.readFileSync(INDEX_PATH, 'utf8');
}

/**
 * Locate the inline `const UI_TRANSLATIONS = { ... };` declaration and return
 * its object body as a string we can eval safely in a sandboxed Function.
 */
function extractTranslationsSource(html) {
  const startMarker = 'const UI_TRANSLATIONS =';
  const startIdx = html.indexOf(startMarker);
  if (startIdx === -1) {
    fail('Could not locate `const UI_TRANSLATIONS =` in index.html');
    process.exit(1);
  }

  const braceStart = html.indexOf('{', startIdx);
  if (braceStart === -1) {
    fail('Could not find opening `{` of UI_TRANSLATIONS object');
    process.exit(1);
  }

  let depth = 0;
  let inSingle = false;
  let inDouble = false;
  let inTemplate = false;
  let inLineComment = false;
  let inBlockComment = false;
  let i = braceStart;
  for (; i < html.length; i++) {
    const ch = html[i];
    const next = html[i + 1];

    if (inLineComment) {
      if (ch === '\n') inLineComment = false;
      continue;
    }
    if (inBlockComment) {
      if (ch === '*' && next === '/') { inBlockComment = false; i++; }
      continue;
    }
    if (inSingle) {
      if (ch === '\\') { i++; continue; }
      if (ch === "'") inSingle = false;
      continue;
    }
    if (inDouble) {
      if (ch === '\\') { i++; continue; }
      if (ch === '"') inDouble = false;
      continue;
    }
    if (inTemplate) {
      if (ch === '\\') { i++; continue; }
      if (ch === '`') inTemplate = false;
      continue;
    }

    if (ch === '/' && next === '/') { inLineComment = true; i++; continue; }
    if (ch === '/' && next === '*') { inBlockComment = true; i++; continue; }
    if (ch === "'") { inSingle = true; continue; }
    if (ch === '"') { inDouble = true; continue; }
    if (ch === '`') { inTemplate = true; continue; }

    if (ch === '{') depth++;
    else if (ch === '}') {
      depth--;
      if (depth === 0) {
        return html.slice(braceStart, i + 1);
      }
    }
  }

  fail('Could not find matching `}` for UI_TRANSLATIONS object');
  process.exit(1);
}

function parseTranslations(source) {
  // Use Function() rather than eval to keep an explicit, contained scope.
  // The object literal is plain data with string/array values only.
  try {
    return Function(`"use strict"; return (${source});`)();
  } catch (err) {
    fail(`Failed to parse UI_TRANSLATIONS: ${err.message}`);
    process.exit(1);
  }
}

const HANGUL_RE = /[ᄀ-ᇿ㄰-㆏가-힯ꥠ-꥿ힰ-퟿]/;

function containsHangul(value) {
  if (typeof value === 'string') return HANGUL_RE.test(value);
  if (Array.isArray(value)) return value.some(containsHangul);
  return false;
}

function isEmptyString(value) {
  return typeof value === 'string' && value.trim() === '';
}

function main() {
  const html = readIndex();
  const source = extractTranslationsSource(html);
  const translations = parseTranslations(source);

  if (!translations || typeof translations !== 'object') {
    fail('UI_TRANSLATIONS did not parse to an object');
    return;
  }

  const ko = translations.ko;
  const en = translations.en;

  if (!ko || typeof ko !== 'object') {
    fail('Missing `ko` translation pack');
    return;
  }
  if (!en || typeof en !== 'object') {
    fail('Missing `en` translation pack');
    return;
  }

  const koKeys = new Set(Object.keys(ko));
  const enKeys = new Set(Object.keys(en));

  const missingInEn = [...koKeys].filter((k) => !enKeys.has(k));
  const extraInEn = [...enKeys].filter((k) => !koKeys.has(k));

  if (missingInEn.length) {
    fail(`Keys present in ko but missing in en: ${missingInEn.join(', ')}`);
  }
  if (extraInEn.length) {
    fail(`Keys present in en but missing in ko: ${extraInEn.join(', ')}`);
  }

  for (const key of koKeys) {
    if (!enKeys.has(key)) continue;
    const koVal = ko[key];
    const enVal = en[key];
    if (Array.isArray(koVal) || Array.isArray(enVal)) {
      if (!Array.isArray(koVal) || !Array.isArray(enVal)) {
        fail(`Type mismatch for key "${key}": ko=${Array.isArray(koVal) ? 'array' : typeof koVal}, en=${Array.isArray(enVal) ? 'array' : typeof enVal}`);
        continue;
      }
      if (koVal.length !== enVal.length) {
        fail(`Array length mismatch for key "${key}": ko=${koVal.length}, en=${enVal.length}`);
      }
    }
  }

  for (const [key, value] of Object.entries(en)) {
    if (containsHangul(value)) {
      if (Array.isArray(value)) {
        value.forEach((item, idx) => {
          if (containsHangul(item)) {
            fail(`Hangul character found in en.${key}[${idx}]: ${JSON.stringify(item)}`);
          }
        });
      } else {
        fail(`Hangul character found in en.${key}: ${JSON.stringify(value)}`);
      }
    }
    if (Array.isArray(value)) {
      value.forEach((item, idx) => {
        if (isEmptyString(item)) fail(`Empty string in en.${key}[${idx}]`);
      });
    } else if (isEmptyString(value)) {
      fail(`Empty string in en.${key}`);
    }
  }

  const targetedCoverage = [
    {
      label: 'lower landing hero',
      hardcoded: '복잡한 체류,<br>Paradiso에서 손쉽게.',
      keys: ['brandHeroTitle', 'brandHeroButtons', 'brandHeroStats', 'featureTitle', 'featureBody'],
      wiring: ['brandHeroTitle', 'brandHeroButtons', 'brandHeroStats', 'featureTitle', 'featureBody']
    },
    {
      label: 'pathway/how/source/tools sections',
      hardcoded: '비자 코드보다 먼저, 생활의 경로를 봅니다.',
      keys: ['pathwayTitle', 'pathwayTitles', 'pathwayDescs', 'howTitle', 'sourceTitle', 'toolsTitle'],
      wiring: ['pathwayTitle', 'pathwayTitles', 'pathwayDescs', 'howTitle', 'sourceTitle', 'toolsTitle']
    },
    {
      label: 'agent finder',
      hardcoded: '가까운 행정 도움 찾기',
      keys: ['agentTitle', 'agentSectionCopy', 'agentRegionLabel', 'agentKeywordLabel', 'agentEmpty', 'agentNaver', 'agentKakao'],
      wiring: ['agentTitle', 'agentSectionCopy', 'agentRegionLabel', 'agentKeywordLabel', 'agentEmpty', 'agentNaver', 'agentKakao']
    },
    {
      label: 'footer CTA',
      hardcoded: '내 체류 상황을 직접 검색해보세요.',
      keys: ['footerCtaTitle', 'footerCtaBody', 'footerCtaButtons', 'footerLinks'],
      wiring: ['footerCtaTitle', 'footerCtaBody', 'footerCtaButtons', 'footerLinks']
    },
    {
      label: 'search result labels',
      hardcoded: '데이터 기준:',
      keys: ['resultDataDate', 'resultSubtypes', 'resultCount', 'resultEmptyTitle', 'sourceTitleResult', 'actionAi'],
      wiring: ['resultDataDate', 'resultSubtypes', 'resultCount', 'resultEmptyTitle', 'sourceTitleResult', 'actionAi']
    }
  ];

  for (const item of targetedCoverage) {
    if (!html.includes(item.hardcoded)) continue;
    for (const key of item.keys) {
      if (!koKeys.has(key) || !enKeys.has(key)) {
        fail(`Targeted i18n coverage for ${item.label} is missing key "${key}"`);
      }
    }
    for (const key of item.wiring) {
      const keyRef = new RegExp(`['"\`]${key}['"\`]`);
      if (!keyRef.test(html)) {
        fail(`Targeted i18n coverage for ${item.label} is missing apply/render wiring for "${key}"`);
      }
    }
  }

  if (process.exitCode === 1) {
    console.error('[check_i18n] FAILED');
  } else {
    console.log(`[check_i18n] OK — ${Object.keys(en).length} keys in en, ${Object.keys(ko).length} in ko`);
  }
}

main();
