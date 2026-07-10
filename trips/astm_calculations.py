import math

# ثوابت ASTM D1250 - جدول 54B للمنتجات المكررة
# النظام يتعامل مع البنزين فقط، لذا نُبقي على البنزين فقط ('petrol' = 'gasoline')
CONSTANTS = {
    'gasoline': {'k0': 346.4228, 'k1': 0.4388},
    'petrol':   {'k0': 346.4228, 'k1': 0.4388},   # alias لأن النظام يستخدم 'petrol'
}

# نطاق الكثافة الصالح للبنزين وفق جدول 54B (kg/m3)
GASOLINE_DENSITY_MIN = 653.0
GASOLINE_DENSITY_MAX = 770.0


def _normalize_density(density_15c: float) -> float:
    """
    توحيد وحدة الكثافة إلى kg/m3.
    النظام يُخزّن الكثافة ككثافة نسبية (Specific Gravity) مثل 0.7400،
    بينما معادلة ASTM تتطلبها بوحدة kg/m3 مثل 740. هذه الدالة تُحوّل تلقائياً.
    """
    if density_15c <= 0:
        raise ValueError("الكثافة يجب أن تكون قيمة موجبة أكبر من صفر.")
    # أي قيمة أقل من 10 تُعتبر كثافة نسبية (0.74) فتُحوّل إلى kg/m3 (740)
    if density_15c < 10:
        density_15c = density_15c * 1000.0
    return density_15c


def calculate_astm_vcf(product_type: str, observed_temp: float, density_15c: float) -> float:
    """
    حساب معامل تصحيح الحجم (VCF) وفق معيار ASTM D1250 (جدول 54B - البنزين).
    :param product_type: نوع الوقود ('petrol' أو 'gasoline')
    :param observed_temp: درجة الحرارة المقاسة ميدانياً بالدرجة المئوية (C)
    :param density_15c: الكثافة عند 15°C - تُقبل نسبية (0.74) أو kg/m3 (740)
    :return: معامل تصحيح الحجم (VCF) كقيمة عشرية
    """
    product = (product_type or '').lower()
    if product not in CONSTANTS:
        raise ValueError("نوع المنتج غير مدعوم. النظام يعمل بالبنزين فقط ('petrol').")

    # توحيد وحدة الكثافة إلى kg/m3
    density = _normalize_density(float(density_15c))

    # التحقق من وقوع الكثافة ضمن النطاق العلمي الصالح لجدول 54B للبنزين
    if not (GASOLINE_DENSITY_MIN <= density <= GASOLINE_DENSITY_MAX):
        raise ValueError(
            f"الكثافة {density:.1f} kg/m3 خارج النطاق الصالح للبنزين "
            f"({GASOLINE_DENSITY_MIN}-{GASOLINE_DENSITY_MAX}). تحقّق من صحة الإدخال."
        )

    k0 = CONSTANTS[product]['k0']
    k1 = CONSTANTS[product]['k1']

    # 1. معامل التمدد الحراري عند 15°C
    alpha_15 = (k0 / (density ** 2)) + (k1 / density)

    # 2. الفارق الحراري عن الدرجة القياسية 15°C
    delta_t = float(observed_temp) - 15.0

    # 3. معامل تصحيح الحجم VCF (Volume Correction Factor)
    vcf = math.exp(-alpha_15 * delta_t * (1.0 + 0.8 * alpha_15 * delta_t))

    return round(vcf, 5)


def compute_standard_volume(product_type: str, observed_volume: float,
                            observed_temp: float, density_15c: float) -> float:
    """
    حساب الحجم القياسي الفعلي للوقود عند 15°C.
    :return: الحجم القياسي (لتر) عند 15 درجة مئوية
    """
    observed_volume = float(observed_volume)
    if observed_volume < 0:
        raise ValueError("الحجم الظاهري لا يمكن أن يكون سالباً.")

    vcf = calculate_astm_vcf(product_type, observed_temp, density_15c)
    standard_volume = observed_volume * vcf
    return round(standard_volume, 2)