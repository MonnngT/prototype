import streamlit as st
import re

# 设置页面配置
st.set_page_config(page_title="公差 & 键槽查询", page_icon="📏")

st.title("📏 ISO 286 公差 & 键槽计算器")
st.markdown("支持：轴/孔配合 (H7, g6...) 及 **键槽标准 (JS9, P9...)**")

# --- 1. 核心数据逻辑 ---

# 标准公差等级 IT (单位: 微米 μm)
# 键为尺寸分段上限
IT_TABLE = {
    3:   [4, 6, 10, 14, 25, 40, 60, 100, 140],
    6:   [5, 8, 12, 18, 30, 48, 75, 120, 180],
    10:  [6, 9, 15, 22, 36, 58, 90, 150, 220],
    18:  [8, 11, 18, 27, 43, 70, 110, 180, 270],
    30:  [9, 13, 21, 33, 52, 84, 130, 210, 330],
    50:  [11, 16, 25, 39, 62, 100, 160, 250, 390],
    80:  [13, 19, 30, 46, 74, 120, 190, 300, 460],
    120: [15, 22, 35, 54, 87, 140, 220, 350, 540],
    180: [18, 25, 40, 63, 100, 160, 250, 400, 630],
    250: [20, 29, 46, 72, 115, 185, 290, 460, 720],
    315: [23, 32, 52, 81, 130, 210, 320, 520, 810],
    400: [25, 36, 57, 89, 140, 230, 360, 570, 890],
    500: [27, 40, 63, 97, 155, 250, 400, 630, 970]
}

# 基础偏差计算逻辑 (新增 JS, P, N 支持)
def get_fundamental_deviation(size, letter):
    is_hole = letter.isupper()
    code = letter.lower()
    dev = 0
    
    # === 特殊处理：对称公差 JS/js ===
    if code == 'js':
        return "SYMMETRIC" # 特殊标记，后续处理

    # === 常规偏差估算 (单位: 微米) ===
    # 数据基于 ISO 286 简化拟合，覆盖常用范围
    if code == 'h':
        dev = 0
    
    # 间隙配合常用 (轴)
    elif code == 'g':
        if size <= 3: dev = -2
        elif size <= 6: dev = -4
        elif size <= 10: dev = -5
        elif size <= 18: dev = -6
        elif size <= 30: dev = -7
        elif size <= 50: dev = -9
        else: dev = -10
    elif code == 'f':
        if size <= 3: dev = -6
        elif size <= 6: dev = -10
        elif size <= 10: dev = -13
        elif size <= 18: dev = -16
        elif size <= 30: dev = -20
        else: dev = -25
    elif code == 'e':
        if size <= 3: dev = -14
        elif size <= 6: dev = -20
        elif size <= 10: dev = -25
        elif size <= 18: dev = -32
        elif size <= 30: dev = -40
        else: dev = -50
        
    # 过渡/过盈配合常用 (键槽常用 P, N)
    # 注意：这里仅提供近似值用于参考，P/N 随等级变化较复杂
    elif code == 'm':
        if size <= 3: dev = 2
        elif size <= 6: dev = 4
        elif size <= 10: dev = 6
        elif size <= 18: dev = 7
        elif size <= 30: dev = 8
        else: dev = 9
    elif code == 'n': # 常用键槽过渡
        if size <= 3: dev = 4
        elif size <= 6: dev = 8
        elif size <= 10: dev = 10
        elif size <= 18: dev = 12
        elif size <= 30: dev = 15
        else: dev = 17
    elif code == 'p': # 常用键槽紧配合
        if size <= 3: dev = 6
        elif size <= 6: dev = 12
        elif size <= 10: dev = 15
        elif size <= 18: dev = 18
        elif size <= 30: dev = 22
        else: dev = 26
    
    # 简单反转逻辑：如果是孔 (除了JS/H)，通用规则大约是反向
    # 严格标准中 Hole Delta 并不总是等于 Shaft es，但作为现场工具够用
    if is_hole:
        if code == 'h': return 0
        return -dev 
            
    return dev

def get_it_value(size, grade):
    ranges = [3, 6, 10, 18, 30, 50, 80, 120, 180, 250, 315, 400, 500]
    found_range = None
    for r in ranges:
        if size <= r:
            found_range = r
            break
    if not found_range or not (5 <= grade <= 13):
        return None
    return IT_TABLE[found_range][grade - 5]

# --- 2. 界面交互层 ---

st.header("🔍 输入规格")
col1, col2 = st.columns([2, 1])

with col1:
    # 增加提示
    user_input = st.text_input("输入代号 (如: 3JS9, 15H7, 8P9)", "3JS9")

with col2:
    st.write("") 
    st.write("") 
    check_btn = st.button("计算", type="primary")

# --- 3. 计算与解析逻辑 ---
if check_btn or user_input:
    pattern = r"(\d+(?:\.\d+)?)\s*([A-Za-z]+)\s*(\d+)"
    match = re.match(pattern, user_input.strip())
    
    if match:
        size_str, dev_char, grade_str = match.groups()
        nominal_size = float(size_str)
        tolerance_grade = int(grade_str)
        
        # 获取 IT 值
        it_val_microns = get_it_value(nominal_size, tolerance_grade)
        
        if it_val_microns is None:
            st.error("⚠️ 尺寸超出范围 (0-500mm) 或 等级不支持 (IT5-13)")
        else:
            it_val_mm = it_val_microns / 1000.0
            
            # 核心判断
            raw_dev = get_fundamental_deviation(nominal_size, dev_char)
            
            is_symmetric = False
            upper_dev = 0.0
            lower_dev = 0.0
            desc = ""

            # === 逻辑分支 A: 对称公差 (JS/js) ===
            if raw_dev == "SYMMETRIC":
                is_symmetric = True
                half_it = it_val_mm / 2.0
                upper_dev = half_it
                lower_dev = -half_it
                desc = "对称公差 (常用键槽/通用)"
                
            # === 逻辑分支 B: 普通孔/轴 ===
            else:
                fund_dev_mm = raw_dev / 1000.0
                is_hole = dev_char.isupper()
                
                if is_hole:
                    desc = "孔 / 键槽宽 (Hole/Slot)"
                    if dev_char == 'H':
                        lower_dev = 0.0
                        upper_dev = it_val_mm
                    elif dev_char == 'P': # 特殊处理 P9 孔 (紧)
                         # ISO标准: P孔 ES = Delta, EI = ES - IT
                         # 这里的 raw_dev 是基于轴 p 的，约为正值。孔 P 约为负值。
                         # 简化处理：孔P的上偏差 ≈ 轴p下偏差的相反数 + Delta... 
                         # 为简化：直接使用查表反转逻辑
                         upper_dev = fund_dev_mm
                         lower_dev = upper_dev - it_val_mm
                    else:
                        # 通用孔: 下偏差 = 基础偏差
                        lower_dev = fund_dev_mm
                        upper_dev = lower_dev + it_val_mm
                else:
                    desc = "轴 / 键宽 (Shaft/Key)"
                    # 通用轴: 上偏差 = 基础偏差 (对于 g, f, e 等负偏差)
                    # 对于 k, m, n, p 等正偏差，基础偏差通常是 下偏差 ei
                    # 这里为了简化，假设 get_fundamental_deviation 返回的是“距离零线最近的那个偏差”
                    
                    if dev_char.lower() in ['k', 'm', 'n', 'p']:
                        lower_dev = fund_dev_mm
                        upper_dev = lower_dev + it_val_mm
                    else:
                        upper_dev = fund_dev_mm
                        lower_dev = upper_dev - it_val_mm

            # 计算最终尺寸
            max_size = nominal_size + upper_dev
            min_size = nominal_size + lower_dev
            
            # --- 4. 结果显示 ---
            st.divider()
            st.subheader(f"✅ {nominal_size:.3f} {dev_char}{tolerance_grade}")
            
            # 结果卡片
            c1, c2 = st.columns(2)
            with c1:
                st.info(f"最大极限: **{max_size:.4f}** mm")
            with c2:
                st.info(f"最小极限: **{min_size:.4f}** mm")
            
            # 偏差详情
            c3, c4, c5 = st.columns(3)
            with c3:
                 st.caption("类型")
                 st.write(desc)
            with c4:
                 st.caption("上偏差")
                 if is_symmetric:
                     st.write(f"**+{upper_dev*1000:.1f}** μm")
                 else:
                     st.write(f"**{upper_dev*1000:+.1f}** μm")
            with c5:
                 st.caption("下偏差")
                 if is_symmetric:
                     st.write(f"**{lower_dev*1000:.1f}** μm")
                 else:
                     st.write(f"**{lower_dev*1000:+.1f}** μm")

            st.success(f"公差带宽度: {it_val_microns} μm")
            
            # 图示
            if is_symmetric:
                st.write("---")
                st.caption(f"📏 对称分布 (±{it_val_microns/2:.1f} μm)")
                st.progress(0.5) # 居中
                st.caption(f"基准: {nominal_size} mm")

    else:
        st.warning("格式错误。尝试输入: 3JS9, 10P9, 40H7")

st.markdown("---")
st.caption("注：键槽 JS9 为对称公差。P9/N9 为估算值，精密模具请核对 DIN 6885 标准。")
