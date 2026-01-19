import streamlit as st
import math

# 设置页面配置
st.set_page_config(page_title="标准公差查询 (ISO 286)", page_icon="📐")

st.title("📐 ISO 286 公差计算器 (圆整版)")
st.caption("✅ 已启用标准数值修约 (例如: 2.27mm → 2.3mm)")

# --- 1. 核心计算引擎 (标准分段法) ---

def get_geometric_mean_diameter(size):
    """
    获取尺寸分段的几何平均值 (D)
    """
    ranges = [
        (0, 3), (3, 6), (6, 10), (10, 18), (18, 30), (30, 50), 
        (50, 80), (80, 120), (120, 180), (180, 250), (250, 315), 
        (315, 400), (400, 500), (500, 630), (630, 800), (800, 1000),
        (1000, 1250), (1250, 1600), (1600, 2000), (2000, 2500), (2500, 3150)
    ]
    
    for (min_d, max_d) in ranges:
        if min_d < size <= max_d:
            d_geom = math.sqrt(min_d * max_d)
            return d_geom, min_d, max_d
            
    return size, size, size

def get_it_tolerance(size, grade):
    """
    计算标准公差等级 (IT) 宽度 (单位: 微米)
    """
    if size <= 0: return 0, 0, 0
    
    d_calc, r_min, r_max = get_geometric_mean_diameter(size)
    
    factor = 0.0
    if size <= 500:
        factor = 0.45 * (d_calc ** (1/3)) + 0.001 * d_calc
    else:
        # >500mm 公式: I = 0.004 * D + 2.1
        factor = 0.004 * d_calc + 2.1

    coeffs = {
        6: 10, 7: 16, 8: 25, 9: 40, 10: 64, 
        11: 100, 12: 160, 13: 250, 14: 400
    }
    
    if grade not in coeffs:
        return 0, r_min, r_max
        
    raw_it = coeffs[grade] * factor
    return raw_it, r_min, r_max

def get_fundamental_deviation(size, code):
    """
    计算基础偏差 (单位: 微米)
    """
    c = code.lower()
    is_hole = code.isupper()
    d_calc, _, _ = get_geometric_mean_diameter(size)
    dev = 0 
    
    if c == 'h':
        dev = 0
    elif c == 'f':
        dev = 2.5 * (d_calc ** 0.34)
        if is_hole: return dev # EI
        else: return -dev      # es
    elif c == 'g':
        dev = 2.5 * (d_calc ** 0.34)
        if is_hole: return dev # EI
        else: return -dev      # es
    elif c == 'k':
        return 0 

    return dev

# --- 2. 辅助功能: 智能显示修约 ---

def smart_format_mm(value_mm):
    """
    根据数值大小自动调整小数位数，模拟标准查表的修约风格
    """
    abs_val = abs(value_mm)
    
    if abs_val == 0:
        return "0"
    
    # 逻辑：数值越大，保留的小数位越少
    if abs_val >= 2.0:
        # 大于2mm (通常是IT13-14)，圆整到1位小数 (e.g., 2.27 -> 2.3)
        return f"{value_mm:.1f}"
    elif abs_val >= 1.0:
        # 1-2mm之间，保留2位 (e.g., 1.75)
        return f"{value_mm:.2f}"
    else:
        # 小于1mm (精密公差)，保留3位 (e.g., 0.025)
        return f"{value_mm:.3f}"

# --- 3. 界面交互 ---

col1, col2 = st.columns([3, 1])

with col1:
    size_input = st.number_input("输入公称尺寸 (mm)", min_value=1.0, max_value=3150.0, value=1000.0, step=10.0)

with col2:
    tolerance_code = st.selectbox(
        "公差带",
        ["h14", "h12", "h8", "h7", "g8", "H7", "H8", "F7", "G7", "K7"]
    )

calc_btn = st.button("开始计算", type="primary")

# --- 4. 计算逻辑 ---
if calc_btn:
    code_letter = tolerance_code[0] if tolerance_code[0].isalpha() else tolerance_code[:2]
    grade = int(tolerance_code[len(code_letter):])
    
    # 1. 计算
    it_raw_um, range_min, range_max = get_it_tolerance(size_input, grade)
    # 将计算出的 raw_it (微米) 转为 mm
    it_width_mm = it_raw_um / 1000.0
    
    # 2. 偏差
    is_hole = code_letter.isupper()
    fund_dev_um = get_fundamental_deviation(size_input, code_letter)
    fund_dev_mm = fund_dev_um / 1000.0
    
    upper_dev = 0.0
    lower_dev = 0.0
    
    if is_hole:
        if code_letter == 'H':
            lower_dev = 0.0
            upper_dev = it_width_mm
        elif code_letter in ['F', 'G']:
            lower_dev = fund_dev_mm
            upper_dev = lower_dev + it_width_mm
        elif code_letter == 'K':
             k_shift_um = -1.2 * (size_input ** 0.3)
             if size_input < 3: k_shift_um = 0
             upper_dev = k_shift_um / 1000.0
             lower_dev = upper_dev - it_width_mm
    else:
        if code_letter == 'h':
            upper_dev = 0.0
            lower_dev = -it_width_mm
        elif code_letter == 'g':
            upper_dev = fund_dev_mm
            lower_dev = upper_dev - it_width_mm
            
    max_size = size_input + upper_dev
    min_size = size_input + lower_dev
    
    # --- 5. 结果展示 (应用修约) ---
    st.divider()
    st.subheader(f"✅ 结果: {tolerance_code} (Ø{size_input:g})")
    st.caption(f"分段范围: {range_min} ~ {range_max} mm")
    
    # 格式化显示字符串
    str_max = f"{max_size:.3f}" 
    str_min = f"{min_size:.3f}"
    
    # 公差带宽度的显示优化
    str_it_width = smart_format_mm(it_width_mm) # 这里应用圆整逻辑
    
    # 偏差的显示优化
    str_upper = smart_format_mm(upper_dev)
    str_lower = smart_format_mm(lower_dev)
    
    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("最大极限", f"{str_max} mm")
    with c2:
        st.metric("最小极限", f"{str_min} mm")
    with c3:
        # 显示圆整后的公差值 (例如 2.3 mm)
        st.metric("公差带 (IT)", f"{str_it_width} mm")
        
    st.write("---")
    cd1, cd2 = st.columns(2)
    
    # 添加正负号显示逻辑
    def fmt_sign(val_str):
        if float(val_str) > 0: return "+" + val_str
        return val_str

    with cd1:
        st.info(f"**上偏差**: {fmt_sign(str_upper)} mm")
    with cd2:
        st.info(f"**下偏差**: {fmt_sign(str_lower)} mm")
