# 📋 Task List — Hyperliquid Vault Dashboard

**Managed by**: Project Manager Agent  
**Last updated**: 2026-03-09  
**Project**: Hyperliquid Vault Analyzer — Web Dashboard Upgrade

---

## 🎯 Sprint Goal
Upgrade the web dashboard with interactive ECharts visualizations, improving UX and data visibility.

---

## Task 1: Research Chart Libraries
- **Agent**: Research Agent
- **Status**: ✅ DONE
- **Output**: `agents/research.md`
- **Summary**: Apache ECharts recommended over Chart.js for financial dashboards

## Task 2: Implement Dashboard Upgrade
- **Agent**: Developer Agent
- **Status**: 🔄 IN PROGRESS
- **Output**: `web_dashboard.py` (modified)
- **Sub-tasks**:
  - [ ] 2a. Add ECharts CDN to portfolio page `<head>`
  - [ ] 2b. Replace Chart.js equity curve → ECharts (interactive, zoomable)
  - [ ] 2c. Add new ECharts bar chart (portfolio stats comparison)
  - [ ] 2d. Add APR distribution chart to main dashboard
  - [ ] 2e. Pass `chart_data` from Flask `index()` route
  - [ ] 2f. Verify Python syntax (`py_compile`)

## Task 3: Write Tests / QA
- **Agent**: QA Agent
- **Status**: ⏳ WAITING (blocked by Task 2)
- **Output**: `agents/progress.md`
- **Sub-tasks**:
  - [ ] 3a. Verify dashboard loads at http://localhost:5000
  - [ ] 3b. Check ECharts renders without errors
  - [ ] 3c. Confirm existing features still work (analysis run, downloads)
  - [ ] 3d. Screenshot final UI and report result

---

## Notes for Agents
- All agents coordinate via files in `/agents/`
- Developer: update `agents/progress.md` after each sub-task
- Research: update `agents/research.md` with findings
- QA: report results in `agents/progress.md` under QA section
