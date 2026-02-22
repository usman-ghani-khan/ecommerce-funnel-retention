"""
TheLook eCommerce — Funnel & Retention Analysis
===============================================
Full exploratory analysis covering:
  1. Data validation & quality summary
  2. Purchase funnel analysis (overall + by traffic source + by device)
  3. Cohort retention heatmap
  4. Monthly revenue & conversion trends
  5. Customer segmentation by spend tier
  6. Key findings summary

All charts exported to /outputs/ for inclusion in Tableau and README.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import seaborn as sns
from pathlib import Path
import warnings
warnings.filterwarnings("ignore")

# ── Paths ─────────────────────────────────────────────────────────────────────
BASE    = Path("/home/claude/ecommerce-funnel-retention")
DATA    = BASE / "data"
OUT     = BASE / "outputs"
OUT.mkdir(exist_ok=True)

# ── Style ─────────────────────────────────────────────────────────────────────
BRAND_BLUE   = "#1B4F72"
BRAND_LIGHT  = "#AED6F1"
BRAND_ACCENT = "#E74C3C"
GREY         = "#7F8C8D"
BG           = "#FAFAFA"

plt.rcParams.update({
    "figure.facecolor":  BG,
    "axes.facecolor":    BG,
    "axes.spines.top":   False,
    "axes.spines.right": False,
    "axes.labelcolor":   "#2C3E50",
    "xtick.color":       "#2C3E50",
    "ytick.color":       "#2C3E50",
    "font.family":       "DejaVu Sans",
    "font.size":         11,
})

# ── Load data ─────────────────────────────────────────────────────────────────
print("Loading data...")
events      = pd.read_csv(DATA / "events.csv",      parse_dates=["created_at"])
users       = pd.read_csv(DATA / "users.csv",       parse_dates=["created_at"])
orders      = pd.read_csv(DATA / "orders.csv",      parse_dates=["created_at"])
order_items = pd.read_csv(DATA / "order_items.csv", parse_dates=["created_at","shipped_at","returned_at"])
products    = pd.read_csv(DATA / "products.csv")

print(f"  events:      {len(events):,}")
print(f"  users:       {len(users):,}")
print(f"  orders:      {len(orders):,}")
print(f"  order_items: {len(order_items):,}")
print(f"  products:    {len(products):,}")


# ══════════════════════════════════════════════════════════════════════════════
# 1. DATA QUALITY SUMMARY
# ══════════════════════════════════════════════════════════════════════════════
print("\n── 1. Data Quality ─────────────────────────────────────────────────")

def null_audit(df, name):
    nulls = df.isnull().sum()
    nulls = nulls[nulls > 0]
    pct   = (nulls / len(df) * 100).round(2)
    if len(nulls) == 0:
        print(f"  {name}: ✓ No nulls in any column")
    else:
        print(f"  {name} nulls:\n{pd.DataFrame({'count': nulls, 'pct': pct})}")

null_audit(events, "events")
null_audit(users,  "users")
null_audit(orders, "orders")

# Duplicate sessions check
dup_sessions = events.groupby(["session_id","event_type"]).size()
dup_sessions = dup_sessions[dup_sessions > 1]
print(f"  Duplicate (session, event_type) pairs: {len(dup_sessions)}")

# Orphaned FK check
orphaned = events[~events["user_id"].isin(users["user_id"])]
print(f"  Orphaned event rows (user not in users): {len(orphaned)}")

# Revenue outliers (z-score > 3)
mean_rev = orders["total_sale_price"].mean()
std_rev  = orders["total_sale_price"].std()
outliers = orders[((orders["total_sale_price"] - mean_rev) / std_rev).abs() > 3]
print(f"  Revenue outliers (z>3): {len(outliers)} orders ({len(outliers)/len(orders)*100:.1f}%)")
print(f"  Avg order value: ${mean_rev:.2f}  |  Std: ${std_rev:.2f}")


# ══════════════════════════════════════════════════════════════════════════════
# 2. PURCHASE FUNNEL
# ══════════════════════════════════════════════════════════════════════════════
print("\n── 2. Funnel Analysis ──────────────────────────────────────────────")

stages = ["home", "category", "product", "cart", "purchase"]
labels = ["Home", "Category", "Product\nView", "Add to\nCart", "Purchase"]

funnel_counts = {
    s: events[events["event_type"] == s]["user_id"].nunique()
    for s in stages
}
funnel_df = pd.DataFrame({
    "stage":  labels,
    "users":  [funnel_counts[s] for s in stages],
})
funnel_df["drop_off_pct"] = (
    (1 - funnel_df["users"] / funnel_df["users"].shift(1)) * 100
).round(1)
funnel_df["conversion_from_top"] = (
    funnel_df["users"] / funnel_df["users"].iloc[0] * 100
).round(1)

print(funnel_df.to_string(index=False))

# Chart: Funnel
fig, ax = plt.subplots(figsize=(10, 5.5))
colors = [BRAND_BLUE if i < len(labels)-1 else BRAND_ACCENT for i in range(len(labels))]
bars = ax.barh(labels[::-1], funnel_df["users"].values[::-1],
               color=colors[::-1], height=0.6, edgecolor="white", linewidth=1.2)

for bar, row in zip(bars, funnel_df.iloc[::-1].itertuples()):
    pct = f"{row.conversion_from_top:.1f}% of visitors"
    ax.text(bar.get_width() + 80, bar.get_y() + bar.get_height()/2,
            f"{row.users:,}  ({pct})",
            va="center", fontsize=10, color="#2C3E50")

# Drop-off annotations between bars
for i in range(1, len(funnel_df)):
    drop = funnel_df["drop_off_pct"].iloc[i]
    y    = len(labels) - 1 - i + 0.5
    ax.annotate(f"▼ {drop:.0f}% drop-off",
                xy=(funnel_df["users"].iloc[i] + 80, y),
                fontsize=9, color=BRAND_ACCENT, style="italic")

ax.set_xlabel("Unique Users", labelpad=10)
ax.set_title("Purchase Funnel — Unique Users per Stage", fontsize=14, fontweight="bold",
             color=BRAND_BLUE, pad=15)
ax.set_xlim(0, funnel_df["users"].max() * 1.45)
ax.xaxis.set_major_formatter(mtick.FuncFormatter(lambda x, _: f"{int(x):,}"))
plt.tight_layout()
plt.savefig(OUT / "01_purchase_funnel.png", dpi=150, bbox_inches="tight")
plt.close()
print("  Saved: 01_purchase_funnel.png")


# ══════════════════════════════════════════════════════════════════════════════
# 3. FUNNEL BY TRAFFIC SOURCE
# ══════════════════════════════════════════════════════════════════════════════
print("\n── 3. Funnel by Traffic Source ─────────────────────────────────────")

source_funnel = {}
for source in events["traffic_source"].unique():
    sub = events[events["traffic_source"] == source]
    source_funnel[source] = {s: sub[sub["event_type"]==s]["user_id"].nunique() for s in stages}

source_df = pd.DataFrame(source_funnel).T
source_df.columns = stages
source_df["conversion_pct"] = (source_df["purchase"] / source_df["home"] * 100).round(2)
source_df["cart_to_purchase_pct"] = (source_df["purchase"] / source_df["cart"] * 100).round(1)
source_df = source_df.sort_values("conversion_pct", ascending=False)
print(source_df[["home","cart","purchase","conversion_pct","cart_to_purchase_pct"]].to_string())

# Chart: Conversion by traffic source
fig, axes = plt.subplots(1, 2, figsize=(13, 5))

# Overall conversion rate by source
ax = axes[0]
source_colors = [BRAND_BLUE if i > 0 else BRAND_ACCENT for i in range(len(source_df))]
bars = ax.bar(source_df.index, source_df["conversion_pct"],
              color=source_colors, edgecolor="white", linewidth=1)
for bar, val in zip(bars, source_df["conversion_pct"]):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.05,
            f"{val:.1f}%", ha="center", fontsize=10, fontweight="bold", color=BRAND_BLUE)
ax.set_title("Overall Conversion Rate\nby Traffic Source", fontsize=12,
             fontweight="bold", color=BRAND_BLUE)
ax.set_ylabel("Session-to-Purchase Conversion (%)")
ax.yaxis.set_major_formatter(mtick.PercentFormatter())
ax.set_ylim(0, source_df["conversion_pct"].max() * 1.3)

# Cart-to-purchase by source
ax = axes[1]
bars2 = ax.bar(source_df.index, source_df["cart_to_purchase_pct"],
               color=BRAND_LIGHT, edgecolor=BRAND_BLUE, linewidth=1.2)
for bar, val in zip(bars2, source_df["cart_to_purchase_pct"]):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.3,
            f"{val:.1f}%", ha="center", fontsize=10, fontweight="bold", color=BRAND_BLUE)
ax.set_title("Cart-to-Purchase Rate\nby Traffic Source", fontsize=12,
             fontweight="bold", color=BRAND_BLUE)
ax.set_ylabel("Cart-to-Purchase Conversion (%)")
ax.yaxis.set_major_formatter(mtick.PercentFormatter())
ax.set_ylim(0, source_df["cart_to_purchase_pct"].max() * 1.3)

plt.suptitle("Traffic Source Quality Analysis", fontsize=14, fontweight="bold", y=1.01)
plt.tight_layout()
plt.savefig(OUT / "02_funnel_by_traffic_source.png", dpi=150, bbox_inches="tight")
plt.close()
print("  Saved: 02_funnel_by_traffic_source.png")


# ══════════════════════════════════════════════════════════════════════════════
# 4. COHORT RETENTION HEATMAP
# ══════════════════════════════════════════════════════════════════════════════
print("\n── 4. Cohort Retention ─────────────────────────────────────────────")

# Only completed/shipped/returned orders qualify as real purchases
valid_orders = orders[orders["status"].isin(["Complete","Shipped","Returned"])].copy()
valid_orders["order_month"] = valid_orders["created_at"].dt.to_period("M")

# First purchase month per user
first_purchase = valid_orders.groupby("user_id")["order_month"].min().reset_index()
first_purchase.columns = ["user_id", "cohort_month"]

# Merge back
cohort_df = valid_orders.merge(first_purchase, on="user_id")
cohort_df["month_number"] = (
    cohort_df["order_month"].astype(int) - cohort_df["cohort_month"].astype(int)
)

# Keep months 0-11
cohort_df = cohort_df[cohort_df["month_number"].between(0, 11)]

# Cohort sizes (users in month 0)
cohort_sizes = (
    cohort_df[cohort_df["month_number"] == 0]
    .groupby("cohort_month")["user_id"].nunique()
)

# Retention counts
retention = (
    cohort_df.groupby(["cohort_month","month_number"])["user_id"]
    .nunique()
    .reset_index()
)
retention.columns = ["cohort_month","month_number","users"]
retention["cohort_size"] = retention["cohort_month"].map(cohort_sizes)
retention["retention_pct"] = (retention["users"] / retention["cohort_size"] * 100).round(1)

# Pivot for heatmap
pivot = retention.pivot(index="cohort_month", columns="month_number", values="retention_pct")
# Only keep cohorts with enough data (at least 3 months)
pivot = pivot[pivot.notna().sum(axis=1) >= 3]

print(f"  Cohorts with ≥3 months data: {len(pivot)}")
m1_avg = pivot[1].dropna().mean() if 1 in pivot.columns else float("nan")
m3_avg = pivot[3].dropna().mean() if 3 in pivot.columns else float("nan")
print(f"  Avg Month-1 retention: {m1_avg:.1f}%")
print(f"  Avg Month-3 retention: {m3_avg:.1f}%")

# Chart
fig, ax = plt.subplots(figsize=(14, max(5, len(pivot) * 0.55)))
mask = pivot.isnull()
cmap = sns.light_palette(BRAND_BLUE, as_cmap=True)

sns.heatmap(
    pivot, ax=ax, mask=mask,
    annot=True, fmt=".0f", annot_kws={"size": 9, "weight": "bold"},
    cmap=cmap, vmin=0, vmax=100,
    linewidths=0.5, linecolor="white",
    cbar_kws={"label": "Retention %", "shrink": 0.6}
)

# Month 0 always 100%
for i in range(len(pivot)):
    ax.text(0.5, i + 0.5, "100", ha="center", va="center",
            fontsize=9, fontweight="bold", color="white")

ax.set_title("Monthly Cohort Retention Heatmap\n(% of cohort making ≥1 purchase in month N)",
             fontsize=13, fontweight="bold", color=BRAND_BLUE, pad=15)
ax.set_xlabel("Months Since First Purchase", labelpad=10)
ax.set_ylabel("Acquisition Cohort (First Purchase Month)", labelpad=10)
ax.set_xticklabels([f"M{c}" for c in pivot.columns], rotation=0)
ax.set_yticklabels([str(p) for p in pivot.index], rotation=0, fontsize=9)

plt.tight_layout()
plt.savefig(OUT / "03_cohort_retention_heatmap.png", dpi=150, bbox_inches="tight")
plt.close()
print("  Saved: 03_cohort_retention_heatmap.png")


# ══════════════════════════════════════════════════════════════════════════════
# 5. MONTHLY REVENUE & CONVERSION TREND
# ══════════════════════════════════════════════════════════════════════════════
print("\n── 5. Monthly Revenue & Conversion Trend ───────────────────────────")

monthly_sessions = (
    events[events["event_type"] == "home"]
    .groupby(events["created_at"].dt.to_period("M"))["user_id"].nunique()
    .reset_index()
)
monthly_sessions.columns = ["month","unique_visitors"]

monthly_revenue = (
    valid_orders.groupby(valid_orders["created_at"].dt.to_period("M"))
    .agg(total_revenue=("total_sale_price","sum"),
         unique_buyers=("user_id","nunique"),
         total_orders=("order_id","count"),
         avg_order_value=("total_sale_price","mean"))
    .reset_index()
)
monthly_revenue.columns = ["month","total_revenue","unique_buyers","total_orders","avg_order_value"]

trend = monthly_sessions.merge(monthly_revenue, on="month", how="left").fillna(0)
trend["conversion_pct"] = (trend["unique_buyers"] / trend["unique_visitors"] * 100).round(2)
trend["month_str"] = trend["month"].astype(str)
trend["mom_growth"] = trend["total_revenue"].pct_change() * 100

print(f"  Total revenue (2023-2024): ${trend['total_revenue'].sum():,.0f}")
print(f"  Avg monthly conversion rate: {trend['conversion_pct'].mean():.2f}%")
print(f"  Peak revenue month: {trend.loc[trend['total_revenue'].idxmax(),'month_str']}")

# Chart
fig, axes = plt.subplots(2, 1, figsize=(13, 9), sharex=True)

# Revenue
ax = axes[0]
ax.fill_between(range(len(trend)), trend["total_revenue"], alpha=0.2, color=BRAND_BLUE)
ax.plot(range(len(trend)), trend["total_revenue"], color=BRAND_BLUE, linewidth=2.5, marker="o", markersize=5)
ax.set_ylabel("Monthly Revenue ($)", labelpad=10)
ax.set_title("Monthly Revenue & Conversion Rate (Jan 2023 – Dec 2024)",
             fontsize=13, fontweight="bold", color=BRAND_BLUE, pad=15)
ax.yaxis.set_major_formatter(mtick.FuncFormatter(lambda x, _: f"${x:,.0f}"))
ax.grid(axis="y", linestyle="--", alpha=0.4)

# Conversion rate
ax2 = axes[1]
ax2.plot(range(len(trend)), trend["conversion_pct"], color=BRAND_ACCENT, linewidth=2.5, marker="s", markersize=5)
ax2.fill_between(range(len(trend)), trend["conversion_pct"], alpha=0.15, color=BRAND_ACCENT)
ax2.set_ylabel("Visitor-to-Purchase Conv. (%)", labelpad=10)
ax2.yaxis.set_major_formatter(mtick.PercentFormatter())
ax2.grid(axis="y", linestyle="--", alpha=0.4)
ax2.set_xticks(range(len(trend)))
ax2.set_xticklabels(trend["month_str"], rotation=45, ha="right", fontsize=9)

plt.tight_layout()
plt.savefig(OUT / "04_monthly_revenue_conversion.png", dpi=150, bbox_inches="tight")
plt.close()
print("  Saved: 04_monthly_revenue_conversion.png")


# ══════════════════════════════════════════════════════════════════════════════
# 6. CUSTOMER SPEND SEGMENTATION
# ══════════════════════════════════════════════════════════════════════════════
print("\n── 6. Customer Spend Segmentation ──────────────────────────────────")

customer_spend = (
    valid_orders.groupby("user_id")
    .agg(total_spend=("total_sale_price","sum"),
         order_count=("order_id","count"))
    .reset_index()
)

# Segment by spend tier
customer_spend["segment"] = pd.cut(
    customer_spend["total_spend"],
    bins=[0, 50, 150, 400, float("inf")],
    labels=["Low (<$50)","Mid ($50-$150)","High ($150-$400)","VIP (>$400)"]
)
seg_summary = (
    customer_spend.groupby("segment", observed=True)
    .agg(
        customers=("user_id","count"),
        avg_spend=("total_spend","mean"),
        avg_orders=("order_count","mean"),
        total_revenue=("total_spend","sum")
    )
    .reset_index()
)
seg_summary["revenue_share_pct"] = (seg_summary["total_revenue"] / seg_summary["total_revenue"].sum() * 100).round(1)
print(seg_summary.to_string(index=False))

# Chart: segment revenue share
fig, axes = plt.subplots(1, 2, figsize=(12, 5))
palette = [BRAND_LIGHT, BRAND_BLUE, BRAND_ACCENT, "#1A252F"]

ax = axes[0]
wedges, texts, autotexts = ax.pie(
    seg_summary["revenue_share_pct"],
    labels=seg_summary["segment"],
    autopct="%1.1f%%",
    colors=palette,
    startangle=140,
    wedgeprops={"edgecolor":"white","linewidth":2}
)
for t in autotexts:
    t.set_fontsize(10)
    t.set_fontweight("bold")
ax.set_title("Revenue Share by\nCustomer Segment", fontsize=12, fontweight="bold", color=BRAND_BLUE)

ax = axes[1]
ax.bar(seg_summary["segment"], seg_summary["avg_spend"], color=palette, edgecolor="white")
for i, (_, row) in enumerate(seg_summary.iterrows()):
    ax.text(i, row["avg_spend"] + 2, f"${row['avg_spend']:.0f}", ha="center",
            fontsize=10, fontweight="bold", color=BRAND_BLUE)
ax.set_title("Average Spend by\nCustomer Segment", fontsize=12, fontweight="bold", color=BRAND_BLUE)
ax.set_ylabel("Average Customer Lifetime Spend ($)")
ax.yaxis.set_major_formatter(mtick.FuncFormatter(lambda x, _: f"${x:,.0f}"))

plt.suptitle("Customer Spend Segmentation", fontsize=14, fontweight="bold")
plt.tight_layout()
plt.savefig(OUT / "05_customer_segmentation.png", dpi=150, bbox_inches="tight")
plt.close()
print("  Saved: 05_customer_segmentation.png")


# ══════════════════════════════════════════════════════════════════════════════
# 7. EXPORT SQL RESULT CSVs (for Tableau)
# ══════════════════════════════════════════════════════════════════════════════
print("\n── 7. Exporting CSVs for Tableau ────────────────────────────────────")

# Funnel overall
funnel_export = pd.DataFrame({
    "stage": labels,
    "users": [funnel_counts[s] for s in stages],
    "conversion_from_top_pct": funnel_df["conversion_from_top"].values,
    "drop_off_pct": funnel_df["drop_off_pct"].values,
})
funnel_export.to_csv(OUT / "tableau_funnel_overall.csv", index=False)

# Funnel by source
source_export = source_df.reset_index()
source_export.to_csv(OUT / "tableau_funnel_by_source.csv", index=False)

# Cohort retention pivot
pivot.to_csv(OUT / "tableau_cohort_retention.csv")

# Monthly trend
trend.to_csv(OUT / "tableau_monthly_trend.csv", index=False)

# Customer segments
seg_summary.to_csv(OUT / "tableau_customer_segments.csv", index=False)

print("  All Tableau CSVs exported.")


# ══════════════════════════════════════════════════════════════════════════════
# FINAL FINDINGS SUMMARY
# ══════════════════════════════════════════════════════════════════════════════
print("\n" + "═"*60)
print("KEY FINDINGS SUMMARY")
print("═"*60)
overall_conv = funnel_df["conversion_from_top"].iloc[-1]
biggest_drop_idx = funnel_df["drop_off_pct"].idxmax()
print(f"  Overall conversion (home→purchase):     {overall_conv:.1f}%")
print(f"  Biggest funnel drop-off stage:          {funnel_df['stage'].iloc[biggest_drop_idx]} ({funnel_df['drop_off_pct'].iloc[biggest_drop_idx]:.0f}%)")
print(f"  Best converting traffic source:         {source_df.index[0]} ({source_df['conversion_pct'].iloc[0]:.2f}%)")
print(f"  Worst converting traffic source:        {source_df.index[-1]} ({source_df['conversion_pct'].iloc[-1]:.2f}%)")
m1 = pivot[1].dropna().mean() if 1 in pivot.columns else float("nan")
print(f"  Avg Month-1 cohort retention:           {m1:.1f}%")
vip = seg_summary[seg_summary["segment"]=="VIP (>$400)"]
vip_share = vip["revenue_share_pct"].values[0] if len(vip) > 0 else 0.0
print(f"  VIP segment revenue share:              {vip_share:.1f}%")
print(f"  Total orders analysed:                  {len(valid_orders):,}")
print(f"  Total revenue analysed:                 ${valid_orders['total_sale_price'].sum():,.0f}")
print("═"*60)
print("\nAll outputs saved to /outputs/")
