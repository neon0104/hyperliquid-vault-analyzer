# 🔬 Research Report — Dashboard Chart Libraries

**Agent**: Research Agent  
**Completed**: 2026-03-09  
**Task ref**: tasks.md → Task 1

---

## 🏆 Top 3 Recommended Libraries

| Rank | Library | Reason |
|------|---------|--------|
| 1st | **Apache ECharts** | Best for financial data, dark theme built-in, high performance Canvas, specialized financial chart types (candlestick, K-line), built-in zoom/pan |
| 2nd | **Plotly / Dash** | Python-first, highest interactivity, but heavier and Dash replaces Flask structure |
| 3rd | **ApexCharts** | Modern/aesthetic, glow effects, lighter than Plotly, good for time-series |

---

## 📌 Final Recommendation

> **Keep Flask backend + replace Chart.js with Apache ECharts**

### Rationale:
- ECharts is drop-in CDN compatible (no rebuild needed)
- Dark mode theming matches existing `--bg: #0b0f1a` design
- Built-in `dataZoom` for zooming/panning equity curves
- Synchronized tooltips (crosshair shows all 4 portfolio values at same time)
- Handles 10,000+ data points smoothly vs Chart.js lag
- No Python-side changes needed — just swap JS library

---

## 🔧 Integration Notes for Developer Agent

```html
<!-- Replace in PORTFOLIO_HTML <head>: -->
<!-- OLD: -->
<script src="https://cdn.jsdelivr.net/npm/chart.js@4/dist/chart.umd.min.js"></script>

<!-- NEW: -->
<script src="https://cdn.jsdelivr.net/npm/echarts@5/dist/echarts.min.js"></script>
```

### ECharts Dark Theme Init:
```javascript
const chart = echarts.init(document.getElementById('btc'), 'dark');
chart.setOption({ backgroundColor: '#0b0f1a', ... });
```

### Key ECharts Options for Financial Use:
- `dataZoom`: `[{type:'slider'}, {type:'inside'}]`
- `tooltip`: `{trigger:'axis', axisPointer:{type:'cross'}}`
- `yAxis.axisLabel.formatter`: `v => '$' + v.toLocaleString()`

---

## ✅ Best Practices Found

1. **Asset externalization**: Move CSS/JS to `static/` folder for caching (future improvement)
2. **Async updates**: Use Fetch API for data refresh (already implemented via `/analysis-status`)
3. **Responsive**: ECharts auto-resizes with `window.addEventListener('resize', () => chart.resize())`
