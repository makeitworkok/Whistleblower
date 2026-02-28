# React/SPA Documentation Map

Quick navigation guide to help you find the right document for your situation.

---

## 🎯 Choose Your Path

### Path 1: I'm Setting Up a New React Site
**Goal**: Generate initial config for a React/SPA frontend

**Steps**:
1. Read: **[REACTJS-GUIDE.md](REACTJS-GUIDE.md)** Quick Start section (5 min)
2. Run: `bootstrap_recorder.py` (see guide for command)
3. Reference: **[REACT-QUICK-REF.md](REACT-QUICK-REF.md)** while editing config
4. If stuck: **[REACT-TROUBLESHOOTING.md](REACT-TROUBLESHOOTING.md)**

**Time**: 30-60 minutes

---

### Path 2: I'm Troubleshooting Failed Captures
**Goal**: Fix "element not found" or timing issues

**Steps**:
1. Start: **[REACT-TROUBLESHOOTING.md](REACT-TROUBLESHOOTING.md)**
2. Find your symptom in the problem sections
3. Follow diagnostic steps
4. Apply solutions
5. Reference: **[REACT-QUICK-REF.md](REACT-QUICK-REF.md)** for config patterns

**Time**: 15-30 minutes

---

### Path 3: I Need a Quick Config Pattern
**Goal**: Copy-paste working config for common scenario

**Steps**:
1. Go to: **[REACT-QUICK-REF.md](REACT-QUICK-REF.md)**
2. Find matching pattern (tree nav, loading states, etc.)
3. Copy and customize
4. Test

**Time**: 5-10 minutes

---

### Path 4: I Want to Understand React Challenges
**Goal**: Learn why React/SPAs are different and how to handle them

**Steps**:
1. Read: **[REACTJS-GUIDE.md](REACTJS-GUIDE.md)** (full guide)
2. Study: **[ignition_perspective_annotated.example.json](../sites/ignition_perspective_annotated.example.json)**
3. Experiment with your own site

**Time**: 45-60 minutes

---

## 📚 Document Reference

| Document | Purpose | When to Use | Time |
|----------|---------|-------------|------|
| **[REACTJS-GUIDE.md](REACTJS-GUIDE.md)** | Comprehensive guide | Learning, reference | 45-60 min |
| **[REACT-QUICK-REF.md](REACT-QUICK-REF.md)** | Copy-paste patterns | Quick solutions | 5-10 min |
| **[REACT-TROUBLESHOOTING.md](REACT-TROUBLESHOOTING.md)** | Diagnostic checklists | When captures fail | 15-30 min |
| **[ignition_perspective_annotated.example.json](../sites/ignition_perspective_annotated.example.json)** | Annotated example | Understanding configs | 10-15 min |

---

## 🔍 Find By Problem

| Problem | Document | Section |
|---------|----------|---------|
| Element not found | [REACT-TROUBLESHOOTING.md](REACT-TROUBLESHOOTING.md) | Element Not Found |
| Screenshots show loading | [REACT-TROUBLESHOOTING.md](REACT-TROUBLESHOOTING.md) | Screenshot Captures Loading State |
| Navigation fails | [REACT-TROUBLESHOOTING.md](REACT-TROUBLESHOOTING.md) | Navigation Doesn't Reach Target URL |
| Selectors break | [REACTJS-GUIDE.md](REACTJS-GUIDE.md) | Strategy 1: Use Stable Selectors |
| Don't know what selectors to use | [REACTJS-GUIDE.md](REACTJS-GUIDE.md) | Strategy 3: Use Bootstrap Recorder |
| Multi-step navigation | [REACT-QUICK-REF.md](REACT-QUICK-REF.md) | Tree Navigation pattern |
| Login issues | [REACT-TROUBLESHOOTING.md](REACT-TROUBLESHOOTING.md) | Login Success but Re-prompted |

---

## 🎓 Learning Path

### Beginner (Never used Whistleblower with React)
1. [REACTJS-GUIDE.md](REACTJS-GUIDE.md) § Overview - 5 min
2. [REACTJS-GUIDE.md](REACTJS-GUIDE.md) § Strategy 3: Bootstrap Recorder - 10 min
3. Run bootstrap recorder on your site - 15 min
4. [REACT-QUICK-REF.md](REACT-QUICK-REF.md) § Common Patterns - 10 min
5. Edit and test your config - 30 min

**Total**: ~70 minutes to first successful capture

### Intermediate (Have basic config, need optimization)
1. [REACTJS-GUIDE.md](REACTJS-GUIDE.md) § Strategy 1: Stable Selectors - 10 min
2. [REACT-QUICK-REF.md](REACT-QUICK-REF.md) § Selector Priority - 5 min
3. Review your config and improve selectors - 20 min
4. [REACTJS-GUIDE.md](REACTJS-GUIDE.md) § Strategy 2: Loading States - 10 min
5. Add loading detection - 15 min

**Total**: ~60 minutes to optimal config

### Advanced (Troubleshooting complex issues)
1. [REACT-TROUBLESHOOTING.md](REACT-TROUBLESHOOTING.md) § General Workflow - 10 min
2. [REACTJS-GUIDE.md](REACTJS-GUIDE.md) § Debugging - 15 min
3. Use DevTools and video recording - 30 min
4. Iterate solutions - 30 min

**Total**: ~85 minutes to resolve complex issues

---

## 🎯 Quick Decision Tree

```
Do you have a config file already?
├─ NO
│  └─ Use: bootstrap_recorder.py + REACT-QUICK-REF.md
│
└─ YES
   ├─ Is it working?
   │  ├─ YES → Optimize with REACTJS-GUIDE.md
   │  └─ NO → Fix with REACT-TROUBLESHOOTING.md
   │
   └─ Do you understand why it works/fails?
      ├─ YES → You're good!
      └─ NO → Read REACTJS-GUIDE.md
```

---

## 📞 Still Need Help?

1. ✅ Check [REACT-TROUBLESHOOTING.md](REACT-TROUBLESHOOTING.md) first
2. ✅ Review [ignition_perspective_annotated.example.json](../sites/ignition_perspective_annotated.example.json) for patterns
3. ✅ Run bootstrap recorder with `--record-video` to see what's happening
4. ✅ Test selectors in browser DevTools console
5. ✅ Start with simplest possible config and add complexity gradually

---

**Remember**: All these docs work together. Start with the right one for your situation, then cross-reference as needed.

<!-- Copyright (c) 2025-2026 Chris Favre - MIT License -->
<!-- See LICENSE file for full terms -->
