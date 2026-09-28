from __future__ import annotations

import json
import os
import re
import time
import zipfile
from io import BytesIO
from pathlib import Path
from typing import Dict, Iterable, List, Optional

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "config" / "settings.json"
DATA_DIR = ROOT / "data"
RAW_DIR = ROOT / "raw"
BASE_URL = "https://opendart.fss.or.kr/api"

ACCOUNT_ALIASES = {
    "total_assets": ["자산총계", "총자산"],
    "cash": ["현금및현금성자산", "현금 및 현금성자산"],
    "receivables": ["매출채권", "매출채권및기타채권", "매출채권 및 기타채권"],
    "inventory": ["재고자산"],
    "ppe": ["유형자산"],
    "total_liabilities": ["부채총계", "총부채"],
    "interest_bearing_debt": ["차입금", "단기차입금", "장기차입금", "사채", "유동성장기부채"],
    "equity": ["자본총계", "총자본"],
    "revenue": ["매출액", "수익(매출액)", "영업수익"],
    "gross_profit": ["매출총이익"],
    "sga": ["판매비와관리비", "판매비와 관리비"],
    "operating_income": ["영업이익", "영업이익(손실)"],
    "ebt": ["법인세비용차감전순이익", "법인세비용차감전순이익(손실)", "세전이익"],
    "net_income": ["당기순이익", "당기순이익(손실)"],
    "net_income_parent": ["지배기업의 소유주에게 귀속되는 당기순이익", "지배기업 소유주지분", "지배주주순이익"],
    "interest_expense": ["이자비용", "금융비용"],
    "cfo": ["영업활동으로 인한 현금흐름", "영업활동현금흐름", "영업활동 현금흐름"],
    "cfi": ["투자활동으로 인한 현금흐름", "투자활동현금흐름", "투자활동 현금흐름"],
    "cff": ["재무활동으로 인한 현금흐름", "재무활동현금흐름", "재무활동 현금흐름"],
    "capex": ["유형자산의 취득", "유형자산 취득", "유형자산의 취득(증가)", "무형자산의 취득"],
    "eps": ["기본주당이익", "희석주당이익", "주당이익"],
}

REPORTS = {
    "annual": "11011",
    "half_year": "11012",
    "quarterly_q1": "11013",
    "quarterly_q3": "11014",
}


def load_config() -> dict:
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def require_key() -> str:
    key = os.getenv("DART_API_KEY", "").strip()
    if not key:
        raise RuntimeError("DART_API_KEY 환경변수가 없습니다. GitHub Actions에서는 Repository Secret으로 설정하세요.")
    return key


def api_get(endpoint: str, params: dict, binary: bool = False, timeout: int = 60):
    key = require_key()
    q = dict(params)
    q["crtfc_key"] = key
    r = requests.get(f"{BASE_URL}/{endpoint}", params=q, timeout=timeout)
    r.raise_for_status()
    if binary:
        return r.content
    data = r.json()
    if str(data.get("status")) != "000":
        raise RuntimeError(f"OpenDART error {data.get('status')}: {data.get('message')}")
    return data


def normalize_text(value: str) -> str:
    return re.sub(r"\s+", "", str(value)).replace("ㆍ", "·").lower()


def to_number(value) -> Optional[float]:
    if value is None:
        return None
    s = str(value).strip().replace(",", "")
    if s in {"", "-", "—", "N/A", "nan", "None"}:
        return None
    negative = s.startswith("(") and s.endswith(")")
    s = s.strip("()")
    try:
        n = float(s)
        return -n if negative else n
    except ValueError:
        return None


def account_score(account_nm: str, aliases: List[str]) -> int:
    n = normalize_text(account_nm)
    scores = []
    for alias in aliases:
        a = normalize_text(alias)
        if n == a:
            scores.append(100)
        elif a in n:
            scores.append(60)
    return max(scores, default=0)


def choose_account(rows: List[dict], aliases: List[str]) -> Optional[dict]:
    scored = [(account_score(r.get("account_nm", ""), aliases), r) for r in rows]
    scored = [x for x in scored if x[0] > 0]
    if not scored:
        return None
    scored.sort(key=lambda x: x[0], reverse=True)
    return scored[0][1]


def get_amount(row: Optional[dict], period: str) -> Optional[float]:
    if not row:
        return None
    # The API returns current period in thstrm_amount and previous period in frmtrm_amount.
    return to_number(row.get("thstrm_amount" if period == "current" else "frmtrm_amount"))


def fetch_financials(year: int, reprt_code: str, fs_div: str) -> List[dict]:
    return api_get(
        "fnlttSinglAcntAll.json",
        {"corp_code": "00126380", "bsns_year": str(year), "reprt_code": reprt_code, "fs_div": fs_div},
    ).get("list", [])


def fetch_filings(year: int) -> List[dict]:
    # OpenDART disclosure search is used only for the supported API period.
    data = api_get(
        "list.json",
        {
            "corp_code": "00126380",
            "bgn_de": f"{year}0101",
            "end_de": f"{year}1231",
            "pblntf_ty": "A",
            "page_no": 1,
            "page_count": 100,
            "sort": "date",
            "sort_mth": "desc",
        },
    )
    rows = data.get("list", [])
    keep = []
    keywords = ("사업보고서", "반기보고서", "1분기보고서", "3분기보고서")
    for r in rows:
        report_nm = r.get("report_nm", "")
        if any(k in report_nm for k in keywords):
            keep.append(r)
    return keep


def download_original(rcept_no: str, year: int, report_name: str) -> Optional[str]:
    try:
        content = api_get("document.xml", {"rcept_no": rcept_no}, binary=True)
        target_dir = RAW_DIR / str(year)
        target_dir.mkdir(parents=True, exist_ok=True)
        safe = re.sub(r"[^0-9A-Za-z가-힣._-]+", "_", report_name)
        out = target_dir / f"{rcept_no}_{safe}.zip"
        out.write_bytes(content)
        # Validate the ZIP without extracting it into the repository.
        with zipfile.ZipFile(BytesIO(content)) as zf:
            bad = zf.testzip()
            if bad:
                raise RuntimeError(f"원문 ZIP 검증 실패: {bad}")
        return str(out.relative_to(ROOT))
    except Exception as exc:
        print(f"[WARN] original filing {rcept_no}: {exc}")
        return None


def extract_metrics(rows: List[dict], year: int, report_code: str, report_label: str) -> dict:
    result = {"year": year, "report_code": report_code, "report_type": report_label, "fs_div": "CFS"}
    for metric, aliases in ACCOUNT_ALIASES.items():
        row = choose_account(rows, aliases)
        result[metric] = get_amount(row, "current")
    return result


def sum_debt(metrics: dict) -> Optional[float]:
    # Avoid double-counting when a broad 차입금 line is already present.
    direct = metrics.get("interest_bearing_debt")
    return direct


def safe_div(a, b):
    if a is None or b in (None, 0):
        return None
    return a / b


def calculate_ratios(df: pd.DataFrame) -> pd.DataFrame:
    df = df.sort_values(["year", "report_type"]).copy()
    df["net_debt"] = df["interest_bearing_debt"] - df["cash"]
    df["ebitda"] = df["operating_income"]
    # EBITDA is calculated as EBIT + depreciation/amortization when available.
    if "depreciation_amortization" in df.columns:
        df["ebitda"] = df["operating_income"] + df["depreciation_amortization"].fillna(0)
    df["gross_margin"] = df.apply(lambda r: safe_div(r.gross_profit, r.revenue), axis=1)
    df["operating_margin"] = df.apply(lambda r: safe_div(r.operating_income, r.revenue), axis=1)
    df["net_margin"] = df.apply(lambda r: safe_div(r.net_income, r.revenue), axis=1)
    df["ebitda_margin"] = df.apply(lambda r: safe_div(r.ebitda, r.revenue), axis=1)
    df["current_ratio"] = df.apply(lambda r: safe_div(r.current_assets, r.current_liabilities) if "current_assets" in df else None, axis=1)
    df["debt_ratio"] = df.apply(lambda r: safe_div(r.total_liabilities, r.equity), axis=1)
    df["equity_ratio"] = df.apply(lambda r: safe_div(r.equity, r.total_assets), axis=1)
    df["debt_dependency"] = df.apply(lambda r: safe_div(r.interest_bearing_debt, r.total_assets), axis=1)
    df["interest_coverage"] = df.apply(lambda r: safe_div(r.operating_income, r.interest_expense), axis=1)
    df["net_debt_to_ebitda"] = df.apply(lambda r: safe_div(r.net_debt, r.ebitda), axis=1)
    df["asset_turnover"] = df.apply(lambda r: safe_div(r.revenue, r.total_assets), axis=1)
    df["cfo_to_net_income"] = df.apply(lambda r: safe_div(r.cfo, r.net_income), axis=1)
    df["fcf"] = df["cfo"] - df["capex"].abs()
    df["revenue_growth"] = df.groupby("report_type")["revenue"].pct_change()
    return df


def build_legacy_status(start_year: int, end_year: int):
    rows = []
    for year in range(start_year, min(end_year, 2014) + 1):
        for report_type, code in REPORTS.items():
            rows.append({
                "year": year,
                "report_type": report_type,
                "report_code": code,
                "status": "API_UNAVAILABLE_PRE_2015",
                "note": "OpenDART fnltt financial APIs officially provide data from 2015 onward."
            })
    pd.DataFrame(rows).to_csv(DATA_DIR / "legacy_status.csv", index=False, encoding="utf-8-sig")


def main():
    cfg = load_config()
    start_year = int(cfg.get("start_year", 2010))
    end_year = int(pd.Timestamp.utcnow().year)
    DATA_DIR.mkdir(exist_ok=True)
    RAW_DIR.mkdir(exist_ok=True)

    all_metrics = []
    filings = []
    build_legacy_status(start_year, end_year)

    for year in range(max(start_year, 2015), end_year + 1):
        print(f"[INFO] {year}")
        try:
            year_filings = fetch_filings(year)
            for f in year_filings:
                report_nm = f.get("report_nm", "")
                rcept_no = f.get("rcept_no", "")
                filing_row = {
                    "year": year,
                    "report_nm": report_nm,
                    "rcept_no": rcept_no,
                    "corp_name": f.get("corp_name"),
                    "stock_code": f.get("stock_code"),
                    "flr_nm": f.get("flr_nm"),
                    "rcept_dt": f.get("rcept_dt"),
                    "report_url": f"https://dart.fss.or.kr/dsaf001/main.do?rcpNo={rcept_no}" if rcept_no else "",
                }
                if cfg.get("download_original_filings") and rcept_no:
                    filing_row["raw_file"] = download_original(rcept_no, year, report_nm) or ""
                filings.append(filing_row)
        except Exception as exc:
            print(f"[WARN] filing search {year}: {exc}")

        for report_type, code in REPORTS.items():
            label = {"annual": "annual", "half_year": "half-year", "quarterly_q1": "quarterly", "quarterly_q3": "quarterly"}[report_type]
            try:
                rows = fetch_financials(year, code, cfg.get("fs_div", "CFS"))
                if not rows:
                    continue
                m = extract_metrics(rows, year, code, label)
                m["report_variant"] = report_type
                all_metrics.append(m)
            except Exception as exc:
                print(f"[WARN] financials {year}/{code}: {exc}")
            time.sleep(0.1)

    if all_metrics:
        df = pd.DataFrame(all_metrics)
        # Add stable columns expected by the dashboard even if an account was absent.
        for col in ["current_assets", "current_liabilities", "depreciation_amortization"]:
            if col not in df.columns:
                df[col] = None
        df = calculate_ratios(df)
        df.to_csv(DATA_DIR / "financials.csv", index=False, encoding="utf-8-sig")
        ratio_cols = [c for c in df.columns if c in {
            "year", "report_code", "report_type", "report_variant", "gross_margin", "operating_margin", "net_margin",
            "ebitda_margin", "current_ratio", "debt_ratio", "equity_ratio", "debt_dependency", "interest_coverage",
            "net_debt_to_ebitda", "asset_turnover", "cfo_to_net_income", "fcf", "revenue_growth", "net_debt", "ebitda"
        }]
        df[ratio_cols].to_csv(DATA_DIR / "ratios.csv", index=False, encoding="utf-8-sig")
    else:
        pd.DataFrame(columns=["year", "report_code", "report_type"]).to_csv(DATA_DIR / "financials.csv", index=False, encoding="utf-8-sig")
        pd.DataFrame(columns=["year", "report_code", "report_type"]).to_csv(DATA_DIR / "ratios.csv", index=False, encoding="utf-8-sig")

    pd.DataFrame(filings).drop_duplicates(subset=["rcept_no"]).to_csv(DATA_DIR / "filings.csv", index=False, encoding="utf-8-sig")
    print("[OK] OpenDART update complete")


if __name__ == "__main__":
    main()
