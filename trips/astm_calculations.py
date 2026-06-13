import math

def calculate_astm_vcf(product_type: str, observed_temp: float, density_15c: float) -> float:
    """
    حساب معامل تصحيح الحجم (VCF) بناءً على معيار ASTM D1250 (المنتجات المكررة - جدول 54B)
    :param product_type: نوع الوقود ('gasoline' أو 'diesel')
    :param observed_temp: درجة الحرارة المقاسة ميدانياً بالدرجة المئوية (C)
    :param density_15c: الكثافة القياسية للمنتج عند 15 درجة مئوية (kg/m3)
    :return: معامل تصحيح الحجم (VCF) كقيمة عشرية
    """
    # الثوابت الفيزيائية القياسية لمعيار ASTM D1250 لمنتجات الوقود المكررة
    CONSTANTS = {
        'gasoline': {'k0': 346.4228, 'k1': 0.4388},  # البنزين (كثافة بين 610 و 770)
        'diesel': {'k0': 186.9696, 'k1': 0.48618}   # الديزل/النافطة (كثافة بين 788 و 1075)
    }
    
    product = product_type.lower()
    if product not in CONSTANTS:
        raise ValueError("نوع المنتج غير مدعوم. اختر 'gasoline' أو 'diesel'.")
        
    k0 = CONSTANTS[product]['k0']
    k1 = CONSTANTS[product]['k1']
    
    # 1. حساب معامل التمدد الحراري عند 15 درجة مئوية
    alpha_15 = (k0 / (density_15c ** 2)) + (k1 / density_15c)
    
    # 2. حساب الفارق الحراري عن الدرجة القياسية 15
    delta_t = observed_temp - 15.0
    
    # 3. حساب معامل VCF (Volume Correction Factor)
    vcf = math.exp(-alpha_15 * delta_t * (1.0 + 0.8 * alpha_15 * delta_t))
    
    return round(vcf, 5)


def compute_standard_volume(product_type: str, observed_volume: float, observed_temp: float, density_15c: float) -> float:
    """
    حساب الحجم القياسي الفعلي للوقود عند 15 درجة مئوية
    """
    vcf = calculate_astm_vcf(product_type, observed_temp, density_15c)
    standard_volume = observed_volume * vcf
    return round(standard_volume, 2)