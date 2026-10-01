# TutorLinkAI Research Report: Feedback-Aware Ranking Stress-Test & Sensitivity Analysis (Step 6B)

---

## 1. Executive Summary & Objective

This report details the offline empirical evaluation of the Bayesian feedback signal integrated with the multi-criteria hybrid recommendation engine. 

The primary research question investigated is:
> *How does a Bayesian-smoothed learner feedback signal interact with multi-criteria recommendation compatibility under controlled edge cases, including cold-start conditions, sample-size variance, and large compatibility-versus-quality trade-offs?*

**Production Safety Statement:**
> [!IMPORTANT]
> **Production recommendation scoring was NOT changed.**
> Feedback-aware ranking exists **strictly as an offline research evaluation** in this step. The live production recommendation service continues to use the established multi-criteria hybrid ranker without feedback weighting.

---

## 2. Experimental Methodology & Mathematical Formulation

### 2.1 Bayesian Shrinkage Formulation
To prevent small-sample rating distortion and address the cold-start problem, empirical tutor ratings are regularized toward a global prior:

$$r_{\text{adj}} = \left(\frac{n}{n + m}\right) \cdot \overline{r} + \left(\frac{m}{n + m}\right) \cdot \mu_{\text{prior}}$$

Where:
- $n$: Number of completed-session learner reviews ($n \ge 0$).
- $m$: Smoothing parameter / pseudocount confidence threshold (evaluated across $m \in \{1, 5, 10, 20\}$, default $m=5.0$).
- $\overline{r}$: Empirical arithmetic mean rating of the tutor ($1.0 \le \overline{r} \le 5.0$).
- $\mu_{\text{prior}}$: Global empirical prior rating (default $\mu_{\text{prior}} = 3.5$).

### 2.2 Normalized Feedback Score & Evidence Confidence
The adjusted rating is normalized onto $[0.0, 1.0]$:

$$S_{\text{feedback}} = \frac{r_{\text{adj}} - r_{\min}}{r_{\max} - r_{\min}} = \frac{r_{\text{adj}} - 1.0}{4.0}$$

Review evidence confidence is quantified as:

$$C_{\text{feedback}} = \frac{n}{n + m} \in [0.0, 1.0)$$

### 2.3 Experimental Composite Score
For research evaluation, the experimental composite score balances hybrid compatibility against feedback:

$$\text{Score}_{\text{exp}} = (1.0 - w_{\text{feedback}}) \cdot \text{Score}_{\text{hybrid}} + w_{\text{feedback}} \cdot S_{\text{feedback}}$$

Where $w_{\text{feedback}} \in [0.00, 0.40]$ is swept systematically.

---

## 3. Controlled Challenge Scenarios

The evaluation executes over 6 deterministic stress-test scenarios in `feedback_scenarios.json`:

| Scenario ID | Title | Candidate A | Candidate B | Evaluation Focus |
| :--- | :--- | :--- | :--- | :--- |
| **S1** | **Quality vs Compatibility** | Compat: 0.94, Rating: 4.8 ($n=30$) | Compat: 0.96, Rating: 3.2 ($n=30$) | Can strong feedback overcome a minor compatibility deficit? |
| **S2** | **Cold Start vs Established** | Compat: 0.94, Rating: 5.0 ($n=1$) | Compat: 0.93, Rating: 4.7 ($n=40$) | Does Bayesian shrinkage protect against single-review overconfidence? |
| **S3** | **New Tutor (0 Reviews)** | Compat: 0.94, Rating: None ($n=0$) | Compat: 0.92, Rating: 4.8 ($n=30$) | Does neutral prior treatment avoid unfair cold-start penalties? |
| **S4** | **Strong Compat vs Strong Feedback**| Compat: 0.98, Rating: 3.5 ($n=30$) | Compat: 0.88, Rating: 4.9 ($n=30$) | Does dominant compatibility prevail under moderate feedback weights? |
| **S5** | **Similar Compatibility** | Compat: 0.91, Rating: 4.9 ($n=50$) | Compat: 0.90, Rating: 3.8 ($n=50$) | Does feedback effectively break ties between similar candidates? |
| **S6** | **Same Rating, Different Evidence**| Compat: 0.93, Rating: 5.0 ($n=1$) | Compat: 0.92, Rating: 5.0 ($n=40$) | Does evidence confidence favor high-volume verified consistency? |

---

## 4. Ranking Flip Analysis ($m = 5.0, \mu_{\text{prior}} = 3.5$)

The table below reports top-ranked candidates and score margins across feedback weights $w_{\text{feedback}} \in [0.00, 0.40]$:

| Scenario | $w=0.00$ (Base) | $w=0.05$ | $w=0.10$ | $w=0.15$ | $w=0.20$ | $w=0.30$ | $w=0.40$ | Flip Threshold ($w^*$) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **S1: Quality vs Compat** | Tutor B (0.960) | Tutor B (0.940) | **Tutor A (0.936)** | **Tutor A (0.935)** | **Tutor A (0.933)** | **Tutor A (0.929)** | **Tutor A (0.925)** | $w^* = 0.10$ |
| **S2: Cold Start vs Estab** | Tutor A (0.940) | **Tutor B (0.928)** | **Tutor B (0.926)** | **Tutor B (0.924)** | **Tutor B (0.922)** | **Tutor B (0.919)** | **Tutor B (0.915)** | $w^* = 0.05$ |
| **S3: New Tutor (0 Revs)** | Tutor A (0.940) | Tutor A (0.924) | **Tutor B (0.918)** | **Tutor B (0.918)** | **Tutor B (0.917)** | **Tutor B (0.915)** | **Tutor B (0.913)** | $w^* = 0.10$ |
| **S4: Large Compat Gap** | Tutor A (0.980) | Tutor A (0.962) | Tutor A (0.945) | Tutor A (0.927) | Tutor A (0.909) | **Tutor B (0.894)** | **Tutor B (0.898)** | $w^* = 0.30$ |
| **S5: Similar Compat** | Tutor A (0.910) | Tutor A (0.912) | Tutor A (0.913) | Tutor A (0.915) | Tutor A (0.917) | Tutor A (0.920) | Tutor A (0.923) | *No flip (margin expands)* |
| **S6: Same Rating Diff N** | Tutor A (0.930) | **Tutor B (0.922)** | **Tutor B (0.924)** | **Tutor B (0.926)** | **Tutor B (0.928)** | **Tutor B (0.931)** | **Tutor B (0.935)** | $w^* = 0.05$ |

---

## 5. Cold-Start Shrinkage Dynamics

To analyze the mathematical behavior of the Bayesian estimator across review volumes, the progression for a 5.0-star rating ($\mu_{\text{prior}} = 3.5, m = 5.0$) is detailed below:

| Review Count ($n$) | Raw Rating | Adjusted Rating ($r_{\text{adj}}$) | Feedback Score ($S_{\text{feedback}}$) | Confidence ($C_{\text{feedback}}$) | Distance From Raw ($|r_{\text{adj}} - \overline{r}|$) |
| :---: | :---: | :---: | :---: | :---: | :---: |
| **0** | None | 3.5000 | 0.6250 | 0.0000 | 0.0000 (at prior) |
| **1** | 5.00 | 3.7500 | 0.6875 | 0.1667 | 1.2500 (83.3% shrinkage) |
| **2** | 5.00 | 3.9286 | 0.7321 | 0.2857 | 1.0714 (71.4% shrinkage) |
| **5** | 5.00 | 4.2500 | 0.8125 | 0.5000 | 0.7500 (50.0% shrinkage) |
| **10** | 5.00 | 4.5000 | 0.8750 | 0.6667 | 0.5000 (33.3% shrinkage) |
| **20** | 5.00 | 4.7000 | 0.9250 | 0.8000 | 0.3000 (20.0% shrinkage) |
| **40** | 5.00 | 4.8333 | 0.9583 | 0.8889 | 0.1667 (11.1% shrinkage) |
| **50** | 5.00 | 4.8636 | 0.9659 | 0.9091 | 0.1364 (9.1% shrinkage) |
| **100** | 5.00 | 4.9286 | 0.9821 | 0.9524 | 0.0714 (4.8% shrinkage) |

---

## 6. Bayesian Smoothing Sensitivity Analysis ($m \in \{1, 5, 10, 20\}$)

Evaluating smoothing parameter $m$ on a single 5.0-star review ($n=1, \overline{r}=5.0, \mu_{\text{prior}}=3.5$):

| Smoothing $m$ | Weight on Raw Rating ($\frac{n}{n+m}$) | Weight on Prior ($\frac{m}{n+m}$) | Adjusted Rating ($r_{\text{adj}}$) | Feedback Score | Interpretation |
| :---: | :---: | :---: | :---: | :---: | :--- |
| **1.0** | 50.0% | 50.0% | 4.2500 | 0.8125 | Weak regularization; high variance |
| **5.0** | 16.7% | 83.3% | 3.7500 | 0.6875 | **Balanced baseline**; effective variance control |
| **10.0** | 9.1% | 90.9% | 3.6364 | 0.6591 | Conservative; requires substantial review volume |
| **20.0** | 4.8% | 95.2% | 3.5714 | 0.6429 | Highly conservative; slow to acknowledge genuine quality |

---

## 7. Key Findings & Empirical Observations

1. **Cold-Start Protection:** In Scenario 2 and Scenario 6, a single 5-star review ($n=1$) is prevented from overtaking high-volume established tutors ($n=40$), confirming that Bayesian shrinkage eliminates single-review anomalies.
2. **Controlled Trade-offs:** In Scenario 1, small compatibility margins (0.02) are cleanly superseded by major quality differences (4.8 vs 3.2 stars) at $w_{\text{feedback}} \ge 0.10$.
3. **Compatibility Resilience:** In Scenario 4, a major compatibility advantage (0.10 margin) resists feedback disruption across typical weights ($w \le 0.20$) and only flips at aggressive weights ($w \ge 0.30$), ensuring domain relevance remains primary.
4. **Tie-Breaking Utility:** In Scenario 5, where compatibility is near-identical (0.91 vs 0.90), the feedback signal smoothly widens the ranking margin without introducing instability.

---

## 8. Research Limitations & Future Work

1. **Synthetic Scenario Benchmarking:** These challenge scenarios represent curated synthetic tests designed to probe mathematical boundary behavior, not longitudinal student click-through data.
2. **Static Weighting:** The current formulation utilizes static linear interpolation rather than context-dependent dynamic weights learned via pairwise learning-to-rank.
3. **Future Production Path:** If feedback is to be introduced into production ranking in a subsequent step, a conservative provisional weight $w_{\text{feedback}} \in [0.05, 0.10]$ with $m = 5.0$ provides the most balanced trade-off between compatibility preservation and reputation awareness.
