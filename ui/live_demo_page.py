"""
Live Demo Page - Interactive Clinical Risk Analysis
Provides step-by-step visualization of how the CLINICAL pipeline processes
patient data: base inputs -> 26 engineered features -> Clinical ML model ->
domain rules -> fused final decision.
"""

import streamlit as st
import pandas as pd
import time
from typing import Dict
from ui.decision_tree_viz import create_simple_decision_tree_flow, create_decision_tree_diagram
from config.field_definitions import FIELD_OPTIONS
from config.translations import get_field_name


# =========================================================
#  Bilingual Text
# =========================================================

TEXT = {
    'ar': {
        'page_title': 'العرض التفاعلي المباشر',
        'page_subtitle': 'أدخل بيانات المريض وشاهد كيف يعالجها المسار السريري خطوة بخطوة',
        'patient_data': 'بيانات المريض',
        'age': 'العمر',
        'gender': 'الجنس',
        'male': 'ذكر',
        'female': 'أنثى',
        'height_cm': 'الطول (سم)',
        'weight_kg': 'الوزن (كغم)',
        'smoking_status': 'حالة التدخين',
        'smoke_non': 'غير مدخن',
        'smoke_ex': 'مدخن سابق',
        'smoke_current': 'مدخن حالي',
        'workplace_type': 'نوع مكان العمل',
        'work_office': 'مكتب',
        'work_factory': 'مصنع',
        'environmental_hazards': 'المخاطر البيئية',
        'family_history': 'التاريخ العائلي',
        'yes': 'نعم',
        'no': 'لا',
        'run_analysis': 'تشغيل التحليل',
        'step1_title': 'الخطوة 1: توليد الخصائص المهندَسة',
        'step1_desc': 'اشتقاق 26 خاصية مهندَسة من البيانات الأساسية الثمانية',
        'step2_title': 'الخطوة 2: تنبؤ نموذج التعلم الآلي السريري',
        'step2_desc': 'تنبؤ النموذج باحتمالية الخطر القلبي الوعائي',
        'step3_title': 'الخطوة 3: محرك القواعد الطبية',
        'step3_desc': 'تطبيق القواعد الطبية المتخصصة على الخصائص المهندَسة',
        'step4_title': 'الخطوة 4: القرار النهائي المدمج',
        'step4_desc': 'دمج التعلم الآلي والقواعد في تقييم خطر شامل',
        'processing': 'جارٍ المعالجة...',
        'risk_level': 'مستوى الخطورة',
        'triggered_rules': 'القواعد المفعّلة',
        'active_features': 'الخصائص النشطة',
        'no_active_features': 'لا توجد خصائص نشطة ملحوظة',
        'features_generated': 'خاصية تم توليدها',
        'engineered_features': 'الخصائص المهندَسة (26)',
        'active_features_tab': 'الخصائص النشطة',
        'probability': 'الاحتمالية',
        'prediction': 'التنبؤ',
        'positive': 'إيجابي (خطر محتمل)',
        'negative': 'سلبي (طبيعي)',
        'confidence': 'الثقة',
        'model_source': 'مصدر النموذج',
        'rule_score': 'درجة القواعد',
        'final_risk': 'مستوى الخطر النهائي',
        'reasoning': 'التفسير',
        'processing_time': 'وقت المعالجة',
        'seconds': 'ثانية',
        'rules_count': 'عدد القواعد المفعّلة',
        'top_rules': 'أهم القواعد المفعّلة',
        'rule_id': 'معرّف القاعدة',
        'condition': 'الشرط',
        'weight': 'الوزن',
        'no_rules': 'لم تُفعَّل أي قاعدة طبية',
        'error_msg': 'حدث خطأ أثناء المعالجة',
        'all_steps_complete': 'اكتمل التحليل بنجاح',
        'analysis_pipeline': 'مسار التحليل',
        'decision_path': 'مسار شجرة القرار',
    },
    'en': {
        'page_title': 'Interactive Live Demo',
        'page_subtitle': 'Enter patient data and watch how the clinical pipeline processes it step-by-step',
        'patient_data': 'Patient Data',
        'age': 'Age',
        'gender': 'Gender',
        'male': 'Male',
        'female': 'Female',
        'height_cm': 'Height (cm)',
        'weight_kg': 'Weight (kg)',
        'smoking_status': 'Smoking Status',
        'smoke_non': 'Non-smoker',
        'smoke_ex': 'Ex-smoker',
        'smoke_current': 'Current smoker',
        'workplace_type': 'Workplace Type',
        'work_office': 'Office',
        'work_factory': 'Factory',
        'environmental_hazards': 'Environmental Hazards',
        'family_history': 'Family History',
        'yes': 'Yes',
        'no': 'No',
        'run_analysis': 'Run Analysis',
        'step1_title': 'Step 1: Engineered Features Generation',
        'step1_desc': 'Deriving 26 engineered features from the 8 base inputs',
        'step2_title': 'Step 2: Clinical ML Model Prediction',
        'step2_desc': 'Predicting cardiovascular risk probability',
        'step3_title': 'Step 3: Domain Rules Engine',
        'step3_desc': 'Applying specialized medical rules to the engineered features',
        'step4_title': 'Step 4: Fused Final Decision',
        'step4_desc': 'Combining ML and rules into a comprehensive risk assessment',
        'processing': 'Processing...',
        'risk_level': 'Risk Level',
        'triggered_rules': 'Triggered Rules',
        'active_features': 'Active Features',
        'no_active_features': 'No notable active features detected',
        'features_generated': 'features generated',
        'engineered_features': 'Engineered Features (26)',
        'active_features_tab': 'Active Features',
        'probability': 'Probability',
        'prediction': 'Prediction',
        'positive': 'Positive (Risk Likely)',
        'negative': 'Negative (Normal)',
        'confidence': 'Confidence',
        'model_source': 'Model Source',
        'rule_score': 'Rule Score',
        'final_risk': 'Final Risk Level',
        'reasoning': 'Reasoning',
        'processing_time': 'Processing Time',
        'seconds': 'seconds',
        'rules_count': 'Triggered Rules Count',
        'top_rules': 'Top Triggered Rules',
        'rule_id': 'Rule ID',
        'condition': 'Condition',
        'weight': 'Weight',
        'no_rules': 'No medical rules triggered',
        'error_msg': 'An error occurred during processing',
        'all_steps_complete': 'Analysis completed successfully',
        'analysis_pipeline': 'Analysis Pipeline',
        'decision_path': 'Decision Tree Path',
    }
}


# =========================================================
#  Risk Level Color Mapping
# =========================================================

RISK_COLORS = {
    'LOW': '#10B981',
    'Low': '#10B981',
    'MODERATE': '#F59E0B',
    'Medium': '#F59E0B',
    'LOW-MODERATE': '#84CC16',
    'MODERATE-HIGH': '#F97316',
    'HIGH': '#F97316',
    'High': '#F97316',
    'CRITICAL': '#EF4444',
}


def _get_risk_color(risk_level: str) -> str:
    """Return hex color for a given risk level string."""
    return RISK_COLORS.get(risk_level, '#6B7280')


def _risk_badge(label: str, risk_level: str) -> str:
    """Return an HTML badge for a risk level."""
    color = _get_risk_color(risk_level)
    return (
        f'<span style="background:{color}; color:white; padding:4px 14px; '
        f'border-radius:20px; font-weight:600; font-size:0.95rem;">'
        f'{label}</span>'
    )


# =========================================================
#  Page CSS
# =========================================================

PAGE_CSS = """
<style>
.demo-header {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    padding: 2rem 1.5rem;
    border-radius: 16px;
    margin-bottom: 1.5rem;
    color: white;
    text-align: center;
}
.demo-header h1 { margin: 0; font-size: 1.8rem; }
.demo-header p { margin: 0.4rem 0 0; opacity: 0.9; font-size: 1rem; }

.step-card {
    background: white;
    border-radius: 12px;
    padding: 1.2rem 1.5rem;
    margin-bottom: 1rem;
    border-left: 4px solid #667eea;
    box-shadow: 0 2px 8px rgba(0,0,0,0.06);
}
.step-card.success { border-left-color: #10B981; }
.step-card.error { border-left-color: #EF4444; }

.step-title {
    font-size: 1.1rem;
    font-weight: 700;
    color: #1E293B;
    margin-bottom: 0.3rem;
}
.step-desc {
    font-size: 0.85rem;
    color: #64748B;
    margin-bottom: 0.6rem;
}
.step-time {
    font-size: 0.78rem;
    color: #94A3B8;
}

.metric-row {
    display: flex;
    gap: 1rem;
    flex-wrap: wrap;
    margin: 0.6rem 0;
}
.metric-box {
    background: #F8FAFC;
    border-radius: 8px;
    padding: 0.7rem 1rem;
    flex: 1;
    min-width: 140px;
    text-align: center;
}
.metric-box .label {
    font-size: 0.78rem;
    color: #64748B;
    margin-bottom: 0.2rem;
}
.metric-box .value {
    font-size: 1.2rem;
    font-weight: 700;
    color: #1E293B;
}

.feature-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
    gap: 0.5rem;
    max-height: 320px;
    overflow-y: auto;
    padding: 0.5rem;
}
.feature-item {
    background: #F1F5F9;
    padding: 0.4rem 0.7rem;
    border-radius: 6px;
    font-size: 0.8rem;
    display: flex;
    justify-content: space-between;
}
.feature-item .fname { color: #475569; }
.feature-item .fval { font-weight: 600; color: #1E293B; }

.rules-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.85rem;
}
.rules-table th {
    background: #F1F5F9;
    padding: 0.5rem 0.7rem;
    text-align: left;
    font-weight: 600;
    color: #475569;
}
.rules-table td {
    padding: 0.5rem 0.7rem;
    border-bottom: 1px solid #F1F5F9;
    color: #1E293B;
}

.final-box {
    background: linear-gradient(135deg, #F8FAFC, #EFF6FF);
    border-radius: 12px;
    padding: 1.5rem;
    text-align: center;
    margin: 1rem 0;
    border: 1px solid #E2E8F0;
}
.final-box .final-level {
    font-size: 1.6rem;
    font-weight: 800;
    margin: 0.5rem 0;
}
</style>
"""


# =========================================================
#  Main Entry Point
# =========================================================

def render_live_demo_page(lang: str = 'en'):
    """
    Render the interactive live demo page.

    Args:
        lang: 'ar' or 'en' for bilingual support.
    """
    t = TEXT.get(lang, TEXT['en'])
    is_rtl = lang == 'ar'

    # Inject CSS
    st.markdown(PAGE_CSS, unsafe_allow_html=True)

    # Header
    st.markdown(
        f'<div class="demo-header">'
        f'<h1>{t["page_title"]}</h1>'
        f'<p>{t["page_subtitle"]}</p>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # ----- Input Form (8 base clinical fields) -----
    st.markdown(f'### {t["patient_data"]}')

    col1, col2, col3 = st.columns(3)

    with col1:
        age = st.slider(t['age'], 20, 90, 55, key='demo_age')
        gender_options = [t['male'], t['female']]
        gender_label = st.selectbox(t['gender'], gender_options, key='demo_gender')
        gender = 'male' if gender_label == t['male'] else 'female'
        family_options = [t['no'], t['yes']]
        family_label = st.selectbox(t['family_history'], family_options, key='demo_family')
        family_history = 'yes' if family_label == t['yes'] else 'no'

    with col2:
        height_cm = st.number_input(t['height_cm'], 120, 220, 170, key='demo_height')
        weight_kg = st.number_input(t['weight_kg'], 30, 200, 75, key='demo_weight')
        smoking_labels = [t['smoke_non'], t['smoke_ex'], t['smoke_current']]
        smoking_map = {
            t['smoke_non']: 'non-smoker',
            t['smoke_ex']: 'ex-smoker',
            t['smoke_current']: 'current smoker',
        }
        smoking_label = st.selectbox(t['smoking_status'], smoking_labels, key='demo_smoke')
        smoking_status = smoking_map[smoking_label]

    with col3:
        work_labels = [t['work_office'], t['work_factory']]
        work_map = {t['work_office']: 'office', t['work_factory']: 'factory'}
        work_label = st.selectbox(t['workplace_type'], work_labels, key='demo_work')
        workplace_type = work_map[work_label]
        environmental_hazards = st.multiselect(
            t['environmental_hazards'],
            FIELD_OPTIONS['environmental_hazards'],
            key='demo_hazards',
        )

    # Build base dict matching feature_deriver.derive (bmi auto-computed by derive)
    base = {
        'age': age,
        'gender': gender,
        'height_cm': height_cm,
        'weight_kg': weight_kg,
        'smoking_status': smoking_status,
        'workplace_type': workplace_type,
        'environmental_hazards': environmental_hazards,
        'family_history': family_history,
    }

    st.markdown('---')

    # ----- Run Analysis Button -----
    if st.button(t['run_analysis'], type='primary', use_container_width=True, key='demo_run'):
        _run_pipeline(base, t, lang)


# =========================================================
#  Pipeline Execution
# =========================================================

def _run_pipeline(base: Dict, t: Dict, lang: str):
    """Run the clinical domain pipeline and render the four result steps."""

    progress = st.progress(0, text=t['processing'])

    start = time.time()
    try:
        from engine.domain_pipeline import domain_pipeline
        progress.progress(40, text=f"{t['processing']} {t['step2_title']}")
        result = domain_pipeline.assess(base)
        elapsed = time.time() - start
        ok = True
        error = ''
    except Exception as e:
        elapsed = time.time() - start
        result = {}
        ok = False
        error = str(e)

    progress.progress(100, text=t['all_steps_complete'])

    st.markdown('---')

    if not ok:
        st.error(f"{t['error_msg']}: {error}")
        return

    # ── Render results ──
    _render_step1(result, elapsed, t, lang)
    _render_step2(result, elapsed, t, lang)
    _render_step3(result, elapsed, t, lang)
    _render_step4(result, elapsed, t, lang)


# =========================================================
#  Step Renderers
# =========================================================

def _render_step1(result: Dict, elapsed: float, t: Dict, lang: str):
    """Render Step 1: Engineered Features (26)."""
    with st.expander(t['step1_title'], expanded=True):
        st.caption(t['step1_desc'])
        st.caption(f"{t['processing_time']}: {elapsed:.4f} {t['seconds']}")

        feats = result.get('derived_features', {})
        active = result.get('active_features', [])

        st.metric(t['features_generated'], f'{len(feats)}')

        tab1, tab2 = st.tabs([t['engineered_features'], t['active_features_tab']])

        with tab1:
            _render_feature_grid(feats, list(feats.keys()))
        with tab2:
            if active:
                _render_feature_grid(feats, active)
            else:
                st.info(t['no_active_features'])


def _render_feature_grid(feats: Dict, names: list):
    """Render a grid of feature name-value pairs."""
    if not names:
        st.info('---')
        return
    html = '<div class="feature-grid">'
    for name in names:
        val = feats.get(name)
        if isinstance(val, float):
            val_str = f'{val:.4f}' if abs(val) < 10 else f'{val:.2f}'
        else:
            val_str = str(val)
        html += (
            f'<div class="feature-item">'
            f'<span class="fname">{name}</span>'
            f'<span class="fval">{val_str}</span>'
            f'</div>'
        )
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)


def _render_step2(result: Dict, elapsed: float, t: Dict, lang: str):
    """Render Step 2: Clinical ML prediction."""
    with st.expander(t['step2_title'], expanded=True):
        st.caption(t['step2_desc'])

        ml = result.get('ml', {})
        probability = ml.get('probability', 0.0)
        prediction = ml.get('prediction', 'Unknown')
        confidence = ml.get('confidence', 0.0)
        risk_level = ml.get('risk_level', 'MODERATE')
        source = ml.get('source', 'Unknown')

        c1, c2, c3 = st.columns(3)
        with c1:
            prob_color = _get_risk_color(risk_level)
            st.markdown(
                f'<div class="metric-box">'
                f'<div class="label">{t["probability"]}</div>'
                f'<div class="value" style="color:{prob_color};">{probability:.1%}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )
        with c2:
            pred_label = t['positive'] if prediction == 'Positive' else t['negative']
            pred_color = '#EF4444' if prediction == 'Positive' else '#10B981'
            st.markdown(
                f'<div class="metric-box">'
                f'<div class="label">{t["prediction"]}</div>'
                f'<div class="value" style="color:{pred_color};">{pred_label}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )
        with c3:
            st.markdown(
                f'<div class="metric-box">'
                f'<div class="label">{t["confidence"]}</div>'
                f'<div class="value">{confidence:.1%}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

        # Probability bar
        st.progress(min(probability, 1.0))

        # Risk level + source
        st.markdown(
            f'**{t["risk_level"]}:** {_risk_badge(risk_level, risk_level)}',
            unsafe_allow_html=True,
        )
        st.caption(f'{t["model_source"]}: {source}')


def _render_step3(result: Dict, elapsed: float, t: Dict, lang: str):
    """Render Step 3: Domain Rules Engine."""
    with st.expander(t['step3_title'], expanded=True):
        st.caption(t['step3_desc'])

        rules = result.get('rules', {})
        triggered = rules.get('triggered', [])
        rule_score = rules.get('score', 0.0)
        rule_level = rules.get('risk_level', 'Low')

        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown(
                f'**{t["risk_level"]}:** {_risk_badge(rule_level, rule_level)}',
                unsafe_allow_html=True,
            )
        with c2:
            st.metric(t['rules_count'], len(triggered))
        with c3:
            st.metric(t['rule_score'], f'{rule_score:.2f}')

        if triggered:
            st.markdown(f'**{t["top_rules"]}**')
            top = triggered[:8]
            table_html = '<table class="rules-table"><tr>'
            table_html += f'<th>{t["rule_id"]}</th><th>{t["condition"]}</th><th>{t["weight"]}</th>'
            table_html += '</tr>'
            for r in top:
                table_html += (
                    f'<tr><td>{r.get("rule_id", "")}</td>'
                    f'<td style="font-family:monospace;font-size:0.8rem;">{r.get("condition", "")}</td>'
                    f'<td>{r.get("weight", 0):.2f}</td></tr>'
                )
            table_html += '</table>'
            st.markdown(table_html, unsafe_allow_html=True)
        else:
            st.info(t['no_rules'])


def _render_step4(result: Dict, elapsed: float, t: Dict, lang: str):
    """Render Step 4: Fused Final Decision."""
    with st.expander(t['step4_title'], expanded=True):
        st.caption(t['step4_desc'])

        decision = result.get('decision', {})
        ml = result.get('ml', {})
        rules = result.get('rules', {})

        risk_level = decision.get('final_risk_level', 'MODERATE')
        confidence = decision.get('confidence', 0.0)
        reasoning = decision.get('reasoning', '')

        color = _get_risk_color(risk_level)

        # Final decision box
        st.markdown(
            f'<div class="final-box">'
            f'<div class="label" style="font-size:0.9rem;color:#64748B;">{t["final_risk"]}</div>'
            f'<div class="final-level" style="color:{color};">{risk_level}</div>'
            f'<div style="margin:0.3rem 0;">{t["confidence"]}: {confidence:.0%}</div>'
            f'<div style="font-size:0.9rem; color:#475569;">{reasoning}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

        # Sources breakdown
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f'**{t["step2_title"]}**')
            st.markdown(f'- {t["probability"]}: {ml.get("probability", 0.0):.1%}')
            st.markdown(f'- {t["risk_level"]}: {ml.get("risk_level", "N/A")}')
        with c2:
            st.markdown(f'**{t["step3_title"]}**')
            st.markdown(f'- {t["risk_level"]}: {rules.get("risk_level", "N/A")}')
            st.markdown(f'- {t["triggered_rules"]}: {len(rules.get("triggered", []))}')

        # Decision tree path (from pipeline)
        tree_path = result.get('decision_tree_path', [])
        if tree_path:
            st.markdown(f'**{t["decision_path"]}**')
            for label, value in tree_path:
                st.markdown(f'- **{label}:** {value}')

        # Build a compatibility dict for the decision-tree visualizations,
        # which expect the FinalDecisionEngine output shape.
        final_compat = {
            'final_risk_level': risk_level,
            'confidence': confidence,
            'sources': {
                'ml_model': {
                    'probability': ml.get('probability', 0.0),
                    'prediction': ml.get('prediction', 'N/A'),
                    'risk_level': ml.get('risk_level', 'N/A'),
                },
                'domain_rules': {
                    'risk_level': rules.get('risk_level', 'N/A'),
                    'triggered_rules': len(rules.get('triggered', [])),
                },
            },
            'metadata': {},
        }

        # Decision Tree Visualization
        tree_title = 'مخطط شجرة القرار' if lang == 'ar' else 'Decision Tree Diagram'
        st.markdown(f'**{tree_title}**')
        try:
            tree_fig = create_simple_decision_tree_flow(final_compat)
            st.plotly_chart(tree_fig, use_container_width=True)
        except Exception as e:
            st.warning(f"Decision Tree: {e}")

        # Detailed Decision Tree
        detail_title = 'شجرة القرار التفصيلية' if lang == 'ar' else 'Detailed Decision Tree'
        st.markdown(f'**{detail_title}**')
        try:
            detail_fig = create_decision_tree_diagram(final_compat)
            st.plotly_chart(detail_fig, use_container_width=True)
        except Exception as e:
            st.warning(f"Detailed Tree: {e}")
