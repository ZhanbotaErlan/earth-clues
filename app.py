# -*- coding: utf-8 -*-
# Complete app: save as app.py beside the data folder.
import csv
import tempfile
import zipfile
from pathlib import Path
import pandas as pd
import streamlit as st

LANGUAGES = {'English': 'en', 'Русский': 'ru', '中文': 'zh'}

TEXT = {'en': {'title': 'Be an Earth System Trend Detective',
        'subtitle': 'Explore Earth system trends across continents.',
        'region': 'Choose a region',
        'country': 'Choose a country',
        'analyze': 'Analyze',
        'missing': 'No usable values are available for this variable and country.',
        'data_error': 'The data folder was not found.',
        'no_regions': 'No region folders were found in the data folder.',
        'no_countries': 'No country folders were found for this region.',
        'about': 'About this variable',
        'source': 'Data source'},
 'ru': {'title': 'Станьте исследователем тенденций системы Земли',
        'subtitle': 'Изучайте изменения системы Земли на разных континентах.',
        'region': 'Выберите регион',
        'country': 'Выберите страну',
        'analyze': 'Анализировать',
        'missing': 'Для этой переменной и страны нет пригодных данных.',
        'data_error': 'Папка с данными не найдена.',
        'no_regions': 'В папке данных не найдены папки регионов.',
        'no_countries': 'Для этого региона не найдены папки стран.',
        'about': 'О переменной',
        'source': 'Источник данных'},
 'zh': {'title': '成为地球系统趋势侦探',
        'subtitle': '探索不同大洲的地球系统变化。',
        'region': '选择地区',
        'country': '选择国家',
        'analyze': '开始分析',
        'missing': '这个国家的该变量没有可用数值。',
        'data_error': '没有找到数据文件夹。',
        'no_regions': '数据文件夹中没有找到地区文件夹。',
        'no_countries': '这个地区文件夹中没有找到国家文件夹。',
        'about': '变量说明',
        'source': '数据来源'}}

METRICS = {'T2M': ('Atmosphere & precipitation', '°C', '2 米气温', '2 m air temperature', 'Температура на высоте 2 м'),
 'QV2M': ('Atmosphere & precipitation',
          'g/kg',
          '2 米比湿',
          '2 m specific humidity',
          'Удельная влажность на высоте 2 м'),
 'PRECTOTCORR': ('Atmosphere & precipitation',
                 'mm/month',
                 '订正降水',
                 'Bias-corrected precipitation',
                 'Скорректированные осадки'),
 'PS': ('Atmosphere & precipitation',
        'CSV unit; verify',
        '地表气压',
        'Surface pressure',
        'Давление у поверхности'),
 'TQV': ('Atmosphere & precipitation',
         'kg/m²',
         '整层可降水量',
         'Total precipitable water',
         'Общее содержание водяного пара'),
 'RootMoist_inst': ('Soil moisture', 'kg/m²', '根区土壤储水量', 'Root-zone soil moisture', 'Влага в корневой зоне'),
 'SoilMoi0_10cm_inst': ('Soil moisture',
                        'kg/m²',
                        '0–10 cm 土壤水分',
                        'Soil moisture, 0–10 cm',
                        'Влага почвы, 0–10 см'),
 'SoilMoi10_40cm_inst': ('Soil moisture',
                         'kg/m²',
                         '10–40 cm 土壤水分',
                         'Soil moisture, 10–40 cm',
                         'Влага почвы, 10–40 см'),
 'SoilMoi40_100cm_inst': ('Soil moisture',
                          'kg/m²',
                          '40–100 cm 土壤水分',
                          'Soil moisture, 40–100 cm',
                          'Влага почвы, 40–100 см'),
 'SoilMoi100_200cm_inst': ('Soil moisture',
                           'kg/m²',
                           '100–200 cm 土壤水分',
                           'Soil moisture, 100–200 cm',
                           'Влага почвы, 100–200 см'),
 'Evap_tavg': ('Snow & water movement', 'mm/month', '蒸散发', 'Evapotranspiration', 'Эвапотранспирация'),
 'Qs_acc': ('Snow & water movement', 'mm/month', '地表径流', 'Storm surface runoff', 'Поверхностный сток'),
 'Qsb_acc': ('Snow & water movement', 'mm/month', '地下径流', 'Baseflow runoff', 'Подземный сток'),
 'Qsm_acc': ('Snow & water movement', 'mm/month', '融雪', 'Snowmelt', 'Таяние снега'),
 'SWE_inst': ('Snow & water movement',
              'kg/m²',
              '雪水当量',
              'Snow water equivalent',
              'Снегозапас в водном эквиваленте'),
 'Qle_tavg': ('Energy exchange', 'W/m²', '潜热净通量', 'Latent heat flux', 'Поток скрытого тепла'),
 'Qh_tavg': ('Energy exchange', 'W/m²', '感热净通量', 'Sensible heat flux', 'Поток явного тепла')}

EXPLANATIONS = {'T2M': {'zh': '近地面约 2 米高度的空气温度。',
         'en': 'Air temperature about 2 meters above the surface.',
         'ru': 'Температура воздуха примерно на высоте 2 метров над поверхностью.'},
 'QV2M': {'zh': '近地面空气中水汽相对于空气质量的比例。',
          'en': 'The mass of water vapor in near-surface air relative to the mass of air.',
          'ru': 'Массовая доля водяного пара в воздухе у поверхности.'},
 'PRECTOTCORR': {'zh': '经过偏差订正的地表总降水量。',
                 'en': 'Bias-corrected total precipitation reaching the surface.',
                 'ru': 'Общее количество осадков у поверхности с коррекцией смещения.'},
 'PS': {'zh': '地表上方大气的压力；原文件单位需要核实。',
        'en': 'Atmospheric pressure at the surface; the source unit needs verification.',
        'ru': 'Давление атмосферы у поверхности; единицу исходных данных нужно проверить.'},
 'TQV': {'zh': '整层大气中的水汽全部凝结后可形成的水层量。',
         'en': 'The depth of water that would result if all atmospheric water vapor condensed.',
         'ru': 'Слой воды, который образовался бы при конденсации всего водяного пара.'},
 'RootMoist_inst': {'zh': '模型估算的植物根系范围内土壤储水量。',
                    'en': 'Model-estimated water stored in the soil within the root zone.',
                    'ru': 'Расчётный запас воды в почве в пределах корневой зоны.'},
 'SoilMoi0_10cm_inst': {'zh': '表层 0–10 厘米土壤中的储水量。',
                        'en': 'Water stored in the top 0–10 cm of soil.',
                        'ru': 'Запас воды в верхнем слое почвы 0–10 см.'},
 'SoilMoi10_40cm_inst': {'zh': '10–40 厘米土层中的储水量。',
                         'en': 'Water stored in the 10–40 cm soil layer.',
                         'ru': 'Запас воды в слое почвы 10–40 см.'},
 'SoilMoi40_100cm_inst': {'zh': '40–100 厘米土层中的储水量。',
                          'en': 'Water stored in the 40–100 cm soil layer.',
                          'ru': 'Запас воды в слое почвы 40–100 см.'},
 'SoilMoi100_200cm_inst': {'zh': '100–200 厘米土层中的储水量。',
                           'en': 'Water stored in the 100–200 cm soil layer.',
                           'ru': 'Запас воды в слое почвы 100–200 см.'},
 'Evap_tavg': {'zh': '通过地表蒸发和植物蒸腾进入大气的水分。',
               'en': 'Water transferred to the atmosphere through evaporation and plant transpiration.',
               'ru': 'Вода, поступающая в атмосферу через испарение и транспирацию растений.'},
 'Qs_acc': {'zh': '模型估算的地表径流，不是河道实测流量。',
            'en': 'Model-estimated surface runoff; it is not measured river discharge.',
            'ru': 'Расчётный поверхностный сток модели; это не измеренный расход воды в реке.'},
 'Qsb_acc': {'zh': '模型估算的地下排水过程，不是地下水总储量。',
             'en': 'Model-estimated subsurface runoff; it is not total groundwater storage.',
             'ru': 'Расчётный подземный сток модели; это не общий запас подземных вод.'},
 'Qsm_acc': {'zh': '模型估算的融雪水量。',
             'en': 'Model-estimated water released by snowmelt.',
             'ru': 'Расчётное количество воды, образовавшейся при таянии снега.'},
 'SWE_inst': {'zh': '积雪完全融化后相当的水量，不是积雪物理厚度。',
              'en': 'The water equivalent of snow; it is not the physical depth of the snowpack.',
              'ru': 'Водный эквивалент снега; это не физическая высота снежного покрова.'},
 'Qle_tavg': {'zh': '与蒸发和水汽交换有关的地表能量通量。',
              'en': 'Surface energy flux associated with evaporation and water-vapor exchange.',
              'ru': 'Поток энергии у поверхности, связанный с испарением и обменом водяным паром.'},
 'Qh_tavg': {'zh': '地表与近地面空气之间的热量交换。',
             'en': 'Heat exchanged between the surface and the air above it.',
             'ru': 'Теплообмен между поверхностью и воздухом над ней.'}}

GROUP_NAMES = {'en': {'Atmosphere & precipitation': 'Atmosphere & precipitation',
        'Soil moisture': 'Soil moisture',
        'Snow & water movement': 'Snow & water movement',
        'Energy exchange': 'Energy exchange'},
 'ru': {'Atmosphere & precipitation': 'Атмосфера и осадки',
        'Soil moisture': 'Влажность почвы',
        'Snow & water movement': 'Снег и движение воды',
        'Energy exchange': 'Энергообмен'},
 'zh': {'Atmosphere & precipitation': '大气与降水',
        'Soil moisture': '土壤水分',
        'Snow & water movement': '积雪与水流',
        'Energy exchange': '能量交换'}}

NAME_INDEX = {'zh': 2, 'en': 3, 'ru': 4}

GROUP_ORDER = ['Atmosphere & precipitation', 'Soil moisture', 'Snow & water movement', 'Energy exchange']

# This body is assembled with the existing metric definitions into one app.py.
import io
import numpy as np
import altair as alt
from urllib.parse import urlsplit, parse_qs

LANG_INDEX = {"en": 0, "ru": 1, "zh": 2}
UI = {
    "overview": ("Country findings", "Результаты по стране", "国家分析结果"),
    "robustness": ("Does the time window change the conclusion?", "Влияет ли период на вывод?", "换个时间范围，结论还一样吗？"),
    "methods": ("Data & methods", "Данные и методы", "数据与方法"),
    "start": ("Choose a country and press Analyze.", "Выберите страну и нажмите «Анализировать».", "选择国家，然后点击开始分析。"),
    "loading": ("Calculating annual results…", "Расчёт годовых результатов…", "正在计算年度结果……"),
    "mean": ("Average annual value", "Среднее годовое значение", "多年平均年值"),
    "mean_total": ("Average annual total", "Средняя годовая сумма", "平均年累计量"),
    "highest": ("Highest annual value", "Максимум за год", "最高年值"),
    "lowest": ("Lowest annual value", "Минимум за год", "最低年值"),
    "change": ("First-to-last change", "Изменение от первого к последнему году", "首尾年份变化"),
    "slope": ("Fitted change per year", "Наклон тренда за год", "拟合变化速率"),
    "years": ("{start}–{end}: {n} complete years", "{start}–{end}: {n} полных лет", "{start}—{end}：{n} 个完整年份"),
    "count": ("{available} of {total} variables have complete-year results", "Годовые результаты: {available} из {total} переменных", "{total} 个变量中，{available} 个具有完整年度结果"),
    "excluded": ("Incomplete years excluded from annual statistics: {years}.", "Неполные годы исключены из годовой статистики: {years}.", "年度统计排除不完整年份：{years}。"),
    "no_years": ("No complete year is available; monthly records remain available below.", "Нет полного года; месячные записи доступны ниже.", "没有完整年份，仍可在下方查看已有月度记录。"),
    "missing": ("No usable values in this source. Missing data are not zero.", "В источнике нет пригодных значений. Пропуски не равны нулю.", "源数据没有可用数值；缺失不代表零。"),
    "maldives": ("GLDAS coverage limitation noted for the Maldives; the official explanation link still needs to be attached.", "Для Мальдив отмечено ограничение покрытия GLDAS; ссылку на официальное пояснение ещё нужно добавить.", "马尔代夫此项已知存在 GLDAS 覆盖限制，官方说明链接待补充。"),
    "definition": ("What does this measure?", "Что измеряет показатель?", "这个变量测量什么？"),
    "evidence": ("Open charts, annual values and source", "Графики, годовые значения и источник", "展开图表、逐年数据和来源"),
    "annual": ("Annual values", "Годовые значения", "逐年数据"),
    "monthly": ("Monthly records", "Месячные записи", "月度记录"),
    "seasonal": ("Average seasonal cycle", "Средний сезонный цикл", "多年平均季节规律"),
    "year": ("Year", "Год", "年份"),
    "date": ("Date", "Дата", "日期"),
    "month": ("Month", "Месяц", "月份"),
    "value": ("Value", "Значение", "数值"),
    "fit": ("Linear fit", "Линейная аппроксимация", "线性拟合"),
    "actual": ("Annual value", "Годовое значение", "实际年值"),
    "series": ("Series", "Ряд", "数据系列"),
    "per_year": ("{unit}/year", "{unit}/год", "{unit}/年"),
    "raw_unit": ("CSV value (unit unverified)", "Значение CSV (единица не подтверждена)", "CSV 原值（单位待核实）"),
    "month_unit": ("mm/month", "мм/месяц", "mm/月"),
    "narrative": (
        "Over {start}–{end}, the annual indicator changed from **{first} {unit}** to **{last} {unit}**. The endpoint difference is **{delta} {unit}**{percent}. This is an endpoint comparison, not the fitted trend rate.",
        "За {start}–{end} годовой показатель изменился с **{first} {unit}** до **{last} {unit}**. Разность конечного и начального значений: **{delta} {unit}**{percent}. Это сравнение крайних лет, а не наклон тренда.",
        "{start}—{end} 年，该年度指标从 **{first} {unit}** 变为 **{last} {unit}**，首尾差为 **{delta} {unit}**{percent}。首尾变化与利用全部年度值拟合的趋势速率是两项不同结果。"),
    "fit_note": (
        "The fitted slope is **{slope} {rate_unit}**; R² = **{r2}**. This describes the selected record. Trend significance has not been tested.",
        "Наклон линейной аппроксимации: **{slope} {rate_unit}**; R² = **{r2}**. Это описание выбранного ряда. Статистическая значимость тренда не проверена.",
        "线性拟合速率为 **{slope} {rate_unit}**，R² 为 **{r2}**。这是所选记录的描述性结果，尚未进行趋势显著性检验。"),
    "constant": ("The annual values are constant in this record; R² is undefined.", "Годовые значения постоянны; R² не определён.", "此记录中的年度值恒定，R² 不适用。"),
    "seasons": ("The seasonal average peaks in **{peak}** and is lowest in **{trough}**. This is a seasonal pattern, not evidence of a shifting season.", "Сезонное среднее максимально в **{peak}**, минимально в **{trough}**. Это сезонный цикл, а не доказательство сдвига сезона.", "多年平均季节值在 **{peak}** 最高、**{trough}** 最低。这是季节规律，不代表季节时间正在发生长期变化。"),
    "summary": ("{name}: {start} **{first} {unit}** → {end} **{last} {unit}**; highest in {high_years}, lowest in {low_years}.", "{name}: {start} **{first} {unit}** → {end} **{last} {unit}**; максимум — {high_years}, минимум — {low_years}.", "{name}：{start} 年 **{first} {unit}** → {end} 年 **{last} {unit}**；最高年份为 {high_years}，最低年份为 {low_years}。"),
    "headline": ("What changed?", "Что изменилось?", "整体发生了什么变化？"),
    "all_metrics": ("All 17 variables: results before charts", "Все 17 переменных: сначала результаты", "全部 17 个变量：先看结果，再查看图表"),
    "no_tests": ("Descriptive analysis. Statistical significance is not yet tested; R² is not a confidence probability. Results are country-area averages.", "Описательный анализ. Значимость ещё не проверена; R² не является вероятностью достоверности. Данные усреднены по территории страны.", "当前为描述性分析，尚未检验统计显著性；R² 不是结论可信概率。结果基于国家面积平均数据。"),
    "robust_intro": ("Keep the full record as the baseline. Change the starting year and compare all variables over the same ending year. A change of direction indicates sensitivity, not a forecast.", "Полный ряд — базовый период. Меняйте начальный год и сравнивайте все переменные при одинаковом конечном годе. Смена направления означает чувствительность к периоду, а не прогноз.", "保留完整记录作为基准，调整起始年份，比较相同结束年份下所有变量的结果。方向变化提示时间范围敏感，不是未来预测。"),
    "start_year": ("Exploratory starting year", "Начальный год для сравнения", "探索性比较的起始年份"),
    "baseline": ("Baseline", "Базовый период", "完整时段基准"),
    "alternative": ("Selected window", "Выбранный период", "所选时段"),
    "same_direction": ("Same fitted direction", "То же направление", "拟合方向相同"),
    "changed_direction": ("Fitted direction changed", "Направление изменилось", "拟合方向改变"),
    "insufficient": ("Fewer than 3 complete years", "Менее 3 полных лет", "不足 3 个完整年份"),
    "comparison_note": ("Matching signs do not establish significance or robustness. Shorter periods have fewer observations; do not select a window solely to obtain a preferred result.", "Совпадение знаков не доказывает значимость или устойчивость. В коротких периодах меньше наблюдений; не выбирайте период ради желаемого результата.", "方向相同不等于已经证明显著或稳健。短时段样本更少，不能只挑选符合预期结论的时间窗。"),
    "variable": ("Variable", "Переменная", "变量"),
    "n": ("Complete years", "Полные годы", "完整年份数"),
    "result": ("Comparison", "Сравнение", "比较结果"),
    "unit": ("Unit", "Единица", "单位"),
    "export": ("Save the findings", "Сохранить результаты", "保存分析发现"),
    "download": ("Download all statistics (CSV)", "Скачать статистику (CSV)", "下载全部统计数据（CSV）"),
    "report": ("Download findings (Markdown)", "Скачать выводы (Markdown)", "下载分析说明（Markdown）"),
    "source": ("NASA Giovanni reproduction link", "Ссылка NASA Giovanni для воспроизведения", "NASA Giovanni 结果重现链接"),
    "no_link": ("No reproduction link in this CSV.", "В CSV нет ссылки для воспроизведения.", "CSV 中没有重现链接。"),
    "read_error": ("Some files could not be read. Open the details below.", "Некоторые файлы не прочитаны. Подробности ниже.", "部分文件无法读取，请展开查看具体文件。"),
    "read_details": ("File-reading details", "Подробности чтения файлов", "文件读取详情"),
    "duplicate": ("Duplicate variable files; no automatic selection was made.", "Файлы переменной дублируются; автоматический выбор не выполнен.", "发现同一变量的多个文件，未自动选择其中一份。"),
    "state_aggregation": ("Annual values are month-length-weighted means; the multi-year value averages complete annual values.", "Годовые значения — средние с весами по числу дней в месяце; многолетнее значение — среднее полных годовых значений.", "年值按每月天数加权平均；多年值为完整年度年值的平均。"),
    "total_aggregation": ("Annual values sum converted monthly totals; the multi-year value is the average annual total.", "Годовые значения — суммы пересчитанных месячных итогов; многолетнее значение — средняя годовая сумма.", "年值为换算后月累计量的总和；多年值为平均年累计量。"),
    "method_body": (
        "A year is included only when all 12 distinct months have valid values. Fill values and non-finite values are missing, not zero. Air temperature: K − 273.15; specific humidity: kg/kg × 1000. Precipitation and evapotranspiration rates are multiplied by days × 86400; Qs/Qsb/Qsm monthly mean 3-hour accumulations by days × 8. Soil moisture and SWE are storage per area. Pressure stays in CSV units pending verification. Linear slopes use all complete annual values. These data cannot resolve city-scale conditions, flood peaks, groundwater storage or causal effects. MERRA-2 and GLDAS are different systems; their water-budget terms cannot be assumed to close together.",
        "Год включается только при наличии 12 разных месяцев с пригодными значениями. Заполнители и бесконечности считаются пропусками, не нулями. Температура: K − 273,15; удельная влажность: кг/кг × 1000. Интенсивности осадков и эвапотранспирации умножаются на дни × 86400; средние трёхчасовые накопления Qs/Qsb/Qsm — на дни × 8. Влажность почвы и SWE — запасы на единицу площади. Давление остаётся в единицах CSV до проверки. Наклоны рассчитаны по всем полным годам. Данные не описывают условия в городах, пики паводков, запасы подземных вод или причинные эффекты. MERRA-2 и GLDAS — разные системы; их водный баланс нельзя считать совместно замкнутым.",
        "只有 12 个不同月份都有有效值的年份才纳入年度统计。填充值与非有限数值作为缺失，不填零。气温由 K 减去 273.15，比湿由 kg/kg 乘 1000；降水和蒸散发速率乘当月天数与 86400；Qs/Qsb/Qsm 的月平均三小时累计值乘天数与 8。土壤水分及雪水当量表示单位面积储水；气压保留 CSV 原值，单位待核实。线性斜率使用全部完整年值。国家月平均数据不能识别城市状况、洪峰、地下水总储量或因果效应。MERRA-2 与 GLDAS 来自不同系统，不能直接假定跨产品水量平衡闭合。"),
}
REGION_LABELS = {
    "Central Asia": ("Central Asia", "Центральная Азия", "中亚"),
    "South Asia": ("South Asia", "Южная Азия", "南亚"),
    "East Asia": ("East Asia", "Восточная Азия", "东亚"),
    "Southeast Asia": ("Southeast Asia", "Юго-Восточная Азия", "东南亚"),
    "West Asia": ("West Asia", "Западная Азия", "西亚"),
    "Europe": ("Europe", "Европа", "欧洲"),
}
COUNTRY_LABELS = {
    "Kazakhstan": ("Kazakhstan", "Казахстан", "哈萨克斯坦"),
    "Kyrgyzstan": ("Kyrgyzstan", "Кыргызстан", "吉尔吉斯斯坦"),
    "Tajikistan": ("Tajikistan", "Таджикистан", "塔吉克斯坦"),
    "Turkmenistan": ("Turkmenistan", "Туркменистан", "土库曼斯坦"),
    "Uzbekistan": ("Uzbekistan", "Узбекистан", "乌兹别克斯坦"),
    "Afghanistan": ("Afghanistan", "Афганистан", "阿富汗"),
    "Bangladesh": ("Bangladesh", "Бангладеш", "孟加拉国"),
    "Bhutan": ("Bhutan", "Бутан", "不丹"),
    "India": ("India", "Индия", "印度"),
    "Iran": ("Iran", "Иран", "伊朗"),
    "Lanka": ("Sri Lanka", "Шри-Ланка", "斯里兰卡"),
    "Maldives": ("Maldives", "Мальдивы", "马尔代夫"),
    "Nepal": ("Nepal", "Непал", "尼泊尔"),
    "Pakistan": ("Pakistan", "Пакистан", "巴基斯坦"),
    "Brunei": ("Brunei", "Бруней", "文莱"),
    "Burma": ("Myanmar", "Мьянма", "缅甸"),
    "Cambodia": ("Cambodia", "Камбоджа", "柬埔寨"),
    "Indonesia": ("Indonesia", "Индонезия", "印度尼西亚"),
    "Laos": ("Laos", "Лаос", "老挝"),
    "Malaysia": ("Malaysia", "Малайзия", "马来西亚"),
    "Philippines": ("Philippines", "Филиппины", "菲律宾"),
    "Singapore": ("Singapore", "Сингапур", "新加坡"),
    "Thailand": ("Thailand", "Таиланд", "泰国"),
    "Timor-Leste": ("Timor-Leste", "Восточный Тимор", "东帝汶"),
    "Vietnam": ("Vietnam", "Вьетнам", "越南"),
    "China": ("China", "Китай", "中国"),
    "Mongolia": ("Mongolia", "Монголия", "蒙古国"),
    "North Korea": ("North Korea", "КНДР", "朝鲜"),
    "South Korea": ("South Korea", "Республика Корея", "韩国"),
    "Armenia": ("Armenia", "Армения", "亚美尼亚"),
    "Azerbaijan": ("Azerbaijan", "Азербайджан", "阿塞拜疆"),
    "Bahrain": ("Bahrain", "Бахрейн", "巴林"),
    "Cyprus": ("Cyprus", "Кипр", "塞浦路斯"),
    "Georgia": ("Georgia", "Грузия", "格鲁吉亚"),
    "Iraq": ("Iraq", "Ирак", "伊拉克"),
    "Israel": ("Israel", "Израиль", "以色列"),
    "Jordan": ("Jordan", "Иордания", "约旦"),
    "Kuwait": ("Kuwait", "Кувейт", "科威特"),
    "Lebanon": ("Lebanon", "Ливан", "黎巴嫩"),
    "Oman": ("Oman", "Оман", "阿曼"),
    "Qatar": ("Qatar", "Катар", "卡塔尔"),
    "Saudi Arabia": ("Saudi Arabia", "Саудовская Аравия", "沙特阿拉伯"),
    "Shape Yemen": ("Yemen", "Йемен", "也门"),
    "Yemen": ("Yemen", "Йемен", "也门"),
    "Syria": ("Syria", "Сирия", "叙利亚"),
    "Turkey": ("Türkiye", "Турция", "土耳其"),
    "United Arab Emirates": ("United Arab Emirates", "ОАЭ", "阿联酋"),
    "West Bank": ("West Bank", "Западный берег", "约旦河西岸"),
}
MONTHS = {
    "en": ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"],
    "ru": ["январь", "февраль", "март", "апрель", "май", "июнь", "июль", "август", "сентябрь", "октябрь", "ноябрь", "декабрь"],
    "zh": [f"{i} 月" for i in range(1, 13)],
}
TOTALS = {"PRECTOTCORR", "Evap_tavg", "Qs_acc", "Qsb_acc", "Qsm_acc"}
RATIO_SAFE = set(METRICS) - {"T2M", "PS", "Qh_tavg", "Qle_tavg"}


def tr(key, lang, **kwargs):
    return UI[key][LANG_INDEX[lang]].format(**kwargs)


def label(value, table, lang):
    return table[value][LANG_INDEX[lang]] if value in table else value


def name(code, lang):
    return METRICS[code][NAME_INDEX[lang]]


def unit(code, lang, monthly=False):
    if code == "PS":
        return tr("raw_unit", lang)
    if code in TOTALS:
        return tr("month_unit", lang) if monthly else "mm"
    return METRICS[code][1]


def fmt(value, signed=False):
    if value is None or not np.isfinite(value):
        return "—"
    if value != 0 and abs(value) < 0.01:
        return format(value, "+.3g" if signed else ".3g")
    return format(value, "+,.2f" if signed else ",.2f")


def read_source(path):
    with Path(path).open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.reader(handle))
    header = next(i for i, r in enumerate(rows) if r and r[0].strip() == "time")
    column = rows[header][1].strip()
    code = next((v for v in METRICS if column.endswith("_" + v)), None)
    if code is None:
        raise ValueError("Unrecognized variable: " + column)
    fill = None
    source = None
    for r in rows[:header]:
        if len(r) < 2:
            continue
        if r[0].startswith("Fill Value"):
            fill = float(r[1])
        if r[0].strip() == "URL to Reproduce Results:":
            source = r[1]
    data = [r[:2] for r in rows[header + 1:] if len(r) >= 2]
    df = pd.DataFrame(data, columns=["date", "value"])
    df["date"] = pd.to_datetime(df["date"], errors="raise").dt.to_period("M").dt.to_timestamp()
    if df["date"].duplicated().any():
        raise ValueError("Duplicate month")
    values = pd.to_numeric(df["value"], errors="coerce").astype(float)
    values = values.where(np.isfinite(values) & (values.abs() < 1e14))
    if fill is not None:
        values = values.mask(values == fill)
    series = pd.Series(values.to_numpy(), index=pd.DatetimeIndex(df["date"]), name="value").sort_index()
    if len(series):
        series = series.reindex(pd.date_range(series.index.min(), series.index.max(), freq="MS"))
    if code == "T2M":
        series = series - 273.15
    elif code == "QV2M":
        series = series * 1000
    elif code in {"PRECTOTCORR", "Evap_tavg"}:
        series = series * series.index.days_in_month * 86400
    elif code in {"Qs_acc", "Qsb_acc", "Qsm_acc"}:
        series = series * series.index.days_in_month * 8
    shape = parse_qs(urlsplit(source).fragment).get("shape", [None])[0] if source else None
    return code, {"series": series, "source": source, "shape": shape, "file": Path(path).name}


@st.cache_data(show_spinner=False)
def load_country(signature):
    result, errors, duplicates = {}, [], set()
    for path, modified, size in signature:
        try:
            code, record = read_source(path)
            if code in result or code in duplicates:
                duplicates.add(code)
                result.pop(code, None)
                errors.append((Path(path).name, "Duplicate variable: " + code))
            else:
                result[code] = record
        except Exception as exc:
            errors.append((Path(path).name, str(exc)))
    return result, errors


def annual_values(series, code):
    values = {}
    for year, part in series.groupby(series.index.year):
        good = part.dropna()
        if len(good) != 12 or set(good.index.month) != set(range(1, 13)):
            continue
        values[int(year)] = float(good.sum() if code in TOTALS else np.average(good, weights=good.index.days_in_month))
    return pd.Series(values, dtype=float).sort_index()


def summarize(annual):
    if annual.empty:
        return None
    x = annual.index.to_numpy(dtype=float)
    y = annual.to_numpy(dtype=float)
    slope, r2, prediction = None, None, None
    if len(y) >= 3:
        xc = x - x.mean()
        slope = float(np.dot(xc, y - y.mean()) / np.dot(xc, xc))
        prediction = y.mean() + slope * xc
        total = float(np.sum((y - y.mean()) ** 2))
        if total > 0:
            r2 = float(1 - np.sum((y - prediction) ** 2) / total)
    return {
        "start": int(x[0]), "end": int(x[-1]), "n": len(y), "mean": float(y.mean()),
        "first": float(y[0]), "last": float(y[-1]), "delta": float(y[-1] - y[0]),
        "high": float(y.max()), "low": float(y.min()),
        "high_years": ", ".join(str(int(v)) for v in annual.index[annual == annual.max()]),
        "low_years": ", ".join(str(int(v)) for v in annual.index[annual == annual.min()]),
        "slope": slope, "r2": r2, "prediction": prediction,
    }


def seasonal_values(series, code, complete_years):
    valid = series[series.index.year.isin(complete_years)].dropna()
    values = {}
    for month, part in valid.groupby(valid.index.month):
        values[int(month)] = float(part.mean() if code in TOTALS else np.average(part, weights=part.index.days_in_month))
    return pd.Series(values, dtype=float).sort_index()


def explanation(code, stats, lang):
    pct = ""
    if code in RATIO_SAFE and stats["first"] > 1e-9:
        pct = " (" + fmt(stats["delta"] / stats["first"] * 100, signed=True) + "%)"
    return tr("narrative", lang, start=stats["start"], end=stats["end"],
              first=fmt(stats["first"]), last=fmt(stats["last"]), delta=fmt(stats["delta"], True),
              unit=unit(code, lang), percent=pct)


def data_context(annual, code, lang):
    """Create a plain-language classification from the country's own record."""
    if len(annual) < 5:
        return tr("ref_not_enough", lang)
    values = annual.to_numpy(dtype=float)
    mean = float(np.mean(values))
    sd = float(np.std(values, ddof=1))
    last = float(values[-1])
    year = int(annual.index[-1])
    unit_text = unit(code, lang)
    if not np.isfinite(sd) or sd <= max(1e-12, abs(mean) * 1e-12):
        z = 0.0
    else:
        z = (last - mean) / sd
    category = ("far_above" if z >= 2 else "above" if z >= 1 else
                "far_below" if z <= -2 else "below" if z <= -1 else "typical")
    return (tr("ref_period", lang, start=int(annual.index[0]), end=int(annual.index[-1]), n=len(annual))
            + "\n\n" + tr("latest_assessment", lang, year=year, variable=name(code, lang),
                           value=fmt(last), difference=fmt(abs(last - mean)), mean=fmt(mean),
                           direction=tr("above_mean" if last > mean else "below_mean" if last < mean else "equal_mean", lang),
                           start=int(annual.index[0]), end=int(annual.index[-1]),
                           unit=unit_text, category=tr(category, lang))
            + "\n\n" + tr("threshold_explain", lang, start=int(annual.index[0]), end=int(annual.index[-1]),
                             typical_low=fmt(mean - sd), typical_high=fmt(mean + sd), unit=unit_text))


def draw_annual(annual, stats, code, lang):
    date_key, value_key, type_key = tr("year", lang), name(code, lang), tr("series", lang)
    data = pd.DataFrame({date_key: annual.index.astype(int), value_key: annual.to_numpy(), type_key: tr("actual", lang)})
    if stats["prediction"] is not None:
        fit = pd.DataFrame({date_key: annual.index.astype(int), value_key: stats["prediction"], type_key: tr("fit", lang)})
        data = pd.concat([data, fit], ignore_index=True)
    chart = alt.Chart(data).mark_line(point=True).encode(
        x=alt.X(date_key + ":O", title=date_key),
        y=alt.Y(value_key + ":Q", title=f"{value_key} ({unit(code, lang)})", scale=alt.Scale(zero=False)),
        color=alt.Color(type_key + ":N", title=type_key),
        strokeDash=alt.StrokeDash(type_key + ":N", legend=None),
        tooltip=[alt.Tooltip(date_key + ":O"), alt.Tooltip(value_key + ":Q", format=".3f"), alt.Tooltip(type_key + ":N")],
    ).properties(height=260)
    st.altair_chart(chart, use_container_width=True)


def render_metric(code, record, annual, stats, lang, country, role="resident"):
    with st.container(border=True, key=f"metric_{code}"):
        st.subheader(name(code, lang))
        st.caption(EXPLANATIONS[code][lang])
        st.caption(unit(code, lang))
        if record is None or record["series"].notna().sum() == 0:
            st.info(tr("missing", lang))
            if country == "Maldives" and code not in {"T2M", "QV2M", "PRECTOTCORR", "PS", "TQV"}:
                st.caption(tr("maldives", lang))
            return
        if stats is not None:
            st.caption(tr("years", lang, **{k: stats[k] for k in ("start", "end", "n")}))
            a, b = st.columns(2)
            a.metric(tr("mean_total" if code in TOTALS else "mean", lang), fmt(stats["mean"]))
            b.metric(tr("change", lang), fmt(stats["delta"], True))
            a, b = st.columns(2)
            a.metric(tr("highest", lang) + " · " + stats["high_years"], fmt(stats["high"]))
            b.metric(tr("lowest", lang) + " · " + stats["low_years"], fmt(stats["low"]))
            st.markdown(explanation(code, stats, lang))
            st.info(data_context(annual, code, lang))
            note = solution_text(code, country, stats, lang, role)
            if note:
                st.markdown("### " + UI["solution_title"][LANG_INDEX[lang]])
                st.markdown(note)
                source_text = " · ".join(f"[{title}]({url})" for title, url in report_links(country))
                st.caption(("参考报告：" if lang == "zh" else "Источники: " if lang == "ru" else "Evidence sources: ") + source_text)
            if stats["slope"] is not None:
                st.markdown(tr("fit_note", lang, slope=fmt(stats["slope"], True), rate_unit=tr("per_year", lang, unit=unit(code, lang)), r2=fmt(stats["r2"])))
                if stats["r2"] is None:
                    st.caption(tr("constant", lang))
            seasonal = seasonal_values(record["series"], code, annual.index)
            if len(seasonal) and seasonal.max() != seasonal.min():
                peak = ", ".join(MONTHS[lang][int(m)-1] for m in seasonal.index[seasonal == seasonal.max()])
                trough = ", ".join(MONTHS[lang][int(m)-1] for m in seasonal.index[seasonal == seasonal.min()])
                st.markdown(tr("seasons", lang, peak=peak, trough=trough))
        else:
            st.info(tr("no_years", lang))
        with st.expander(tr("evidence", lang)):
            if stats is not None:
                st.caption(tr("total_aggregation" if code in TOTALS else "state_aggregation", lang))
                draw_annual(annual, stats, code, lang)
                table = pd.DataFrame({tr("year", lang): annual.index.astype(int), f"{name(code, lang)} ({unit(code, lang)})": annual.to_numpy()})
                st.dataframe(table, hide_index=True, width="stretch")
                if len(seasonal):
                    st.caption(tr("seasonal", lang))
                    st.bar_chart(seasonal.rename(name(code, lang)), x_label=tr("month", lang), y_label=unit(code, lang, True))
            st.caption(tr("monthly", lang))
            st.line_chart(record["series"].rename(name(code, lang)), x_label=tr("date", lang), y_label=unit(code, lang, True))
            if record["source"]:
                st.markdown(f"[{tr('source', lang)}]({record['source']})")
            else:
                st.caption(tr("no_link", lang))


def render_robustness(annuals, lang):
    st.subheader(tr("robustness", lang))
    st.write(tr("robust_intro", lang))
    years = sorted(set(y for series in annuals.values() for y in series.index))
    if len(years) < 4:
        st.info(tr("insufficient", lang))
        return
    if st.session_state.get("selected_start_year") not in years[:-2]:
        st.session_state["selected_start_year"] = years[min(2, len(years)-3)]
    start = st.select_slider(tr("start_year", lang), options=years[:-2], value=st.session_state["selected_start_year"],
                             key="window_start", on_change=remember_selection, args=("window_start", "selected_start_year"))
    rows = []
    for code in METRICS:
        baseline = summarize(annuals.get(code, pd.Series(dtype=float)))
        annual = annuals.get(code, pd.Series(dtype=float))
        selected = summarize(annual[annual.index >= start])
        if not baseline:
            continue
        valid = selected and selected["slope"] is not None and baseline["slope"] is not None
        if valid:
            sign_base, sign_selected = np.sign(baseline["slope"]), np.sign(selected["slope"])
            status = tr("same_direction" if sign_base == sign_selected else "changed_direction", lang)
        else:
            status = tr("insufficient", lang)
        rows.append({
            tr("variable", lang): name(code, lang), tr("unit", lang): tr("per_year", lang, unit=unit(code, lang)),
            tr("baseline", lang): f"{baseline['start']}–{baseline['end']}",
            tr("baseline", lang) + " · " + tr("slope", lang): fmt(baseline["slope"], True),
            tr("baseline", lang) + " · " + tr("n", lang): baseline["n"],
            tr("alternative", lang): f"{selected['start']}–{selected['end']}" if selected else "—",
            tr("alternative", lang) + " · " + tr("slope", lang): fmt(selected["slope"], True) if selected else "—",
            tr("alternative", lang) + " · " + tr("n", lang): selected["n"] if selected else 0,
            tr("result", lang): status,
        })
    st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")
    st.caption(tr("comparison_note", lang))


def remember_selection(widget_key, saved_key):
    st.session_state[saved_key] = st.session_state[widget_key]


def render_risk_summary(stats, annuals, selected_groups, lang):
    candidates = []
    for code, stat in stats.items():
        if not stat or METRICS[code][0] not in selected_groups:
            continue
        annual = annuals.get(code, pd.Series(dtype=float))
        if len(annual) < 5:
            continue
        sd = float(annual.std())
        z = 0.0 if not np.isfinite(sd) or sd == 0 else float((annual.iloc[-1] - annual.mean()) / sd)
        candidates.append((abs(z), z, code, stat))
    candidates.sort(reverse=True)
    title = {"zh": "综合风险摘要", "ru": "Интегрированный обзор рисков", "en": "Integrated risk brief"}[lang]
    note = {
        "zh": "根据所选国家自身参考期计算；这是筛选线索，不是安全阈值或因果结论。",
        "ru": "Расчёт выполнен по собственному периоду сравнения страны; это ориентир для отбора, а не порог безопасности и не доказательство причинности.",
        "en": "Calculated from the selected country's own reference period; this is a screening clue, not a safety threshold or causal conclusion.",
    }[lang]
    st.subheader(title)
    if not candidates:
        st.info("目前没有足够的完整年度数据生成综合摘要。")
        return
    st.caption(note)
    for _, z, code, stat in candidates[:3]:
        labels = {
            "zh": ("明显偏离", "偏离常见范围", "常见范围内", "偏高", "偏低", "接近平均", "个标准差"),
            "ru": ("необычное отклонение", "выше/ниже обычного", "в обычном диапазоне", "выше", "ниже", "около среднего", "стандартных отклонения"),
            "en": ("unusual deviation", "outside the typical band", "within the typical band", "above", "below", "near the average", "standard deviations"),
        }[lang]
        level = labels[0] if abs(z) >= 2 else labels[1] if abs(z) >= 1 else labels[2]
        direction = labels[3] if z > 0 else labels[4] if z < 0 else labels[5]
        st.markdown(f"- **{name(code, lang)}**: {direction} in the latest complete year, about **{abs(z):.2f} {labels[6]}**; assessment: **{level}**." if lang == "en" else f"- **{name(code, lang)}**：{direction}，约 **{abs(z):.2f} {labels[6]}**；判断：**{level}**。" if lang == "zh" else f"- **{name(code, lang)}**: в последнем полном году {direction}, около **{abs(z):.2f} {labels[6]}**; оценка: **{level}**.")
    return candidates[:3]


# Annual-series statistics used by the application.
# Inputs already contain annual values calculated from complete monthly years.
# Calculations use actual calendar years and require only NumPy and pandas.

import numpy as np
import pandas as pd


# NIST, Student's t distribution, 0.975 column (two-sided 95% intervals).
# https://www.itl.nist.gov/div898/handbook/eda/section3/eda3672.htm
_EXTENSION_T975 = (
    np.nan, 12.706, 4.303, 3.182, 2.776, 2.571, 2.447, 2.365,
    2.306, 2.262, 2.228, 2.201, 2.179, 2.160, 2.145, 2.131,
    2.120, 2.110, 2.101, 2.093, 2.086, 2.080, 2.074, 2.069,
    2.064, 2.060, 2.056, 2.052, 2.048, 2.045, 2.042,
)


def _extension_clean_annual(annual):
    """Return finite values with sorted, unique integer-year labels.

    Non-numeric/non-finite observations or labels are unavailable and are dropped.
    Fractional years and duplicate usable years raise ValueError: silently
    truncating, averaging, or counting them would change the annual observations.
    """
    series = annual.copy() if isinstance(annual, pd.Series) else pd.Series(annual)
    years = np.asarray(pd.to_numeric(series.index, errors="coerce"), dtype=float)
    values = pd.to_numeric(series, errors="coerce").to_numpy(dtype=float, na_value=np.nan)
    valid = np.isfinite(years) & np.isfinite(values)
    years, values = years[valid], values[valid]
    if np.any(years != np.floor(years)):
        raise ValueError("Annual observations require integer calendar-year labels.")
    # Prevent unsafe float-to-int conversion of malformed labels.
    if np.any(years < -(2.0 ** 63)) or np.any(years >= 2.0 ** 63):
        raise ValueError("Calendar-year labels exceed the supported integer range.")
    clean = pd.Series(values, index=pd.Index(years.astype(np.int64), name="year"), dtype=float)
    if clean.index.has_duplicates:
        raise ValueError("Annual observations must contain at most one value per year.")
    return clean.sort_index()


def _extension_numerical_tolerance(values):
    """Absolute round-off tolerance: 32 machine epsilons of the value scale.

    No unit-sized floor is applied, so small-magnitude scientific quantities do
    not become constant merely because their numeric values are smaller than 1.
    """
    values = np.asarray(values, dtype=float)
    values = values[np.isfinite(values)]
    if values.size == 0:
        return 0.0
    scale = max(float(np.max(np.abs(values))), np.finfo(float).tiny)
    return float(32.0 * np.finfo(float).eps * scale)


def nearly_constant(values):
    """Whether the finite observations differ only at numerical precision.

    An empty/all-missing input is not constant; a single finite value is constant.
    """
    values = np.asarray(values, dtype=float)
    values = values[np.isfinite(values)]
    if values.size == 0:
        return False
    return bool(np.max(values) - np.min(values) <= _extension_numerical_tolerance(values))


def fit_line(annual):
    """Fit annual value ~ calendar year by OLS, or return None with <3 values.

    The fit and residuals arrays follow the sorted integer `years` array.
    `mse` is SSE/(n-2), not the mean squared in-sample error SSE/n.
    """
    series = _extension_clean_annual(annual)
    n = len(series)
    if n < 3:
        return None
    years = series.index.to_numpy(dtype=np.int64)
    x = years.astype(float)
    y = series.to_numpy(dtype=float)
    xmean = float(np.mean(x))
    ymean = float(np.mean(y))
    dx = x - xmean
    sxx = float(np.dot(dx, dx))
    slope = float(np.dot(dx, y - ymean) / sxx)
    fitted = ymean + slope * dx
    residuals = y - fitted
    sse = float(np.dot(residuals, residuals))
    df = n - 2
    return {
        "slope": slope,
        "xmean": xmean,
        "ymean": ymean,
        "sxx": sxx,
        "sse": sse,
        "mse": sse / df,
        "n": n,
        "df": df,
        "fit": fitted,
        "residuals": residuals,
        "years": years,
        "values": y,
    }


def _extension_empty_predictions():
    return pd.DataFrame({
        "year": pd.Series(dtype="int64"),
        "estimate": pd.Series(dtype="float64"),
        "lower": pd.Series(dtype="float64"),
        "upper": pd.Series(dtype="float64"),
    })


def future_estimates(annual, horizon=3):
    """Extrapolate the next 1-3 calendar years using at least 8 annual values.

    Bounds are pointwise, conditional 95% prediction intervals, including future
    residual variation. They assume a continuing linear relationship and iid
    Gaussian errors with constant variance. For df>30 the df=30 t multiplier is
    conservative. Near-constant or numerically perfect fits retain estimates but
    use NaN bounds, since the sample cannot supply meaningful residual uncertainty.
    Neither estimates nor bounds are clipped to variable-specific physical limits.
    """
    if isinstance(horizon, (bool, np.bool_)) or not isinstance(horizon, (int, np.integer)):
        raise ValueError("Forecast horizon must be an integer from 1 to 3.")
    if not 1 <= horizon <= 3:
        raise ValueError("Forecast horizon must be an integer from 1 to 3.")
    series = _extension_clean_annual(annual)
    model = fit_line(series)
    if len(series) < 8:
        return {"status": "insufficient", "predictions": _extension_empty_predictions(), "model": model}

    years = np.arange(int(series.index[-1]) + 1, int(series.index[-1]) + int(horizon) + 1, dtype=np.int64)
    estimates = model["ymean"] + model["slope"] * (years - model["xmean"])
    lower = np.full(years.size, np.nan, dtype=float)
    upper = np.full(years.size, np.nan, dtype=float)
    if nearly_constant(model["values"]):
        status = "constant"
    elif (np.max(np.abs(model["residuals"])) <= _extension_numerical_tolerance(model["values"])
          or model["mse"] <= 0.0):
        status = "zero_residual"
    else:
        status = "ok"
        tcrit = _EXTENSION_T975[min(model["df"], 30)]
        prediction_se = np.sqrt(model["mse"] * (
            1.0 + 1.0 / model["n"]
            + (years - model["xmean"]) ** 2 / model["sxx"]
        ))
        lower = estimates - tcrit * prediction_se
        upper = estimates + tcrit * prediction_se
    predictions = pd.DataFrame({"year": years, "estimate": estimates, "lower": lower, "upper": upper})
    return {"status": status, "predictions": predictions, "model": model}


def rolling_validation(annual):
    """Last up to 3 eligible one-calendar-year-ahead folds, with >=8 train years.

    Every fit uses only earlier finite observations. A held-out year is eligible
    only when its immediately preceding calendar year is present. Older gaps may
    remain in training; calendar-year coordinates preserve their elapsed time.
    Both error columns contain absolute errors in the variable's original units.
    A complete 2016-2025 series therefore yields only 2024 and 2025 test folds.
    """
    series = _extension_clean_annual(annual)
    eligible = []
    for year in series.index:
        training = series.loc[series.index < year]
        if len(training) >= 8 and int(year) - 1 in training.index:
            eligible.append(int(year))
    rows = []
    for year in eligible[-3:]:
        training = series.loc[series.index < year]
        model = fit_line(training)
        linear = float(model["ymean"] + model["slope"] * (year - model["xmean"]))
        persistence = float(training.loc[year - 1])
        actual = float(series.loc[year])
        rows.append({
            "year": year,
            "actual": actual,
            "linear": linear,
            "persistence": persistence,
            "linear_error": abs(actual - linear),
            "persistence_error": abs(actual - persistence),
        })
    columns = ["year", "actual", "linear", "persistence", "linear_error", "persistence_error"]
    result = pd.DataFrame(rows, columns=columns)
    return result.astype({"year": "int64", **{name: "float64" for name in columns[1:]}})


def rank_similar(reference, candidates):
    """Rank eligible countries by raw-unit RMSE over all valid reference years.

    Callers must exclude the reference country and unresolved boundary identities.
    At least 3 reference years are required. Each candidate must cover every one
    of those years; extra candidate years do not affect the calculation. Pearson
    correlation is descriptive and is None if either vector is nearly constant.
    """
    reference = _extension_clean_annual(reference)
    columns = ["country_id", "rmse", "correlation", "n"]
    if len(reference) < 3:
        return pd.DataFrame({
            "country_id": pd.Series(dtype="object"),
            "rmse": pd.Series(dtype="float64"),
            "correlation": pd.Series(dtype="object"),
            "n": pd.Series(dtype="int64"),
        })
    ref_values = reference.to_numpy(dtype=float)
    rows = []
    for country_id, candidate in candidates.items():
        candidate = _extension_clean_annual(candidate).reindex(reference.index)
        if candidate.isna().any():
            continue
        values = candidate.to_numpy(dtype=float)
        differences = values - ref_values
        # Rescale before squaring to avoid unnecessary overflow/underflow.
        difference_scale = float(np.max(np.abs(differences)))
        rmse = (0.0 if difference_scale == 0.0 else
                float(difference_scale * np.sqrt(np.mean((differences / difference_scale) ** 2))))
        correlation = None
        if not nearly_constant(ref_values) and not nearly_constant(values):
            ref_centered = ref_values - np.mean(ref_values)
            candidate_centered = values - np.mean(values)
            # Scale each centered vector before its dot product for stability.
            ref_centered = ref_centered / np.max(np.abs(ref_centered))
            candidate_centered = candidate_centered / np.max(np.abs(candidate_centered))
            correlation = float(np.clip(
                np.dot(ref_centered, candidate_centered)
                / np.sqrt(np.dot(ref_centered, ref_centered) * np.dot(candidate_centered, candidate_centered)),
                -1.0, 1.0,
            ))
        rows.append({"country_id": country_id, "rmse": rmse, "correlation": correlation, "n": len(reference)})
    if not rows:
        return pd.DataFrame({
            "country_id": pd.Series(dtype="object"),
            "rmse": pd.Series(dtype="float64"),
            "correlation": pd.Series(dtype="object"),
            "n": pd.Series(dtype="int64"),
        })
    result = pd.DataFrame(rows, columns=columns)
    # Preserve None rather than converting unavailable correlations to float NaN.
    result["correlation"] = pd.Series([row["correlation"] for row in rows], dtype="object")
    return result.sort_values(["rmse", "country_id"], kind="mergesort").reset_index(drop=True)


# Added pages for the complete, manually installed Streamlit app.
UI.update({
    "solution_title": ("Possible drivers & practical response", "Возможные причины и меры", "可能驱动因素与解决方案"),
    "solution_note": ("This is an evidence-informed hypothesis, not proof of causation. Confirm it with local observations before acting.", "Это обоснованная гипотеза, а не доказательство причинности. Перед действиями подтвердите её местными наблюдениями.", "这是基于证据的可能解释，不是因果证明。采取行动前应结合本地观测进一步确认。"),
    "map_unavailable": ("Country outline unavailable in the bundled map.", "Контур страны отсутствует во встроенной карте.", "内置地图中暂时没有该国家轮廓。"),
    "map_temperature": ("Map color represents the latest complete-year average temperature: {year}, {value} °C.", "Цвет карты показывает среднюю температуру последнего полного года: {year}, {value} °C.", "地图颜色表示最近完整年份的平均气温：{year} 年，{value} °C。"),
    "map_temperature_missing": ("Temperature color is unavailable because there is no complete annual temperature value.", "Цвет температуры недоступен: нет полного годового значения.", "由于没有完整年度气温值，无法使用气温着色。"),
    "hero_clues": ("Country climate clues", "Климатические признаки страны", "国家气候线索"),
    "latest_temperature": ("Latest annual temperature", "Последняя годовая температура", "最近完整年平均气温"),
    "latest_precipitation": ("Latest annual precipitation", "Последние годовые осадки", "最近完整年降水量"),
    "latest_soil": ("Latest root-zone moisture", "Последняя влажность корневой зоны", "最近完整年根区土壤水分"),
    "clue_missing": ("No complete annual value", "Нет полного годового значения", "没有完整年值"),
    "theme_atmosphere": ("Atmosphere & precipitation · heat, moisture and rainfall", "Атмосфера и осадки · тепло, влага и дождь", "大气与降水 · 热量、水汽和降雨"),
    "theme_soil": ("Soil moisture · water stored below the surface", "Влажность почвы · вода под поверхностью", "土壤水分 · 地表以下的储水"),
    "theme_water": ("Snow & water movement · evaporation, runoff and snow", "Снег и движение воды · испарение, сток и снег", "积雪与水流 · 蒸发、径流和融雪"),
    "theme_energy": ("Energy exchange · heat moving between land and air", "Энергообмен · тепло между сушей и воздухом", "能量交换 · 地表与空气之间的热量传递"),
    "climate_context": (
        "**Climate context:** {description}\n\nThis is geographic context for interpretation, not a new classification calculated from the short NASA record.",
        "**Климатический контекст:** {description}\n\nЭто географический контекст для интерпретации, а не новая классификация по короткому ряду NASA.",
        "**气候背景：**{description}\n\n这是帮助理解数据的地理背景，不是根据这段较短 NASA 记录重新计算的气候分类。"),
    "ref_period": (
        "Reference: the available complete annual values from {start} to {end} ({n} years). This is this country's own data reference, not a universal climate normal.",
        "Основа сравнения: доступные полные годовые значения с {start} по {end} ({n} лет). Это собственный ряд страны, а не универсальная климатическая норма.",
        "参考范围：{start}—{end} 年的完整年值（共 {n} 年）。这是该国自身数据的参照，不是全球统一的气候正常值。"),
    "latest_assessment": (
        "In {year}, {variable} was **{value} {unit}**, {difference} {unit} {direction} the reference-period average ({mean} {unit}). Compared with its own {start}–{end} record, this is **{category}**.",
        "В {year} году показатель «{variable}» составил **{value} {unit}** — на {difference} {unit} {direction} среднего за период ({mean} {unit}). По сравнению с собственным рядом за {start}–{end} годы это **{category}**.",
        "{year} 年，{variable}为 **{value} {unit}**，比参考期平均值（{mean} {unit}）{direction}{difference} {unit}。与该国 {start}—{end} 年记录相比，属于**{category}**。"),
    "above_mean": ("above", "выше", "高出"),
    "below_mean": ("below", "ниже", "低"),
    "equal_mean": ("equal to", "равен", "等于"),
    "ref_not_enough": (
        "At least 5 complete years are needed for a data-based high/typical/low label. The values and year-to-year changes are still shown.",
        "Для классификации «выше типичного / типично / ниже типичного» нужно не менее 5 полных лет. Значения и годовые изменения по-прежнему отображаются.",
        "至少需要 5 个完整年份，才能按数据判断偏高、典型或偏低；数值和年度变化仍会照常展示。"),
    "typical": ("typical", "типичным", "常见范围内"),
    "above": ("above typical", "выше типичного", "偏高"),
    "below": ("below typical", "ниже типичного", "偏低"),
    "far_above": ("unusually high", "необычно высоким", "明显偏高"),
    "far_below": ("unusually low", "необычно низким", "明显偏低"),
    "threshold_explain": (
        "Rule for this country and variable in {start}–{end}: the typical band is {typical_low} to {typical_high} {unit} (mean ±1 standard deviation). Values 1–2 standard deviations beyond the mean are above/below typical; beyond ±2 standard deviations are unusually high/low. The displayed thresholds come from this record, not a safety limit or a significance test.",
        "Правило для этой переменной и страны за {start}–{end}: типичный диапазон — от {typical_low} до {typical_high} {unit} (среднее ±1 стандартное отклонение). На 1–2 отклонения выше/ниже среднего — выше/ниже типичного; за пределами ±2 — необычно высоко/низко. Пороги рассчитаны по этому ряду; это не предел безопасности и не тест значимости.",
        "本国该变量在 {start}—{end} 年的判断规则：常见范围为 {typical_low} 至 {typical_high} {unit}（均值 ±1 个标准差）。高于或低于均值 1—2 个标准差为偏高或偏低；超出 ±2 个标准差为明显偏高或明显偏低。具体阈值由本段记录计算，不是安全标准，也不代表统计显著。"),
    "comparison_means": (
        "Average values over the shared years: {details}. Highest: **{high}**; lowest: **{low}**; gap: **{gap} {unit}**.",
        "Средние значения за общие годы: {details}. Максимум: **{high}**; минимум: **{low}**; разница: **{gap} {unit}**.",
        "共同年份的平均值：{details}。最高：**{high}**；最低：**{low}**；相差 **{gap} {unit}**。"),
    "comparison_tied": (
        "Average values over the shared years: {details}. The countries are equal within numerical precision; their annual records may still differ.",
        "Средние значения за общие годы: {details}. В пределах точности средние равны; годовые ряды при этом могут различаться.",
        "共同年份的平均值：{details}。各国平均值在计算精度内相同，但逐年数据仍可能不同。"),
    "comparison_context": (
        "These are area-averaged country values for the same years. A larger value does not automatically mean a more severe impact; interpretation depends on the variable and local context.",
        "Это средние по территории страны значения за одни и те же годы. Большее значение не всегда означает более сильное воздействие: смысл зависит от переменной и местных условий.",
        "这些是相同年份的国家面积平均值。数值较大不一定代表影响更严重，具体含义取决于变量和当地情况。"),
    "empty_country": ("This country folder has no CSV files yet. Add its data files, then press Analyze again.", "В папке страны пока нет CSV-файлов. Добавьте данные и снова нажмите «Анализировать».", "这个国家文件夹还没有 CSV 文件。加入数据文件后，再点击开始分析。"),
    "compare_tab": ("Comparison", "Сравнение стран", "国家对比"),
    "similar_tab": ("Similarities & differences", "Сходства и различия", "相似与差异"),
    "future_tab": ("Trends & outlook", "Тренды и оценки будущего", "整体趋势与未来预估"),
    "compare_choose": ("Compare up to 3 countries", "Сравните до 3 стран", "选择最多 3 个国家进行对比"),
    "compare_intro": (
        "Compare all 17 variables. Each variable uses only complete years shared by every selected country. The shared period can differ between variables.",
        "Сравниваются все 17 переменных. Для каждой используются только полные годы, общие для всех выбранных стран. Периоды разных переменных могут различаться.",
        "一次比较全部 17 个变量。每个变量只使用所选国家共同拥有的完整年份；不同变量的共同年份可能不同。"),
    "choose_two": ("Choose 2 or 3 countries above to see their differences.", "Выберите выше 2 или 3 страны для сравнения.", "请在上方选择 2 或 3 个国家，查看它们的差异。"),
    "too_many": ("The maximum is 3 countries.", "Можно выбрать не более 3 стран.", "最多只能选择 3 个国家。"),
    "country_col": ("Country", "Страна", "国家"),
    "shared_years": ("Shared years", "Общие годы", "共同年份"),
    "no_shared": ("No complete year is shared by every selected country for this variable.", "Для этой переменной нет полного года, общего для всех выбранных стран.", "这个变量没有所选全部国家共同拥有的完整年份。"),
    "missing_country": ("Cannot compare this variable across all selected countries. No complete annual values for: {countries}.", "Нельзя сравнить переменную по всем выбранным странам. Нет полных годовых значений: {countries}.", "此变量无法在全部所选国家间对比。以下国家没有完整年值：{countries}。"),
    "mean_order": ("Over the shared years, the highest multi-year average is **{high}**; the lowest is **{low}**. The difference is **{gap} {unit}**. All ties are included.", "За общие годы наибольшее многолетнее среднее: **{high}**; наименьшее: **{low}**. Разность: **{gap} {unit}**. Указаны все совпадения.", "共同年份内，多年平均值最高的是 **{high}**，最低的是 **{low}**，两者相差 **{gap} {unit}**。并列国家全部列出。"),
    "same_means": ("The multi-year averages are equal within numerical precision. This does not mean that every annual value is identical.", "Многолетние средние равны в пределах точности вычислений. Это не означает совпадения каждого годового значения.", "这些国家的多年平均值在计算精度内相同，但不代表每一年的数值都相同。"),
    "compare_evidence": ("Open shared-year values and chart", "Общие годовые значения и график", "展开共同年份的数据与图表"),
    "download_compare": ("Download comparison (CSV)", "Скачать сравнение (CSV)", "下载国家对比（CSV）"),
    "catalog_loading": ("Reading the available country records…", "Чтение данных доступных стран…", "正在读取可比较国家的数据……"),
    "boundary_alert": ("Country-boundary identity needs verification for: {countries}. Their source links reuse a boundary ID in another country folder. They are excluded from independent-country comparisons and similarity rankings.", "Нужно проверить границы стран: {countries}. В ссылках источников один идентификатор границы используется в папках разных стран. Эти записи исключены из межстрановых сравнений и рейтингов сходства.", "以下国家的边界身份需要核实：{countries}。其来源链接与其他国家文件夹重复使用了相同的边界 ID，因此暂不纳入独立国家对比和相似度排名。"),
    "selected_boundary": ("The selected country's source boundary is unresolved. Its recorded values can be inspected, but country-specific conclusions and future estimates must wait for correction.", "Граница выбранной страны в источнике не подтверждена. Значения доступны для просмотра, но выводы о стране и оценки будущего требуют исправления источника.", "所选国家的来源边界尚未核实。可以检查原始记录，但国家归属结论与未来预估需要先更正来源。"),
    "blocked_compare": ("Remove the countries with unresolved boundaries to run this comparison.", "Для сравнения уберите страны с неподтверждёнными границами.", "请先移除边界尚未核实的国家，再进行这组对比。"),
    "catalog_errors": ("Some country files were excluded because they could not be read.", "Некоторые файлы стран исключены из-за ошибок чтения.", "部分国家文件读取失败，已排除对应文件。"),
    "similar_intro": (
        "For each variable, find the closest and most different annual values among eligible countries. Distance is RMSE: smaller means closer numerical levels over the same years. This is not a ranking of overall national similarity or specifically of trend similarity.",
        "Для каждой переменной найдите наиболее близкие и наиболее отличающиеся годовые значения среди подходящих стран. Расстояние — RMSE: чем меньше, тем ближе уровни за одинаковые годы. Это не рейтинг общего сходства стран или сходства именно трендов.",
        "逐个变量寻找年值最接近、差异最大的国家。距离采用均方根误差（RMSE）：越小，表示同一批年份内数值水平越接近。这不是国家整体相似度，也不是专门衡量趋势形状的相似度。"),
    "ranking_guide": (
        "**How to read the table**\n\n**RMSE:** It is measured in the variable's own unit; smaller means the annual values are closer. There is no universal cutoff for “high” or “low” because temperature, precipitation and soil moisture use different units and scales. Here, low/high mean the lower/upper quarter of eligible countries for this variable; the table also names the closest and farthest country.\n\n**Pearson r:** It ranges from −1 to +1. Positive means the two countries tend to rise and fall together; negative means they tend to move in opposite directions; near 0 means little linear co-movement. As a rough guide, |r| below 0.3 is weak, 0.3–0.7 moderate, and above 0.7 strong. These are context-dependent rules of thumb, not pass/fail limits. A high r means similar ups and downs, not similar values or a cause-and-effect relationship.",
        "**Как читать таблицу**\n\n**RMSE:** измеряется в единицах переменной; чем меньше значение, тем ближе годовые ряды. Единого порога «высокого» или «низкого» RMSE нет: у температуры, осадков и влажности почвы разные единицы и масштабы. Здесь низкий/высокий означает нижнюю/верхнюю четверть среди подходящих стран по этой переменной; в таблице также указаны ближайшая и наиболее отличающаяся страны.\n\n**Корреляция Пирсона r:** от −1 до +1. Положительное значение означает, что страны обычно растут и снижаются вместе; отрицательное — что изменения направлены противоположно; около 0 — слабую линейную совместную изменчивость. Ориентир: |r| < 0,3 — слабая, 0,3–0,7 — умеренная, > 0,7 — сильная связь. Это приблизительные ориентиры, а не границы нормы. Высокий r означает схожие колебания, но не одинаковые уровни и не причинную связь.",
        "**怎么看表格**\n\n**均方根误差（RMSE）：**单位与该变量相同；数值越小，年度数值越接近。不同变量的单位和尺度不同，因此没有通用的“高 RMSE”或“低 RMSE”绝对界限。这里的高低是相对于该变量可比较国家的排名：最低四分之一代表差异较小，最高四分之一代表差异较大；表格也会列出最接近和差异最大的国家。\n\n**皮尔逊相关系数 r：**范围为 −1 到 +1。正值表示两国数值倾向于同涨同跌；负值表示倾向于反向变化；接近 0 表示线性共同变化较弱。粗略参考：|r| < 0.3 较弱，0.3–0.7 中等，> 0.7 较强。这些是随场景变化的经验参考，并非正常/异常的判定线。r 较高只表示变化方向较同步，不表示绝对数值相近，也不代表因果关系。"),
    "rmse_relative": ("Relative RMSE", "Сравнительная категория RMSE", "相对 RMSE 档位"),
    "rmse_low": ("Lower quarter: smaller differences", "Нижняя четверть: меньшие различия", "差异较小：较低四分之一"),
    "rmse_middle": ("Middle range", "Средний диапазон", "中间范围"),
    "rmse_high": ("Upper quarter: larger differences", "Верхняя четверть: большие различия", "差异较大：较高四分之一"),
    "rmse_equal": ("All distances tied", "Все расстояния равны", "所有差异并列"),
    "similar_scope": ("Search among", "Область поиска", "比较对象范围"),
    "all_regions": ("All available regions", "Все доступные регионы", "所有已加入的地区"),
    "same_region": ("The selected region", "Выбранный регион", "当前选择的地区"),
    "similar_coverage": ("Candidates must cover every complete year of the selected country for that variable (minimum 3 years). Missing years are not filled. Smaller candidate counts mean a narrower search.", "Кандидат должен иметь данные за каждый полный год выбранной страны по этой переменной (минимум 3 года). Пропуски не заполняются. Чем меньше кандидатов, тем уже поиск.", "候选国家必须覆盖所选国家该变量的全部完整年份（至少 3 年），不补填缺失年份。候选国家数量越少，比较范围越有限。"),
    "closest": ("Closest annual values", "Наиболее близкие годовые значения", "年值最接近"),
    "farthest": ("Most different annual values", "Наиболее отличающиеся годовые значения", "年值差异最大"),
    "distance": ("RMSE", "RMSE", "均方根误差 RMSE"),
    "candidates": ("Eligible other countries", "Подходящие другие страны", "可比较的其他国家数"),
    "correlation": ("Pearson r", "Корреляция Пирсона r", "皮尔逊相关系数 r"),
    "ranking_details": ("Open every candidate and distance", "Все кандидаты и расстояния", "展开所有候选国家与差异数值"),
    "ranking_note": ("Equal distances are tied. Pearson r describes co-variation, not causality; it is undefined for a nearly constant series. A zero RMSE means matching annual records, not matching every Earth-system process.", "Равные расстояния считаются совпадением. Коэффициент r описывает совместные изменения, не причинность; для почти постоянного ряда он не определён. Нулевой RMSE означает совпадение годовых записей, не всех процессов системы Земли.", "距离相同的国家并列展示。相关系数描述共同变化，不代表因果关系；近乎恒定的序列不计算相关系数。RMSE 为零只表示这份年度记录相同，不代表所有地球系统过程相同。"),
    "no_candidates": ("No eligible comparison country", "Нет подходящих стран для сравнения", "没有满足条件的比较国家"),
    "equal_distances": ("All candidate distances are tied; there is no distinct closest/farthest country.", "Расстояния всех кандидатов равны; единственной ближайшей или наиболее отличающейся страны нет.", "所有候选国家的距离并列，无法区分唯一的最近或最远国家。"),
    "download_similar": ("Download similarity rankings (CSV)", "Скачать рейтинги сходства (CSV)", "下载相似度排名（CSV）"),
    "outlook_intro": (
        "First read the observed trends, then explore what a continued linear trend would imply. Each variable keeps its own units. No combined climate score is calculated.",
        "Сначала изучите наблюдаемые тренды, затем — возможное продолжение линейной зависимости. У каждой переменной свои единицы. Сводный климатический балл не рассчитывается.",
        "先看实际记录中的变化，再探索线性趋势继续时可能出现的年值。每个变量保留自身单位，不把不同量纲合成一个气候分数。"),
    "trend_table": ("Observed trends across all variables", "Наблюдаемые тренды всех переменных", "全部变量的历史变化趋势"),
    "direction": ("Fitted direction", "Направление тренда", "拟合方向"),
    "up": ("Increasing", "Рост", "上升"),
    "down": ("Decreasing", "Снижение", "下降"),
    "flat": ("Nearly constant", "Почти постоянный ряд", "近乎不变"),
    "no_linear_direction": ("Linear slope near zero", "Линейный наклон близок к нулю", "线性斜率近零"),
    "latest": ("Last complete-year value", "Последнее полное годовое значение", "最近完整年份的值"),
    "per_decade": ("{unit}/decade", "{unit}/10 лет", "{unit}/十年"),
    "decade_slope": ("Fitted change per decade", "Наклон тренда за 10 лет", "每十年拟合变化量"),
    "trend_sentence": ("**{name}**: fitted direction **{direction}**, **{slope} {rate}** over {start}–{end}. This is a descriptive slope, not a tested significant trend.", "**{name}**: направление — **{direction}**, **{slope} {rate}** за {start}–{end}. Это описательный наклон, а не подтверждённый значимый тренд.", "**{name}**：{start}—{end} 年拟合方向为 **{direction}**，变化速率为 **{slope} {rate}**。这是描述性斜率，尚未证明显著。"),
    "horizon": ("Years after the last complete year", "Лет после последнего полного года", "在最近完整年份之后推算几年"),
    "forecast_heading": ("Conditional linear extrapolation", "Условная линейная экстраполяция", "有条件的线性趋势外推"),
    "forecast_intro": (
        "Use at least 8 complete annual observations and extrapolate only 1–3 years after the last complete year. An unfinished calendar year can therefore appear below. These are illustrative annual estimates, not weather forecasts or climate-model projections.",
        "Используется не менее 8 полных годовых наблюдений, экстраполяция — на 1–3 года после последнего полного года. Поэтому ниже может быть ещё незавершённый год. Это иллюстративные годовые оценки, не прогноз погоды и не проекции климатической модели.",
        "至少需要 8 个完整年值，只向最后一个完整年份之后外推 1—3 年，因此结果可能包含尚未结束的当年。这些是演示性的年度估计，不是天气预报，也不是气候模型情景预测。"),
    "interval_note": (
        "The nominal 95% prediction interval assumes the linear relationship continues, with independent Gaussian errors and constant variance. It does not include data-source uncertainty, structural model error or all climate drivers; each interval is pointwise, not a joint guarantee for all variables and years.",
        "Номинальный 95%-й предиктивный интервал предполагает сохранение линейной зависимости, независимые нормальные ошибки и постоянную дисперсию. Он не включает неопределённость источников, структуры модели или всех климатических факторов; это отдельные интервалы, не совместная гарантия для всех переменных и лет.",
        "名义 95% 预测区间以线性关系持续、误差独立且服从正态分布、方差恒定为前提，不包含数据来源误差、模型结构误差或全部气候驱动因素。这是逐项区间，不是全部变量和年份同时成立的保证。"),
    "estimate": ("Estimated annual value", "Оценка годового значения", "估计年值"),
    "lower": ("95% PI lower bound", "Нижняя граница 95% интервала", "95% 预测区间下界"),
    "upper": ("95% PI upper bound", "Верхняя граница 95% интервала", "95% 预测区间上界"),
    "forecast_sentence": ("For **{year}**, the linear estimate is **{estimate} {unit}**, with a conditional 95% prediction interval of **{lower} to {upper} {unit}**.", "Для **{year}** линейная оценка: **{estimate} {unit}**; условный 95%-й предиктивный интервал: **{lower} — {upper} {unit}**.", "**{year} 年**的线性估计为 **{estimate} {unit}**，有条件的 95% 预测区间为 **{lower}—{upper} {unit}**。"),
    "forecast_insufficient": ("Fewer than 8 complete years: no extrapolation.", "Менее 8 полных лет: экстраполяция не выполняется.", "不足 8 个完整年份，不生成外推结果。"),
    "forecast_constant": ("The record is nearly constant. It cannot support a credible future-uncertainty estimate, so no forecast is shown.", "Ряд почти постоянен. По нему нельзя надёжно оценить будущую неопределённость, поэтому прогноз не показан.", "记录近乎恒定，无法据此合理估计未来不确定性，因此不显示预测。"),
    "forecast_zero_residual": ("The fitted residual variation is effectively zero. An apparent zero-width prediction interval would be misleading, so no forecast is shown.", "Разброс остатков практически нулевой. Интервал нулевой ширины был бы вводящим в заблуждение, поэтому прогноз не показан.", "拟合残差变动近乎为零，零宽度预测区间容易产生误导，因此不显示预测。"),
    "forecast_physical": ("This unconstrained estimate or its interval crosses the variable's non-negative physical range. Treat it as evidence of model limitations; values have not been clipped to zero.", "Оценка или интервал этой неограниченной модели выходит за неотрицательную физическую область переменной. Это ограничение модели; значения не заменены нулями.", "这项无约束模型的点估计或区间越过了该变量非负的物理范围，说明模型存在限制；数值没有被悄悄截断为零。"),
    "physical_point": ("Point estimate outside physical range", "Оценка вне физической области", "点估计超出物理范围"),
    "physical_interval": ("Interval extends below zero", "Интервал заходит ниже нуля", "区间延伸至零以下"),
    "conditional": ("Conditional estimate", "Условная оценка", "有条件估计"),
    "status": ("Status", "Статус", "状态"),
    "backtest": ("Could this method estimate a held-out year?", "Как метод оценивает скрытый год?", "把最后几年藏起来，方法还能估准吗？"),
    "backtest_note": ("Rolling one-year checks use only earlier years, with at least 8 training years, for up to the last 3 eligible years. Persistence uses the immediately preceding year's value. This small check does not validate multi-year predictions.", "Скользящая проверка на год вперёд использует только прошлые годы, минимум 8 лет обучения, для последних 3 подходящих лет. Базовый метод повторяет значение предыдущего года. Эта малая проверка не подтверждает многолетние прогнозы.", "滚动检验只用此前的年份训练，每次至少 8 年，最多检验最后 3 个满足条件的年份。简单基准直接沿用上一年数值。这一小样本检查不能验证多年预测。"),
    "validation_sentence": ("{folds} one-year checks: linear MAE **{linear} {unit}**; previous-year baseline MAE **{baseline} {unit}**. Lower is better.", "Проверок на год вперёд: {folds}. MAE линейного метода: **{linear} {unit}**; базового: **{baseline} {unit}**. Меньше — лучше.", "共 {folds} 次一年期检验：线性方法平均绝对误差 **{linear} {unit}**，沿用上一年基准误差 **{baseline} {unit}**。误差越小越好。"),
    "validation_worse": ("The linear model did not beat the previous-year baseline in these checks. Its future estimates have not demonstrated added predictive value.", "В этих проверках линейный метод не превзошёл повторение прошлого года. Дополнительная прогностическая ценность не показана.", "这些检验中，线性方法未优于沿用上一年的简单基准，尚未体现额外预测价值。"),
    "no_validation": ("No eligible held-out year after 8 training years; predictive performance has not been checked.", "Нет подходящего проверочного года после 8 лет обучения; качество прогноза не проверено.", "没有在至少 8 个训练年之后可用的检验年份，尚未检查预测表现。"),
    "forecast_evidence": ("Open trend, interval chart and validation details", "Тренд, интервал и детали проверки", "展开趋势、区间图及检验明细"),
    "linear_error": ("Linear absolute error", "Абсолютная ошибка линейного метода", "线性方法绝对误差"),
    "persistence_error": ("Baseline absolute error", "Абсолютная ошибка базового метода", "简单基准绝对误差"),
    "persistence": ("Previous-year baseline", "Значение прошлого года", "沿用上一年基准"),
    "residual": ("Residual", "Остаток", "残差"),
    "download_future": ("Download estimates and intervals (CSV)", "Скачать оценки и интервалы (CSV)", "下载预估值与区间（CSV）"),
    "download_trends": ("Download trend summary (CSV)", "Скачать сводку трендов (CSV)", "下载整体趋势（CSV）"),
    "new_methods": (
        "Comparison uses the intersection of complete annual records for all selected countries. Similarity uses unstandardized annual RMSE over the target's entire complete-year record, requiring all those years in each candidate. Predictions use ordinary least squares in calendar years and a Student-t future-observation interval: estimate ± t × sqrt(MSE × [1 + 1/n + (future year − mean year)²/Sxx]), df = n − 2. The t table uses two-sided 95% values; for df > 30, the df=30 value is conservatively used. No forecast is generated for almost constant data or negligible residual variance. Physical support checks cover non-negative humidity, precipitation, water storage, runoff and snowmelt; signed energy fluxes and Celsius temperatures can be negative. This is a short-record exploratory tool, not an attribution model.",
        "Сравнение использует пересечение полных годовых записей всех выбранных стран. Сходство — нестандартизированный годовой RMSE за весь набор полных лет целевой страны; у каждого кандидата должны быть все эти годы. Оценки используют МНК по календарным годам и интервал будущего наблюдения Стьюдента: оценка ± t × sqrt(MSE × [1 + 1/n + (будущий год − средний год)²/Sxx]), df = n − 2. Таблица t — двусторонние 95% значения; при df > 30 консервативно используется df=30. Почти постоянные ряды и пренебрежимо малая дисперсия остатков исключены. Проверки физической области применяются к неотрицательным влажности, осадкам, запасам воды, стоку и таянию снега; знаковые потоки энергии и температура в °C могут быть отрицательными. Это исследовательский инструмент для коротких рядов, не модель установления причин.",
        "国家对比使用所有所选国家完整年份的交集。相似度采用未标准化的年度 RMSE，固定使用目标国家该变量的全部完整年份，要求每个候选国家覆盖这些年份。预估使用实际公历年份进行普通最小二乘拟合，以 Student-t 构造未来年值区间：估计值 ± t × sqrt(MSE × [1 + 1/n + (未来年份 − 平均年份)²/Sxx])，自由度为 n−2。t 表使用双侧 95% 临界值；自由度超过 30 时保守使用 df=30 的临界值。近乎恒定或残差方差近乎为零时不输出预测。非负范围检查适用于比湿、降水、储水、径流与融雪；带方向的能量通量和摄氏气温允许为负。这是短记录探索工具，不能用于因果归因。"),
})

CENTRAL_ASIA_SOURCE_LINKS = [
    ("World Bank · Central Asia water and energy", "https://www.worldbank.org/en/brief/2026/08/20/cawep"),
    ("World Bank · Kazakhstan water diagnosis", "https://documents1.worldbank.org/curated/en/099062424121021579/pdf/P170030-c5804310-6273-46e1-8aca-917d53b41c92.pdf"),
    ("UNEP · Kyrgyz Republic Environmental Change Atlas", "https://www.unep.org/en/news-and-stories/press-release/climate-change-reshaping-kyrgyz-republic-finds-new-unep-atlas"),
    ("World Bank · Kyrgyz Republic climate report", "https://www.worldbank.org/en/country/kyrgyzrepublic/publication/ccdr"),
    ("World Bank · Turkmenistan climate profile", "https://climateknowledgeportal.worldbank.org/sites/default/files/2021-06/15837-Turkmenistan%20Country%20Profile-WEB.pdf"),
    ("UNEP · Tajikistan Environmental Change Atlas", "https://www.unep.org/news-and-stories/press-release/tajikistans-melting-glaciers-put-water-resources-under-stress-unep"),
    ("UNEP · Uzbekistan Environmental Change Atlas", "https://www.unep.org/en/news-and-stories/press-release/climate-change-drives-rising-temperatures-and-severe-drought"),
    ("UNEP · Third Pole assessment", "https://wedocs.unep.org/items/ff4ec14b-09bf-414b-8664-5a1fe44ee7b5"),
]
SOUTH_SOUTHEAST_ASIA = {
    "Afghanistan", "Bangladesh", "Bhutan", "India", "Iran", "Lanka", "Maldives", "Nepal", "Pakistan",
    "Brunei", "Burma", "Cambodia", "Indonesia", "Laos", "Malaysia", "Philippines", "Singapore", "Thailand", "Timor-Leste", "Vietnam",
}
WEST_ASIA = {"Armenia", "Azerbaijan", "Bahrain", "Cyprus", "Georgia", "Iraq", "Israel", "Jordan", "Kuwait", "Lebanon", "Oman", "Qatar", "Saudi Arabia", "Shape Yemen", "Syria", "Turkey", "United Arab Emirates", "West Bank"}
EAST_ASIA = {"China", "Mongolia", "North Korea", "South Korea"}
SOUTH_SOUTHEAST_SOURCE_LINKS = [
    ("ADB · Asian Water Development Outlook 2025", "https://www.adb.org/awdo/editions/2025"),
    ("UNEP · Third Pole assessment", "https://wedocs.unep.org/items/ff4ec14b-09bf-414b-8664-5a1fe44ee7b5"),
    ("ADB · Asia-Pacific Climate Report 2026", "https://www.adb.org/climate-report/editions/2026"),
]
EAST_ASIA_SOURCE_LINKS = [
    ("ADB · Asian Water Development Outlook 2025", "https://www.adb.org/awdo/editions/2025"),
    ("UNEP · Third Pole assessment", "https://wedocs.unep.org/items/ff4ec14b-09bf-414b-8664-5a1fe44ee7b5"),
    ("UNEP · Asia-Pacific climate and water evidence", "https://www.unep.org/regions/asia-and-pacific"),
]
COUNTRY_REPORT_SLUGS = {
    "Kyrgyzstan": "kyrgyz-republic", "Lanka": "sri-lanka", "Burma": "myanmar",
    "Shape Yemen": "yemen-rep", "West Bank": "west-bank-and-gaza",
    "Timor-Leste": "timor-leste", "North Korea": "korea-democratic-peoples-republic",
    "South Korea": "korea-republic", "Iran": "iran-islamic-republic",
    "Turkey": "turkiye", "United Arab Emirates": "united-arab-emirates",
    "Laos": "lao-pdr", "Brunei": "brunei-darussalam",
}
COUNTRY_DETAILED_REPORTS = {
    "Mongolia": ("World Bank · Mongolia climate risk report", "https://climateknowledgeportal.worldbank.org/sites/default/files/country-profiles/15813-Mongolia%20Country%20Profile-WEB.pdf"),
    "Maldives": ("World Bank · Maldives climate risk report", "https://climateknowledgeportal.worldbank.org/sites/default/files/2021-05/15649-WB_Maldives%20Country%20Profile-WEB.pdf"),
    "Vietnam": ("World Bank · Vietnam climate risk report", "https://climateknowledgeportal.worldbank.org/sites/default/files/2021-04/15077-Vietnam%20Country%20Profile-WEB.pdf"),
    "Laos": ("World Bank · Lao PDR climate risk report", "https://climateknowledgeportal.worldbank.org/sites/default/files/country-profiles/15505-Lao%20PDR%20Country%20Profile-WEB.pdf"),
    "Shape Yemen": ("World Bank · Yemen climate risk report", "https://climateknowledgeportal.worldbank.org/sites/default/files/country-profiles/16696-WB_Yemen%20Country%20Profile-WEB.pdf"),
}

def report_links(country):
    slug = COUNTRY_REPORT_SLUGS.get(country, country.lower().replace(" ", "-"))
    country_profile = ("World Bank · " + country + " climate profile",
                       "https://climateknowledgeportal.worldbank.org/country/" + slug)
    specific = {
        "Kazakhstan": CENTRAL_ASIA_SOURCE_LINKS[1],
        "Kyrgyzstan": CENTRAL_ASIA_SOURCE_LINKS[2],
        "Tajikistan": next(x for x in CENTRAL_ASIA_SOURCE_LINKS if "Tajikistan" in x[0]),
        "Turkmenistan": next(x for x in CENTRAL_ASIA_SOURCE_LINKS if "Turkmenistan" in x[0]),
        "Uzbekistan": next(x for x in CENTRAL_ASIA_SOURCE_LINKS if "Uzbekistan" in x[0]),
    }
    if country in specific:
        return [specific[country], country_profile]
    if country in COUNTRY_DETAILED_REPORTS:
        return [COUNTRY_DETAILED_REPORTS[country], country_profile]
    return [country_profile]

def action_brief_pdf(country, lang, role, top_risks, selected_groups):
    import io
    from reportlab.pdfgen import canvas
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.lib.colors import HexColor
    font = "Helvetica"
    for path in ("/System/Library/Fonts/Supplemental/Arial Unicode.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"):
        if Path(path).exists():
            if "EarthCluesFont" not in pdfmetrics.getRegisteredFontNames():
                pdfmetrics.registerFont(TTFont("EarthCluesFont", path))
            font = "EarthCluesFont"
            break
    if font == "Helvetica" and lang == "zh":
        from reportlab.pdfbase.cidfonts import UnicodeCIDFont
        if "STSong-Light" not in pdfmetrics.getRegisteredFontNames():
            pdfmetrics.registerFont(UnicodeCIDFont("STSong-Light"))
        font = "STSong-Light"
    output = io.BytesIO()
    page = canvas.Canvas(output, pagesize=(595, 842))
    page.setTitle("Earth Clues - " + country)
    y = 795
    def line(value, size=10, gap=18, color="#24343A"):
        nonlocal y
        page.setFillColor(HexColor(color)); page.setFont(font, size)
        words = value.split(" ") if lang != "zh" else list(value)
        current = ""
        for word in words:
            candidate = current + ("" if lang == "zh" or not current else " ") + word
            if pdfmetrics.stringWidth(candidate, font, size) > 510 and current:
                page.drawString(42, y, current); y -= gap; current = word
            else:
                current = candidate
        if current:
            page.drawString(42, y, current); y -= gap
    page.setFillColor(HexColor("#0C5863")); page.rect(0, 750, 595, 92, fill=1, stroke=0)
    line("EARTH CLUES  |  " + country, 18, 26, "#FFFFFF")
    y = 740
    line({"zh":"角色", "ru":"Роль", "en":"Role"}[lang] + ": " + ROLE_LABELS[role][LANG_INDEX[lang]], 12, 25)
    line({"zh":"主要数据线索", "ru":"Основные сигналы", "en":"Key data clues"}[lang], 14, 23, "#0C5863")
    for _, z, code, stat in top_risks:
        direction = ({"zh":"偏高", "ru":"выше", "en":"above"} if z > 0 else {"zh":"偏低", "ru":"ниже", "en":"below"})[lang]
        line(f"• {name(code, lang)}: {fmt(stat['last'])} {unit(code, lang)}, {direction} ({abs(z):.2f} SD)", 10, 20)
    y -= 8
    line({"zh":"可能影响与下一步", "ru":"Возможные последствия и действия", "en":"Potential impacts and next steps"}[lang], 14, 23, "#0C5863")
    for _, _, code, stat in top_risks[:2]:
        note = solution_text(code, country, stat, lang, role)
        if note:
            import re
            plain = re.sub(r"\*\*", "", note).split("\n\n")
            for part in plain[1:3]:
                line(part, 9, 15)
    line(ROLE_ACTIONS[role][lang], 9, 16)
    y -= 5
    line({"zh":"国家资料与参考报告", "ru":"Источники по стране", "en":"Country sources"}[lang], 14, 23, "#0C5863")
    for title, url in report_links(country)[:2]:
        previous_y = y
        line(title, 9, 16, "#155C97")
        page.linkURL(url, (42, previous_y - 2, 550, previous_y + 14), relative=0)
    y -= 6
    line({"zh":"说明：国家平均值与短期参考期仅用于筛选线索；可能原因需要当地观测核实。", "ru":"Примечание: национальные средние служат для отбора; причины требуют местной проверки.", "en":"Note: national averages are screening clues; possible causes require local verification."}[lang], 8, 13, "#657780")
    page.setStrokeColor(HexColor("#D4E3E5")); page.line(42, 55, 553, 55)
    page.setFont(font, 8); page.drawString(42, 39, "Quanthelix team | Zhanbota Erlan")
    page.showPage(); page.save()
    return output.getvalue()

@st.cache_data(show_spinner=False)
def interactive_features(asset_path, country_ids):
    import json
    with open(asset_path, encoding="utf-8") as handle:
        features = json.load(handle)["features"]
    lookup = {MAP_NAMES.get(cid.split("/", 1)[1], cid.split("/", 1)[1]): cid for cid in country_ids}
    selected = []
    for feature in features:
        cid = lookup.get(feature.get("properties", {}).get("name"))
        if cid:
            feature["properties"]["country_id"] = cid
            selected.append(feature)
    return selected

def render_interactive_map(data_dir, lang):
    import pydeck as pdk
    codes = ["T2M", "PRECTOTCORR", "RootMoist_inst", "SWE_inst", "Qs_acc"]
    code = st.selectbox({"zh":"地图着色变量", "ru":"Показатель на карте", "en":"Map variable"}[lang],
                        codes, format_func=lambda c: name(c, lang), key="map_variable")
    catalog, blocked, _ = load_catalog(catalog_signature(data_dir))
    features = interactive_features(str(Path(__file__).resolve().parent / "world_countries.geojson"), tuple(catalog))
    values = {}
    for cid, metrics in catalog.items():
        series = metrics.get(code, pd.Series(dtype=float)).dropna()
        if not series.empty and cid not in blocked:
            values[cid] = float(series.iloc[-1])
    if values:
        low, high = min(values.values()), max(values.values())
        for feature in features:
            cid = feature["properties"]["country_id"]
            value = values.get(cid)
            feature["properties"]["value_label"] = "—" if value is None else f"{value:.2f} {unit(code, lang)}"
            fraction = .5 if value is None or high == low else (value - low) / (high - low)
            feature["properties"]["fill"] = [int(37 + 205 * fraction), int(153 - 75 * fraction), int(181 - 110 * fraction), 190]
    layer = pdk.Layer("GeoJsonLayer", {"type":"FeatureCollection", "features":features}, id="countries",
                      pickable=True, auto_highlight=True, filled=True, stroked=True,
                      get_fill_color="properties.fill", get_line_color=[255,255,255], line_width_min_pixels=1)
    deck = pdk.Deck(layers=[layer], initial_view_state=pdk.ViewState(latitude=30, longitude=65, zoom=2.2),
                    map_style=None, tooltip={"html":"<b>{properties.name}</b><br/>{properties.value_label}"})
    event = st.pydeck_chart(deck, on_select="rerun", selection_mode="single-object", key="country_map", height=400)
    items = event.selection.get("objects", {}).get("countries", [])
    if items:
        chosen = items[0].get("properties", {}).get("country_id")
        if chosen and chosen != st.session_state.get("map_last_choice"):
            st.session_state["map_last_choice"] = chosen
            region, country = chosen.split("/", 1)
            st.session_state["selected_region"] = region
            st.session_state["selected_country"] = country
            st.session_state["region"] = region
            st.session_state["country"] = country
            st.session_state["analysis_target"] = (region, country)
            st.rerun()
    st.caption({"zh":"点击地图上的国家即可切换分析；颜色表示各国最近完整年数值，按当前地图变量范围着色。",
                "ru":"Выберите страну на карте. Цвет показывает значение последнего полного года по выбранному показателю.",
                "en":"Click a country to analyze it. Color shows its latest complete-year value for the selected variable."}[lang])
ROLE_LABELS = {
    "farmer": ("Farmer", "Фермер", "农民"),
    "planner": ("City planner", "Городской планировщик", "城市规划者"),
    "water_manager": ("Water manager", "Менеджер водных ресурсов", "水资源管理者"),
    "resident": ("Resident", "Житель", "普通居民"),
}
ROLE_ACTIONS = {
    "farmer": {
        "en": "Role focus: protect yields with soil-moisture monitoring, efficient irrigation and heat/drought alerts.",
        "ru": "Фокус роли: защищать урожай с помощью мониторинга влажности почвы, эффективного орошения и предупреждений о жаре/засухе.",
        "zh": "角色重点：通过土壤水分监测、高效灌溉和高温/干旱预警保护产量。",
    },
    "planner": {
        "en": "Role focus: use heat, rainfall and runoff signals to guide drainage, shade, floodplain and resilient-infrastructure planning.",
        "ru": "Фокус роли: использовать сигналы жары, осадков и стока для дренажа, озеленения, пойм и устойчивой инфраструктуры.",
        "zh": "角色重点：利用气温、降水和径流信号指导排水、遮阴、洪泛区和韧性基础设施规划。",
    },
    "water_manager": {
        "en": "Role focus: coordinate snow, runoff, soil storage and demand across seasons and shared river basins.",
        "ru": "Фокус роли: согласовывать снег, сток, запасы почвы и спрос по сезонам и общим речным бассейнам.",
        "zh": "角色重点：跨季节、跨流域协调积雪、径流、土壤储水和用水需求。",
    },
    "resident": {
        "en": "Role focus: follow heat, rainfall and flood alerts, reduce household water waste and prepare for local hazards.",
        "ru": "Фокус роли: следить за предупреждениями о жаре, осадках и паводках, экономить воду и готовиться к местным рискам.",
        "zh": "角色重点：关注高温、降雨和洪水预警，减少家庭用水浪费并准备应对本地风险。",
    },
}
ROLE_VARIABLE_FOCUS = {
    "farmer": {"T2M": "优先关注热害与作物水分需求", "PRECTOTCORR": "优先关注播种期降水和干旱预警", "RootMoist_inst": "优先关注根区含水量和灌溉时机"},
    "planner": {"T2M": "优先关注热岛、遮阴和热健康", "PRECTOTCORR": "优先关注排水能力和洪泛区", "Qs_acc": "优先关注暴雨径流和城市内涝"},
    "water_manager": {"SWE_inst": "优先关注积雪储量和季节融水", "Qsm_acc": "优先关注融雪洪峰", "Qsb_acc": "优先关注地下水补给"},
    "resident": {"T2M": "优先关注高温预警和健康防护", "PRECTOTCORR": "优先关注暴雨、洪水和用水储备"},
}

def solution_text(code, country, stats, lang, role="resident"):
    """Return an evidence-informed driver/response note for the first country batch."""
    if not stats or (country not in {"Kazakhstan", "Kyrgyzstan", "Tajikistan", "Turkmenistan", "Uzbekistan"} and country not in SOUTH_SOUTHEAST_ASIA and country not in EAST_ASIA and country not in WEST_ASIA):
        return None
    delta = float(stats.get("delta", 0.0))
    direction = "high" if delta > 0 else "low" if delta < 0 else "flat"
    central_water = {
        "T2M": {
            "en": ("warming, stronger evaporative demand and heat stress", "heat-health plans, drought-tolerant crops, shade/early-warning systems"),
            "ru": ("потепление, рост испарительного спроса и теплового стресса", "планы защиты от жары, засухоустойчивые культуры, тень и раннее предупреждение"),
            "zh": ("变暖、蒸发需求增强和热应激", "完善高温预警，推广耐旱作物，并减少高温时段的户外暴露"),
        },
        "PRECTOTCORR": {
            "en": ("highly seasonal precipitation, drought variability and changing mountain runoff", "rainwater storage, drought/flood early warning and basin-level water allocation"),
            "ru": ("сезонность осадков, изменчивость засух и изменение горного стока", "накопление дождевой воды, раннее предупреждение и бассейновое распределение воды"),
            "zh": ("降水季节性、干旱波动和山地径流变化", "建设雨水蓄存和旱涝预警，并按流域统筹分配水资源"),
        },
        "RootMoist_inst": {
            "en": ("heat-driven evapotranspiration, irrigation demand, conveyance losses and upstream water changes", "upgrade irrigation efficiency, reduce canal losses, monitor soil moisture and coordinate transboundary basins"),
            "ru": ("испарение из-за жары, спрос на орошение, потери в каналах и изменения стока upstream", "повысить эффективность орошения, сократить потери, мониторить влажность почвы и координировать трансграничные бассейны"),
            "zh": ("高温蒸散增强、灌溉需求、输水损失和上游来水变化", "提高灌溉效率、减少渠道损失、监测土壤水分，并加强跨境流域协调"),
        },
        "SoilMoi0_10cm_inst": {
            "en": ("short-term rainfall gaps, heat and rapid surface evaporation", "mulching, conservation agriculture, soil-moisture alerts and irrigation scheduling"),
            "ru": ("дефицит осадков, жара и быстрое испарение с поверхности", "мульчирование, почвозащитное земледелие, мониторинг влажности и планирование полива"),
            "zh": ("降水短缺、高温和表层快速蒸发", "采用覆盖和保护性耕作，结合土壤水分预警安排灌溉"),
        },
        "SoilMoi10_40cm_inst": {
            "en": ("seasonal water deficit and repeated irrigation demand", "improve infiltration, reduce bare-soil evaporation and use deficit-irrigation planning"),
            "ru": ("сезонный дефицит воды и повторяющаяся потребность в орошении", "улучшать инфильтрацию, уменьшать испарение с открытой почвы и планировать дефицитное орошение"),
            "zh": ("季节性水分亏缺和持续灌溉需求", "提高土壤入渗、减少裸地蒸发，并采用适度亏缺灌溉"),
        },
        "SoilMoi40_100cm_inst": {
            "en": ("longer-lived root-zone deficits, groundwater/irrigation pressure and land degradation", "protect recharge areas, improve irrigation productivity and track salinity/erosion"),
            "ru": ("длительный дефицит в корнеобитаемом слое, давление орошения и деградация земель", "защищать зоны пополнения, повышать продуктивность воды и отслеживать засоление/эрозию"),
            "zh": ("根区长期亏缺、地下水或灌溉压力以及土地退化", "保护补给区、提高单位水产出，并监测盐碱化和侵蚀"),
        },
        "SoilMoi100_200cm_inst": {
            "en": ("multi-season water deficits and slow recovery of deep storage", "set groundwater and irrigation limits, protect recharge and plan drought reserves"),
            "ru": ("многосезонный дефицит воды и медленное восстановление глубокого запаса", "ограничивать водозабор, защищать пополнение и планировать резерв на засуху"),
            "zh": ("跨季节水分亏缺和深层储水恢复缓慢", "控制地下水与灌溉取水，保护补给区，并建立干旱储备"),
        },
        "SWE_inst": {
            "en": ("warming, reduced snow persistence and earlier melt in mountain water towers", "snowpack monitoring, seasonal runoff forecasts and reservoir rule curves"),
            "ru": ("потепление, сокращение сохранности снега и более раннее таяние в горах", "мониторинг снега, прогноз сезонного стока и адаптация правил работы водохранилищ"),
            "zh": ("变暖、积雪持续时间缩短和山地水塔提前融雪", "加强积雪监测和季节径流预报，并调整水库调度规则"),
        },
        "Qsm_acc": {
            "en": ("earlier snowmelt, glacier change and intense meltwater pulses", "combine snow/glacier monitoring with flood warnings and downstream reservoir planning"),
            "ru": ("более раннее таяние снега, изменения ледников и резкие волны талой воды", "совмещать мониторинг снега и ледников с предупреждением о паводках и планированием водохранилищ"),
            "zh": ("提前融雪、冰川变化和融水脉冲增强", "把积雪冰川监测与洪水预警、水库调度结合起来"),
        },
        "Qs_acc": {
            "en": ("intense rainfall, rapid snowmelt, soil saturation and land-surface runoff", "restore riparian buffers, improve flood early warning and protect floodplains"),
            "ru": ("сильные осадки, быстрое таяние снега, насыщение почвы и поверхностный сток", "восстанавливать прибрежные буферы, улучшать предупреждение о паводках и не застраивать поймы"),
            "zh": ("强降水、快速融雪、土壤饱和和地表产流", "恢复河岸缓冲带、加强洪水预警，并保护洪泛区"),
        },
        "Qsb_acc": {
            "en": ("changes in infiltration, soil storage and aquifer recharge", "protect recharge zones, reduce over-irrigation and monitor groundwater levels"),
            "ru": ("изменения инфильтрации, почвенного запаса и пополнения водоносных горизонтов", "защищать зоны пополнения, сокращать избыточный полив и мониторить подземные воды"),
            "zh": ("入渗、土壤储水和含水层补给变化", "保护补给区、减少过度灌溉，并监测地下水位"),
        },
    }
    entry = central_water.get(code)
    source_links = CENTRAL_ASIA_SOURCE_LINKS
    if country in WEST_ASIA:
        west = {
            "T2M": {"en": ("heat exposure and higher evaporative demand", "expand heat alerts, cooling access and water-efficient urban design"), "ru": ("тепловая нагрузка и рост испарения", "расширить предупреждения о жаре, доступ к охлаждению и водосберегающее планирование"), "zh": ("高温暴露与蒸发需求增强", "加强高温预警、公共降温设施和节水型城市设计")},
            "PRECTOTCORR": {"en": ("irregular rainfall and regional drought variability", "improve water storage, watershed monitoring and drought plans"), "ru": ("неустойчивые осадки и изменчивость засух", "улучшить водохранилища, мониторинг бассейнов и планы на случай засухи"), "zh": ("降水不稳定及区域干旱波动", "改善蓄水、流域监测和干旱应对预案")},
            "RootMoist_inst": {"en": ("water scarcity, irrigation demand and soil evaporation", "use soil-moisture scheduling, efficient irrigation and groundwater safeguards"), "ru": ("нехватка воды, спрос на орошение и испарение почвы", "планировать полив по влажности почвы, повышать эффективность и защищать подземные воды"), "zh": ("水资源紧张、灌溉需求和土壤蒸发", "按土壤水分安排灌溉，提高灌溉效率并保护地下水")},
            "Qs_acc": {"en": ("episodic heavy rain and rapid runoff from dry or urban surfaces", "map flood channels, restore infiltration and improve flash-flood warnings"), "ru": ("ливни и быстрый сток с сухих или городских поверхностей", "картировать зоны стока, восстанавливать инфильтрацию и предупреждать о внезапных паводках"), "zh": ("间歇性暴雨与干燥或城市地表的快速产流", "绘制洪水通道、恢复入渗并加强山洪预警")},
        }
        entry = west.get(code)
    if not entry and (country in SOUTH_SOUTHEAST_ASIA or country in EAST_ASIA):
        south = {
            "T2M": {
                "en": ("warming, heatwaves and changing monsoon timing", "heat action plans, urban cooling, drought-tolerant crops and early warning"),
                "ru": ("потепление, волны жары и изменение сроков муссона", "планы защиты от жары, охлаждение городов, засухоустойчивые культуры и раннее предупреждение"),
                "zh": ("变暖、热浪和季风时间变化", "制定高温行动计划，改善城市降温，推广耐旱作物并加强预警"),
            },
            "PRECTOTCORR": {
                "en": ("monsoon variability, intense rainfall and longer dry spells", "rainfall nowcasting, flood storage, wetland protection and drought planning"),
                "ru": ("изменчивость муссона, сильные ливни и более длительные сухие периоды", "краткосрочный прогноз осадков, накопление воды, защита водно-болотных угодий и планы засухи"),
                "zh": ("季风波动、强降雨和更长的干旱间隔", "加强降雨临近预报、蓄洪、湿地保护和干旱预案"),
            },
            "RootMoist_inst": {
                "en": ("heat-driven evapotranspiration, irrigation pressure and monsoon gaps", "efficient irrigation, soil-moisture monitoring, rainwater harvesting and groundwater safeguards"),
                "ru": ("испарение из-за жары, давление орошения и паузы муссона", "эффективное орошение, мониторинг влажности, сбор дождевой воды и защита подземных вод"),
                "zh": ("高温蒸散、灌溉压力和季风降水间歇", "提高灌溉效率，监测土壤水分，收集雨水并保护地下水"),
            },
            "SWE_inst": {
                "en": ("warming and declining snow/glacier storage in the Hindu Kush–Himalaya", "snow and glacier monitoring, seasonal flow forecasts and downstream flood planning"),
                "ru": ("потепление и сокращение запасов снега и ледников в Гиндукуше и Гималаях", "мониторинг снега и ледников, прогноз сезонного стока и планирование паводков"),
                "zh": ("兴都库什—喜马拉雅地区变暖以及积雪、冰川储水减少", "加强积雪冰川监测、季节径流预报和下游洪水规划"),
            },
            "Qs_acc": {
                "en": ("monsoon downpours, tropical storms, snowmelt and expanding impervious surfaces", "restore floodplains and mangroves, improve drainage and use impact-based warnings"),
                "ru": ("муссонные ливни, тропические штормы, таяние снега и рост непроницаемых поверхностей", "восстанавливать поймы и мангры, улучшать дренаж и применять предупреждения по последствиям"),
                "zh": ("季风暴雨、热带风暴、融雪以及不透水地面增加", "恢复洪泛区和红树林，改善排水，并采用基于影响的预警"),
            },
            "Qsb_acc": {
                "en": ("changes in infiltration, aquifer recharge and groundwater pumping", "protect recharge zones, regulate pumping and monitor groundwater quality"),
                "ru": ("изменения инфильтрации, пополнения водоносных горизонтов и откачки подземных вод", "защищать зоны пополнения, регулировать откачку и контролировать качество воды"),
                "zh": ("入渗、含水层补给和地下水开采变化", "保护补给区、规范开采并监测地下水质量"),
            },
        }
        entry = south.get(code)
        source_links = EAST_ASIA_SOURCE_LINKS if country in EAST_ASIA else SOUTH_SOUTHEAST_SOURCE_LINKS
    if not entry:
        return None
    lang_key = {0: "en", 1: "ru", 2: "zh"}[LANG_INDEX[lang]] if isinstance(LANG_INDEX.get(lang), int) else lang
    # LANG_INDEX maps language codes to positions; use the explicit code for clarity.
    lang_key = {"en": "en", "ru": "ru", "zh": "zh"}.get(lang, "en")
    drivers, response = entry[lang_key]
    focus = ROLE_VARIABLE_FOCUS.get(role, {}).get(code)
    if lang_key == "zh":
        anomaly = "首尾变化偏高" if direction == "high" else "首尾变化偏低" if direction == "low" else "变化接近稳定"
        focus_text = f"\n\n**当前变量重点：**{focus}。" if focus else ""
        return f"**数据线索：**{anomaly}。\n\n**可能原因：**{drivers}。\n\n**建议方案：**{response}。\n\n**角色建议：**{ROLE_ACTIONS.get(role, ROLE_ACTIONS['resident'])['zh']}。{focus_text}\n\n{UI['solution_note'][2]}"
    if lang_key == "ru":
        return f"**Сигнал данных:** изменение от первого к последнему году — {direction}.\n\n**Возможные факторы:** {drivers}.\n\n**Меры:** {response}.\n\n**Совет для роли:** {ROLE_ACTIONS.get(role, ROLE_ACTIONS['resident'])['ru']}\n\n{UI['solution_note'][1]}"
    return f"**Data clue:** the endpoint change is {direction}.\n\n**Possible drivers:** {drivers}.\n\n**Practical response:** {response}.\n\n**Role advice:** {ROLE_ACTIONS.get(role, ROLE_ACTIONS['resident'])['en']}\n\n{UI['solution_note'][0]}"

# Keep signed fluxes and Celsius temperature out of the non-negative check.
NONNEGATIVE = {"QV2M", "PRECTOTCORR", "TQV", "RootMoist_inst", "SoilMoi0_10cm_inst",
               "SoilMoi10_40cm_inst", "SoilMoi40_100cm_inst", "SoilMoi100_200cm_inst",
               "Qs_acc", "Qsb_acc", "Qsm_acc", "SWE_inst"}

MAP_NAMES = {"Lanka": "Sri Lanka", "Burma": "Myanmar", "Shape Yemen": "Yemen",
             "West Bank": "Palestine", "Timor-Leste": "East Timor"}

CLIMATE_CONTEXT = {
    "Kazakhstan": ("Temperate continental climate dominates. The north is colder, the south is warmer and drier, and the southeast has strong mountain influence.", "Преобладает умеренно-континентальный климат. Север холоднее, юг теплее и суше, а на юго-востоке сильно влияние гор.", "以温带大陆性气候为主。北部更冷，南部更温暖干燥，东南部受到明显山地影响。"),
    "Kyrgyzstan": ("Mountain climate dominates. Elevation creates strong local differences in temperature, snow and water availability.", "Преобладает горный климат. Высота создаёт сильные местные различия температуры, снега и доступности воды.", "以山地气候为主。海拔变化会造成气温、积雪和水资源条件的明显差异。"),
    "Tajikistan": ("Mountain and continental conditions dominate. Elevation and glaciers strongly shape snowmelt and runoff.", "Преобладают горные и континентальные условия. Высота и ледники сильно влияют на таяние снега и сток.", "以山地和大陆性气候为主。海拔与冰川会明显影响融雪和径流。"),
    "Turkmenistan": ("Arid desert and semi-arid conditions dominate. Heat, limited precipitation and strong evaporation are central features.", "Преобладают засушливые пустынные и полузасушливые условия. Главные особенности — жара, малое количество осадков и сильное испарение.", "以干旱荒漠和半干旱气候为主。高温、降水少和蒸发强是重要特征。"),
    "Uzbekistan": ("Arid and semi-arid continental conditions dominate, with strong seasonal temperature changes and mountain influence in the east.", "Преобладают засушливые и полузасушливые континентальные условия с сильной сезонностью температуры; на востоке важно влияние гор.", "以干旱、半干旱大陆性气候为主，气温季节变化明显，东部受到山地影响。"),
}


def climate_context(country, lang):
    values = CLIMATE_CONTEXT.get(country, (
        "This country contains geographic climate variation. Interpret the national average together with seasonality, terrain and the map.",
        "В стране есть географические климатические различия. Интерпретируйте среднее по стране вместе с сезонностью, рельефом и картой.",
        "该国存在地理气候差异。解读全国平均值时，还要结合季节性、地形和地图。"))
    return values[LANG_INDEX[lang]]


def apply_global_style():
    card_styles = {
        "T2M": "linear-gradient(135deg, rgba(255,248,235,.96), rgba(255,216,168,.78))",
        "QV2M": "linear-gradient(135deg, rgba(241,252,255,.96), rgba(173,224,239,.72))",
        "PRECTOTCORR": "linear-gradient(135deg, rgba(237,248,255,.96), rgba(142,202,230,.72))",
        "PS": "linear-gradient(135deg, rgba(248,250,252,.96), rgba(203,213,225,.78))",
        "TQV": "linear-gradient(135deg, rgba(239,250,255,.96), rgba(164,220,235,.72))",
        "RootMoist_inst": "linear-gradient(135deg, rgba(248,252,239,.96), rgba(188,214,139,.72))",
        "SoilMoi0_10cm_inst": "linear-gradient(135deg, rgba(251,248,235,.96), rgba(205,183,132,.68))",
        "SoilMoi10_40cm_inst": "linear-gradient(135deg, rgba(248,246,232,.96), rgba(187,165,116,.68))",
        "SoilMoi40_100cm_inst": "linear-gradient(135deg, rgba(246,244,230,.96), rgba(169,149,105,.68))",
        "SoilMoi100_200cm_inst": "linear-gradient(135deg, rgba(244,242,230,.96), rgba(151,133,94,.68))",
        "Evap_tavg": "linear-gradient(135deg, rgba(240,252,250,.96), rgba(137,214,199,.68))",
        "Qs_acc": "linear-gradient(135deg, rgba(238,249,255,.96), rgba(120,190,225,.68))",
        "Qsb_acc": "linear-gradient(135deg, rgba(239,247,252,.96), rgba(116,169,204,.68))",
        "Qsm_acc": "linear-gradient(135deg, rgba(247,252,255,.98), rgba(184,220,239,.78))",
        "SWE_inst": "linear-gradient(135deg, rgba(250,253,255,.98), rgba(204,232,246,.82))",
        "Qle_tavg": "linear-gradient(135deg, rgba(250,243,255,.96), rgba(202,172,226,.66))",
        "Qh_tavg": "linear-gradient(135deg, rgba(255,246,237,.96), rgba(235,178,131,.68))",
    }
    selectors = []
    for code, background in card_styles.items():
        selectors.append(f".st-key-metric_{code}, .st-key-comparison_{code} {{background:{background};}}")
    st.html("""
    <style>
    .stApp {
      background:
        radial-gradient(circle at 8% 9%, rgba(36,130,142,.14), transparent 24rem),
        radial-gradient(circle at 92% 16%, rgba(231,111,81,.12), transparent 23rem),
        repeating-radial-gradient(ellipse at 50% 115%, transparent 0 44px, rgba(35,82,96,.035) 45px 46px),
        linear-gradient(180deg, #f4faf8 0%, #edf5f2 46%, #f8f5ec 100%);
      background-attachment: fixed;
    }
    [data-testid="stHeader"] {background: rgba(244,250,248,.82); backdrop-filter: blur(10px);}
    .st-key-country_hero {
      background: linear-gradient(125deg, rgba(10,61,68,.96), rgba(24,106,114,.92) 55%, rgba(230,154,88,.88));
      border: 1px solid rgba(255,255,255,.28); border-radius: 24px; padding: 1.15rem 1.35rem;
      box-shadow: 0 18px 42px rgba(18,67,72,.18); color: white;
    }
    .st-key-country_hero h2, .st-key-country_hero h3, .st-key-country_hero p,
    .st-key-country_hero [data-testid="stMetricLabel"], .st-key-country_hero [data-testid="stMetricValue"] {color:white !important;}
    .country-map-svg {width:100%; min-height:260px; display:flex; align-items:center; justify-content:center;
      border-radius:18px; background:radial-gradient(circle at 50% 45%,rgba(255,255,255,.13),rgba(3,38,44,.18));
      overflow:hidden; padding:.7rem;}
    .country-map-svg svg {width:100%; height:270px; overflow:visible;}
    .st-key-group_atmosphere, .st-key-group_soil, .st-key-group_water, .st-key-group_energy {
      border-radius: 24px; padding: 1.1rem; margin: .8rem 0 1.3rem; border: 1px solid rgba(30,80,82,.10);
      box-shadow: 0 8px 28px rgba(26,73,75,.08);
    }
    .st-key-group_atmosphere {background:linear-gradient(145deg,rgba(255,248,235,.72),rgba(226,244,248,.72));}
    .st-key-group_soil {background:linear-gradient(145deg,rgba(246,249,232,.78),rgba(231,220,188,.68));}
    .st-key-group_water {background:linear-gradient(145deg,rgba(238,250,255,.80),rgba(220,243,239,.70));}
    .st-key-group_energy {background:linear-gradient(145deg,rgba(249,240,255,.76),rgba(255,238,220,.70));}
    [class*="st-key-metric_"], [class*="st-key-comparison_"] {
      border-radius: 20px; padding: .55rem; box-shadow: 0 7px 22px rgba(28,70,72,.08);
    }
    .quanthelix-signature {
      position: fixed; right: 1.15rem; bottom: .7rem; z-index: 9999;
      padding: .28rem .65rem; border-radius: 999px;
      color: rgba(35, 63, 68, .72); background: rgba(255,255,255,.58);
      border: 1px solid rgba(35,63,68,.12); backdrop-filter: blur(8px);
      font-size: 1.02rem; font-weight: 600; letter-spacing: .01em; pointer-events: none;
    }
    </style>
    """ + "<style>" + "\n".join(selectors) + "</style>")


@st.cache_data(show_spinner=False)
def load_map_feature(asset_path, country):
    import json
    path = Path(asset_path)
    if not path.exists():
        return None
    wanted = MAP_NAMES.get(country, country)
    with path.open(encoding="utf-8") as handle:
        collection = json.load(handle)
    return next((feature for feature in collection.get("features", [])
                 if feature.get("properties", {}).get("name") == wanted), None)


def temperature_color(value):
    if value is None or not np.isfinite(value):
        return "#88a8a8"
    if value < 0:
        return "#5aa9e6"
    if value < 10:
        return "#63c7b2"
    if value < 20:
        return "#f2c14e"
    if value < 30:
        return "#f28f3b"
    return "#d1495b"


def feature_svg(feature, fill):
    """Convert Polygon or MultiPolygon GeoJSON into a fitted inline SVG."""
    geometry = feature.get("geometry", {})
    kind, coordinates = geometry.get("type"), geometry.get("coordinates", [])
    polygons = [coordinates] if kind == "Polygon" else coordinates if kind == "MultiPolygon" else []
    rings = [ring for polygon in polygons for ring in polygon if ring]
    points = [point for ring in rings for point in ring if len(point) >= 2]
    if not points:
        return None
    xs, ys = [float(p[0]) for p in points], [float(p[1]) for p in points]
    min_x, max_x, min_y, max_y = min(xs), max(xs), min(ys), max(ys)
    width, height, padding = 660.0, 300.0, 18.0
    span_x, span_y = max(max_x - min_x, 1e-9), max(max_y - min_y, 1e-9)
    scale = min((width - 2 * padding) / span_x, (height - 2 * padding) / span_y)
    offset_x = (width - span_x * scale) / 2
    offset_y = (height - span_y * scale) / 2
    paths = []
    for ring in rings:
        transformed = [(offset_x + (float(p[0]) - min_x) * scale,
                        height - offset_y - (float(p[1]) - min_y) * scale) for p in ring]
        if transformed:
            paths.append("M " + " L ".join(f"{x:.1f},{y:.1f}" for x, y in transformed) + " Z")
    path_data = " ".join(paths)
    return f'''<div class="country-map-svg"><svg viewBox="0 0 {int(width)} {int(height)}"
      role="img" aria-label="Country outline"><defs><filter id="mapGlow" x="-30%" y="-30%" width="160%" height="160%">
      <feDropShadow dx="0" dy="7" stdDeviation="7" flood-color="#062f35" flood-opacity="0.55"/></filter></defs>
      <path d="{path_data}" fill="{fill}" fill-rule="evenodd" stroke="#ffffff" stroke-width="2"
      vector-effect="non-scaling-stroke" filter="url(#mapGlow)"/></svg></div>'''


def last_value(annuals, code):
    series = annuals.get(code, pd.Series(dtype=float)).dropna()
    return (int(series.index[-1]), float(series.iloc[-1])) if not series.empty else (None, None)


def render_country_hero(region, country, annuals, lang, app_dir):
    with st.container(key="country_hero"):
        left, right = st.columns([1.05, 1.25], gap="large")
        with left:
            st.subheader("🧭 " + label(country, COUNTRY_LABELS, lang))
            st.caption(label(region, REGION_LABELS, lang) + " · " + tr("hero_clues", lang))
            st.info(tr("climate_context", lang, description=climate_context(country, lang)))
            st.caption(" · ".join(f"[{title}]({url})" for title, url in report_links(country)))
            feature = load_map_feature(str(Path(app_dir) / "world_countries.geojson"), country)
            year, temperature = last_value(annuals, "T2M")
            if feature:
                svg = feature_svg(feature, temperature_color(temperature))
                if svg:
                    st.markdown(svg, unsafe_allow_html=True)
                else:
                    st.info(tr("map_unavailable", lang))
                if temperature is not None:
                    st.caption(tr("map_temperature", lang, year=year, value=fmt(temperature)))
                else:
                    st.caption(tr("map_temperature_missing", lang))
            else:
                st.info(tr("map_unavailable", lang))
        with right:
            st.subheader(tr("hero_clues", lang))
            clues = [("T2M", "latest_temperature"), ("PRECTOTCORR", "latest_precipitation"),
                     ("RootMoist_inst", "latest_soil")]
            for code, title in clues:
                year, value = last_value(annuals, code)
                if value is None:
                    st.metric(tr(title, lang), tr("clue_missing", lang))
                else:
                    st.metric(tr(title, lang) + f" · {year}", f"{fmt(value)} {unit(code, lang)}")
                    st.caption(data_context(annuals[code], code, lang).split("\n\n")[1])


def country_label(country_id, lang):
    region, country = country_id.split("/", 1)
    return f"{label(country, COUNTRY_LABELS, lang)} ({label(region, REGION_LABELS, lang)})"


def catalog_signature(data_dir):
    result = []
    for region in sorted(data_dir.iterdir()):
        if not region.is_dir() or region.name.startswith("."):
            continue
        for country in sorted(region.iterdir()):
            if not country.is_dir() or country.name.startswith("."):
                continue
            files = sorted(country.glob("*.csv"))
            if files:
                signature = tuple((str(p), p.stat().st_mtime_ns, p.stat().st_size) for p in files)
                result.append((region.name + "/" + country.name, signature))
    return tuple(result)


@st.cache_data(show_spinner=False)
def load_catalog(signature):
    catalog, shapes, problems = {}, {}, []
    for country_id, files in signature:
        records, errors = load_country(files)
        catalog[country_id] = {code: annual_values(rec["series"], code) for code, rec in records.items()}
        problems.extend((country_id, filename, error) for filename, error in errors)
        for code, rec in records.items():
            if rec["shape"]:
                shapes.setdefault((code, rec["shape"]), set()).add(country_id)
    blocked = set()
    for ids in shapes.values():
        if len(ids) > 1:
            blocked.update(ids)
    return catalog, sorted(blocked), problems


def years_text(years):
    years = sorted(int(y) for y in years)
    if not years:
        return "—"
    if years[-1] - years[0] + 1 == len(years):
        return str(years[0]) if len(years) == 1 else f"{years[0]}–{years[-1]}"
    return ", ".join(map(str, years))


def shared_annual(catalog, selected, code):
    series = {cid: catalog[cid].get(code, pd.Series(dtype=float)).dropna() for cid in selected}
    if not series or any(s.empty for s in series.values()):
        return pd.DataFrame()
    years = sorted(set.intersection(*(set(s.index) for s in series.values())))
    return pd.DataFrame({cid: s.reindex(years) for cid, s in series.items()}, index=years)


def save_table(table, filename, title, key):
    st.download_button(title, table.to_csv(index=False).encode("utf-8-sig"),
                       file_name=filename, mime="text/csv", key=key)


def comparison_chart(frame, code, lang):
    rows = [{"year": int(year), "value": float(value), "country": country_label(cid, lang)}
            for cid in frame.columns for year, value in frame[cid].items()]
    data = pd.DataFrame(rows)
    countries = [country_label(cid, lang) for cid in frame.columns]
    chart = alt.Chart(data).mark_line(point=True).encode(
        x=alt.X("year:O", title=tr("year", lang)),
        y=alt.Y("value:Q", title=unit(code, lang), scale=alt.Scale(zero=False)),
        color=alt.Color("country:N", title=tr("country_col", lang),
                        scale=alt.Scale(domain=countries, range=["#137c8b", "#db6d28", "#8064bc"][:len(countries)])),
        tooltip=[alt.Tooltip("country:N", title=tr("country_col", lang)),
                 alt.Tooltip("year:O", title=tr("year", lang)), alt.Tooltip("value:Q", title=tr("value", lang), format=".3f")],
    ).properties(height=270)
    st.altair_chart(chart, use_container_width=True)


def render_comparison(catalog, blocked, target, lang):
    st.subheader(tr("compare_tab", lang))
    st.write(tr("compare_intro", lang))
    options = list(catalog)
    saved = [c for c in st.session_state.get("saved_compare_countries", [target]) if c in options][:3]
    selected = st.multiselect(tr("compare_choose", lang), options, default=saved,
                              format_func=lambda cid: country_label(cid, lang), max_selections=3,
                              key="compare_countries", on_change=remember_selection,
                              args=("compare_countries", "saved_compare_countries"))
    if len(selected) > 3:
        st.error(tr("too_many", lang))
        return
    if any(cid in blocked for cid in selected):
        st.warning(tr("blocked_compare", lang))
        return
    if len(selected) < 2:
        st.info(tr("choose_two", lang))
        return
    export_rows = []
    for code in METRICS:
        with st.container(border=True, key=f"comparison_{code}"):
            st.subheader(name(code, lang))
            st.caption(EXPLANATIONS[code][lang] + " · " + unit(code, lang))
            missing = [cid for cid in selected if catalog[cid].get(code, pd.Series(dtype=float)).empty]
            frame = shared_annual(catalog, selected, code)
            if frame.empty:
                message = tr("missing_country", lang, countries=", ".join(country_label(cid, lang) for cid in missing)) if missing else tr("no_shared", lang)
                st.info(message)
                for cid in selected:
                    export_rows.append({tr("variable", lang): name(code, lang), tr("country_col", lang): country_label(cid, lang), tr("status", lang): message})
                continue
            st.caption(tr("shared_years", lang) + ": " + years_text(frame.index) + " · " + str(len(frame)) + " " + tr("n", lang))
            means = frame.mean()
            tol = max(1e-12, float(means.abs().max()) * 1e-10)
            details = "; ".join(f"{country_label(cid, lang)} — {fmt(means[cid])} {unit(code, lang)}" for cid in frame.columns)
            if float(means.max() - means.min()) <= tol:
                st.markdown(tr("comparison_tied", lang, details=details))
            else:
                high = ", ".join(country_label(c, lang) for c in means.index[np.isclose(means, means.max(), rtol=0, atol=tol)])
                low = ", ".join(country_label(c, lang) for c in means.index[np.isclose(means, means.min(), rtol=0, atol=tol)])
                st.markdown(tr("comparison_means", lang, details=details, high=high, low=low,
                               gap=fmt(means.max()-means.min()), unit=unit(code, lang)))
            st.caption(tr("comparison_context", lang))
            rows = []
            for cid in selected:
                s = summarize(frame[cid])
                row = {tr("country_col", lang): country_label(cid, lang), tr("mean", lang): s["mean"],
                       tr("change", lang): s["delta"], tr("highest", lang): s["high"],
                       tr("highest", lang)+" · "+tr("year", lang): s["high_years"],
                       tr("lowest", lang): s["low"], tr("lowest", lang)+" · "+tr("year", lang): s["low_years"],
                       tr("slope", lang): s["slope"],
                       tr("slope", lang)+" · "+tr("unit", lang): tr("per_year", lang, unit=unit(code, lang))}
                rows.append(row)
                export_rows.append({tr("variable", lang): name(code, lang), tr("unit", lang): unit(code, lang),
                                    tr("shared_years", lang): years_text(frame.index), tr("n", lang): len(frame), **row})
            st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")
            with st.expander(tr("compare_evidence", lang)):
                comparison_chart(frame, code, lang)
                display = frame.rename(columns={cid: country_label(cid, lang) for cid in selected})
                display.index.name = tr("year", lang)
                st.dataframe(display, width="stretch")
    if export_rows:
        save_table(pd.DataFrame(export_rows), "country_comparison.csv", tr("download_compare", lang), "compare_export")


def render_similarities(catalog, blocked, target, lang):
    st.subheader(tr("similar_tab", lang))
    st.write(tr("similar_intro", lang))
    st.info(tr("ranking_guide", lang))
    if target in blocked:
        st.warning(tr("selected_boundary", lang))
        return
    st.caption(tr("similar_coverage", lang))
    scopes = ["all_regions", "same_region"]
    chosen = st.session_state.get("saved_similarity_scope", "all_regions")
    scope = st.radio(tr("similar_scope", lang), scopes, index=scopes.index(chosen),
                     format_func=lambda v: tr(v, lang), key="similarity_scope", horizontal=True,
                     on_change=remember_selection, args=("similarity_scope", "saved_similarity_scope"))
    region = target.split("/", 1)[0]
    candidates = {cid: values for cid, values in catalog.items() if cid != target and cid not in blocked
                  and (scope == "all_regions" or cid.split("/", 1)[0] == region)}
    summary, details, exports = [], [], []
    for code in METRICS:
        reference = catalog[target].get(code, pd.Series(dtype=float))
        ranked = rank_similar(reference, {cid: values.get(code, pd.Series(dtype=float)) for cid, values in candidates.items()})
        row = {tr("variable", lang): name(code, lang), tr("unit", lang): unit(code, lang),
               tr("shared_years", lang): years_text(reference.index), tr("candidates", lang): len(ranked)}
        if ranked.empty:
            status = tr("insufficient", lang) if len(reference) < 3 else tr("no_candidates", lang)
            row[tr("closest", lang)] = status
            row[tr("farthest", lang)] = "—"
            exports.append({tr("variable", lang): name(code, lang), tr("status", lang): status})
        else:
            minimum, maximum = float(ranked.rmse.min()), float(ranked.rmse.max())
            tolerance = max(1e-12, maximum * 1e-10)
            nearest = ranked.loc[np.isclose(ranked.rmse, minimum, rtol=0, atol=tolerance), "country_id"]
            farthest = ranked.loc[np.isclose(ranked.rmse, maximum, rtol=0, atol=tolerance), "country_id"]
            row[tr("closest", lang)] = "; ".join(country_label(cid, lang) for cid in nearest)
            row[tr("closest", lang)+" · RMSE"] = minimum
            row[tr("farthest", lang)] = "; ".join(country_label(cid, lang) for cid in farthest)
            row[tr("farthest", lang)+" · RMSE"] = maximum
            localized = ranked.copy()
            if maximum - minimum <= tolerance:
                localized["relative_rmse"] = tr("rmse_equal", lang)
            else:
                percentile = localized["rmse"].rank(method="average", pct=True)
                localized["relative_rmse"] = [tr("rmse_low", lang) if rank <= 0.25 else
                                               tr("rmse_high", lang) if rank >= 0.75 else
                                               tr("rmse_middle", lang) for rank in percentile]
            localized["country_id"] = localized["country_id"].map(lambda cid: country_label(cid, lang))
            localized = localized.rename(columns={"country_id": tr("country_col", lang), "rmse": tr("distance", lang),
                                                   "correlation": tr("correlation", lang), "n": tr("n", lang),
                                                   "relative_rmse": tr("rmse_relative", lang)})
            details.append((code, localized, maximum-minimum <= tolerance))
            for record in localized.to_dict("records"):
                exports.append({tr("variable", lang): name(code, lang), tr("unit", lang): unit(code, lang),
                                tr("shared_years", lang): years_text(reference.index), **record})
        summary.append(row)
    st.dataframe(pd.DataFrame(summary), hide_index=True, width="stretch")
    st.caption(tr("ranking_note", lang))
    with st.expander(tr("ranking_details", lang)):
        for code, table, tied in details:
            st.subheader(name(code, lang))
            st.caption(unit(code, lang))
            if tied:
                st.info(tr("equal_distances", lang))
            st.dataframe(table, hide_index=True, width="stretch")
    save_table(pd.DataFrame(exports), "country_similarity.csv", tr("download_similar", lang), "similar_export")


def fitted_direction(annual, stat, lang):
    if not stat or stat["slope"] is None:
        return "—"
    if nearly_constant(annual.to_numpy()):
        return tr("flat", lang)
    if abs(stat["slope"]) <= _extension_numerical_tolerance(annual.to_numpy()) / max(1, annual.index[-1] - annual.index[0]):
        return tr("no_linear_direction", lang)
    return tr("up" if stat["slope"] > 0 else "down", lang)


def forecast_chart(annual, result, code, lang):
    observed = pd.DataFrame({"year": annual.index.astype(int), "value": annual.to_numpy()})
    projected = result["predictions"]
    y = alt.Y("value:Q", title=unit(code, lang), scale=alt.Scale(zero=False))
    historical = alt.Chart(observed).mark_line(point=True, color="#137c8b").encode(
        x=alt.X("year:O", title=tr("year", lang)), y=y,
        tooltip=[alt.Tooltip("year:O", title=tr("year", lang)), alt.Tooltip("value:Q", title=tr("actual", lang), format=".3f")])
    band = alt.Chart(projected).mark_area(color="#db6d28", opacity=0.17).encode(
        x="year:O", y=alt.Y("lower:Q", title=unit(code, lang), scale=alt.Scale(zero=False)), y2="upper:Q")
    intervals = alt.Chart(projected).mark_rule(color="#db6d28").encode(x="year:O", y="lower:Q", y2="upper:Q")
    estimates = alt.Chart(projected).mark_line(point=True, color="#db6d28", strokeDash=[5, 4]).encode(
        x="year:O", y="estimate:Q", tooltip=[alt.Tooltip("year:O", title=tr("year", lang)),
        alt.Tooltip("estimate:Q", title=tr("estimate", lang), format=".3f"),
        alt.Tooltip("lower:Q", title=tr("lower", lang), format=".3f"), alt.Tooltip("upper:Q", title=tr("upper", lang), format=".3f")])
    st.altair_chart((band + intervals + historical + estimates).properties(height=290), use_container_width=True)


def render_outlook(annuals, blocked, target, lang):
    st.subheader(tr("future_tab", lang))
    st.write(tr("outlook_intro", lang))
    if target in blocked:
        st.warning(tr("selected_boundary", lang))
        return
    rows, stats = [], {}
    for code in METRICS:
        annual = annuals.get(code, pd.Series(dtype=float))
        s = summarize(annual)
        stats[code] = s
        row = {tr("variable", lang): name(code, lang), tr("unit", lang): unit(code, lang),
               tr("shared_years", lang): years_text(annual.index), tr("n", lang): len(annual)}
        if s:
            row.update({tr("latest", lang): s["last"], tr("change", lang): s["delta"],
                        tr("decade_slope", lang): s["slope"]*10 if s["slope"] is not None else None,
                        tr("direction", lang): fitted_direction(annual, s, lang)})
        else:
            row[tr("direction", lang)] = tr("missing", lang)
        rows.append(row)
    for code in ["T2M", "PRECTOTCORR", "RootMoist_inst"]:
        s = stats[code]
        if s and s["slope"] is not None:
            st.markdown(tr("trend_sentence", lang, name=name(code, lang), direction=fitted_direction(annuals[code], s, lang),
                           slope=fmt(s["slope"]*10, True), rate=tr("per_decade", lang, unit=unit(code, lang)), start=s["start"], end=s["end"]))
    st.subheader(tr("trend_table", lang))
    st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")
    save_table(pd.DataFrame(rows), "observed_trends.csv", tr("download_trends", lang), "trends_export")
    st.subheader(tr("forecast_heading", lang))
    st.write(tr("forecast_intro", lang))
    st.caption(tr("interval_note", lang))
    horizon = st.select_slider(tr("horizon", lang), options=[1, 2, 3],
                               value=st.session_state.get("saved_horizon", 3), key="forecast_horizon",
                               on_change=remember_selection, args=("forecast_horizon", "saved_horizon"))
    st.caption(tr("backtest_note", lang))
    exported = []
    for code in METRICS:
        annual = annuals.get(code, pd.Series(dtype=float))
        result = future_estimates(annual, horizon)
        with st.container(border=True):
            st.subheader(name(code, lang))
            st.caption(unit(code, lang) + " · " + years_text(annual.index))
            if result["status"] != "ok":
                message = tr("forecast_" + result["status"], lang)
                st.info(message)
                exported.append({tr("variable", lang): name(code, lang), tr("status", lang): message})
                continue
            predicted = result["predictions"].copy()
            predicted["status"] = "conditional"
            if code in NONNEGATIVE:
                predicted.loc[predicted["lower"] < 0, "status"] = "physical_interval"
                predicted.loc[predicted["estimate"] < 0, "status"] = "physical_point"
            first = predicted.iloc[0]
            st.markdown(tr("forecast_sentence", lang, year=int(first.year), estimate=fmt(first.estimate),
                           lower=fmt(first.lower), upper=fmt(first.upper), unit=unit(code, lang)))
            if (predicted["status"] != "conditional").any():
                st.warning(tr("forecast_physical", lang))
            predicted["status"] = predicted["status"].map(lambda value: tr(value, lang))
            display = predicted.rename(columns={"year": tr("year", lang), "estimate": tr("estimate", lang),
                                                 "lower": tr("lower", lang), "upper": tr("upper", lang), "status": tr("status", lang)})
            st.dataframe(display, hide_index=True, width="stretch")
            for record in display.to_dict("records"):
                exported.append({tr("variable", lang): name(code, lang), tr("unit", lang): unit(code, lang),
                                 tr("baseline", lang): years_text(annual.index), **record})
            validation = rolling_validation(annual)
            st.caption(tr("backtest", lang))
            if validation.empty:
                st.caption(tr("no_validation", lang))
            else:
                linear_mae, baseline_mae = validation.linear_error.mean(), validation.persistence_error.mean()
                st.markdown(tr("validation_sentence", lang, folds=len(validation), linear=fmt(linear_mae), baseline=fmt(baseline_mae), unit=unit(code, lang)))
                if linear_mae >= baseline_mae:
                    st.warning(tr("validation_worse", lang))
            with st.expander(tr("forecast_evidence", lang)):
                forecast_chart(annual, result, code, lang)
                if not validation.empty:
                    st.dataframe(validation.rename(columns={"year": tr("year", lang), "actual": tr("actual", lang),
                                  "linear": tr("estimate", lang), "persistence": tr("persistence", lang),
                                  "linear_error": tr("linear_error", lang), "persistence_error": tr("persistence_error", lang)}),
                                  hide_index=True, width="stretch")
                residuals = pd.Series(result["model"]["residuals"], index=annual.index, name=tr("residual", lang))
                st.line_chart(residuals, x_label=tr("year", lang), y_label=unit(code, lang))
    if exported:
        save_table(pd.DataFrame(exported), "conditional_estimates.csv", tr("download_future", lang), "future_export")


@st.cache_resource
def unpack_data_archive(archive_path: str, modified_at: int) -> Path:
    destination = Path(tempfile.mkdtemp(prefix="earth_clues_data_"))
    with zipfile.ZipFile(archive_path) as archive:
        for member in archive.infolist():
            member_path = (destination / member.filename).resolve()
            if not member_path.is_relative_to(destination.resolve()):
                raise ValueError("Invalid path in data archive")
        archive.extractall(destination)
    return destination / "data"


def main():
    st.set_page_config(page_title="Earth Clues", page_icon="🌍", layout="wide")
    apply_global_style()
    st.html('<div class="quanthelix-signature">made by Quanthelix team, Zhanbota Erlan</div>')
    lang_choice = st.selectbox("Language / Язык / 语言", list(LANGUAGES), key="language")
    lang = LANGUAGES[lang_choice]
    text = TEXT[lang]
    st.title(text["title"])
    st.caption(text["subtitle"])
    app_dir = Path(__file__).resolve().parent
    data_dir = app_dir / "data"
    if not data_dir.is_dir():
        archive_path = app_dir / "earth_clues_data.zip"
        if archive_path.is_file():
            data_dir = unpack_data_archive(str(archive_path), archive_path.stat().st_mtime_ns)
    if not data_dir.is_dir():
        st.error(text["data_error"])
        return
    regions = sorted(p.name for p in data_dir.iterdir() if p.is_dir() and not p.name.startswith("."))
    if not regions:
        st.info(text["no_regions"])
        return
    st.subheader({"zh":"点击地图选择国家", "ru":"Выберите страну на карте", "en":"Choose a country on the map"}[lang])
    render_interactive_map(data_dir, lang)
    a, b = st.columns(2)
    if st.session_state.get("selected_region") not in regions:
        st.session_state["selected_region"] = "Central Asia" if "Central Asia" in regions else regions[0]
    region = a.selectbox(text["region"], regions, index=regions.index(st.session_state["selected_region"]),
                         format_func=lambda v: label(v, REGION_LABELS, lang), key="region",
                         on_change=remember_selection, args=("region", "selected_region"))
    countries = sorted(p.name for p in (data_dir / region).iterdir() if p.is_dir() and not p.name.startswith("."))
    if not countries:
        st.info(text["no_countries"])
        return
    if st.session_state.get("selected_country") not in countries:
        st.session_state["selected_country"] = countries[0]
    country = b.selectbox(text["country"], countries, index=countries.index(st.session_state["selected_country"]),
                          format_func=lambda v: label(v, COUNTRY_LABELS, lang), key="country",
                          on_change=remember_selection, args=("country", "selected_country"))
    selected_groups = st.multiselect(
        "Analyze modules / Анализируемые разделы / 分析模块",
        GROUP_ORDER,
        default=GROUP_ORDER,
        format_func=lambda v: GROUP_NAMES[lang][v],
        key="analysis_modules",
    )
    role = st.selectbox(
        "User role / Роль пользователя / 用户角色",
        list(ROLE_LABELS),
        format_func=lambda v: ROLE_LABELS[v][LANG_INDEX[lang]],
        key="user_role",
    )
    presentation_mode = st.checkbox("Presentation Mode / 演示模式", key="presentation_mode")
    if st.button(text["analyze"], type="primary", key="analyze"):
        st.session_state["analysis_target"] = (region, country)
    if st.session_state.get("analysis_target") != (region, country):
        st.info(tr("start", lang))
        return
    files = sorted((data_dir / region / country).glob("*.csv"))
    if not files:
        st.info(tr("empty_country", lang))
        return
    signature = tuple((str(p), p.stat().st_mtime_ns, p.stat().st_size) for p in files)
    with st.spinner(tr("loading", lang)):
        records, errors = load_country(signature)
    if errors:
        st.warning(tr("read_error", lang))
        with st.expander(tr("read_details", lang)):
            for filename, problem in errors:
                st.write(filename + ": " + problem)
    annuals = {code: annual_values(rec["series"], code) for code, rec in records.items()}
    stats = {code: summarize(values) for code, values in annuals.items()}
    render_country_hero(region, country, annuals, lang, Path(__file__).resolve().parent)
    top_risks = render_risk_summary(stats, annuals, selected_groups, lang)
    brief_labels = {
        "zh": ("角色", "三项主要数据线索", "行动建议", "说明", "最新值", "偏离标准差"),
        "ru": ("Роль", "Три основных сигнала", "Рекомендации", "Примечание", "Последнее значение", "стандартных отклонения"),
        "en": ("Role", "Three key data clues", "Recommended actions", "Note", "Latest value", "standard deviations"),
    }[lang]
    brief_lines = [f"# Earth Clues — {country}", f"{brief_labels[0]}: {ROLE_LABELS[role][LANG_INDEX[lang]]}", "", f"## {brief_labels[1]}"]
    for _, z, code, stat in top_risks:
        brief_lines.append(f"- {name(code, lang)}: {brief_labels[4]} {fmt(stat['last'])} {unit(code, lang)}; {brief_labels[5]} {abs(z):.2f}.")
    brief_lines += ["", f"## {brief_labels[2]}", ROLE_ACTIONS[role][lang], "", f"## {brief_labels[3]}", UI["solution_note"][LANG_INDEX[lang]]]
    brief_lines += ["", "## Sources", *(f"- {title}: {url}" for title, url in report_links(country))]
    st.download_button("下载一页式行动简报 / Download action brief", "\n".join(brief_lines), file_name=f"{country}_action_brief.md", mime="text/markdown")
    st.download_button({"zh":"下载一页式 PDF 行动简报", "ru":"Скачать краткий PDF-отчёт", "en":"Download one-page PDF action brief"}[lang],
                       action_brief_pdf(country, lang, role, top_risks, selected_groups),
                       file_name=f"{country}_action_brief.pdf", mime="application/pdf")
    if presentation_mode:
        st.success("演示模式：已保留地图、综合摘要和关键行动建议。关闭此选项可查看完整数据。")
        for code in ["T2M", "PRECTOTCORR", "RootMoist_inst"]:
            if code in stats and METRICS[code][0] in selected_groups:
                render_metric(code, records.get(code), annuals.get(code, pd.Series(dtype=float)), stats.get(code), lang, country, role)
        return
    st.caption(tr("count", lang, available=sum(v is not None for v in stats.values()), total=len(METRICS)))
    excluded = sorted(set(int(y) for code, rec in records.items() for y in rec["series"].index.year if y not in annuals[code].index and rec["series"].notna().any()))
    if excluded:
        st.caption(tr("excluded", lang, years=", ".join(map(str, excluded))))
    st.caption(tr("no_tests", lang))
    with st.spinner(tr("catalog_loading", lang)):
        catalog, blocked, catalog_errors = load_catalog(catalog_signature(data_dir))
    target = region + "/" + country
    if target in blocked:
        st.warning(tr("selected_boundary", lang))
    if st.session_state.get("comparison_target") != target:
        st.session_state["saved_compare_countries"] = [target]
        st.session_state.pop("compare_countries", None)
        st.session_state["comparison_target"] = target
    overview, robustness, comparison, similarities, outlook, methods = st.tabs([
        tr("overview", lang), tr("robustness", lang), tr("compare_tab", lang),
        tr("similar_tab", lang), tr("future_tab", lang), tr("methods", lang)])
    with overview:
        st.subheader(tr("headline", lang))
        headline_codes = [code for code in ["T2M", "PRECTOTCORR", "RootMoist_inst"]
                          if METRICS[code][0] in selected_groups]
        for code in headline_codes:
            s = stats.get(code)
            if s:
                st.markdown("- " + tr("summary", lang, name=name(code, lang), unit=unit(code, lang), start=s["start"], end=s["end"], first=fmt(s["first"]), last=fmt(s["last"]), high_years=s["high_years"], low_years=s["low_years"]))
        st.subheader(tr("all_metrics", lang))
        group_keys = {"Atmosphere & precipitation": "atmosphere", "Soil moisture": "soil",
                      "Snow & water movement": "water", "Energy exchange": "energy"}
        group_titles = {"Atmosphere & precipitation": "theme_atmosphere", "Soil moisture": "theme_soil",
                        "Snow & water movement": "theme_water", "Energy exchange": "theme_energy"}
        for group in GROUP_ORDER:
            if group not in selected_groups:
                continue
            with st.container(key="group_" + group_keys[group]):
                st.header(GROUP_NAMES[lang][group])
                st.caption(tr(group_titles[group], lang))
                columns = st.columns(2)
                for i, code in enumerate(v for v in METRICS if METRICS[v][0] == group):
                    with columns[i % 2]:
                        render_metric(code, records.get(code), annuals.get(code, pd.Series(dtype=float)), stats.get(code), lang, country, role)
        rows, report = [], ["# " + label(country, COUNTRY_LABELS, lang), tr("no_tests", lang)]
        for code in METRICS:
            s = stats.get(code)
            if not s:
                continue
            rows.append({tr("variable", lang): name(code, lang), tr("unit", lang): unit(code, lang),
                         tr("baseline", lang): f"{s['start']}–{s['end']}", tr("n", lang): s["n"],
                         tr("mean", lang): s["mean"], tr("change", lang): s["delta"],
                         tr("highest", lang): s["high"], tr("highest", lang)+" · "+tr("year", lang): s["high_years"],
                         tr("lowest", lang): s["low"], tr("lowest", lang)+" · "+tr("year", lang): s["low_years"],
                         tr("slope", lang): s["slope"], "R²": s["r2"]})
            report.extend(["## " + name(code, lang), explanation(code, s, lang),
                           f"{tr('highest', lang)}: {s['high_years']} · {fmt(s['high'])} {unit(code, lang)}",
                           f"{tr('lowest', lang)}: {s['low_years']} · {fmt(s['low'])} {unit(code, lang)}"])
            if s["slope"] is not None:
                report.append(tr("fit_note", lang, slope=fmt(s["slope"], True), rate_unit=tr("per_year", lang, unit=unit(code, lang)), r2=fmt(s["r2"])))
            if records[code]["source"]:
                report.append(f"[{tr('source', lang)}]({records[code]['source']})")
        if rows and target not in blocked:
            st.subheader(tr("export", lang))
            st.download_button(tr("download", lang), pd.DataFrame(rows).to_csv(index=False).encode("utf-8-sig"),
                               file_name=f"{country}_annual_summary.csv", mime="text/csv")
            st.download_button(tr("report", lang), "\n\n".join(report), file_name=f"{country}_findings_{lang}.md", mime="text/markdown")
    with robustness:
        render_robustness(annuals, lang)
    with comparison:
        if blocked:
            st.warning(tr("boundary_alert", lang, countries=", ".join(country_label(cid, lang) for cid in blocked)))
        render_comparison(catalog, blocked, target, lang)
    with similarities:
        if blocked:
            st.caption(tr("boundary_alert", lang, countries=", ".join(country_label(cid, lang) for cid in blocked)))
        render_similarities(catalog, blocked, target, lang)
    with outlook:
        render_outlook(annuals, blocked, target, lang)
    with methods:
        st.write(tr("method_body", lang))
        st.write(tr("new_methods", lang))
        if catalog_errors:
            st.warning(tr("catalog_errors", lang))
            with st.expander(tr("read_details", lang)):
                for cid, filename, error in catalog_errors:
                    st.write(country_label(cid, lang) + ": " + filename + " — " + error)
        st.markdown("[NIST: Student-t](https://www.itl.nist.gov/div898/handbook/eda/section3/eda3672.htm) · "
                    "[Penn State: Regression](https://online.stat.psu.edu/stat501/Lesson03) · "
                    "[Forecasting: Time-series cross-validation](https://otexts.com/fpp3/toolbox.html#time-series-cross-validation)")
        st.markdown("[MERRA-2](https://gmao.gsfc.nasa.gov/gmaoftp/mikeb/Harvey/MERRA2.README.pdf) · [GLDAS](https://ldas.gsfc.nasa.gov/gldas/model-output)")


if __name__ == "__main__":
    main()
