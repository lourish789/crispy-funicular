"""Generate black-and-white diagrams for the AgriTech Suite project document.

All figures are strictly monochrome (black lines / white fill) so the document
prints cleanly and reads well for non-technical audiences.
"""
from __future__ import annotations

import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

OUT = os.path.dirname(os.path.abspath(__file__))
plt.rcParams["font.family"] = "DejaVu Sans"

BOX = dict(boxstyle="round,pad=0.34", facecolor="white", edgecolor="black", linewidth=1.3)
BOX_SQ = dict(boxstyle="square,pad=0.34", facecolor="white", edgecolor="black", linewidth=1.3)


def box(ax, x, y, w, h, text, fs=9, style="round", lw=1.3, dashed=False):
    b = FancyBboxPatch(
        (x - w / 2, y - h / 2), w, h,
        boxstyle=f"{style},pad=0.02",
        facecolor="white", edgecolor="black", linewidth=lw,
        linestyle="--" if dashed else "-",
        mutation_scale=1,
    )
    ax.add_patch(b)
    ax.text(x, y, text, ha="center", va="center", fontsize=fs, color="black", wrap=True)
    return b


def arrow(ax, x1, y1, x2, y2, text="", fs=7.5, style="-|>", dashed=False):
    a = FancyArrowPatch(
        (x1, y1), (x2, y2), arrowstyle=style, mutation_scale=13,
        color="black", linewidth=1.1, linestyle="--" if dashed else "-",
        shrinkA=2, shrinkB=2,
    )
    ax.add_patch(a)
    if text:
        ax.text((x1 + x2) / 2, (y1 + y2) / 2, text, ha="center", va="center",
                fontsize=fs, color="black",
                bbox=dict(facecolor="white", edgecolor="none", pad=1.2))


def finish(fig, ax, name, xlim, ylim):
    ax.set_xlim(*xlim)
    ax.set_ylim(*ylim)
    ax.axis("off")
    fig.savefig(os.path.join(OUT, name), dpi=200, bbox_inches="tight",
                facecolor="white")
    plt.close(fig)
    print("wrote", name)


# ---------------------------------------------------------------- Fig 1
def fig_architecture():
    fig, ax = plt.subplots(figsize=(9.2, 6.4))
    # Layer bands
    bands = [
        (5.3, "USERS"),
        (4.15, "PRESENTATION LAYER"),
        (3.0, "APPLICATION / API LAYER"),
        (1.85, "INTELLIGENCE LAYER"),
        (0.6, "DATA LAYER"),
    ]
    for y, label in bands:
        ax.text(-0.35, y, label, ha="right", va="center", fontsize=8,
                color="black", style="italic")

    box(ax, 2.2, 5.3, 3.0, 0.7, "Farmer (Producer)\nsmartphone / feature phone", fs=8.5)
    box(ax, 6.6, 5.3, 3.0, 0.7, "Buyer (Consumer)\ntrader / processor / household", fs=8.5)

    box(ax, 4.4, 4.15, 7.6, 0.72,
        "Web Application (React + Vite)\nDashboard · Diagnose · Advisory · News · Market · Community · AI Chat", fs=8.5)

    box(ax, 4.4, 3.0, 7.6, 0.72,
        "REST API (FastAPI)  ·  JWT + Firebase Auth  ·  Role engine (Farmer / Buyer)\n"
        "Streaming endpoint (Server-Sent Events)", fs=8.5)

    box(ax, 1.35, 1.85, 2.4, 0.86, "Computer Vision\nOpen-source model\n(on-device)", fs=8)
    box(ax, 3.95, 1.85, 2.4, 0.86, "Language Model\nGroq Llama 3.1\n(advice + chat)", fs=8)
    box(ax, 6.55, 1.85, 2.4, 0.86, "Embeddings + RAG\nGemini vectors\n(knowledge search)", fs=8)

    box(ax, 2.2, 0.6, 3.0, 0.66, "Relational database\nusers · listings · posts · history", fs=8)
    box(ax, 6.6, 0.6, 3.0, 0.66, "Knowledge base\n(vector store)  ·  News cache", fs=8)

    for x in (2.2, 6.6):
        arrow(ax, x, 4.95, x, 4.52)
    arrow(ax, 4.4, 3.79, 4.4, 3.37)
    for x in (1.35, 3.95, 6.55):
        arrow(ax, 4.4, 2.64, x, 2.29)
    arrow(ax, 2.4, 1.42, 2.4, 0.94)
    arrow(ax, 6.3, 1.42, 6.3, 0.94)
    finish(fig, ax, "fig1_architecture.png", (-1.4, 8.6), (0.0, 5.9))


# ---------------------------------------------------------------- Fig 2
def fig_diagnosis_flow():
    fig, ax = plt.subplots(figsize=(9.4, 7.1))
    CX = 5.6  # main column
    box(ax, CX, 6.6, 4.4, 0.6, "Farmer photographs a sick plant or animal\n(image or short video)", fs=8.5)
    arrow(ax, CX, 6.3, CX, 5.95)
    box(ax, CX, 5.65, 4.4, 0.6, "Upload to platform\n(video: representative frames are sampled)", fs=8.5)
    arrow(ax, CX, 5.35, CX, 5.0)

    # Decision
    box(ax, CX, 4.62, 3.5, 0.68, "Is the on-device open-source\nvision model available?", fs=8.3)
    # "no" branch -> left
    arrow(ax, CX - 1.75, 4.62, 3.05, 4.62)
    ax.text(3.95, 4.8, "no", fontsize=8, ha="center")
    box(ax, 1.75, 4.62, 2.6, 0.8, "Fallback chain:\ncloud vision → text\nreasoning → rule-based", fs=7.8, dashed=True)
    # "yes" branch -> down
    arrow(ax, CX, 4.28, CX, 3.9)
    ax.text(CX + 0.22, 4.09, "yes", fontsize=8)

    box(ax, CX, 3.55, 4.4, 0.62, "Disease identified\n(label + confidence score)", fs=8.5)
    # fallback merges into the advice step
    arrow(ax, 1.75, 4.22, 1.75, 2.62, dashed=True)
    arrow(ax, 1.75, 2.62, CX - 2.2, 2.62, dashed=True)

    arrow(ax, CX, 3.24, CX, 2.94)
    box(ax, CX, 2.62, 4.4, 0.62, "Advice generated for that diagnosis\n(offline knowledge base if no connection)", fs=8.5)
    arrow(ax, CX, 2.31, CX, 1.94)

    box(ax, CX, 1.45, 5.4, 0.9,
        "RESULT RETURNED TO FARMER\nDisease name  ·  Cause  ·  Immediate solution  ·  Prevention steps", fs=8.8)
    arrow(ax, CX, 1.0, CX, 0.62)
    box(ax, CX, 0.34, 4.6, 0.46, "Saved to history → feeds the personalised advisory engine", fs=8)
    finish(fig, ax, "fig2_diagnosis_flow.png", (0.2, 9.2), (0.0, 7.05))


# ---------------------------------------------------------------- Fig 3
def fig_marketplace():
    fig, ax = plt.subplots(figsize=(9.0, 4.6))
    box(ax, 1.6, 3.5, 2.6, 0.7, "FARMER\n(Producer / Seller)", fs=9)
    box(ax, 7.4, 3.5, 2.6, 0.7, "BUYER\n(Consumer / Trader)", fs=9)

    box(ax, 1.6, 2.15, 2.6, 0.6, "Publishes a\nSELL offer", fs=8.5)
    box(ax, 7.4, 2.15, 2.6, 0.6, "Publishes a\nBUY request", fs=8.5)
    arrow(ax, 1.6, 3.15, 1.6, 2.45)
    arrow(ax, 7.4, 3.15, 7.4, 2.45)

    box(ax, 4.5, 2.15, 2.4, 0.8, "PLATFORM\nRole engine matches\nthe two sides", fs=8.5)
    arrow(ax, 2.9, 2.15, 3.3, 2.15)
    arrow(ax, 6.1, 2.15, 5.7, 2.15)

    box(ax, 1.6, 0.75, 2.6, 0.72, "Farmer's feed shows\nbuyers seeking produce", fs=8.2)
    box(ax, 7.4, 0.75, 2.6, 0.72, "Buyer's feed shows\nfresh produce for sale", fs=8.2)
    arrow(ax, 4.0, 1.75, 2.0, 1.11)
    arrow(ax, 5.0, 1.75, 7.0, 1.11)

    ax.text(4.5, 0.75, "Middlemen\nbypassed", fontsize=8.5, ha="center", va="center",
            bbox=dict(boxstyle="round,pad=0.4", facecolor="white", edgecolor="black",
                      linewidth=1.2, linestyle="--"))
    finish(fig, ax, "fig3_marketplace.png", (0.0, 9.0), (0.2, 4.1))


# ---------------------------------------------------------------- Fig 4
def fig_inclusivity():
    fig, ax = plt.subplots(figsize=(9.0, 4.9))
    ax.text(4.5, 4.55, "ONE PLATFORM — FOUR WAYS IN", fontsize=10, ha="center", weight="bold")

    tiers = [
        (1.25, "FEATURE PHONE\nNo internet", "USSD short-code\nSMS price alerts\nVoice / IVR advice", "Lowest-income\nrural farmer"),
        (3.4, "BASIC SMARTPHONE\nIntermittent data", "Offline-first app\nOn-device diagnosis\nSyncs when online", "Typical smallholder"),
        (5.6, "SMARTPHONE\nRegular data", "Full web platform\nAI chat + advisory\nMarketplace", "Commercial farmer\n/ trader"),
        (7.75, "DESKTOP / API\nBusiness user", "Bulk trading\nAnalytics\nIntegrations", "Agribusiness\ncooperative, processor"),
    ]
    for x, head, mid, who in tiers:
        box(ax, x, 3.55, 1.95, 0.72, head, fs=8)
        box(ax, x, 2.45, 1.95, 0.92, mid, fs=7.6)
        box(ax, x, 1.35, 1.95, 0.66, who, fs=7.6, dashed=True)
        arrow(ax, x, 3.19, x, 2.91)
        arrow(ax, x, 1.99, x, 1.68)

    ax.annotate("", xy=(8.85, 0.6), xytext=(0.2, 0.6),
                arrowprops=dict(arrowstyle="-|>", color="black", linewidth=1.2))
    ax.text(4.5, 0.36, "increasing device capability and income  →  no farmer is excluded",
            fontsize=8.4, ha="center", style="italic")
    finish(fig, ax, "fig4_inclusivity.png", (0.0, 9.0), (0.1, 4.8))


# ---------------------------------------------------------------- Fig 5
def fig_roadmap():
    fig, ax = plt.subplots(figsize=(9.0, 4.6))
    phases = [
        ("PHASE 1\nCore platform", "COMPLETE", 0.4, 2.35),
        ("PHASE 2\nDeployment\n& pilot", "NEXT", 2.55, 1.9),
        ("PHASE 3\nInclusion\n(USSD/SMS,\nlanguages)", "PLANNED", 4.65, 1.9),
        ("PHASE 4\nPayments,\nlogistics,\nfinance", "PLANNED", 6.75, 1.9),
    ]
    for label, status, x, w in phases:
        box(ax, x + w / 2, 2.7, w, 1.0, label, fs=8.4)
        box(ax, x + w / 2, 1.55, w, 0.5, status, fs=8,
            dashed=(status != "COMPLETE"), lw=1.6 if status == "COMPLETE" else 1.1)
        if x > 0.4:
            arrow(ax, x - 0.15, 2.7, x + 0.02, 2.7)

    ax.annotate("", xy=(8.8, 0.75), xytext=(0.3, 0.75),
                arrowprops=dict(arrowstyle="-|>", color="black", linewidth=1.2))
    ax.text(0.4, 0.5, "today", fontsize=8, style="italic")
    ax.text(8.6, 0.5, "scale", fontsize=8, style="italic", ha="right")
    ax.text(4.5, 3.9, "DEVELOPMENT ROADMAP", fontsize=10, ha="center", weight="bold")
    finish(fig, ax, "fig5_roadmap.png", (0.0, 9.0), (0.2, 4.2))


# ---------------------------------------------------------------- Fig 6
def fig_revenue():
    fig, ax = plt.subplots(figsize=(9.0, 5.2))
    box(ax, 4.5, 4.6, 3.2, 0.6, "AGRITECH SUITE\nRevenue engine", fs=9)

    streams = [
        (1.15, "Marketplace\ncommission", "small % on\ncompleted trades"),
        (3.05, "Premium\nsubscription", "verified badge,\npriority listing,\nprice alerts"),
        (4.95, "Business /\nAPI tier", "cooperatives,\nprocessors,\nexporters"),
        (6.85, "Input & service\nreferrals", "seed, fertiliser,\nvet, logistics"),
        (8.6, "Data & insight\nreports (aggregate,\nconsented)", "anonymised\nmarket trends"),
    ]
    for x, head, sub in streams:
        box(ax, x, 3.0, 1.7, 0.62, head, fs=7.8)
        box(ax, x, 1.95, 1.7, 0.7, sub, fs=7.2, dashed=True)
        arrow(ax, 4.5, 4.28, x, 3.35)
        arrow(ax, x, 2.67, x, 2.32)

    box(ax, 4.5, 0.75, 8.2, 0.66,
        "FREE FOREVER TIER — diagnosis, advisory, news, community, basic listings\n"
        "(the platform earns only when the farmer earns)", fs=8.4)
    finish(fig, ax, "fig6_revenue.png", (0.0, 9.5), (0.3, 5.05))


if __name__ == "__main__":
    fig_architecture()
    fig_diagnosis_flow()
    fig_marketplace()
    fig_inclusivity()
    fig_roadmap()
    fig_revenue()
    print("All diagrams generated.")
