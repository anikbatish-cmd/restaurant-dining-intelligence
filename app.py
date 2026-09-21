import html

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from data_lab import PLATFORM_NOTES, PLATFORM_ROLES
from report_engine import build_report
from trends import load_monthly_history, save_monthly_snapshot, latest_changes, persistence_ready


st.set_page_config(
    page_title="Dining Intelligence",
    page_icon="◉",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# -----------------------------------------------------------------------------
# VISUAL SYSTEM
# -----------------------------------------------------------------------------

st.markdown(
    """
    <style>
        :root {
            --bg:#07111f;
            --panel:#0d1b2a;
            --panel2:#13243a;
            --line:rgba(137,190,255,.16);
            --text:#f7f9fc;
            --muted:#93a7bf;
            --green:#55d7ff;
            --green2:#4aa3ff;
            --amber:#ffc857;
            --red:#ff7d73;
            --blue:#69b7ff;
            --purple:#b89cff;
        }
        .stApp {
            background:
                radial-gradient(circle at 10% -10%, rgba(43,112,190,.22), transparent 32rem),
                radial-gradient(circle at 92% 5%, rgba(84,214,255,.10), transparent 30rem),
                linear-gradient(180deg,#07111f,#050b14 62%);
            color:var(--text);
        }
        [data-testid="stHeader"]{background:transparent;}
        .block-container{max-width:1500px;padding-top:1.1rem;padding-bottom:4.5rem;}
        h1,h2,h3,h4{letter-spacing:-.03em;color:var(--text)}
        p,label,.stCaption{color:#c1cec8}
        .brandbar{display:flex;justify-content:space-between;align-items:center;margin-bottom:.8rem;gap:1rem;}
        .brandname{display:flex;align-items:center;gap:.65rem;font-weight:850;font-size:1.03rem;}
        .brandmark{width:31px;height:31px;border-radius:9px;background:linear-gradient(145deg,#69dcff,#4776ff);box-shadow:0 0 28px rgba(84,214,255,.22)}
        .micro{font-size:.69rem;text-transform:uppercase;letter-spacing:.14em;font-weight:800;color:#70887d}
        .hero{position:relative;overflow:hidden;border:1px solid var(--line);border-radius:28px;padding:1.45rem 1.65rem;background:linear-gradient(125deg,rgba(16,39,67,.98),rgba(8,18,32,.97));box-shadow:0 26px 80px rgba(0,0,0,.26);margin-bottom:1rem;}
        .hero:before{content:"";position:absolute;width:410px;height:410px;border-radius:50%;right:-145px;top:-215px;background:radial-gradient(circle,rgba(84,214,255,.18),transparent 68%)}
        .hero h1{font-size:clamp(2rem,4vw,3.4rem);line-height:.94;max-width:900px;margin:.45rem 0 .8rem;font-weight:900;}
        .hero-copy{max-width:820px;color:#9eb2c9;font-size:1.02rem;line-height:1.6}
        .pillrow{display:flex;flex-wrap:wrap;gap:.5rem;margin-top:1.2rem}.pill{border:1px solid rgba(84,214,255,.18);background:rgba(84,214,255,.07);padding:.4rem .7rem;border-radius:999px;font-size:.75rem;color:#cceeff}
        .story{border:1px solid rgba(143,240,189,.18);background:linear-gradient(135deg,rgba(27,52,42,.72),rgba(12,23,19,.74));border-radius:22px;padding:1.15rem 1.25rem;margin:.8rem 0 1.1rem;}
        .story-line{font-size:1.02rem;line-height:1.52;color:#dce7e1;margin:.34rem 0}.story-line:before{content:"↳";color:#7de0aa;margin-right:.6rem}
        .metriccard{min-height:128px;border:1px solid var(--line);border-radius:20px;padding:1.05rem 1.05rem;background:linear-gradient(180deg,rgba(15,31,50,.94),rgba(8,18,31,.96));}
        .metriclabel{font-size:.68rem;text-transform:uppercase;letter-spacing:.1em;font-weight:800;color:#7f98b3}.metricvalue{font-size:1.95rem;font-weight:900;margin-top:.42rem;color:#ffffff}.metricsub{font-size:.74rem;line-height:1.4;color:#8298b0;margin-top:.43rem}
        .metriccard.risk{border-color:rgba(255,124,135,.30)}.metriccard.good{border-color:rgba(78,210,143,.30)}.metriccard.watch{border-color:rgba(240,199,107,.28)}
        .signal{border:1px solid var(--line);border-radius:19px;padding:1.05rem;background:linear-gradient(180deg,rgba(14,28,45,.96),rgba(7,16,28,.97));min-height:218px;margin-bottom:.75rem}.signal.critical{border-color:rgba(255,124,135,.35)}.signal.watch{border-color:rgba(240,199,107,.30)}.signal.opportunity{border-color:rgba(131,184,255,.30)}.signal.advantage{border-color:rgba(78,210,143,.30)}
        .sighead{display:flex;justify-content:space-between;gap:.7rem;align-items:center}.badge{font-size:.65rem;text-transform:uppercase;letter-spacing:.08em;font-weight:850;border-radius:999px;padding:.27rem .54rem;background:rgba(255,255,255,.055);color:#d4dfda}.score{font-size:.7rem;color:#71887d}.sigtitle{font-size:1.13rem;font-weight:850;margin:.7rem 0 .42rem}.sigvalue{font-size:.86rem;color:#74ddff;font-weight:720}.sigwhy{font-size:.8rem;color:#94a9c0;line-height:1.5;margin-top:.55rem}
        .gapcard{border-radius:18px;padding:1rem;border:1px solid var(--line);background:rgba(13,27,44,.88);min-height:155px}.gapname{font-size:.69rem;text-transform:uppercase;letter-spacing:.1em;color:#8098b2;font-weight:800}.gapvalue{font-size:1.75rem;font-weight:900;margin:.42rem 0}.gapcopy{font-size:.76rem;line-height:1.42;color:#91a6bd}
        .position-card{border:1px solid rgba(197,166,255,.20);background:linear-gradient(140deg,rgba(47,54,92,.34),rgba(10,24,40,.82));border-radius:22px;padding:1.2rem 1.25rem}.position-name{font-size:1.65rem;font-weight:900}.position-copy{color:#a8b8ca;margin-top:.35rem;line-height:1.5}
        .tag{display:inline-block;border-radius:999px;padding:.35rem .62rem;margin:.2rem .18rem .2rem 0;font-size:.72rem;background:rgba(131,184,255,.08);border:1px solid rgba(131,184,255,.16);color:#bcd4f8}
        div[data-baseweb="tab-list"]{gap:.3rem;background:rgba(11,20,17,.8);border:1px solid rgba(255,255,255,.055);padding:.32rem;border-radius:15px}button[data-baseweb="tab"]{border-radius:10px;padding-left:1rem;padding-right:1rem}
        [data-testid="stForm"]{background:rgba(12,23,19,.78);border:1px solid var(--line);border-radius:18px;padding:.9rem 1rem .25rem}
        [data-testid="stDataFrame"]{border:1px solid rgba(255,255,255,.06);border-radius:14px;overflow:hidden}[data-testid="stExpander"]{border-color:rgba(255,255,255,.07);border-radius:14px;background:rgba(10,18,15,.45)}
        .stButton>button,.stFormSubmitButton>button{border-radius:12px;min-height:44px;font-weight:780}
        @media(max-width:720px){.hero{padding:1.35rem}.hero h1{font-size:2.5rem}.signal{min-height:auto}}
    </style>
    """,
    unsafe_allow_html=True,
)


def esc(value):
    return html.escape(str(value if value is not None else "—"))


def money(value):
    return f"₹{value:,.0f}" if value is not None else "—"


def number(value):
    return f"{value:,.0f}" if value is not None else "—"


def metric_card(label, value, sub, tone=""):
    st.markdown(
        f'<div class="metriccard {tone}"><div class="metriclabel">{esc(label)}</div><div class="metricvalue">{esc(value)}</div><div class="metricsub">{esc(sub)}</div></div>',
        unsafe_allow_html=True,
    )


def signal_card(signal):
    severity = signal.get("severity", "Watch")
    st.markdown(
        f'''<div class="signal {severity.lower()}">
        <div class="sighead"><span class="badge">#{signal.get('rank','—')} · {esc(severity)} · {esc(signal.get('category','Signal'))}</span><span class="score">priority {signal.get('score',0)}/100</span></div>
        <div class="sigtitle">{esc(signal.get('title',''))}</div>
        <div class="sigvalue">{esc(signal.get('signal',''))}</div>
        <div class="sigwhy">{esc(signal.get('why',''))}</div>
        </div>''',
        unsafe_allow_html=True,
    )


def gap_card(name, value, copy, tone=""):
    st.markdown(
        f'<div class="gapcard {tone}"><div class="gapname">{esc(name)}</div><div class="gapvalue">{esc(value)}</div><div class="gapcopy">{esc(copy)}</div></div>',
        unsafe_allow_html=True,
    )


def market_map_figure(restaurant, target, competitors):
    rows = []
    if target.get("rating") is not None and target.get("cost_for_two") is not None:
        rows.append({
            "Restaurant": restaurant,
            "Cost for Two": target.get("cost_for_two"),
            "Rating": target.get("rating"),
            "Reviews": target.get("review_count") or 1,
            "Role": "Target",
        })
    for item in competitors:
        m = item.get("metrics", {})
        if m.get("rating") is None or m.get("cost_for_two") is None:
            continue
        rows.append({
            "Restaurant": item.get("name"),
            "Cost for Two": m.get("cost_for_two"),
            "Rating": m.get("rating"),
            "Reviews": m.get("review_count") or 1,
            "Role": "Competitor",
        })
    if len(rows) < 2:
        return None
    df = pd.DataFrame(rows)
    fig = px.scatter(
        df,
        x="Cost for Two",
        y="Rating",
        size="Reviews",
        color="Role",
        hover_name="Restaurant",
        hover_data={"Reviews": True, "Role": False},
        text="Restaurant",
        size_max=42,
        color_discrete_map={"Target": "#55d7ff", "Competitor": "#657d98"},
    )
    fig.update_traces(textposition="top center", textfont_size=11)
    fig.update_layout(
        height=500,
        margin=dict(l=10,r=10,t=30,b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(8,16,13,.35)",
        font=dict(color="#dbe8f5"),
        legend=dict(orientation="h", y=1.08, x=0),
        xaxis=dict(gridcolor="rgba(255,255,255,.06)", title="Public cost for two"),
        yaxis=dict(gridcolor="rgba(255,255,255,.06)", title="Public rating", range=[3,5]),
    )
    return fig


# -----------------------------------------------------------------------------
# HEADER
# -----------------------------------------------------------------------------

st.markdown('<div class="brandbar"><div class="brandname"><span class="brandmark"></span>Dining Intelligence</div><div class="micro">Restaurant market intelligence OS · dine-in only</div></div>', unsafe_allow_html=True)
st.markdown(
    '''<div class="hero"><div class="micro">Dining Intelligence</div><h1>Restaurant market scan.</h1><div class="hero-copy">Competitive position · customer signals · discovery · platform truth</div></div>''',
    unsafe_allow_html=True,
)

with st.form("search"):
    c1,c2,c3=st.columns([1.5,.85,.6])
    with c1:
        restaurant_input=st.text_input("Restaurant",value=st.session_state.get("last_restaurant",""),placeholder="Kijiji - On The Roof")
    with c2:
        location_input=st.text_input("Location",value=st.session_state.get("last_location",""),placeholder="Gurgaon")
    with c3:
        st.write("")
        submitted=st.form_submit_button("Run intelligence scan",type="primary",use_container_width=True)

if submitted:
    restaurant_input=restaurant_input.strip();location_input=location_input.strip()
    if not restaurant_input or not location_input:
        st.warning("Enter both restaurant name and location.")
    else:
        st.session_state["last_restaurant"]=restaurant_input;st.session_state["last_location"]=location_input
        with st.status("Building the outside-in market view…",expanded=False) as status:
            st.session_state["report"]=build_report(restaurant_input,location_input)
            status.update(label="Market intelligence ready",state="complete")

report=st.session_state.get("report")
if not report:
    cols=st.columns(4)
    previews=[("01","Market position","Where price and reputation place the restaurant."),("02","Signal radar","The anomalies that deserve a conversation."),("03","Demand gaps","Where reputation, discovery, advocacy or promotions are misaligned."),("04","Evidence lab","Why every number exists and where it came from.")]
    for col,(n,t,c) in zip(cols,previews):
        with col: gap_card(n+" · "+t,"→",c)
    st.stop()

restaurant=report["restaurant"];location=report["location"];target=report["benchmark_target"];competitors=report["competitors"]
cm=report["competitive_metrics"];gaps=report["gap_metrics"];market=report["market_position"];signals=report["signals"]
source_summaries=report["source_summaries"];customer=report["customer_voice"];content=report["content_summary"];discovery=report["discovery"]

# Presentation-grade evidence coverage: count only actually observed public fields.
core_fields = [target.get("rating"), target.get("review_count"), target.get("cost_for_two"), target.get("discount_percent")]
observed_core = sum(v is not None for v in core_fields)
active_sources = sum(1 for v in source_summaries.values() if v and any(v.get(k) is not None for k in ["rating","review_count","cost_for_two","discount_percent"]))
coverage_pct = round((observed_core / 4) * 70 + min(active_sources, 3) / 3 * 30)

head1,head2=st.columns([4,1])
with head1:
    st.markdown(f"## {restaurant}")
    st.caption(f"{location} · {len(competitors)}-restaurant cohort · District primary when available")
with head2:
    if st.button("↻ Refresh",use_container_width=True):
        build_report.clear();st.session_state["report"]=build_report(restaurant,location);st.rerun()

# Headline metrics
cols=st.columns(5)
with cols[0]: metric_card("Market position",market.get("quadrant","—"),f"{market.get('price_delta_pct',0):+.0f}% price · {market.get('rating_gap',0):+.1f} rating" if market.get("price_delta_pct") is not None else "insufficient public data")
with cols[1]: metric_card("Price index",f"{cm.get('price_index'):.2f}x" if cm.get("price_index") is not None else "—","vs cohort","watch" if cm.get("price_index") and cm.get("price_index")>1.1 else "")
with cols[2]: metric_card("Rating gap",f"{cm.get('rating_gap'):+.1f}" if cm.get("rating_gap") is not None else "—","vs cohort","risk" if cm.get("rating_gap") is not None and cm.get("rating_gap")<0 else "good")
with cols[3]: metric_card("Evidence coverage",f"{coverage_pct}%","verified public fields","good" if coverage_pct>=75 else "watch")
with cols[4]: metric_card("Platform fragmentation",f"{gaps.get('platform_fragmentation_index'):.0f}/100" if gaps.get("platform_fragmentation_index") is not None else "—","cross-platform variance","risk" if gaps.get("platform_fragmentation_index") is not None and gaps.get("platform_fragmentation_index")>=55 else "")

st.write("")
tabs=st.tabs(["◉ Command Center","↗ Monthly Pulse","⌁ Market Map","△ Customer Reality","◎ Attention & Discovery","⇄ Platform Truth","⌘ Data Lab"])

with tabs[0]:
    st.markdown("### The signals worth discussing")
    for start in range(0,min(6,len(signals)),3):
        row=st.columns(3)
        for col,s in zip(row,signals[start:start+3]):
            with col: signal_card(s)

with tabs[1]:
    st.markdown("### Monthly Pulse")
    st.caption("What changed since the last monthly snapshot — the recurring layer for owner reviews.")
    history = load_monthly_history(restaurant, location)
    if persistence_ready():
        save_monthly_snapshot(report)
        history = load_monthly_history(restaurant, location)
    if len(history) >= 2:
        changes = latest_changes(history)
        mc = st.columns(5)
        latest = history[-1]
        with mc[0]: metric_card("Rating", f"{latest.get('rating'):.1f}" if latest.get('rating') is not None else "—", f"{changes.get('rating'):+.1f} MoM" if changes.get('rating') is not None else "no comparable change")
        with mc[1]: metric_card("Public reviews", number(latest.get("review_count")), f"{changes.get('review_count'):+,.0f} MoM" if changes.get('review_count') is not None else "no comparable change")
        with mc[2]: metric_card("Instagram", number(latest.get("instagram_followers")), f"{changes.get('instagram_followers'):+,.0f} followers" if changes.get('instagram_followers') is not None else "no comparable change")
        with mc[3]: metric_card("Discovery", f"{latest.get('discovery_share'):.0%}" if latest.get('discovery_share') is not None else "—", f"{changes.get('discovery_share'):+.1%} MoM" if changes.get('discovery_share') is not None else "no comparable change")
        with mc[4]: metric_card("Offer", f"{latest.get('discount_percent'):.0f}%" if latest.get('discount_percent') is not None else "—", f"{changes.get('discount_percent'):+.0f} pp MoM" if changes.get('discount_percent') is not None else "no comparable change")

        trend_df = pd.DataFrame(history)
        left_t, right_t = st.columns(2)
        with left_t:
            if trend_df["review_count"].notna().sum() >= 2:
                fig = px.line(trend_df, x="month", y="review_count", markers=True, title="Public review growth")
                fig.update_layout(height=330, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font=dict(color="#dbe8f5"), margin=dict(l=10,r=10,t=45,b=10))
                st.plotly_chart(fig, use_container_width=True, config={"displayModeBar":False})
        with right_t:
            if trend_df["instagram_followers"].notna().sum() >= 2:
                fig = px.line(trend_df, x="month", y="instagram_followers", markers=True, title="Instagram audience")
                fig.update_layout(height=330, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font=dict(color="#dbe8f5"), margin=dict(l=10,r=10,t=45,b=10))
                st.plotly_chart(fig, use_container_width=True, config={"displayModeBar":False})

        st.markdown("#### Month-over-month scorecard")
        show_cols = ["month","rating","review_count","cost_for_two","discount_percent","rating_gap","instagram_followers","discovery_share","top_strength","top_concern"]
        st.dataframe(trend_df[[x for x in show_cols if x in trend_df.columns]], use_container_width=True, hide_index=True)
    elif persistence_ready():
        st.info("Baseline captured. From the next monthly snapshot, this page will show movement instead of a static profile.")
    else:
        st.info("Monthly tracking is built, but persistent storage is not connected yet. Add the two Supabase secrets to start accumulating merchant history.")

with tabs[2]:
    left,right=st.columns([1.45,.55])
    with left:
        st.markdown("### Price × reputation battlefield")
        fig=market_map_figure(restaurant,target,competitors)
        if fig: st.plotly_chart(fig,use_container_width=True,config={"displayModeBar":False})
        else: st.info("Not enough comparable price/rating data to draw the battlefield.")
    with right:
        st.markdown("### Positioning read")
        st.markdown(f'<div class="position-card"><div class="micro">Current quadrant</div><div class="position-name">{esc(market.get("quadrant"))}</div><div class="position-copy">{esc(market.get("headline"))}</div></div>',unsafe_allow_html=True)
        st.markdown("#### White space")
        ws=report["white_space"]
        if ws.get("distinctive_tags"):
            for tag in ws["distinctive_tags"]: st.markdown(f'<span class="tag">{esc(tag)}</span>',unsafe_allow_html=True)
        else: st.caption("No clearly distinctive public positioning cue surfaced.")
        st.markdown("#### Crowded territory")
        if ws.get("crowded_tags"):
            for tag in ws["crowded_tags"]: st.markdown(f'<span class="tag">{esc(tag)}</span>',unsafe_allow_html=True)
        else: st.caption("No strongly crowded positioning cue detected.")
    st.markdown("### Competitive cohort")
    rows=[]
    rows.append({"Restaurant":restaurant,"Role":"TARGET","Match %":100,"Rating":target.get("rating"),"Reviews":target.get("review_count"),"Cost for Two":target.get("cost_for_two"),"Offer %":target.get("discount_percent")})
    for item in competitors:
        m=item.get("metrics",{});rows.append({"Restaurant":item.get("name"),"Role":"Competitor","Match %":item.get("match_score",0)*100,"Rating":m.get("rating"),"Reviews":m.get("review_count"),"Cost for Two":m.get("cost_for_two"),"Offer %":m.get("discount_percent")})
    st.dataframe(pd.DataFrame(rows),use_container_width=True,hide_index=True,column_config={"Match %":st.column_config.ProgressColumn(min_value=0,max_value=100,format="%.0f%%"),"Rating":st.column_config.NumberColumn(format="%.1f"),"Cost for Two":st.column_config.NumberColumn(format="₹%d"),"Offer %":st.column_config.NumberColumn(format="%d%%")})
    with st.expander("How competitors are selected"):
        st.markdown("**Final match = 50% price + 25% cuisine + 15% positioning + 10% location.**")
        st.caption("Small fallback adjustments apply when cuisine or positioning is not exposed publicly. Price is intentionally the dominant criterion because the dashboard is trying to identify restaurants competing for a similar spending occasion.")
        for item in competitors:
            p=item.get("match_components",{});st.write(f"**{item.get('name')}** · Price {p.get('price_similarity',0):.0%} · Cuisine {p.get('cuisine_similarity',0):.0%} · Positioning {p.get('positioning_similarity',0):.0%} · Location {p.get('location_score',0):.0%}")

with tabs[3]:
    st.markdown("### What customers reward vs punish")
    topics=customer.get("topics",[])
    if topics:
        df=pd.DataFrame([{"Topic":x["topic"],"Mentions":x["mentions"],"Positive":x["positive"],"Negative":x["negative"],"Net sentiment":x["net_sentiment"]} for x in topics])
        fig=go.Figure()
        fig.add_bar(y=df["Topic"],x=df["Positive"],name="Positive",orientation="h",marker_color="#48cfa0")
        fig.add_bar(y=df["Topic"],x=-df["Negative"],name="Negative",orientation="h",marker_color="#ff7d73")
        fig.update_layout(barmode="relative",height=430,paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",font=dict(color="#dbe8f5"),margin=dict(l=10,r=10,t=20,b=10),xaxis=dict(gridcolor="rgba(255,255,255,.06)"),legend=dict(orientation="h"))
        st.plotly_chart(fig,use_container_width=True,config={"displayModeBar":False})
        st.dataframe(df,use_container_width=True,hide_index=True)
    else: st.info("The current public sample is too thin for a customer-theme view.")
    with st.expander("Review evidence"):
        for item in customer.get("evidence",[])[:20]:
            st.markdown(f"**{item.get('title','')}**");st.write(item.get("snippet",""));
            if item.get("url"): st.markdown(item["url"])
            st.divider()

with tabs[4]:
    m1,m2,m3,m4=st.columns(4)
    ig=report["instagram_metrics"]
    with m1: metric_card("Instagram audience",number(ig.get("followers")),"canonical indexed profile")
    with m2: metric_card("Content sample",content.get("sample_size",0),"owned + creator/UGC")
    with m3: metric_card("Creator lift",f"{content.get('creator_lift'):.2f}x" if content.get("creator_lift") is not None else "—","visible engagement only")
    share=discovery.get("share_of_observed_mentions")
    with m4: metric_card("Discovery share",f"{share:.0%}" if share is not None else "—","share of observed cohort mentions","risk" if share is not None and share<.15 else "")
    left,right=st.columns(2)
    with left:
        st.markdown("### Content territories")
        if content.get("themes"): st.dataframe(pd.DataFrame(content["themes"]),use_container_width=True,hide_index=True)
        if ig.get("bio"): st.info(ig["bio"])
    with right:
        st.markdown("### Generic discovery matrix")
        rows=[{"Search occasion":x.get("query"),restaurant:"Surfaced" if x.get("target_found") else "Absent","Competitors surfaced":", ".join(x.get("competitors_found",[])) or "—"} for x in discovery.get("queries",[])]
        if rows: st.dataframe(pd.DataFrame(rows),use_container_width=True,hide_index=True)

    with st.expander("Content / creator evidence"):
        for item in report["content_items"][:20]:
            st.markdown(f"**{item.get('type')} · {item.get('theme')}**");st.write(item.get("snippet",""));
            if item.get("url"): st.markdown(item["url"])
            st.divider()

with tabs[5]:
    st.markdown("### Where platforms disagree")
    tensions=report["platform_tensions"]
    if tensions:
        with st.expander("Platform differences", expanded=False):
            for t in tensions:
                st.markdown(f"**{t.get('title')}** · {t.get('signal')}")
    comparison=pd.DataFrame(report["platform_comparison"])
    if not comparison.empty:
        columns=["Platform","Role","Rating","Δ rating vs District","Ratings / Reviews","Cost for Two","Δ price vs District %","Top Offer %","Confidence","Method"]
        st.dataframe(comparison[[c for c in columns if c in comparison.columns]],use_container_width=True,hide_index=True)

with tabs[6]:
    st.markdown("### Metric logic explorer")
    dictionary=report["metric_dictionary"]
    names=[x["Metric"] for x in dictionary]
    if names:
        choice=st.selectbox("Metric",names)
        item=next(x for x in dictionary if x["Metric"]==choice)
        st.code(item["Formula"],language=None)
        st.markdown(f"**Current value:** {item['Value']}  \n**Live calculation:** {item['Live calculation']}  \n**Interpretation:** {item['Interpretation']}  \n**Guardrail:** {item['Guardrail']}  \n**Source layer:** {item['Source']}")
    st.markdown("### Scan performance")
    st.dataframe(pd.DataFrame([report["scan_summary"]]),use_container_width=True,hide_index=True)
    if report.get("search_errors"):
        st.markdown("### Search coverage / failures")
        st.dataframe(pd.DataFrame(report["search_errors"]),use_container_width=True,hide_index=True)
    st.markdown("### Instagram freshness audit")
    if report.get("instagram_snapshots"): st.dataframe(pd.DataFrame(report["instagram_snapshots"]),use_container_width=True,hide_index=True)
    with st.expander("Raw platform evidence"):
        for source,items in report["dining_metrics"].get("by_source",{}).items():
            st.markdown(f"### {source}")
            for item in items:
                st.markdown(f"**{item.get('title','')}**");st.caption(f"{item.get('extraction_method','search_snippet').replace('_',' ').title()} · {item.get('confidence','Medium')} confidence");st.write(item.get("snippet",""));
                if item.get("url"): st.markdown(item["url"])
                st.divider()

st.divider()
st.caption("Claim boundary · Public-market intelligence only. The dashboard does not infer footfall, bookings, revenue, profitability, paid spend, ROAS or causal business impact without internal restaurant data.")
