"""
Ablation Study Plots
Reads results from ablation_results.json and generates charts

Usage:
    python result_ablation_study/plot_ablation.py
"""

import json
import os
import sys
from pathlib import Path

# Add project path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import plotly.graph_objects as go
from plotly.subplots import make_subplots

# ═══════════════════════════════════════════════════════
#  Colors (same as comparison_page.py)
# ═══════════════════════════════════════════════════════

COLORS = {
    'proposed': '#34D399',
    'proposed_dark': '#059669',
    'traditional': '#5B8DEF',
    'danger': '#EF4444',
    'warning': '#F59E0B',
    'success': '#10B981',
    'accent1': '#8B5CF6',
    'accent2': '#EC4899',
    'accent3': '#F97316',
    'accent4': '#06B6D4',
    'text': '#1E293B',
    'text_light': '#64748B',
    'grid': '#F1F5F9',
}

EXPERIMENT_COLORS = [
    COLORS['proposed'],    # Full System (Baseline)
    COLORS['danger'],      # Without ML
    COLORS['accent1'],     # Without Domain Rules
    COLORS['warning'],     # Base Features Only
    COLORS['accent4'],     # Without Framingham
    COLORS['traditional'], # Simple IF/ELSE
]

# Short names to avoid text overlap on charts
SHORT_NAMES = {
    '1. Full System (Baseline)': 'Full System',
    '2. Without ML Model': 'No ML Model',
    '3. Without Domain Rules': 'No Domain Rules',
    '4. Base Features Only (12)': 'Base Features',
    '5. Without Framingham Score': 'No Framingham',
    '6. Simple IF/ELSE (Traditional)': 'Simple Rules',
}

CHART_LAYOUT = dict(
    plot_bgcolor='rgba(0,0,0,0)',
    paper_bgcolor='white',
    font=dict(family="Segoe UI, Tahoma, sans-serif", color=COLORS['text']),
    hoverlabel=dict(
        bgcolor="white", font_size=13,
        font_family="Segoe UI, Tahoma, sans-serif",
        bordercolor="#e2e8f0"
    ),
    margin=dict(t=100, b=60, l=60, r=40),
)

# ═══════════════════════════════════════════════════════
#  Load Data
# ═══════════════════════════════════════════════════════

def load_results():
    results_path = Path(__file__).parent / 'ablation_results.json'
    with open(results_path, 'r', encoding='utf-8') as f:
        return json.load(f)


# ═══════════════════════════════════════════════════════
#  1. Accuracy & F1 Comparison for All Experiments
# ═══════════════════════════════════════════════════════

def plot_accuracy_comparison(data, output_dir):
    """Bar chart: Accuracy & F1 for all experiments"""
    experiments = data['experiments']
    names = [SHORT_NAMES.get(e['name'], e['name']) for e in experiments]
    accuracies = [e['accuracy'] for e in experiments]
    f1_scores = [e['f1_score'] for e in experiments]
    baseline_acc = experiments[0]['accuracy']

    fig = go.Figure()

    # Accuracy bars
    fig.add_trace(go.Bar(
        x=names, y=accuracies,
        name='Accuracy',
        marker=dict(color=EXPERIMENT_COLORS, cornerradius=6,
                    line=dict(width=[3]+[0]*5,
                              color=[COLORS['proposed_dark']]+['rgba(0,0,0,0)']*5)),
        text=[f'{a:.1f}%' for a in accuracies],
        textposition='outside',
        textfont=dict(size=13, color=COLORS['text']),
        width=0.35, offset=-0.2,
    ))

    # F1 bars
    fig.add_trace(go.Bar(
        x=names, y=f1_scores,
        name='F1-Score',
        marker=dict(
            color=[c.replace(')', ',0.5)').replace('rgb', 'rgba') if 'rgb' in c
                   else f'rgba({int(c[1:3],16)},{int(c[3:5],16)},{int(c[5:7],16)},0.5)'
                   for c in EXPERIMENT_COLORS],
            cornerradius=6,
        ),
        text=[f'{f:.1f}%' for f in f1_scores],
        textposition='outside',
        textfont=dict(size=12, color=COLORS['text_light']),
        width=0.35, offset=0.2,
    ))

    # Baseline reference line
    fig.add_hline(y=baseline_acc, line_dash="dash", line_color=COLORS['proposed'],
                  line_width=2, annotation_text=f"Baseline: {baseline_acc}%",
                  annotation_position="top right",
                  annotation_font=dict(size=12, color=COLORS['proposed_dark']))

    acc_layout = dict(CHART_LAYOUT)
    acc_layout['margin'] = dict(t=150, b=80, l=60, r=40)
    fig.update_layout(
        **acc_layout,
        title=dict(
            text=(f"<b>Ablation Study</b><br>"
                  f"<span style='font-size:13px;color:{COLORS['text_light']}'>"
                  f"Impact of Each Component on System Performance</span>"),
            x=0.5, font=dict(size=18)
        ),
        barmode='group',
        yaxis=dict(range=[0, 95], dtick=10, gridcolor=COLORS['grid'], title='%'),
        xaxis=dict(tickfont=dict(size=11), tickangle=-20),
        height=600,
        legend=dict(orientation="h", yanchor="bottom", y=-0.2,
                    xanchor="center", x=0.5, font=dict(size=13)),
    )

    path = output_dir / 'ablation_accuracy_comparison.html'
    fig.write_html(str(path))
    print(f"[+] Saved: {path}")

    # Save as image too
    try:
        img_path = output_dir / 'ablation_accuracy_comparison.png'
        fig.write_image(str(img_path), width=1200, height=600, scale=2)
        print(f"[+] Saved: {img_path}")
    except Exception as e:
        print(f"[!] Could not save PNG (install kaleido): {e}")

    return fig


# ═══════════════════════════════════════════════════════
#  2. Component Contribution (Horizontal Bar)
# ═══════════════════════════════════════════════════════

def plot_contribution(data, output_dir):
    """Horizontal bar: contribution of each component (drop when removed)"""
    experiments = data['experiments']
    baseline_acc = experiments[0]['accuracy']

    # Skip baseline and simple rules
    components = experiments[1:-1]
    names = [SHORT_NAMES.get(e['name'], e['name']) for e in components]
    drops = [max(baseline_acc - e['accuracy'], 0) for e in components]
    colors = EXPERIMENT_COLORS[1:-1]

    # Sort by drop
    sorted_data = sorted(zip(names, drops, colors), key=lambda x: x[1], reverse=True)
    names = [d[0] for d in sorted_data]
    drops = [d[1] for d in sorted_data]
    colors = [d[2] for d in sorted_data]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=names, x=drops, orientation='h',
        marker=dict(color=colors, cornerradius=6),
        text=[f'-{d:.1f}%' for d in drops],
        textposition='outside',
        textfont=dict(size=14, color=COLORS['text']),
        hovertemplate='%{y}<br>Drop: %{x:.1f}%<extra></extra>',
    ))

    layout_kwargs = dict(CHART_LAYOUT)
    layout_kwargs['margin'] = dict(t=100, b=60, l=180, r=120)
    fig.update_layout(
        **layout_kwargs,
        title=dict(text="<b>Component Contribution to Performance</b>", x=0.5, font=dict(size=18)),
        xaxis=dict(title='Accuracy Drop When Removed (%)', gridcolor=COLORS['grid']),
        yaxis=dict(tickfont=dict(size=12)),
        height=400, showlegend=False,
    )

    path = output_dir / 'ablation_contribution.html'
    fig.write_html(str(path))
    print(f"[+] Saved: {path}")

    try:
        img_path = output_dir / 'ablation_contribution.png'
        fig.write_image(str(img_path), width=1100, height=400, scale=2)
        print(f"[+] Saved: {img_path}")
    except Exception:
        pass

    return fig


# ═══════════════════════════════════════════════════════
#  3. TPR vs FPR (ROC-style)
# ═══════════════════════════════════════════════════════

def plot_roc(data, output_dir):
    """Scatter: TPR vs FPR for each experiment"""
    experiments = data['experiments']
    symbols = ['star', 'circle', 'diamond', 'square', 'triangle-up', 'x']

    fig = go.Figure()

    # Random classifier line
    fig.add_trace(go.Scatter(
        x=[0, 1], y=[0, 1], mode='lines',
        line=dict(dash='dash', color=COLORS['text_light'], width=1.5),
        name='Random Classifier', showlegend=True, hoverinfo='skip',
    ))

    for i, exp in enumerate(experiments):
        short = SHORT_NAMES.get(exp['name'], exp['name'])
        tpr = exp['recall'] / 100
        fpr = 1 - (exp['specificity'] / 100)
        fig.add_trace(go.Scatter(
            x=[fpr], y=[tpr], mode='markers',
            marker=dict(size=16, color=EXPERIMENT_COLORS[i], symbol=symbols[i],
                        line=dict(width=1.5, color='white')),
            name=short,
            hovertemplate=(f"<b>{short}</b><br>"
                           f"TPR: {tpr:.3f}<br>FPR: {fpr:.3f}<extra></extra>"),
        ))

    fig.update_layout(
        **CHART_LAYOUT,
        title=dict(
            text=(f"<b>TPR vs FPR — Ablation Experiments</b><br>"
                  f"<span style='font-size:13px;color:{COLORS['text_light']}'>"
                  f"Closer to upper-left corner = better performance</span>"),
            x=0.5, font=dict(size=18),
        ),
        xaxis=dict(title='FPR (1 - Specificity)', range=[-0.05, 1.1], dtick=0.2,
                   gridcolor=COLORS['grid']),
        yaxis=dict(title='TPR (Recall)', range=[-0.05, 1.1], dtick=0.2,
                   gridcolor=COLORS['grid']),
        height=550,
        legend=dict(orientation='v', yanchor='bottom', y=0.02,
                    xanchor='left', x=0.02, font=dict(size=11),
                    bgcolor='rgba(255,255,255,0.8)'),
    )

    path = output_dir / 'ablation_roc.html'
    fig.write_html(str(path))
    print(f"[+] Saved: {path}")

    try:
        img_path = output_dir / 'ablation_roc.png'
        fig.write_image(str(img_path), width=1000, height=550, scale=2)
        print(f"[+] Saved: {img_path}")
    except Exception:
        pass

    return fig


# ═══════════════════════════════════════════════════════
#  4. Cross-Validation (5 Folds)
# ═══════════════════════════════════════════════════════

def plot_cv_folds(data, output_dir):
    """Bar chart: 5-Fold CV results for Full System"""
    folds = data['experiments'][0]['fold_details']
    fold_names = [f"Fold {i+1}" for i in range(len(folds))]
    accuracies = [f['accuracy'] for f in folds]
    f1_scores = [f['f1_score'] for f in folds]
    avg_acc = sum(accuracies) / len(accuracies)
    avg_f1 = sum(f1_scores) / len(f1_scores)

    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=fold_names, y=accuracies,
        name='Accuracy',
        marker=dict(color=COLORS['proposed'], cornerradius=6),
        text=[f'{a:.1f}%' for a in accuracies],
        textposition='outside', textfont=dict(size=13, color=COLORS['text']),
        width=0.35, offset=-0.2,
    ))

    fig.add_trace(go.Bar(
        x=fold_names, y=f1_scores,
        name='F1-Score',
        marker=dict(color=COLORS['accent1'], cornerradius=6),
        text=[f'{f:.1f}%' for f in f1_scores],
        textposition='outside', textfont=dict(size=13, color=COLORS['text']),
        width=0.35, offset=0.2,
    ))

    # Average lines
    fig.add_hline(y=avg_acc, line_dash="dot", line_color=COLORS['proposed'],
                  line_width=2, annotation_text=f"Avg Acc: {avg_acc:.1f}%",
                  annotation_position="top left",
                  annotation_font=dict(size=11, color=COLORS['proposed_dark']))
    fig.add_hline(y=avg_f1, line_dash="dot", line_color=COLORS['accent1'],
                  line_width=2, annotation_text=f"Avg F1: {avg_f1:.1f}%",
                  annotation_position="bottom right",
                  annotation_font=dict(size=11, color=COLORS['accent1']))

    fig.update_layout(
        **CHART_LAYOUT,
        title=dict(
            text=f"<b>5-Fold Cross-Validation — Full System</b>",
            x=0.5, font=dict(size=18)),
        barmode='group',
        yaxis=dict(range=[55, 90], dtick=5, gridcolor=COLORS['grid'], title='%'),
        height=480,
        legend=dict(orientation="h", yanchor="bottom", y=1.05,
                    xanchor="center", x=0.5, font=dict(size=13)),
    )

    path = output_dir / 'ablation_cv_folds.html'
    fig.write_html(str(path))
    print(f"[+] Saved: {path}")

    try:
        img_path = output_dir / 'ablation_cv_folds.png'
        fig.write_image(str(img_path), width=1000, height=480, scale=2)
        print(f"[+] Saved: {img_path}")
    except Exception:
        pass

    return fig


# ═══════════════════════════════════════════════════════
#  5. Confusion Matrix
# ═══════════════════════════════════════════════════════

def plot_confusion_matrix(data, output_dir):
    """Confusion matrix: Full System vs Simple Rules"""
    ds = data['dataset']
    pos, neg = ds['high_risk'], ds['low_risk']

    full = data['experiments'][0]
    simple = data['experiments'][-1]

    fs_tp = round(pos * full['recall'] / 100)
    fs_fn = pos - fs_tp
    fs_tn = round(neg * full['specificity'] / 100)
    fs_fp = neg - fs_tn

    sr_tp = round(pos * simple['recall'] / 100)
    sr_fn = pos - sr_tp
    sr_tn = round(neg * simple['specificity'] / 100)
    sr_fp = neg - sr_tn

    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=["<b>Full System</b>", "<b>Simple Rules (Traditional)</b>"],
        horizontal_spacing=0.12,
    )

    for col, (tp, fn, fp, tn) in enumerate([
        (fs_tp, fs_fn, fs_fp, fs_tn),
        (sr_tp, sr_fn, sr_fp, sr_tn),
    ], 1):
        color_vals = [[1, 0], [0, 1]]
        colorscale = [[0.0, '#FEE2E2'], [0.5, '#FFFFFF'], [1.0, '#D1FAE5']]

        annotations_text = [
            [f"TP<br><b>{tp}</b>", f"FN<br><b>{fn}</b>"],
            [f"FP<br><b>{fp}</b>", f"TN<br><b>{tn}</b>"],
        ]

        fig.add_trace(go.Heatmap(
            z=color_vals, text=annotations_text,
            texttemplate="%{text}",
            textfont=dict(size=16, family='Segoe UI'),
            x=['Predicted: High', 'Predicted: Low'],
            y=['Actual: High', 'Actual: Low'],
            colorscale=colorscale, showscale=False,
            xgap=3, ygap=3,
        ), row=1, col=col)

    fig.update_layout(
        **CHART_LAYOUT,
        title=dict(
            text="<b>Confusion Matrix — Full System vs Simple Rules</b>",
            x=0.5, font=dict(size=18)),
        height=420,
    )
    fig.update_yaxes(autorange='reversed')

    path = output_dir / 'ablation_confusion_matrix.html'
    fig.write_html(str(path))
    print(f"[+] Saved: {path}")

    try:
        img_path = output_dir / 'ablation_confusion_matrix.png'
        fig.write_image(str(img_path), width=1100, height=420, scale=2)
        print(f"[+] Saved: {img_path}")
    except Exception:
        pass

    return fig


# ═══════════════════════════════════════════════════════
#  6. Radar Chart (Comprehensive Comparison)
# ═══════════════════════════════════════════════════════

def plot_radar(data, output_dir):
    """Radar chart: Full System vs Simple Rules across all metrics"""
    full = data['experiments'][0]
    simple = data['experiments'][-1]

    metrics = ['Accuracy', 'F1-Score', 'Precision', 'Recall', 'Specificity']
    full_vals = [full['accuracy'], full['f1_score'], full['precision'],
                 full['recall'], full['specificity']]
    simple_vals = [simple['accuracy'], simple['f1_score'], simple['precision'],
                   simple['recall'], simple['specificity']]

    fig = go.Figure()

    fig.add_trace(go.Scatterpolar(
        r=full_vals + [full_vals[0]],
        theta=metrics + [metrics[0]],
        fill='toself', fillcolor='rgba(52, 211, 153, 0.2)',
        line=dict(color=COLORS['proposed'], width=2),
        name='Full System',
    ))

    fig.add_trace(go.Scatterpolar(
        r=simple_vals + [simple_vals[0]],
        theta=metrics + [metrics[0]],
        fill='toself', fillcolor='rgba(91, 141, 239, 0.2)',
        line=dict(color=COLORS['traditional'], width=2),
        name='Simple Rules (Traditional)',
    ))

    fig.update_layout(
        **CHART_LAYOUT,
        title=dict(
            text="<b>Full System vs Simple Rules — All Metrics</b>",
            x=0.5, font=dict(size=18)),
        polar=dict(
            radialaxis=dict(range=[0, 100], tickfont=dict(size=10),
                            gridcolor=COLORS['grid']),
            angularaxis=dict(tickfont=dict(size=12)),
        ),
        height=520,
        legend=dict(orientation="h", yanchor="bottom", y=-0.15,
                    xanchor="center", x=0.5, font=dict(size=13)),
    )

    path = output_dir / 'ablation_radar.html'
    fig.write_html(str(path))
    print(f"[+] Saved: {path}")

    try:
        img_path = output_dir / 'ablation_radar.png'
        fig.write_image(str(img_path), width=800, height=520, scale=2)
        print(f"[+] Saved: {img_path}")
    except Exception:
        pass

    return fig


# ═══════════════════════════════════════════════════════
#  Main Execution
# ═══════════════════════════════════════════════════════

if __name__ == '__main__':
    print("=" * 60)
    print("  Ablation Study — Plot Generator")
    print("=" * 60)

    data = load_results()
    output_dir = Path(__file__).parent

    print(f"\n[*] Dataset: {data['dataset']['total_records']} records")
    print(f"[*] Output: {output_dir}\n")

    plot_accuracy_comparison(data, output_dir)
    plot_contribution(data, output_dir)
    plot_roc(data, output_dir)
    plot_cv_folds(data, output_dir)
    plot_confusion_matrix(data, output_dir)
    plot_radar(data, output_dir)

    print(f"\n{'='*60}")
    print("  Done! All plots saved.")
    print(f"{'='*60}")
