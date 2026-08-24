import subprocess
import sys

# Tự động cài đặt vnstock ngầm để tránh lỗi xung đột hệ thống Streamlit
try:
  import vnstock
except ImportError:
  subprocess.run(
      [sys.executable, "-m", "pip", "install", "vnstock", "--no-deps"],
      check=True,
  )

import concurrent.futures
from datetime import datetime
import time
import numpy as np
import pandas as pd
import streamlit as st
from vnstock import stock_historical_data

st.set_page_config(
    page_title="Hệ Thống Quét Sóng Thời Gian Thực", page_icon="🚀", layout="wide"
)

DEFAULT_SYMBOLS = [
    "HPG",
    "VIC",
    "VHM",
    "VRE",
    "VCB",
    "BID",
    "CTG",
    "TCB",
    "MBB",
    "ACB",
    "VPB",
    "STB",
    "SHB",
    "LPB",
    "SSB",
    "MSN",
    "VNM",
    "SAB",
    "GAS",
    "POW",
    "FPT",
    "MWG",
    "PNJ",
    "REE",
    "NVL",
    "DIG",
    "PDR",
    "KDH",
    "CEO",
    "SSI",
    "VCI",
    "VND",
    "HCM",
    "MBS",
    "FTS",
    "BSI",
    "ORS",
    "VIX",
    "DGC",
    "DCM",
    "DPM",
    "GEX",
    "VGC",
    "KBC",
    "IDC",
    "VHC",
    "ANV",
    "HHV",
    "LCG",
    "VCG",
    "CII",
    "PC1",
    "VPI",
    "TVN",
    "PAS",
    "HAG",
    "DBC",
    "BAF",
    "SBT",
    "ASM",
    "HSG",
    "NKG",
    "TLG",
    "PTB",
]

st.markdown(
    """
    <h2 style='text-align: center; color: #FF4B4B;'>🚀 HỆ THỐNG QUÉT SÓNG THỜI GIAN THỰC (KHUNG 5 PHÚT)</h2>
""",
    unsafe_allow_html=True,
)
st.write(
    "Hệ thống đa luồng tốc độ cao quét toàn bộ danh sách mã cổ phiếu, lọc ra"
    " các mã có thanh khoản đột biến so với trung bình 20 nến 5 phút gần nhất."
)

st.sidebar.markdown("### ⚙️ Tùy chỉnh quét thời gian thực")
selected_symbols = st.sidebar.multiselect(
    "Danh sách mã theo dõi:", DEFAULT_SYMBOLS, default=DEFAULT_SYMBOLS[:30]
)
volume_threshold = st.sidebar.slider(
    "Ngưỡng đột biến khối lượng (X lần so với TB 20 nến 5p):",
    1.0,
    5.0,
    1.6,
    0.1,
)
max_workers = st.sidebar.slider("Số luồng xử lý song song (Tốc độ):", 5, 30, 15)


def check_stock(symbol):
  try:
    df = stock_historical_data(
        symbol=symbol,
        resolution="5",
        start_date="2026-01-01",
        end_date=datetime.now().strftime("%Y-%m-%d"),
        source="VCI",
    )
    if df is not None and len(df) > 20:
      df["Vol_MA20"] = df["volume"].rolling(window=20).mean()
      last_row = df.iloc[-1]
      prev_vol_ma = last_row["Vol_MA20"]
      last_vol = last_row["volume"]
      last_close = last_row["close"]
      prev_close = df.iloc[-2]["close"]
      price_change = ((last_close - prev_close) / prev_close) * 100

      if prev_vol_ma > 0 and last_vol >= (prev_vol_ma * volume_threshold):
        return {
            "Mã": symbol,
            "Giá Hiện Tại": last_close,
            "Biến Động (%)": round(price_change, 2),
            "Khối Lượng Nến Cuối": int(last_vol),
            "TB 20 Nến (5p)": int(prev_vol_ma),
            "Đột Biến (Lần)": round(last_vol / prev_vol_ma, 2),
        }
  except Exception:
    pass
  return None


if st.button(
    "🔍 CHẠY QUÉT THỜI GIAN THỰC NGAY", type="primary", use_container_width=True
):
  if not selected_symbols:
    st.warning("Vui lòng chọn ít nhất một mã cổ phiếu để quét.")
  else:
    with st.spinner(
        "Đang quét dữ liệu thời gian thực toàn bộ danh sách mã..."
    ):
      results = []
      start_time = time.time()

      with concurrent.futures.ThreadPoolExecutor(
          max_workers=max_workers
      ) as executor:
        futures = {
            executor.submit(check_stock, sym): sym for sym in selected_symbols
        }
        for future in concurrent.futures.as_completed(futures):
          res = future.result()
          if res:
            results.append(res)

      elapsed_time = time.time() - start_time
      st.success(
          f"Quét hoàn tất {len(selected_symbols)} mã trong {elapsed_time:.2f}"
          " giây!"
      )

      if results:
        res_df = pd.DataFrame(results)
        res_df = res_df.sort_values(by="Đột Biến (Lần)", ascending=False)
        st.dataframe(res_df, use_container_width=True)
      else:
        st.info(
            "Hiện tại chưa có mã nào chạm ngưỡng đột biến trong khung 5 phút"
            " vừa qua."
        )

st.markdown("---")
st.markdown(
    "💡 *Mẹo thực chiến: Trong phiên giao dịch, bạn hãy mở trang web này và"
    " bấm nút quét liên tục để nắm bắt ngay các mã đang bùng nổ thanh khoản.*"
)

