import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed

try:
    from vnstock.api.quote import Quote
except ImportError:
    pass

st.set_page_config(page_title="Hệ Thống Quét Sóng Real-Time 150+ Mã", layout="wide")

st.title("🚀 HỆ THỐNG QUÉT SÓNG THỜI GIAN THỰC (KHUNG 5 PHÚT)")
st.markdown("Hệ thống đa luồng tốc độ cao quét toàn bộ danh sách mã cổ phiếu, lọc ra các mã có thanh khoản đột biến so với trung bình 20 nến 5 phút gần nhất.")

# Tích hợp toàn bộ danh sách mã cổ phiếu của bạn vào đây
DEFAULT_SYMBOLS = [
    "SHS", "VND", "GEX", "VDS", "PHP", "VIX", "HCM", "VRE", "IDC", 
    "ACB", "HSG", "VPB", "TV2", "NLG", "PAN", "VGS", "EVF", "PHR", 
    "CTD", "PVD", "PET", "ELC", "NAB", "CTR", "OCB", "GAS", "TCH", 
    "SBG", "DXG", "HPG", "CTG", "TCB", "DPR", "POW", "MSB", "BFC", 
    "MSR", "GMD", "FCN", "DCM", "VSC", "VCK", "VOS", "MWG", "FPT", 
    "PAC", "VCG", "GVR", "HAH", "ACV", "VTO", "BAF", "NT2", "NTP", 
    "PVS", "LPB", "BSR", "CTS", "VCI", "BVS", "EVS", "APS", "CII", 
    "HDG", "DBC", "GIL", "BVB", "QCG", "OIL", "DDV", "YEG", "PVP", 
    "KBC", "HHP", "VEA", "AGG", "CEO", "FTS", "KDH", "SZC", "BIC", 
    "DRI", "ANV", "G36", "HHV", "GEG", "TNG", "VGT", "IJC", "DXP", 
    "KLB", "QTP", "D2D", "DTD", "FOX", "HUT", "BVH", "AAS", "ORS", 
    "PNJ", "SSI", "DIG", "PDR", "TCX", "CSV", "NVB", "TPB", "DPM", 
    "HDB", "BMS", "VGC", "BMP", "PSD", "HAG", "MSH", "NTL", "SAB", 
    "ITC", "VTP", "MBS", "HHS", "BSI", "L14", "AGR", "DPG", "EIB", 
    "BID", "TCI", "NKG", "NVL", "MIG", "PC1", "VIB", "LCG", "VPI", 
    "TVN", "PVC", "SSB", "VGI", "AAV", "VIW", "DHC"
]

st.sidebar.header("⚙️ Tùy chỉnh quét thời gian thực")
selected_symbols = st.sidebar.multiselect("Danh sách mã theo dõi:", DEFAULT_SYMBOLS, default=DEFAULT_SYMBOLS)
volume_multiplier = st.sidebar.slider("Ngưỡng đột biến khối lượng (X lần so với TB 20 nến 5p):", 1.5, 5.0, 2.0, 0.1)
max_threads = st.sidebar.slider("Số luồng xử lý song song (Tốc độ):", 5, 30, 15)

# Hàm quét từng mã độc lập an toàn
def scan_single_symbol(symbol, volume_multiplier):
    try:
        today = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=3)).strftime('%Y-%m-%d')
        
        q = Quote(symbol=symbol, source='VCI')
        df = q.history(start=start_date, end=today, interval='5m')
        
        if df is not None and len(df) > 20:
            df.columns = [str(c).strip().lower() for c in df.columns]
            col_map = {}
            for c in df.columns:
                if 'time' in c or 'date' in c or 'ngay' in c:
                    col_map[c] = 'datetime'
                elif 'close' in c:
                    col_map[c] = 'close'
                elif 'vol' in c or 'kl' in c or 'volume' in c:
                    col_map[c] = 'volume'
            df = df.rename(columns=col_map)
            
            if 'close' in df.columns and 'volume' in df.columns:
                df['vol_ma20'] = df['volume'].rolling(20).mean()
                latest = df.iloc[-1]
                prev_vol_ma = latest['vol_ma20']
                
                if pd.notna(prev_vol_ma) and prev_vol_ma > 0:
                    ratio = latest['volume'] / prev_vol_ma
                    if ratio >= volume_multiplier:
                        return {
                            'Mã CP': symbol,
                            'Thời gian nến': str(latest.get('datetime', 'Mới nhất')),
                            'Giá hiện tại': latest['close'],
                            'Khối lượng nến 5p': int(latest['volume']),
                            'Trung bình 20 nến': int(prev_vol_ma),
                            'Mức đột biến': f"{round(ratio, 2)}x lần"
                        }
    except Exception:
        pass
    return None

if st.button("🔍 CHẠY QUÉT THỜI GIAN THỰC NGAY", type="primary"):
    if not selected_symbols:
        st.warning("Vui lòng chọn ít nhất một mã cổ phiếu.")
    else:
        results = []
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        total_symbols = len(selected_symbols)
        completed = 0
        
        # Quét đa luồng toàn bộ danh sách lớn cực nhanh
        with ThreadPoolExecutor(max_workers=max_threads) as executor:
            future_to_symbol = {executor.submit(scan_single_symbol, sym, volume_multiplier): sym for sym in selected_symbols}
            
            for future in as_completed(future_to_symbol):
                completed += 1
                progress_bar.progress(completed / total_symbols)
                status_text.text(f"Đang quét dữ liệu... ({completed}/{total_symbols}) mã")
                
                res = future.result()
                if res:
                    results.append(res)
                    
        status_text.empty()
        progress_bar.empty()
        
        if results:
            res_df = pd.DataFrame(results)
            st.success(f"🔥 Phát hiện {len(res_df)} mã đang có dòng tiền lớn kích hoạt ở khung 5 phút!")
            st.dataframe(res_df, use_container_width=True)
        else:
            st.warning("Hiện tại chưa có mã nào chạm ngưỡng đột biến trong khung 5 phút vừa qua.")

st.markdown("---")
st.markdown("💡 *Mẹo thực chiến: Trong phiên giao dịch, bạn hãy mở trang web này và bấm nút quét liên tục để nắm bắt ngay các mã đang bùng nổ thanh khoản.*")

