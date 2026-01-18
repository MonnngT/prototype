import streamlit as st
import re
import math

# 设置页面配置
st.set_page_config(page_title="公差查询助手", page_icon="📏")

st.title("📏 ISO 286 公差计算器")
st.markdown("快速计算轴孔配合公差，支持常用工业精度。")

# --- 1. 核心数据逻辑 (简化版常用数据库) ---
# 为了保持单文件运行，我们将常用公差表内置在代码中
# 数据来源参考 ISO 286-1 标准

# 标准公差等级 IT (单位: 微米 μm)
# 键为尺寸分段上限 (e.g., 3代表 0-3mm, 6代表 3-6mm)
IT_TABLE = {
    # 尺寸段: [IT5, IT6, IT7, IT8, IT9, IT10, IT11, IT12, IT13]
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

# 基础偏差计算逻辑 (这是一个简化的查找函数，覆盖常用偏差)
def get_fundamental_deviation(size, letter):
    # 将输入转为小写处理，大写即为孔，小写即为轴
    is_hole = letter.isupper()
    code = letter.lower()
    
    # 简单的偏差估算或查表逻辑 (仅示例常用几个，实际标准非常复杂)
    # 单位：微米
    dev = 0
    
    # --- 常用基础偏差 (简略版) ---
    if code == 'h':
        dev = 0
    elif code == 'g':
        # g 的基本偏差通常是负值，随尺寸变化
        if size <= 3: dev = -2
        elif size <= 6: dev = -4
        elif size <= 10: dev = -5
        elif size <= 18: dev = -6
        elif size <= 30: dev = -7
        elif size <= 50: dev = -9
        elif size <= 80: dev = -10
        elif size <= 120: dev = -12
        elif size <= 180: dev = -14
        else: dev = -15
    elif code == 'f':
        # f 的偏差更负
        if size <= 3: dev = -6
        elif size <= 6: dev = -10
        elif size <= 10: dev = -13
        elif size <= 18: dev = -16
        elif size <= 30: dev = -20
        elif size <= 50: dev = -25
        else: dev = -30
    elif code == 'k':
        dev = 0 # 简化处理，实际k在不同等级有细微差别
    elif code == 'm':
        if size <= 3: dev = +2
        elif size <= 6: dev = +4
        elif size <= 10: dev = +6
        elif size <= 18: dev = +7
        elif size <= 30: dev = +8
        else: dev = +9
    # ... 更多偏差可以在此扩展
    
    # 如果是孔 (大写)，基础偏差规则反转 (对于通用规则)
    # H (孔) EI = 0 -> 类似 h (轴) es = 0
    if is_hole:
        if code == 'h': 
            return 0 # H孔，EI=0
        # 这是一个非常简化的转换，实际ISO标准孔轴转换需考虑Delta值
        # 这里为了演示核心逻辑，主要支持 H 孔和 h 轴
        if code != 'h':
            st.warning(f"当前版本主要精确支持 H (基孔制) 和 h (基轴制)。'{letter}' 的计算可能为近似值。")
            return -dev 
            
    return dev

def get_it_value(size, grade):
    ranges = [3, 6, 10, 18, 30, 50, 80, 120, 180, 250, 315, 400, 500]
    # 找到尺寸所在的区间
    found_range = None
    for r in ranges:
        if size <= r:
            found_range = r
            break
    
    if not found_range:
        return None
    
    # IT等级映射 (5 -> index 0, 13 -> index 8)
    if 5 <= grade <= 13:
        idx = grade - 5
        return IT_TABLE[found_range][idx]
    return None

# --- 2. 界面交互层 ---

st.header("🔍 查询输入")
col1, col2 = st.columns([2, 1])

with col1:
    user_input = st.text_input("输入公差代号 (例如: 15H7, 20g6)", "15H7")

with col2:
    st.write("") # 占位
    st.write("") 
    check_btn = st.button("计算", type="primary")

# --- 3. 计算与解析逻辑 ---
if check_btn or user_input:
    # 使用正则表达式解析输入: 15H7 -> 15, H, 7
    pattern = r"(\d+(?:\.\d+)?)\s*([A-Za-z]+)\s*(\d+)"
    match = re.match(pattern, user_input.strip())
    
    if match:
        size_str, dev_char, grade_str = match.groups()
        nominal_size = float(size_str)
        tolerance_grade = int(grade_str)
        
        if nominal_size > 500:
            st.error("⚠️ 本工具目前仅支持 500mm 以内的尺寸。")
        elif tolerance_grade < 5 or tolerance_grade > 13:
            st.error("⚠️ 本工具仅支持 IT5 - IT13 等级。")
        else:
            # 1. 获取标准公差数值 (IT)
            it_val_microns = get_it_value(nominal_size, tolerance_grade)
            it_val_mm = it_val_microns / 1000.0
            
            # 2. 获取基础偏差
            # 逻辑：
            # 孔 (大写 H): 下偏差 EI = 0 (对于 H), 上偏差 ES = EI + IT
            # 轴 (小写 h): 上偏差 es = 0 (对于 h), 下偏差 ei = es - IT
            # 轴 (小写 g): 上偏差 es = 负值, 下偏差 ei = es - IT
            
            is_hole = dev_char.isupper()
            fund_dev_microns = get_fundamental_deviation(nominal_size, dev_char)
            fund_dev_mm = fund_dev_microns / 1000.0
            
            upper_limit = 0.0
            lower_limit = 0.0
            desc = ""
            
            # --- 计算核心 ---
            if is_hole:
                # 孔逻辑 (简化版，以H为例)
                # 对于H: EI (下偏差) = 基础偏差 = 0
                if dev_char == 'H':
                    lower_dev = 0.0
                    upper_dev = it_val_mm
                else:
                    # 对于非H孔，逻辑较复杂，这里做近似处理或提示
                    # 通用公式：孔的偏差通常与轴互为镜像（但不完全是）
                    lower_dev = fund_dev_mm # 假设返回的是EI
                    upper_dev = lower_dev + it_val_mm
                
                max_size = nominal_size + upper_dev
                min_size = nominal_size + lower_dev
                desc = "孔 (Hole)"
                
                val_display_upper = f"+{upper_dev*1000:.0f} μm"
                val_display_lower = f"{lower_dev*1000:.0f} μm"
                if lower_dev == 0: val_display_lower = "0"
                
            else:
                # 轴逻辑
                # 对于 h: es (上偏差) = 0
                # 对于 g: es (上偏差) = 负值
                upper_dev = fund_dev_mm
                lower_dev = upper_dev - it_val_mm
                
                max_size = nominal_size + upper_dev
                min_size = nominal_size + lower_dev
                desc = "轴 (Shaft)"
                
                val_display_upper = f"{upper_dev*1000:.0f} μm"
                if upper_dev == 0: val_display_upper = "0"
                val_display_lower = f"{lower_dev*1000:.0f} μm"

            # --- 4. 结果显示 ---
            st.divider()
            
            # 大字显示结果范围
            st.subheader(f"结果: {min_size:.3f} mm ~ {max_size:.3f} mm")
            
            c1, c2, c3 = st.columns(3)
            with c1:
                st.info(f"**类型**: {desc}")
            with c2:
                st.info(f"**上偏差**: {val_display_upper}")
            with c3:
                st.info(f"**下偏差**: {val_display_lower}")
                
            st.success(f"**公差带宽度 (IT{tolerance_grade})**: {it_val_microns} μm")
            
            # 图示化公差带
            st.write("---")
            st.caption("📊 公差带示意图")
            
            # 用进度条模拟一个简单的相对位置
            bar_range = it_val_mm * 4 # 设定显示范围为公差的4倍
            mid_point = nominal_size
            
            # 归一化位置以便在图表中显示 (Streamlit原生不支持画精密机械图，这里用文字辅助)
            st.text(f"最大极限: {max_size:.3f} mm")
            st.progress(0.8) # 示意条
            st.text(f"公称尺寸: {nominal_size:.0f}.000 mm")
            st.progress(0.5) # 示意条
            st.text(f"最小极限: {min_size:.3f} mm")
            st.progress(0.2) # 示意条

    else:
        st.warning("格式不正确，请使用类似 '15H7' 或 '20g6' 的格式。")

st.markdown("---")
st.caption("注：本工具数据基于 ISO 286-1 常用段简化，仅供快速参考。精密加工请查阅完整标准。")