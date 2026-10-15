"""Build REAU Studio case study pages.

Usage:  python3 cases/build.py            (builds every cases/*.json)
Output: work/<slug>.html

Each case study is one JSON file in cases/. Images go in assets/work/<slug>/
using the filename given in the JSON (the original Squarespace filenames).
Any image that is present is used; any that is missing shows a labelled
placeholder, so pages can go live before every asset is ready.
Sections whose data is empty are left out entirely.
"""
import json, os, re, glob, html

ROOT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "site")
E = lambda s: html.escape(str(s), quote=True)


# ---------------------------------------------------------------- shared CSS
def shared_css():
    """Lift header, buttons, dog strip, section opener and footer styles from the home page."""
    s = open(os.path.join(ROOT, "index.html")).read()
    css = s[s.index("<style>") + 7 : s.index("</style>")]
    def between(a, b):
        i = css.index(a); j = css.index(b, i); return css[i:j]
    parts = [
        between(":root{", "/* ---------- hero"),
        "\n".join(l for l in css.splitlines() if l.startswith(".btn")),
        between("/* dalmatian sprite", "/* ---------- section heads"),
        between(".inquire{", "@media (max-width:860px){.foot"),
        "@media (max-width:860px){.foot{grid-template-columns:repeat(2,minmax(0,1fr))}}",
    ]
    return "\n".join(parts)


CASE_CSS = r"""
/* ================= case study ================= */
main{display:block}
.sec{padding-block:clamp(80px,11vw,170px)}
.sec.tight{padding-top:0}

/* hero */
.c-hero{padding-top:calc(var(--hdr) + clamp(20px,3vw,40px));padding-bottom:clamp(40px,6vw,80px)}
.c-top{display:flex;justify-content:space-between;align-items:center;gap:16px;color:var(--mute);margin-bottom:clamp(56px,10vw,150px)}
.c-top .l{display:flex;gap:12px;align-items:center}
.c-top a{text-decoration:none}
.c-top a:hover{color:var(--ink)}
.c-top .l{white-space:nowrap}
@media (max-width:600px){.c-top>span:last-child{display:none}}
.dot{width:6px;height:6px;border-radius:50%;background:var(--oxblood);flex:none}
.c-hero .wordmark{margin-bottom:clamp(28px,4vw,56px)}
.c-intro{display:grid;grid-template-columns:minmax(0,1.4fr) minmax(0,1fr);gap:clamp(28px,6vw,110px);align-items:start;margin-bottom:clamp(48px,7vw,96px)}
.c-intro .sum{font-family:var(--serif);font-size:clamp(1.7rem,3vw,2.8rem);line-height:1.12;letter-spacing:-.015em;text-wrap:balance}
.meta{display:grid;grid-template-columns:auto minmax(0,1fr);gap:0;margin:0;border-top:1px solid var(--line)}
.meta dt,.meta dd{padding:12px 0;border-bottom:1px solid var(--line);margin:0}
.meta dt{color:var(--mute);padding-right:24px}
.meta dd{text-align:right}
.meta a{text-decoration:none;border-bottom:1px solid var(--line)}
.meta dd{overflow-wrap:anywhere}
@media (max-width:860px){.c-intro{grid-template-columns:minmax(0,1fr)}}
.meta a:hover{border-color:var(--ink)}

.meta .svc{display:flex;flex-direction:column;gap:4px}

/* at a glance */
.glance-grid{display:grid;grid-template-columns:minmax(0,1.15fr) minmax(0,1fr);gap:clamp(28px,6vw,110px);align-items:start;margin-bottom:clamp(56px,8vw,110px)}
.glance-grid .ov{font-family:var(--serif);font-size:clamp(1.7rem,3vw,2.8rem);line-height:1.12;letter-spacing:-.015em;text-wrap:balance}
.winsbox{border-top:1px solid var(--ink)}
.winsbox>.label{display:block;color:var(--mute);padding:12px 0 6px}
.wins{list-style:none;margin:0;padding:0}
.wins li{display:grid;grid-template-columns:1.6rem minmax(0,1fr);gap:10px;padding:14px 0;border-bottom:1px solid var(--line);font-size:1.02rem;line-height:1.45}
.wins li::before{content:"";width:7px;height:7px;border-radius:50%;background:var(--oxblood);margin-top:.55em}
@media (max-width:860px){.glance-grid{grid-template-columns:minmax(0,1fr)}}

/* four-stage strip */
.stages-h{color:var(--mute);margin-bottom:14px}
.stages{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:clamp(10px,1.2vw,16px)}
.stages figcaption{display:flex;gap:10px}
.stages figcaption b{font-weight:500;color:var(--ink)}
@media (max-width:640px){.stages{grid-template-columns:repeat(2,minmax(0,1fr));row-gap:22px}}

/* ecosystem flow */
.flow{list-style:none;margin:0;padding:0;display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:0;border-top:1px solid var(--ink)}
.flow li{display:flex;flex-direction:column;gap:10px;padding:18px clamp(10px,1.4vw,20px) 22px 0;border-right:1px solid var(--line);min-width:0}
.flow li+li{padding-left:clamp(10px,1.4vw,20px)}
.flow li:last-child{border-right:0}
.flow .n{color:var(--mute)}
.flow h3{font-size:clamp(1.15rem,1.45vw,1.45rem);line-height:1.05;overflow-wrap:anywhere}
.flow p{font-size:.92rem;color:var(--ink-2);line-height:1.45}
@media (max-width:860px){.flow{grid-template-columns:minmax(0,1fr)}.flow li{border-right:0;border-bottom:1px solid var(--line);padding:16px 0;display:grid;grid-template-columns:3rem minmax(0,1fr);column-gap:12px}.flow li+li{padding-left:0}.flow li .n{grid-row:span 2;padding-top:.3em}}

/* related case study */
.related{display:flex;flex-direction:column;gap:14px;border:1px solid var(--line);border-radius:6px;padding:clamp(20px,3vw,32px);text-decoration:none;transition:background .5s var(--ease),color .5s var(--ease),border-color .5s}
.related .row1{display:flex;justify-content:space-between;gap:12px}
.related .row1 .label:last-child{color:var(--mute)}
.related h3{font-size:clamp(2rem,3.6vw,3.2rem);display:flex;gap:.3em;align-items:center}
.related p{color:var(--mute);max-width:30em}
.related.live:hover{background:var(--ink);color:var(--paper);border-color:var(--ink)}
.related .arr{font-family:var(--sans);font-size:.5em;transition:transform .5s var(--ease)}
.related.live:hover .arr{transform:translateX(6px)}

html{scroll-behavior:auto}
html.ready{scroll-behavior:smooth}
@media (prefers-reduced-motion:reduce){html.ready{scroll-behavior:auto}}

/* stacked chapter layout */
.chapter.stacked .ch-grid{grid-template-columns:minmax(0,1fr);gap:clamp(36px,5vw,64px)}
.ch-head{display:flex;align-items:baseline;gap:clamp(18px,3vw,44px);flex-wrap:wrap}
.chapter.stacked .ch-num{font-family:var(--sans);font-weight:400;font-size:clamp(1rem,1.2vw,1.1rem);letter-spacing:.16em;color:var(--mute);line-height:1}
.chapter.stacked h2{font-family:var(--sans);font-weight:400;font-size:clamp(2.8rem,7.4vw,7.4rem);line-height:.92;letter-spacing:-.04em}
.chapter.stacked .ch-body{max-width:none;columns:2 22em;column-gap:clamp(28px,5vw,80px);display:block}
.chapter.stacked .ch-body p{break-inside:avoid;margin-bottom:1.1em}

/* website showcase */
.showcase{display:grid;grid-template-columns:minmax(0,1fr) clamp(150px,17vw,230px);gap:clamp(16px,3vw,44px);align-items:end}
.browser{border:1px solid var(--line);border-radius:10px;overflow:hidden;background:var(--paper)}
.chrome{display:flex;align-items:center;gap:14px;padding:10px 14px;border-bottom:1px solid var(--line);flex-wrap:wrap}
.chrome .dots{display:flex;gap:6px}.chrome .dots i{width:9px;height:9px;border-radius:50%;border:1px solid var(--line);display:block}
.tabs{display:flex;gap:4px}
.tabs button{font:500 .7rem var(--sans);letter-spacing:.14em;text-transform:uppercase;color:var(--mute);background:none;border:1px solid transparent;border-radius:999px;padding:6px 12px;cursor:pointer;transition:color .3s,border-color .3s,background .3s}
.tabs button[aria-selected="true"]{color:var(--ink);border-color:var(--line)}
.tabs button:hover{color:var(--ink)}
.chrome .addr{margin-left:auto;font-size:.78rem;color:var(--mute);border:1px solid var(--line);border-radius:999px;padding:5px 14px}
.screen{position:relative;aspect-ratio:16/10;overflow:hidden;background:#ECEBE7;cursor:default}
.screen .shot img{transform:translateY(0);transition:transform 1.4s cubic-bezier(.45,0,.25,1);will-change:transform}
.shot{display:none}
.shot.on{display:block}
.shot img,.shot .ph{display:block;width:100%;height:auto}
.ph.tall{height:auto;aspect-ratio:16/26;justify-content:flex-start;padding-top:12%}
.phone{position:relative;border:1px solid var(--line);border-radius:28px;padding:10px;background:var(--paper)}
.phone .notch{width:34%;height:6px;border-radius:999px;background:var(--line);margin:2px auto 8px}
.phone .screen{aspect-ratio:9/19;border-radius:18px}
.phone .ph.tall{aspect-ratio:9/40}
.sc-foot{display:flex;justify-content:space-between;gap:16px;flex-wrap:wrap;margin-top:14px}
.sc-foot .label{color:var(--mute)}
.sc-foot a{text-decoration:none;color:var(--ink)}
.sc-foot a:hover{color:var(--oxblood)}
@media (max-width:700px){.showcase{grid-template-columns:minmax(0,1fr)}.phone{width:58%;margin:0 auto}.chrome .addr{display:none}}

/* single figure */
.r-54{aspect-ratio:5/4}
.solo{max-width:720px}
.solo figcaption{margin-top:4px}
.solo img{filter:grayscale(1)}

/* portfolio logo wall */
.logos{list-style:none;margin:0;padding:0;display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:2px;background:var(--paper)}
.logos li{position:relative;background:#0B0B0B;aspect-ratio:3/2;display:flex;align-items:center;justify-content:center;padding:14% 16%;overflow:hidden}
.logos li img{max-width:100%;max-height:52%;width:auto;height:auto;object-fit:contain;opacity:.86;transition:opacity .4s,transform .6s var(--ease)}
.logos li:hover img{opacity:1;transform:scale(1.04)}
.logos li .label{position:absolute;left:14px;bottom:12px;color:#8F8E8A;font-size:.58rem}
.logos li.hl{background:#151515;outline:1px solid rgba(243,242,238,.35);outline-offset:-1px}
.logos li.hl .label{color:#F3F2EE}
@media (max-width:700px){.logos{grid-template-columns:repeat(2,minmax(0,1fr))}}

/* roadmap */
.road{--p:0;position:relative;list-style:none;margin:0;padding:0 0 0 clamp(40px,6vw,72px)}
.road::before,.road .fill{content:"";position:absolute;left:7px;top:10px;width:1px;background:var(--line);bottom:10px}
.road .fill{background:var(--ink);bottom:auto;height:calc(var(--p) * (100% - 20px));transition:height .15s linear}
.road li{position:relative;padding-bottom:clamp(56px,8vw,110px);opacity:.32;transition:opacity .6s var(--ease)}
.road li:last-child{padding-bottom:0}
.road li.on{opacity:1}
.road li::before{content:"";position:absolute;left:calc(-1 * clamp(40px,6vw,72px) + 1px);top:.3em;width:13px;height:13px;border-radius:50%;border:1px solid var(--ink);background:var(--paper);transition:background .4s}
.road li.on::before{background:var(--ink)}
.road .k{color:var(--mute);display:block;margin-bottom:12px}
.road h3{font-family:var(--sans);font-weight:400;font-size:clamp(2.2rem,5vw,4.6rem);line-height:.95;letter-spacing:-.035em;margin-bottom:16px}
.road p{font-size:clamp(1.02rem,1.3vw,1.2rem);color:var(--mute);max-width:36em;line-height:1.55}
.js .road li{opacity:.32}
.js .road li.on{opacity:1}
@media (prefers-reduced-motion:reduce){.road li{opacity:1}}

/* dark theme: the brand reversed; header, menu, dog strip and footer keep their own palette */
body.ink{--paper:#0B0B0B;--ink:#F3F2EE;--ink-2:#D8D7D2;--mute:#8F8E8A;--unlit:#3C3C3A;--line:rgba(243,242,238,.15);background:#0B0B0B;color:#F3F2EE;color-scheme:dark}
body.ink .hdr,body.ink .strip,body.ink .sheet,body.ink .inquire{--paper:#FBFBF9;--ink:#0B0B0B;--ink-2:#1A1A1A;--mute:#6E6D6A;--unlit:#C8C7C2;--line:rgba(11,11,11,.13)}
body.ink .hdr,body.ink .strip{color:#0B0B0B}
body.ink .inquire{border-top:1px solid rgba(243,242,238,.12)}
body.ink .ph,body.ink .frame,body.ink .screen,body.ink .case .pic{background:#1A1A19}
body.ink .ph .t{color:#D8D7D2}
body.ink ::selection{background:#F3F2EE;color:#0B0B0B}

/* closing */
.closing .readthru{text-indent:0;max-width:19em}
.closing-cta{display:flex;justify-content:flex-end;margin-top:clamp(36px,5vw,64px)}

/* placeholder + media */
.ph{position:relative;background:#ECEBE7;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:6px;color:var(--mute);text-align:center;padding:16px;overflow:hidden}
.ph .t{font-size:.66rem;font-weight:500;letter-spacing:.18em;text-transform:uppercase;color:var(--ink-2)}
.ph .f{font-family:var(--serif);font-style:italic;font-size:.95rem;word-break:break-word}
.media{width:100%;height:100%;object-fit:cover;display:block}
.frame{overflow:hidden;border-radius:4px;background:#ECEBE7;max-width:100%}
.frame>.ph,.frame>img{width:100%;height:100%}
.r-wide{aspect-ratio:16/9}.r-43{aspect-ratio:4/3}.r-45{aspect-ratio:4/5}.r-916{aspect-ratio:9/16}

/* brief: read-through, as on the home page */
.readthru{font-family:var(--serif);font-size:clamp(2rem,4.2vw,4rem);line-height:1.1;letter-spacing:-.015em;max-width:21em;margin-left:auto;text-indent:clamp(0px,12vw,10rem)}
.js .readthru .w{opacity:.18}

/* stats */
.stats{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:clamp(20px,3vw,44px)}
.stat{display:flex;flex-direction:column;gap:12px;border-top:1px solid var(--line);padding-top:20px}
.stat .v{font-family:var(--sans);font-weight:400;font-size:clamp(3.2rem,6.6vw,6.4rem);line-height:.9;letter-spacing:-.04em;font-variant-numeric:tabular-nums}
.stat .l{color:var(--mute);font-size:.95rem;max-width:16em}
@media (max-width:900px){.stats{grid-template-columns:repeat(2,minmax(0,1fr));row-gap:40px}}

/* chapters */
.chapter{padding-block:clamp(80px,11vw,170px) 0}
.ch-grid{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,2fr);gap:clamp(28px,6vw,110px);align-items:start}
.ch-side{position:sticky;top:calc(var(--hdr) + 40px);display:flex;flex-direction:column;gap:14px}
.ch-num{font-family:var(--serif);font-style:normal;font-size:clamp(5rem,11vw,10rem);line-height:.8;letter-spacing:-.02em}
.ch-side .label{color:var(--mute)}
.ch-side h2{font-size:clamp(2.2rem,3.8vw,3.6rem)}
.ch-main{display:flex;flex-direction:column;gap:clamp(44px,6vw,80px);min-width:0}
.ch-body{display:flex;flex-direction:column;gap:1.1em;font-size:clamp(1.08rem,1.35vw,1.25rem);line-height:1.55;max-width:34em}
.delivered{display:flex;flex-wrap:wrap;gap:8px;align-items:center}
.delivered .label{color:var(--mute);margin-right:8px}
.chip{border:1px solid var(--line);border-radius:999px;padding:7px 14px;font-size:.85rem}
.pair{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:clamp(12px,1.6vw,20px)}
figure{margin:0;display:flex;flex-direction:column;gap:10px}
figcaption{color:var(--mute)}
.aside{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:clamp(16px,3vw,40px);border-top:1px solid var(--line);padding-top:20px}
.aside .v{font-family:var(--sans);font-size:clamp(2.2rem,3.6vw,3.2rem);line-height:1;letter-spacing:-.03em}
.aside .l{color:var(--mute);font-size:.92rem;margin-top:8px}
.milestone{display:flex;flex-direction:column;gap:12px;border-top:1px solid var(--line);padding-top:20px}
.milestone .v{font-family:var(--serif);font-size:clamp(3rem,7vw,6.4rem);line-height:.9;letter-spacing:-.02em}
.milestone .v i{font-style:normal;color:var(--oxblood);margin-inline:.18em}
.milestone .v i .ic{width:.7em;height:.7em;vertical-align:.02em}
.milestone .l{color:var(--mute)}
@media (max-width:860px){.ch-grid{grid-template-columns:minmax(0,1fr)}.ch-side{position:static}}

/* before / after */
.ba{position:relative;aspect-ratio:4/3;border-radius:4px;overflow:hidden;background:#ECEBE7;touch-action:pan-y;cursor:ew-resize;user-select:none;-webkit-user-select:none;--x:50%}
.ba .layer{position:absolute;inset:0}
.ba .layer>*{width:100%;height:100%}
.ba .before{clip-path:inset(0 calc(100% - var(--x)) 0 0)}
.ba .before .ph{background:#E2E1DC}
.ba .tag{position:absolute;top:14px;z-index:4;background:var(--paper);color:var(--ink);border:1px solid var(--paper);border-radius:999px;padding:7px 14px;cursor:pointer;font:inherit;font-size:.68rem;letter-spacing:.16em;transition:background .35s var(--ease),color .35s var(--ease),border-color .35s}
.ba .tag:hover{border-color:var(--ink)}
.ba .tag.on{background:var(--ink);color:var(--paper);border-color:var(--ink)}
.ba img{-webkit-user-drag:none;user-select:none;pointer-events:none}
.ba.glide .before{transition:clip-path .7s var(--ease)}.ba.glide .handle{transition:left .7s var(--ease)}
.ba .tag.b{left:14px}.ba .tag.a{right:14px}
.ba .handle{position:absolute;top:0;bottom:0;left:var(--x);width:1px;background:var(--ink);z-index:3;pointer-events:none}
.ba .knob{position:absolute;top:50%;left:50%;width:46px;height:46px;margin:-23px 0 0 -23px;border-radius:50%;background:var(--paper);border:1px solid var(--ink);display:grid;place-items:center;font-size:1.1rem}
.ba .knob .ic{width:1.3em}
.ba input{position:absolute;inset:auto 0 0 0;width:100%;opacity:0;height:1px;pointer-events:none}
.ba input:focus-visible+.handle .knob{outline:2px solid var(--oxblood);outline-offset:3px}
.ba-hint{color:var(--mute);margin-top:10px}
.ba .ph,.reel .ph{justify-content:flex-start;padding-top:14%}

/* horizontal rows */
.rowwrap{position:relative}
.row{display:grid;grid-auto-flow:column;grid-auto-columns:clamp(180px,22vw,250px);gap:clamp(12px,1.4vw,18px);overflow-x:auto;scroll-snap-type:x mandatory;scrollbar-width:none;padding-bottom:4px;overscroll-behavior-x:contain}
.row::-webkit-scrollbar{display:none}
.row>figure{scroll-snap-align:start}
.row-nav{display:flex;justify-content:space-between;align-items:center;margin-top:16px;gap:12px}
.row-nav .label{color:var(--mute)}
.row-nav .btns{display:flex;gap:8px}
.row-nav button{width:42px;height:42px;border-radius:50%;border:1px solid var(--line);background:none;color:var(--ink);cursor:pointer;font-size:.95rem;transition:background .3s,color .3s,border-color .3s}
.row-nav button:hover{background:var(--ink);color:var(--paper);border-color:var(--ink)}

.readthru a.inl{color:inherit;text-decoration:underline;text-decoration-thickness:1px;text-underline-offset:.12em;transition:color .3s}
.readthru a.inl:hover{color:var(--oxblood)}
/* reel player */
.rmodal{position:fixed;inset:0;z-index:90;background:rgba(11,11,11,.86);display:grid;place-items:center;padding:24px;opacity:0;visibility:hidden;transition:opacity .4s var(--ease),visibility 0s .4s}
.rmodal.on{opacity:1;visibility:visible;transition:opacity .4s var(--ease)}
.rmodal .rbox{position:relative;width:min(400px,92vw);height:min(720px,86vh);background:#fff;border-radius:10px;overflow:hidden}
.rmodal iframe{width:100%;height:100%;border:0;display:block}
.rmodal .rx{position:absolute;top:18px;right:22px;background:none;border:1px solid rgba(251,251,249,.4);color:var(--paper);border-radius:999px;padding:8px 16px;font:500 .78rem var(--sans);cursor:pointer}
.rmodal .rx:hover{border-color:var(--paper)}
/* reels */
.reels{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,160px),1fr));gap:clamp(14px,2vw,28px)}
.reel{text-decoration:none;display:flex;flex-direction:column;gap:14px}
.reel .play{position:absolute;left:50%;top:50%;width:58px;height:58px;margin:-29px 0 0 -29px;border-radius:50%;background:rgba(251,251,249,.94);display:grid;place-items:center;z-index:2;transition:transform .6s var(--ease),background .4s,color .4s}
.reel .play svg{width:14px;height:14px;margin-left:3px;fill:currentColor}
.reel:hover .play{transform:scale(1.12);background:var(--ink);color:var(--paper)}
.reel .rk{position:absolute;top:12px;left:12px;right:12px;z-index:2;justify-self:start;width:max-content;max-width:calc(100% - 24px);background:var(--paper);border-radius:999px;padding:7px 12px;font-size:.62rem;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.reel .ph{padding-top:28%}
.reel h3{font-size:clamp(1.7rem,2.4vw,2.2rem)}
.reel p{color:var(--ink-2);font-size:.95rem;max-width:22em}
.reel .go{font-size:.84rem;font-weight:500;margin-top:auto;display:inline-flex;gap:8px;align-items:center}
.reel .go span{transition:transform .5s var(--ease)}
.reel:hover .go span{transform:translate(3px,-3px)}
@media (max-width:860px){
  .reels{grid-auto-flow:column;grid-template-columns:none;grid-auto-columns:min(72vw,280px);overflow-x:auto;scroll-snap-type:x mandatory;scrollbar-width:none;margin-inline:calc(var(--gutter) * -1);padding-inline:var(--gutter)}
  .reels::-webkit-scrollbar{display:none}
  .reel{scroll-snap-align:start}
}

/* growth chart */
.chart{border-top:1px solid var(--line);padding-top:20px}
.chart-head{display:flex;justify-content:space-between;align-items:baseline;gap:16px;margin-bottom:18px;flex-wrap:wrap}
.chart-head h3{font-size:clamp(1.6rem,2.4vw,2.2rem)}
.chart-head .label{color:var(--mute)}
.plot{position:relative;width:100%;height:clamp(260px,34vw,420px)}
.plot svg{display:block;width:100%;height:100%;overflow:visible}
.plot .grid{stroke:var(--line);stroke-width:1}
.plot .axis{fill:var(--mute);font:500 11px var(--sans);letter-spacing:.06em}
.plot .ln{fill:none;stroke:var(--ink);stroke-width:2;stroke-linejoin:round;stroke-linecap:round}
.plot .pt{fill:var(--ink);stroke:var(--paper);stroke-width:2;transition:opacity .4s}
.plot .pt.hl{fill:var(--oxblood)}
.plot .val{fill:var(--ink);font:500 13px var(--sans);font-variant-numeric:tabular-nums}
.plot .hit{fill:transparent;cursor:pointer}
.tip{position:absolute;pointer-events:none;background:var(--ink);color:var(--paper);border-radius:6px;padding:10px 12px;font-size:.82rem;line-height:1.35;transform:translate(-50%,calc(-100% - 14px));white-space:nowrap;opacity:0;transition:opacity .2s}
.tip b{display:block;font-size:1.05rem;font-weight:500;font-variant-numeric:tabular-nums}
.tip.on{opacity:1}
.chart-note{color:var(--mute);font-size:.85rem;margin-top:14px}

/* also */
.also{list-style:none;margin:0;padding:0;display:grid;grid-template-columns:repeat(2,minmax(0,1fr));column-gap:clamp(24px,5vw,80px)}
.also li{font-family:var(--serif);font-size:clamp(1.7rem,3vw,2.8rem);line-height:1.1;padding:18px 0;border-bottom:1px solid var(--line);letter-spacing:-.01em}
@media (max-width:640px){.also{grid-template-columns:minmax(0,1fr)}}

/* partners */
.p-note{font-family:var(--serif);font-size:clamp(1.5rem,2.4vw,2.2rem);line-height:1.15;max-width:22em;margin-bottom:clamp(36px,5vw,64px)}
.partners{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));row-gap:clamp(32px,4vw,56px);gap:clamp(14px,2vw,28px)}
.partner h3{font-size:clamp(1.5rem,2vw,1.9rem);margin-top:6px}
.partner .label{color:var(--mute);display:block;margin-top:6px}
.r-11{aspect-ratio:1/1}
.partner .frame{border-radius:50%;overflow:hidden;max-width:240px}

@supports (grid-template-rows:subgrid){.partners{row-gap:clamp(44px,5vw,72px)!important}.partner{display:grid;grid-row:span 5;grid-template-rows:subgrid;row-gap:0;margin:0}.partner h3{align-self:start;margin-top:18px}.partner .label{align-self:start}.partner .about{align-self:start}.partner .bio{align-self:start}}
.partner .about{margin-top:12px;font-size:.95rem;line-height:1.55;color:var(--ink-2);max-width:24em}
.partner .bio{margin-top:12px;padding-top:12px;border-top:1px solid var(--line);font-size:.92rem;line-height:1.55;color:var(--mute);max-width:24em}
.partner .bio .label{display:block;margin:0 0 6px;color:var(--ink)}
.partners{grid-template-columns:repeat(4,minmax(0,1fr))!important}
@media (max-width:900px){.partners{grid-template-columns:repeat(2,minmax(0,1fr))!important}}
@media (max-width:600px){.partners{grid-template-columns:repeat(2,minmax(0,1fr))}}

/* quote */
.quote{max-width:56rem;margin:0 auto;text-align:center;display:flex;flex-direction:column;gap:26px;align-items:center}
.quote q{font-family:var(--serif);font-size:clamp(2rem,4.4vw,4rem);line-height:1.08;letter-spacing:-.015em;quotes:"\201C" "\201D"}
.quote .who{color:var(--mute)}
.quote.pending q{color:var(--unlit)}
.quote.pending .flag{border:1px dashed var(--unlit);color:var(--mute);border-radius:999px;padding:6px 14px}

/* next */
.next{display:block;text-decoration:none;border-top:1px solid var(--ink);padding-block:18px clamp(80px,10vw,140px)}
.next .row1{display:flex;justify-content:space-between;gap:16px}
.next .row1 .label:last-child{color:var(--mute)}
.next h2{font-family:var(--sans);font-weight:400;font-size:clamp(2.8rem,9vw,9rem);line-height:.92;letter-spacing:-.04em;margin-top:clamp(28px,4vw,56px);display:flex;align-items:center;gap:.25em;flex-wrap:wrap}
.next h2 .arr{font-size:.5em;transition:transform .6s var(--ease)}
.next:hover h2 .arr{transform:translateX(.2em)}
.next:hover h2 .t{color:var(--oxblood)}
.next h2 .t{transition:color .4s}
"""


# ---------------------------------------------------------------- helpers
def media(slug, item, ratio, cls="frame"):
    path = os.path.join(ROOT, "assets", "work", slug, item["file"])
    inner = (f'<img class="media" src="../assets/work/{slug}/{E(item["file"])}" alt="{E(item.get("alt",""))}" loading="lazy">'
             if os.path.exists(path) else
             f'<div class="ph" role="img" aria-label="{E(item.get("alt") or item.get("label",""))} (image to come)"><span class="t">{E(item.get("label","Image"))}</span><span class="f">{E(item["file"])}</span></div>')
    return f'<div class="{cls} {ratio}">{inner}</div>'

def shead(l, r=""):
    return f'<div class="shead"><span class="label">{E(l)}</span><span class="label r">{E(r)}</span></div>'

def md_links(s):
    out = E(s)
    return re.sub(r'\[([^\]]+)\]\((https?://[^)\s]+)\)', lambda m: f'<a class="inl" href="{m.group(2)}" target="_blank" rel="noopener">{m.group(1)}</a>', out)

def reel_attr(u):
    m = re.search(r'instagram\.com/(reel|p)/([A-Za-z0-9_-]+)', u or '')
    return f' data-reel="{m.group(2)}" data-kind="{m.group(1)}"' if m else ''

PLAY = '<svg viewBox="0 0 10 12" aria-hidden="true"><path d="M0 0l10 6-10 6z"/></svg>'


def chapter(slug, c, idx, layout=""):
    stacked = layout == "stacked"
    out = [f'<section class="chapter wrap{" stacked" if stacked else ""}" id="part-{idx+1}">', shead(f'Chapter {c["numeral"]}', c.get("when","")),
           '<div class="ch-grid">',
           (f'<div class="ch-head"><h2>{E(c["title"])}</h2></div>' if stacked else
            f'<div class="ch-side"><span class="ch-num" aria-hidden="true">{E(c["numeral"])}</span><h2>{E(c["title"])}</h2></div>'),
           '<div class="ch-main">',
           '<div class="ch-body">' + "".join(f"<p>{E(p)}</p>" for p in c["body"]) + '</div>']
    if c.get("deliverables"):
        out.append('<div class="delivered"><span class="label">Delivered</span>' + "".join(f'<span class="chip">{E(d)}</span>' for d in c["deliverables"]) + '</div>')
    if c.get("beforeafter"):
        b, a = c["beforeafter"]["before"], c["beforeafter"]["after"]
        bar = c["beforeafter"].get("ratio")
        out.append(f'''<div><div class="ba" data-ba{f' style="aspect-ratio:{bar};max-width:{c["beforeafter"].get("max","100%")}"' if bar else ""}>
  <div class="layer">{media(slug,a,"",cls="frame")}</div>
  <div class="layer before">{media(slug,b,"",cls="frame")}</div>
  <button type="button" class="tag b label" data-to="100">{E(b.get("label","Before"))}</button><button type="button" class="tag a label" data-to="0">{E(a.get("label","After"))}</button>
  <input type="range" min="0" max="100" value="50" aria-label="Compare before and after">
  <div class="handle"><span class="knob" aria-hidden="true">‹ ›</span></div>
</div><p class="ba-hint label">Drag to compare, or choose before or after</p></div>''')
    if c.get("stages"):
        out.append(f'<div><p class="stages-h label">{E(c.get("stages_label","The process"))}</p><div class="stages">' + "".join(
            f'<figure>{media(slug,p,"r-45")}<figcaption class="label"><b>{i+1:02d}</b>{E(p["label"])}</figcaption></figure>' for i,p in enumerate(c["stages"])) + '</div></div>')
    if c.get("showcase"):
        sc = c["showcase"]; eds = sc["editions"]; last = len(eds) - 1
        def shot(it):
            path = os.path.join(ROOT, "assets", "work", slug, it["file"])
            if os.path.exists(path):
                return f'<img src="../assets/work/{slug}/{E(it["file"])}" alt="{E(it.get("alt",""))}" loading="lazy">'
            return f'<div class="ph tall" role="img" aria-label="{E(it.get("alt",""))} (image to come)"><span class="t">{E(it.get("label",""))}</span><span class="f">{E(it["file"])}</span></div>'
        host = re.sub(r"^https?://(www\.)?", "", sc.get("url","")).rstrip("/")
        tabs = "".join(f'<button type="button" role="tab" aria-selected="{"true" if i==last else "false"}" data-ed="{i}" data-host="{E(re.sub(r"^https?://(www\\.)?", "", e.get("url", sc.get("url",""))).split("/")[0])}">{E(e["label"])}</button>' for i,e in enumerate(eds))
        shots = "".join(f'<div class="shot{" on" if i==last else ""}" data-ed="{i}">{shot(e["desktop"])}</div>' for i,e in enumerate(eds))
        phone = f'<div class="phone" aria-hidden="false"><div class="notch"></div><div class="screen"><div class="shot on">{shot(sc["mobile"])}</div></div></div>' if sc.get("mobile") else ""
        out.append(f'''<div class="showcase" data-showcase>
  <div class="browser"><div class="chrome"><span class="dots" aria-hidden="true"><i></i><i></i><i></i></span><div class="tabs" role="tablist" aria-label="Website editions">{tabs}</div></div>
  <div class="screen" tabindex="0" aria-label="Website preview, hover to explore">{shots}</div></div>
  {phone}
</div>
<div class="sc-foot"><span class="label">Hover over the screens to explore. Switch editions in the tabs.</span>{f'<a class="label" href="{E(sc["url"])}" target="_blank" rel="noopener">Visit {E(host)} ↗</a>' if sc.get("url") else ""}</div>''')
    if c.get("figure"):
        f = c["figure"]
        out.append(f'<figure class="solo">{media(slug,f,"r-54")}<figcaption class="label">{E(f.get("caption",""))}</figcaption></figure>')
    if c.get("logos"):
        out.append(f'<div><p class="stages-h label">{E(c.get("logos_label","Portfolio"))}</p><ul class="logos">' + "".join(
            f'<li class="{"hl" if l.get("hl") else ""}"><img src="../assets/work/{slug}/{E(l["file"])}" alt="{E(l["name"])}" loading="lazy"><span class="label">{E(l["name"])}</span></li>' for l in c["logos"]) + '</ul></div>')
    if c.get("roadmap"):
        out.append(f'<div><p class="stages-h label">{E(c.get("roadmap_label","The roadmap"))}</p><ol class="road" data-road><span class="fill" aria-hidden="true"></span>' + "".join(
            f'<li><span class="k label">{E(r["kicker"])}</span><h3>{E(r["title"])}</h3><p>{E(r["text"])}</p></li>' for r in c["roadmap"]) + '</ol></div>')
    if c.get("flow"):
        out.append(f'<div><p class="stages-h label">{E(c.get("flow_label","The process"))}</p><ol class="flow">' + "".join(
            f'<li><span class="n label">{i+1:02d}</span><h3>{E(f["title"])}</h3><p>{E(f["text"])}</p></li>' for i,f in enumerate(c["flow"])) + '</ol></div>')
    if c.get("related"):
        r = c["related"]; live = bool(r.get("href"))
        tag = "a" if live else "div"; attr = f' href="{E(r["href"])}"' if live else ""
        out.append(f'<{tag} class="related{" live" if live else ""}"{attr}><span class="row1"><span class="label">{E(r.get("label","Related case study"))}</span><span class="label">{E("View case study" if live else r.get("note",""))}</span></span>'
                   f'<h3>{E(r["title"])}{" <span class=arr aria-hidden=true>→</span>" if live else ""}</h3><p>{E(r.get("text",""))}</p></{tag}>')
    if c.get("pair"):
        out.append('<div class="pair">' + "".join(f'<figure>{media(slug,p,"r-45")}<figcaption class="label">{E(p["label"])}</figcaption></figure>' for p in c["pair"]) + '</div>')
    if c.get("aside"):
        out.append('<div class="aside">' + "".join(f'<div><div class="v">{E(s["value"])}</div><p class="l">{E(s["label"])}</p></div>' for s in c["aside"]) + '</div>')
    if c.get("milestone"):
        m = c["milestone"]
        out.append(f'<div class="milestone"><div class="v">{E(m["from"])}<i aria-hidden="true">→</i>{E(m["to"])}</div><p class="l">{E(m["label"])}</p></div>')
    if c.get("row"):
        rid = f"row-{idx}"
        out.append(f'<div class="rowwrap"><div class="row" id="{rid}">' + "".join(f'<figure>{media(slug,p,"r-916")}' + (f'<figcaption class="label">{E(p["label"])}</figcaption>' if p.get("label") else "") + '</figure>' for p in c["row"]) +
                   f'</div><div class="row-nav"><span class="label">Swipe to see more</span><span class="btns"><button type="button" data-row="{rid}" data-dir="-1" aria-label="Previous">←</button><button type="button" data-row="{rid}" data-dir="1" aria-label="Next">→</button></span></div></div>')
    if c.get("reels"):
        out.append('<div class="reels">' + "".join(
            f'<a class="reel" href="{E(r["url"])}" target="_blank" rel="noopener"{reel_attr(r["url"])}><div style="position:relative">{media(slug,{"file":r["file"],"label":"Reel cover","alt":r["title"]},"r-916")}<span class="rk label">{E(r["kicker"])}</span><span class="play">{PLAY}</span></div>'
            f'<h3>{E(r["title"])}</h3><p>{E(r["text"])}</p><span class="go">{"Play here" if reel_attr(r["url"]) else "Watch on Instagram"} <span>↗</span></span></a>'
            for r in c["reels"]) + '</div>')
    if c.get("chart"):
        ch = c["chart"]
        out.append(f'''<div class="chart"><div class="chart-head"><h3>{E(ch["title"])}</h3><span class="label">Tap a point for detail</span></div>
<div class="plot" data-chart='{E(json.dumps(ch))}'><div class="tip" role="status"></div></div>
<p class="chart-note">{E(ch.get("note",""))}</p></div>''')
    out.append('</div></div></section>')
    return "\n".join(out)


def build(path):
    d = json.load(open(path))
    slug = d["slug"]
    css = shared_css() + CASE_CSS

    meta_rows = [("Sector", E(d["sector"]))] + ([("Location", E(d["location"]))] if d.get("location") else []) + [("Engagement", E(d["engagement"]))] + ([("Role", E(d["role"]))] if d.get("role") else []) + [
                 ("Services", '<span class="svc">' + "".join(f"<span>{E(x)}</span>" for x in d["services"]) + '</span>')]
    if d.get("website"):
        host = re.sub(r"^https?://(www\.)?", "", d["website"]).rstrip("/")
        meta_rows.append(("Website", f'<a href="{E(d["website"])}" target="_blank" rel="noopener">{E(host)} ↗</a>'))
    meta = "".join(f"<dt class='label'>{k}</dt><dd>{v}</dd>" for k, v in meta_rows)

    body = []
    body.append(f'''<section class="c-hero wrap" id="top">
  <div class="c-top label"><span class="l"><span class="dot"></span><a href="../index.html#work">Case studies</a>&nbsp;·&nbsp;No. {E(d["number"])}</span><span>{" · ".join(E(x) for x in [d["sector"].split()[0], (d.get("location") or "").split(",")[0]] if x)}</span></div>
  <h1 class="wordmark" aria-label="{E(d["client"])}"><span class="fit" aria-hidden="true">{E(d["wordmark"])}</span></h1>
  <div class="c-intro"><p class="sum">{E(d["summary"])}</p><dl class="meta">{meta}</dl></div>
  {media(slug, d["hero"], "r-wide") if d.get("hero") else ""}
</section>''')
    g = d.get("glance")
    if g or d.get("stats"):
        blk = [f'<section class="sec wrap" id="glance">{shead(g.get("label","At a glance") if g else "In numbers", g.get("right","") if g else "")}']
        if g:
            blk.append(f'<div class="glance-grid"><p class="ov">{E(g["overview"])}</p><div class="winsbox"><span class="label">{E(g.get("wins_label","Quick wins"))}</span><ul class="wins">' +
                       "".join(f"<li>{E(w)}</li>" for w in g["wins"]) + '</ul></div></div>')
        if d.get("stats"):
            blk.append('<div class="stats">' + "".join(
                f'<div class="stat"><span class="v" data-count="{s["value"]}" data-dec="{s.get("decimals",0)}" data-prefix="{E(s.get("prefix",""))}" data-suffix="{E(s.get("suffix",""))}">{E(s.get("prefix",""))}{s["value"]}{E(s.get("suffix",""))}</span><span class="l">{E(s["label"])}</span></div>'
                for s in d["stats"]) + '</div>')
        blk.append('</section>')
        body.append("".join(blk))
    body.append(f'<section class="sec tight wrap" aria-label="{E(d["brief_label"])}">{shead(d["brief_label"], d["client"])}<p class="readthru">{md_links(d["brief"])}</p></section>')
    for i, c in enumerate(d["chapters"]):
        body.append(chapter(slug, c, i, d.get("layout","")))
    if d.get("also"):
        body.append(f'<section class="sec wrap">{shead(d.get("also_label","Also"), "Alongside")}<ul class="also">' + "".join(f"<li>{E(a)}</li>" for a in d["also"]) + '</ul></section>')
    if d.get("partners"):
        body.append(f'<section class="sec wrap">{shead(d.get("partners_label","Partners"), "In good company")}' +
                    (f'<p class="p-note">{E(d["partners_note"])}</p>' if d.get("partners_note") else "") +
                    '<div class="partners">' + "".join(f'<figure class="partner">{media(slug,{"file":p["file"],"label":"Portrait","alt":p["name"]},"r-11")}<h3>{E(p["name"])}</h3><span class="label">{E(p["role"])}{(" · " + E(p["followers"]) + " followers") if p.get("followers") else ""}</span>' + (f'<p class="about">{E(p["about"])}</p>' if p.get("about") else "") + (f'<p class="bio"><span class="label">Our work</span>{E(p["bio"])}</p>' if p.get("bio") else "") + '</figure>' for p in d["partners"]) + '</div></section>')
    q = d.get("quote") or {}
    if q.get("name"):
        if q.get("text"):
            body.append(f'<section class="sec tight wrap"><div class="quote"><q>{E(q["text"])}</q><span class="who label">{E(q["name"])} · {E(q["role"])}</span></div></section>')
        else:
            body.append(f'<section class="sec tight wrap"><div class="quote pending"><span class="flag label">Client quote to come</span><q>A few words from the client will sit here.</q><span class="who label">{E(q["name"])} · {E(q["role"])}</span></div></section>')
    cl = d.get("closing")
    if cl:
        body.append(f'<section class="sec wrap closing">{shead(cl.get("label","The result"), cl.get("right",""))}<p class="readthru">{E(cl["text"])}</p>'
                    f'<div class="closing-cta"><a class="btn solid" href="../consultation.html">Begin your own chapter <span aria-hidden="true">↗</span></a></div></section>')
    n = d.get("next")
    if n:
        body.append(f'<section class="wrap"><a class="next" href="{E(n["href"])}"><span class="row1"><span class="label">{E(n["label"])}</span><span class="label">{E(n.get("note",""))}</span></span><h2><span class="t">{E(n["title"])}</span><span class="arr" aria-hidden="true">→</span></h2></a></section>')

    page = TEMPLATE.replace("{{CSS}}", css).replace("{{TITLE}}", E(d["client"])).replace("{{DESC}}", E(d["summary"])) \
                   .replace("{{BODY}}", "\n\n".join(body)).replace("{{BODYCLASS}}", E(d.get("theme","")))
    os.makedirs(os.path.join(ROOT, "work"), exist_ok=True)
    out = os.path.join(ROOT, "work", slug + ".html")
    open(out, "w").write(iconify(page))
    return out


TEMPLATE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{{TITLE}} · REAU Studio</title>
<meta name="description" content="{{DESC}}">
<meta property="og:title" content="{{TITLE}} · REAU Studio">
<meta property="og:description" content="{{DESC}}">
<script>try{if("scrollRestoration" in history)history.scrollRestoration="manual";}catch(e){}</script>
<link rel="icon" type="image/png" sizes="32x32" href="../assets/favicon-32.png?v=3"><link rel="icon" type="image/png" sizes="512x512" href="../assets/favicon-512.png?v=3"><link rel="apple-touch-icon" href="../assets/apple-touch-icon.png?v=3">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1&family=Hanken+Grotesk:wght@400;500;600&display=swap">
<style>
{{CSS}}
</style>
</head>
<body class="{{BODYCLASS}}">
<header class="hdr">
  <div class="hdr-in wrap">
    <a class="mark" href="../index.html" aria-label="REAU Studio, home">REAU STUDIO</a>
    <nav class="nav" aria-label="Main">
      <a href="../index.html#begin">Begin</a>
      <a href="../index.html#work" aria-current="page">Case Studies</a>
      <a href="../index.html#clients">Clients</a>
      <a href="../index.html#services">Services</a>
      <a href="#inquire">Inquiries</a>
    </nav>
    <button class="menu-btn" id="menuBtn" aria-expanded="false" aria-controls="sheet">Menu</button>
  </div>
</header>
<div class="sheet" id="sheet" hidden>
  <button id="menuClose">Close</button>
  <a href="../index.html#begin">Begin</a><a href="../index.html#work">Case Studies</a><a href="../index.html#clients">Clients</a><a href="../index.html#services">Services</a><a href="#inquire">Inquiries</a>
</div>

<main>
{{BODY}}

<section class="inquire wrap" id="inquire">
  <div class="shead on-ink"><span class="label">Inquiries</span></div>
  <a class="cta-big" href="../consultation.html"><span class="t">Request a consultation</span><span class="circ" aria-hidden="true">↗</span></a>
  <div class="cta-row">
    <a class="email-link" href="mailto:hello@reaustudio.com?subject=RS%20Inquiry" id="emailText">hello@reaustudio.com</a>
  </div>
  <footer class="foot">
    <div><span class="label">Studio</span>128 City Road<br>London, UK</div>
    <div><span class="label">Follow</span><a href="https://instagram.com/reau.studio" target="_blank" rel="noopener">Instagram</a><br><a href="https://linkedin.com/in/reaustudio" target="_blank" rel="noopener">LinkedIn</a></div>
    <div><span class="label">Work with us</span><a href="../consultation.html">Request a consultation</a><br><a href="../index.html#services">Services</a></div>
    <div><span class="label">Legal</span>© <span id="yr">2026</span> REAU Studio LTD<br><a href="https://www.reaustudio.com/terms-and-privacy" target="_blank" rel="noopener">Terms &amp; privacy</a></div>
  </footer>
  <div class="bigmark"><p class="wordmark" aria-label="REAU Studio"><span class="fit">REAU STUDIO</span></p></div>
</section>
</main>

<div class="strip" aria-hidden="true"><div class="rail" id="rail"><div class="bar" id="bar"></div><div class="pos" id="stripPos"><div class="sprite" id="stripDog"></div></div></div></div>

<script>
(function(){
  document.documentElement.classList.add('js');
  if('scrollRestoration' in history)history.scrollRestoration='manual';
  if(!location.hash){
    var touched=false;['wheel','touchstart','keydown','pointerdown'].forEach(function(ev){addEventListener(ev,function(){touched=true;},{once:true,passive:true});});
    function toTop(){if(touched||scrollY===0)return;var h=document.documentElement,sb=h.style.scrollBehavior;h.style.scrollBehavior='auto';scrollTo({top:0,left:0,behavior:'instant'});h.style.scrollBehavior=sb;}
    toTop();addEventListener('DOMContentLoaded',toTop);addEventListener('load',function(){toTop();[60,250,600].forEach(function(ms){setTimeout(toTop,ms);});});
    addEventListener('pageshow',toTop);
  }
  var reduce=window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  function $(s,c){return (c||document).querySelector(s)} function $$(s,c){return [].slice.call((c||document).querySelectorAll(s))}

  // Dalmatian sprite
  function Sprite(el){
    var imgs=[];for(var i=0;i<4;i++){var im=document.createElement('img');im.src='../assets/dog-'+i+'.png';im.alt='';im.dataset.f=i;el.appendChild(im);imgs.push(im);}
    var cur=-1,timer=null,f=1;function show(n){if(n===cur)return;if(cur>=0)imgs[cur].classList.remove('on');imgs[n].classList.add('on');cur=n;}
    show(0);return{run:function(){if(reduce||timer)return;timer=setInterval(function(){show(f);f=f%3+1;},95);},stop:function(){clearInterval(timer);timer=null;show(0);}};
  }
  var rail=$('#rail'),sPos=$('#stripPos'),bar=$('#bar'),dogEl=$('#stripDog'),sd=Sprite(dogEl),idle=null,first=true,lastY=scrollY;
  function onStrip(){
    var max=document.documentElement.scrollHeight-innerHeight,p=max>0?Math.min(1,scrollY/max):0;
    sPos.style.transform='translateX('+((1-p)*(rail.clientWidth-sPos.offsetWidth))+'px)';bar.style.width=(p*100)+'%';
    if(first){first=false;return;}
    var dy=scrollY-lastY;lastY=scrollY;if(dy)dogEl.classList.toggle('rev',dy<0);
    sd.run();clearTimeout(idle);idle=setTimeout(sd.stop,160);
  }

  // Read-through
  function split(el){[].slice.call(el.childNodes).forEach(function(n){if(n.nodeType===3){var f=document.createDocumentFragment();n.textContent.split(/(\s+)/).forEach(function(t){if(!t)return;if(/^\s+$/.test(t))f.appendChild(document.createTextNode(t));else{var sp=document.createElement('span');sp.className='w';sp.textContent=t;f.appendChild(sp);}});n.parentNode.replaceChild(f,n);}else if(n.nodeType===1)split(n);});}
  var reads=$$('.readthru').map(function(el){split(el);return{el:el,w:$$('.w',el)};});
  function onRead(){reads.forEach(function(r){if(reduce){r.w.forEach(function(w){w.style.opacity=1});return;}var b=r.el.getBoundingClientRect(),start=innerHeight*.9,endTop=innerHeight*.5-b.height/2;var p=Math.max(0,Math.min(1,(start-b.top)/Math.max(1,start-endTop))),x=p*(r.w.length+1);for(var i=0;i<r.w.length;i++){var t=Math.max(0,Math.min(1,x-i));r.w[i].style.opacity=(.18+.82*t).toFixed(3);}});}

  // Wordmarks fill the width
  var marks=$$('.wordmark');
  function fitMarks(){marks.forEach(function(m){var f=$('.fit',m);m.style.fontSize='100px';var w=f.getBoundingClientRect().width;if(w)m.style.fontSize=(100*m.clientWidth/w*0.995)+'px';});}
  fitMarks();if(document.fonts&&document.fonts.ready)document.fonts.ready.then(function(){fitMarks();drawCharts();});

  // Count-ups: only for figures that start below the fold, so the page is complete at rest
  var counters=$$('[data-count]');
  if(!reduce&&'IntersectionObserver' in window){
    var io=new IntersectionObserver(function(es){es.forEach(function(e){if(!e.isIntersecting)return;io.unobserve(e.target);var el=e.target,to=+el.dataset.count,t0=null;
      function step(t){if(!t0)t0=t;var p=Math.min(1,(t-t0)/1400),dec=+el.dataset.dec||0,v=(to*(1-Math.pow(1-p,3))).toFixed(dec);el.textContent=el.dataset.prefix+v+el.dataset.suffix;if(p<1)requestAnimationFrame(step);}
      requestAnimationFrame(step);});},{threshold:.6});
    counters.forEach(function(c){if(c.getBoundingClientRect().top>innerHeight){c.textContent=c.dataset.prefix+'0'+c.dataset.suffix;io.observe(c);}});
  }

  // Before / after: drag anywhere on the image (mouse or finger); arrow keys via the slider
  $$('[data-ba]').forEach(function(ba){
    var input=$('input',ba),drag=false;
    var tags=$$('.tag',ba);
    function set(pct){pct=Math.max(0,Math.min(100,pct));ba.style.setProperty('--x',pct+'%');input.value=pct;tags.forEach(function(g){g.classList.toggle('on',(+g.dataset.to)===Math.round(pct));});}
    function fromEvt(e){var r=ba.getBoundingClientRect();set((e.clientX-r.left)/r.width*100);}
    $$('img',ba).forEach(function(i){i.draggable=false;});
    ba.addEventListener('dragstart',function(e){e.preventDefault();});
    tags.forEach(function(g){g.addEventListener('pointerdown',function(e){e.stopPropagation();});g.addEventListener('click',function(e){e.stopPropagation();ba.classList.add('glide');set(+g.dataset.to);setTimeout(function(){ba.classList.remove('glide');},750);});});
    ba.addEventListener('pointerdown',function(e){if(e.button>0)return;e.preventDefault();drag=true;ba.classList.remove('glide');ba.setPointerCapture(e.pointerId);fromEvt(e);});
    ba.addEventListener('pointermove',function(e){if(drag)fromEvt(e);});
    ba.addEventListener('pointerup',function(){drag=false;});ba.addEventListener('pointercancel',function(){drag=false;});
    ba.addEventListener('click',function(){input.focus({preventScroll:true});});
    input.addEventListener('input',function(){set(+input.value);});
  });

  // Reels: play in a lightbox using Instagram's own embed
  (function(){var rs=$$('[data-reel]');if(!rs.length)return;
    var m=document.createElement('div');m.className='rmodal';m.setAttribute('role','dialog');m.setAttribute('aria-modal','true');m.setAttribute('aria-label','Instagram reel');
    m.innerHTML='<button class="rx" type="button">Close</button><div class="rbox"></div>';document.body.appendChild(m);
    var box=$('.rbox',m),last=null;
    function close(){m.classList.remove('on');setTimeout(function(){box.innerHTML='';},400);if(last)last.focus();}
    rs.forEach(function(a){a.addEventListener('click',function(e){if(e.metaKey||e.ctrlKey)return;e.preventDefault();last=a;box.innerHTML='<iframe src="https://www.instagram.com/'+(a.dataset.kind||'reel')+'/'+a.dataset.reel+'/embed/" allow="autoplay; encrypted-media; picture-in-picture" allowfullscreen title="Instagram reel"></iframe>';m.classList.add('on');$('.rx',m).focus();});});
    $('.rx',m).addEventListener('click',close);m.addEventListener('click',function(e){if(e.target===m)close();});
    document.addEventListener('keydown',function(e){if(e.key==='Escape'&&m.classList.contains('on'))close();});
  })();

  // Swipe rows: arrow buttons
  $$('[data-row]').forEach(function(b){b.addEventListener('click',function(){var row=document.getElementById(b.dataset.row),c=row.firstElementChild;row.scrollBy({left:(+b.dataset.dir)*(c.offsetWidth+16)*2,behavior:reduce?'auto':'smooth'});});});

  // Growth chart: drawn to the container's real size; the line draws as it scrolls into view
  var charts=$$('[data-chart]');
  function fmt(n){return n>=1000?(n%1000===0?(n/1000)+'K':n.toLocaleString('en-GB')):String(n);}
  function drawCharts(){charts.forEach(function(box){
    var d=JSON.parse(box.dataset.chart),W=box.clientWidth,H=box.clientHeight,narrow=W<520;
    var L=narrow?40:56,R=narrow?28:40,T=28,B=34,ns='http://www.w3.org/2000/svg';
    var old=$('svg',box);if(old)old.remove();
    var svg=document.createElementNS(ns,'svg');svg.setAttribute('viewBox','0 0 '+W+' '+H);svg.setAttribute('role','img');
    svg.setAttribute('aria-label',d.title+': '+d.points.map(function(p){return p.label+', '+p.y.toLocaleString('en-GB')}).join('; '));
    function X(x){return L+(x/d.xmax)*(W-L-R)}function Y(y){return T+(1-y/d.ymax)*(H-T-B)}
    function el(n,a,txt){var e=document.createElementNS(ns,n);for(var k in a)e.setAttribute(k,a[k]);if(txt!=null)e.textContent=txt;svg.appendChild(e);return e;}
    var step=d.ymax/5;for(var g=0;g<=d.ymax;g+=step){el('line',{class:'grid',x1:L,x2:W-R,y1:Y(g),y2:Y(g)});el('text',{class:'axis',x:L-10,y:Y(g)+4,'text-anchor':'end'},fmt(g));}
    d.points.forEach(function(p){el('text',{class:'axis',x:X(p.x),y:H-8,'text-anchor':p.x===0?'start':(p.x===d.xmax?'end':'middle')},p.tick);});
    var path=el('path',{class:'ln',d:d.points.map(function(p,i){return(i?'L':'M')+X(p.x)+' '+Y(p.y)}).join(' ')});
    var len=path.getTotalLength();path.style.strokeDasharray=len;path.dataset.len=len;
    var tip=$('.tip',box);
    d.points.forEach(function(p,i){
      var cx=X(p.x),cy=Y(p.y),last=i===d.points.length-1;
      var c=el('circle',{class:'pt'+(last?' hl':''),cx:cx,cy:cy,r:6});c.dataset.at=p.x/d.xmax;
      var mid=i>0&&!last;var v=el('text',{class:'val',x:cx+(last?-12:(mid?12:10)),y:cy+(last?-14:(mid?20:-12)),'text-anchor':last?'end':'start'},p.y.toLocaleString('en-GB'));v.dataset.at=p.x/d.xmax;
      var hit=el('circle',{class:'hit',cx:cx,cy:cy,r:22,tabindex:0,role:'button','aria-label':p.label+': '+p.y.toLocaleString('en-GB')+' followers'});
      function show(){tip.innerHTML='<b>'+p.y.toLocaleString('en-GB')+'</b>'+p.label;tip.style.left=Math.min(W-90,Math.max(90,cx))+'px';tip.style.top=cy+'px';tip.classList.add('on');}
      function hide(){tip.classList.remove('on');}
      hit.addEventListener('mouseenter',show);hit.addEventListener('mouseleave',hide);hit.addEventListener('focus',show);hit.addEventListener('blur',hide);
      hit.addEventListener('click',function(e){e.stopPropagation();tip.classList.contains('on')&&tip.dataset.i==i?hide():show();tip.dataset.i=i;});
    });
    box.appendChild(svg);onChart();
  });}
  function onChart(){charts.forEach(function(box){var path=$('.ln',box);if(!path)return;var len=+path.dataset.len,p=1;
    if(!reduce){var r=box.getBoundingClientRect();p=Math.max(0,Math.min(1,(innerHeight*.9-r.top)/(innerHeight*.5)));}
    path.style.strokeDashoffset=len*(1-p);
    $$('.pt,.val',box).forEach(function(n){n.style.opacity=(p>=+n.dataset.at-.001)?1:0;});
  });}
  document.addEventListener('click',function(){$$('.tip').forEach(function(t){t.classList.remove('on')});});
  drawCharts();

  // Website showcase: edition tabs, and scroll the page inside the screen on hover / tap
  $$('[data-showcase]').forEach(function(sc){
    var tabs=$$('.tabs button',sc), shots=$$('.browser .shot',sc);
    tabs.forEach(function(t){t.addEventListener('click',function(){tabs.forEach(function(x){x.setAttribute('aria-selected',x===t?'true':'false')});shots.forEach(function(s){s.classList.toggle('on',s.dataset.ed===t.dataset.ed);});});});
    // Pan the screenshot through the page while hovered (tap to toggle on touch); the page itself never scrolls
    $$('.screen',sc).forEach(function(scr){
      function img(){var o=$('.shot.on img',scr)||$('.shot img',scr);return o;}
      function go(){var i=img();if(!i)return;var d=Math.max(0,i.offsetHeight-scr.clientHeight);if(reduce){i.style.transition='none';}i.style.transitionDuration=Math.min(14,Math.max(2,d/420))+'s';i.style.transform='translateY(-'+d+'px)';scr.classList.add('pan');}
      function back(){var i=img();if(!i)return;i.style.transitionDuration=Math.min(2.4,Math.max(.8,(i.offsetHeight-scr.clientHeight)/2600))+'s';i.style.transform='translateY(0)';scr.classList.remove('pan');}
      scr.addEventListener('mouseenter',go);scr.addEventListener('mouseleave',back);
      scr.addEventListener('focus',go);scr.addEventListener('blur',back);
      scr.addEventListener('click',function(e){if(matchMedia('(hover: none)').matches){scr.classList.contains('pan')?back():go();}});
    });
    tabs.forEach(function(t){t.addEventListener('click',function(){$$('.screen .shot img',sc).forEach(function(i){i.style.transitionDuration='0s';i.style.transform='translateY(0)';});$$('.screen',sc).forEach(function(x){x.classList.remove('pan')});var ad=$('.addr',sc);if(ad&&t.dataset.host)ad.textContent=t.dataset.host;});});
  });

  // Roadmap: the line fills as you scroll and each stage lights when reached
  var roads=$$('[data-road]');
  function onRoad(){roads.forEach(function(r){var b=r.getBoundingClientRect(),mid=innerHeight*.6,p=reduce?1:Math.max(0,Math.min(1,(mid-b.top)/b.height));
    r.style.setProperty('--p',p);$$('li',r).forEach(function(li){li.classList.toggle('on',reduce||li.offsetTop<=p*b.height+4);});});}

  addEventListener('load',function(){setTimeout(function(){document.documentElement.classList.add('ready');},700);});

  // Header hairline once scrolled
  var hdr=$('.hdr');function onHeader(){hdr.classList.toggle('scrolled',scrollY>10);}

  function all(){onStrip();onRead();onChart();onRoad();onHeader();}
  addEventListener('scroll',all,{passive:true});
  var rt;addEventListener('resize',function(){clearTimeout(rt);rt=setTimeout(function(){fitMarks();drawCharts();all();},120);});
  all();

  // Copy email
  var cb=$('#copyBtn');if(cb)cb.onclick=function(){function done(){cb.textContent='Copied';setTimeout(function(){cb.textContent='Copy email'},1600);}function fallback(){var r=document.createRange();r.selectNodeContents($('#emailText'));var s=getSelection();s.removeAllRanges();s.addRange(r);cb.textContent='Selected';}try{navigator.clipboard.writeText('hello@reaustudio.com').then(done,fallback);}catch(e){fallback();}};

  // Mobile menu
  var sheet=$('#sheet'),mb=$('#menuBtn');function close(){sheet.hidden=true;mb.setAttribute('aria-expanded','false');}
  mb.onclick=function(){sheet.hidden=false;mb.setAttribute('aria-expanded','true');};$('#menuClose').onclick=close;$$('a',sheet).forEach(function(a){a.addEventListener('click',close);});

  $('#yr').textContent=new Date().getFullYear();
})();
</script>
<script>
// Every link opens in a new tab, except in-page jumps, email/phone links and the site's own navigation
(function(){function go(){[].forEach.call(document.querySelectorAll('a[href]'),function(a){var h=a.getAttribute('href')||'';
  if(!h||h.charAt(0)==='#'||/^(mailto:|tel:|javascript:)/i.test(h))return;
  if(a.closest('header,.hdr,.sheet,nav'))return;
  a.target='_blank';var r=(a.getAttribute('rel')||'').split(/ +/);if(r.indexOf('noopener')<0)r.push('noopener');a.setAttribute('rel',r.join(' ').trim());});}
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',go);else go();})();
</script>
</body>
</html>
"""



# ---------------------------------------------------------------- icons
# Arrow characters render as emoji on some phones, so every arrow is drawn as a
# thin line icon that takes the colour of the text around it.
_P = 'fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"'
ICONS = {
    "↗": f'<svg class="ic" viewBox="0 0 16 16" aria-hidden="true"><path d="M4.5 11.5l7-7M6 4.5h5.5V10" {_P}/></svg>',
    "→": f'<svg class="ic" viewBox="0 0 16 16" aria-hidden="true"><path d="M2.5 8h11M9.5 4l4 4-4 4" {_P}/></svg>',
    "←": f'<svg class="ic" viewBox="0 0 16 16" aria-hidden="true"><path d="M13.5 8h-11M6.5 4l-4 4 4 4" {_P}/></svg>',
    "‹ ›": f'<svg class="ic" viewBox="0 0 24 16" aria-hidden="true"><path d="M8 4L4 8l4 4M16 4l4 4-4 4" {_P}/></svg>',
}
ICON_CSS = ".ic{display:inline-block;width:.95em;height:.95em;vertical-align:-.12em;flex:none;overflow:visible}"

def iconify(html_text):
    for ch, svg in ICONS.items():
        html_text = html_text.replace(ch, svg)
    if ".ic{display:inline-block" not in html_text and "</style>" in html_text:
        html_text = html_text.replace("</style>", ICON_CSS + "\n</style>", 1)
    return html_text

def iconify_static():
    """Clean the hand-written pages too: the home page and the journal."""
    done = []
    for f in [os.path.join(ROOT, "index.html")] + sorted(glob.glob(os.path.join(ROOT, "journal", "*.html"))):
        t = open(f, encoding="utf-8").read()
        n = iconify(t)
        if n != t:
            open(f, "w", encoding="utf-8").write(n); done.append(os.path.relpath(f, ROOT))
    return done

# ---------------------------------------------------------------- consultation form
CONSULT_CSS = r"""
.consult{padding-top:calc(var(--hdr) + clamp(48px,7vw,110px));padding-bottom:clamp(80px,10vw,150px)}
.c-intro2{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1.3fr);gap:clamp(28px,6vw,110px);align-items:start}
.c-intro2 h1{font-family:var(--sans);font-weight:400;font-size:clamp(2.8rem,6.4vw,6.2rem);line-height:.92;letter-spacing:-.04em}
.c-intro2 .lede{font-family:var(--serif);font-size:clamp(1.4rem,2.2vw,2rem);line-height:1.18;margin-top:22px;max-width:20em}
.c-intro2 .note{color:var(--mute);margin-top:22px;font-size:.95rem;max-width:26em}
.steps-bar{display:flex;gap:10px;margin-bottom:clamp(28px,4vw,44px)}
.steps-bar .s{flex:1;display:flex;flex-direction:column;gap:10px;color:var(--mute);background:none;border:0;padding:0;text-align:left;font:inherit;cursor:default}
.steps-bar .s i{display:block;height:2px;background:var(--line);position:relative;overflow:hidden}
.steps-bar .s i::after{content:"";position:absolute;inset:0;background:var(--ink);transform:scaleX(0);transform-origin:left;transition:transform .6s var(--ease)}
.steps-bar .s.done i::after,.steps-bar .s.cur i::after{transform:none}
.steps-bar .s.cur,.steps-bar .s.done{color:var(--ink)}
.step-panel{display:flex;flex-direction:column;gap:26px}
.step-panel[hidden]{display:none}
.f-row{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:22px}
.f{display:flex;flex-direction:column;gap:8px;min-width:0;border:0;margin:0;padding:0}
.f>label,.f>legend{font-size:.72rem;font-weight:500;letter-spacing:.16em;text-transform:uppercase;color:var(--ink);padding:0}
.f>label .opt,.f>legend .opt{color:var(--mute);letter-spacing:.08em;text-transform:none;font-weight:400;margin-left:6px}
.f input[type=text],.f input[type=email],.f input[type=tel],.f input[type=url],.f select,.f textarea{font:400 1.05rem var(--sans);color:var(--ink);background:transparent;border:0;border-bottom:1px solid var(--line);padding:10px 0;border-radius:0;outline:none;transition:border-color .3s;width:100%;-webkit-appearance:none;appearance:none}
.f select{background-image:linear-gradient(45deg,transparent 50%,var(--ink) 50%),linear-gradient(135deg,var(--ink) 50%,transparent 50%);background-position:calc(100% - 10px) 55%,calc(100% - 5px) 55%;background-size:5px 5px;background-repeat:no-repeat;padding-right:24px;cursor:pointer}
.f textarea{min-height:96px;resize:vertical;line-height:1.5}
.f input:focus,.f select:focus,.f textarea:focus{border-color:var(--ink)}
.f .err{color:var(--oxblood);font-size:.82rem;min-height:1em}
.f.bad input,.f.bad select,.f.bad textarea{border-color:var(--oxblood)}
.chips{display:flex;flex-wrap:wrap;gap:8px;margin-top:4px}
.chips label{position:relative;cursor:pointer}
.chips input{position:absolute;opacity:0;width:1px;height:1px}
.chips span{display:inline-block;border:1px solid var(--line);border-radius:999px;padding:9px 16px;font-size:.9rem;transition:background .3s,color .3s,border-color .3s}
.chips label:hover span{border-color:var(--ink)}
.chips input:checked+span{background:var(--ink);color:var(--paper);border-color:var(--ink)}
.chips input:focus-visible+span{outline:2px solid var(--oxblood);outline-offset:2px}
.f-nav{display:flex;justify-content:space-between;align-items:center;gap:12px;margin-top:8px;border-top:1px solid var(--line);padding-top:22px}
.f-nav .back{background:none;border:0;font:500 .88rem var(--sans);color:var(--mute);cursor:pointer;padding:10px 0}
.f-nav .back:hover{color:var(--ink)}
.f-nav .btn{cursor:pointer;font-family:var(--sans)}
.f-nav .count{color:var(--mute)}
.f-status{color:var(--oxblood);font-size:.92rem}
.thanks{display:flex;flex-direction:column;gap:22px;padding-block:clamp(20px,4vw,40px)}
.thanks h2{font-family:var(--sans);font-weight:400;font-size:clamp(2.4rem,5vw,4.4rem);line-height:.95;letter-spacing:-.035em}
.thanks p{font-family:var(--serif);font-size:clamp(1.3rem,2vw,1.8rem);line-height:1.2;max-width:24em}
.hp{position:absolute;left:-9999px}
@media (max-width:860px){.c-intro2{grid-template-columns:minmax(0,1fr)}}
@media (max-width:600px){.f-row{grid-template-columns:minmax(0,1fr)}}
"""

def chips(name, opts, kind="radio", required=False):
    req = ' required' if required and kind=="radio" else ''
    return '<div class="chips">' + "".join(
        f'<label><input type="{kind}" name="{name}" value="{E(o)}"{req if i==0 else ""}><span>{E(o)}</span></label>' for i,o in enumerate(opts)) + '</div>'

def sel(name, opts, placeholder="Select"):
    return f'<select id="{name}" name="{name}"><option value="">{placeholder}</option>' + "".join(f'<option>{E(o)}</option>' for o in opts) + '</select>'

def build_consult():
    services = ["Business Development","Brand Strategy & Positioning","Operations & Advisory","Creative Direction","AI Workflows & Automation","App Design & Platform Building"]
    form = f"""<form name="consultation" method="POST" data-netlify="true" netlify-honeypot="bot-field" id="cform" novalidate>
  <input type="hidden" name="form-name" value="consultation">
  <p class="hp"><label>Leave this empty <input name="bot-field" tabindex="-1" autocomplete="off"></label></p>
  <div class="steps-bar" aria-hidden="true">
    <span class="s cur label" data-s="0"><i></i>01 · You</span><span class="s label" data-s="1"><i></i>02 · The business</span><span class="s label" data-s="2"><i></i>03 · The brief</span>
  </div>

  <div class="step-panel" data-step="0">
    <div class="f-row">
      <div class="f"><label for="name">Full name</label><input type="text" id="name" name="name" autocomplete="name" required><span class="err"></span></div>
      <div class="f"><label for="email">Email</label><input type="email" id="email" name="email" autocomplete="email" required><span class="err"></span></div>
    </div>
    <div class="f-row">
      <div class="f"><label for="company">Company</label><input type="text" id="company" name="company" autocomplete="organization" required><span class="err"></span></div>
      <div class="f"><label for="role">Your role</label>{sel("role",["Founder / CEO","Executive leadership","Marketing","Operations","Investor","Other"])}<span class="err"></span></div>
    </div>
    <div class="f-row">
      <div class="f"><label for="website">Website or Instagram <span class="opt">optional</span></label><input type="text" id="website" name="website" autocomplete="url"><span class="err"></span></div>
      <div class="f"><label for="phone">Phone <span class="opt">optional</span></label><input type="tel" id="phone" name="phone" autocomplete="tel"><span class="err"></span></div>
    </div>
  </div>

  <div class="step-panel" data-step="1" hidden>
    <div class="f"><label for="industry">Industry</label><input type="text" id="industry" name="industry" placeholder="Medical devices, hospitality, fintech…" required><span class="err"></span></div>
    <fieldset class="f" data-group="stage"><legend>Where is the company today?</legend>{chips("stage",["Pre-launch","Early-stage startup","Growing","Established","Enterprise"],required=True)}<span class="err"></span></fieldset>
    <fieldset class="f"><legend>Team size <span class="opt">optional</span></legend>{chips("team_size",["Just me","2–10","11–50","51–200","200+"])}</fieldset>
    <div class="f"><label for="revenue">Annual revenue <span class="opt">optional</span></label>{sel("revenue",["Pre-revenue","Under $250K","$250K – $1M","$1M – $5M","$5M – $20M","$20M+","Prefer not to say"])}</div>
  </div>

  <div class="step-panel" data-step="2" hidden>
    <fieldset class="f" data-group="services"><legend>How can we help?</legend>{chips("services",services+["Not sure yet"],kind="checkbox")}<span class="err"></span></fieldset>
    <div class="f"><label for="why_now">What prompted you to reach out now?</label><textarea id="why_now" name="why_now" required></textarea><span class="err"></span></div>
    <div class="f"><label for="success">What would success look like in twelve months? <span class="opt">optional</span></label><textarea id="success" name="success"></textarea></div>
    <div class="f-row">
      <div class="f"><label for="timeline">Timeline</label>{sel("timeline",["As soon as possible","Within 1–3 months","Within 3–6 months","Exploring for now"])}<span class="err"></span></div>
      <div class="f"><label for="budget">Investment <span class="opt">optional</span></label>{sel("budget",["Under $5K","$5K – $15K","$15K – $50K","$50K+","Monthly retainer","Not yet defined"])}</div>
    </div>
    <div class="f-row">
      <div class="f"><label for="engagement">Preferred engagement <span class="opt">optional</span></label>{sel("engagement",["A defined project","An ongoing retainer","Advisory sessions","Not sure yet"])}</div>
      <div class="f"><label for="referral">How did you hear about us? <span class="opt">optional</span></label>{sel("referral",["Referral","Instagram","LinkedIn","Search","A client of yours","Other"])}</div>
    </div>
  </div>

  <div class="f-nav">
    <button type="button" class="back" id="fBack" hidden>← Back</button>
    <span class="count label" id="fCount">Step 1 of 3</span>
    <button type="button" class="btn solid" id="fNext">Continue <span aria-hidden="true">→</span></button>
  </div>
  <p class="f-status" id="fStatus" role="status" aria-live="polite"></p>
</form>
<div class="thanks" id="thanks" hidden tabindex="-1">
  <span class="label">Received</span>
  <h2>Thank you.</h2>
  <p>We read every enquiry personally. Expect a reply from us shortly, with a link to book your consultation.</p>
  <div><a class="btn" href="index.html">Back to REAU Studio</a></div>
</div>"""

    body = f"""<section class="consult wrap" id="top">
  <div class="c-intro2">
    <div>
      <span class="label" style="color:var(--mute)">Request a consultation</span>
      <h1 style="margin-top:18px">Let's begin.</h1>
      <p class="lede">A few considered questions, so our first conversation can skip the pleasantries and get straight to the good part.</p>
      <p class="note">It takes about three minutes. We reply personally with a link to book your call.</p>
    </div>
    <div>{form}</div>
  </div>
</section>"""

    js = r"""
<script>
(function(){
  var form=document.getElementById('cform'); if(!form) return;
  var panels=[].slice.call(form.querySelectorAll('.step-panel')), bars=[].slice.call(form.querySelectorAll('.steps-bar .s'));
  var back=document.getElementById('fBack'), next=document.getElementById('fNext'), count=document.getElementById('fCount'), status=document.getElementById('fStatus'), cur=0;
  function show(i){cur=i;panels.forEach(function(p,k){p.hidden=k!==i;});bars.forEach(function(b,k){b.classList.toggle('cur',k===i);b.classList.toggle('done',k<i);});
    back.hidden=i===0;count.textContent='Step '+(i+1)+' of '+panels.length;next.innerHTML=i===panels.length-1?'Send request <span aria-hidden="true">→</span>':'Continue <span aria-hidden="true">→</span>';
    status.textContent='';var t=form.getBoundingClientRect().top;if(t<0||t>innerHeight*.6)scrollTo({top:scrollY+t-110,behavior:'smooth'});}
  function msg(el,text){var f=el.closest('.f');if(!f)return;f.classList.toggle('bad',!!text);var e=f.querySelector('.err');if(e)e.textContent=text||'';}
  function check(i){var ok=true,first=null,p=panels[i];
    p.querySelectorAll('input[required],select[required],textarea[required]').forEach(function(el){
      if(el.type==='radio'){var any=p.querySelector('input[name="'+el.name+'"]:checked');msg(el,any?'':'Please choose one.');if(!any){ok=false;first=first||el;}return;}
      var v=el.value.trim(),bad=!v?'This one is needed.':(el.type==='email'&&!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v)?'Please check the email address.':'');
      msg(el,bad);if(bad){ok=false;first=first||el;}
    });
    if(i===2){var g=p.querySelector('[data-group="services"]'),any=p.querySelector('input[name="services"]:checked');msg(g.querySelector('input'),any?'':'Choose at least one, or “Not sure yet”.');if(!any){ok=false;first=first||g.querySelector('input');}}
    if(first)first.focus();return ok;}
  form.addEventListener('input',function(e){if(e.target.closest('.f.bad'))msg(e.target,'');});
  form.addEventListener('change',function(e){if(e.target.closest('.f.bad'))msg(e.target,'');});
  back.addEventListener('click',function(){show(Math.max(0,cur-1));});
  next.addEventListener('click',function(){if(!check(cur))return;if(cur<panels.length-1){show(cur+1);return;}send();});
  form.addEventListener('submit',function(e){e.preventDefault();next.click();});
  function send(){
    next.disabled=true;status.textContent='Sending…';
    var data=new URLSearchParams(new FormData(form)).toString();
    fetch('/',{method:'POST',headers:{'Content-Type':'application/x-www-form-urlencoded'},body:data}).then(function(r){
      if(!r.ok)throw new Error(r.status);
      form.hidden=true;var t=document.getElementById('thanks');t.hidden=false;t.focus();
    }).catch(function(){next.disabled=false;status.textContent='We couldn’t send this just now. Please try again, or email hello@reaustudio.com and we’ll be in touch.';});
  }
  show(0);
})();
</script>
</body>"""

    page = TEMPLATE.replace("{{CSS}}", shared_css() + CASE_CSS + CONSULT_CSS).replace("{{TITLE}}", "Request a consultation") \
        .replace("{{DESC}}", "Request a consultation with REAU Studio, a global advisory and consulting studio.") \
        .replace("{{BODY}}", body).replace("{{BODYCLASS}}", "consult-page")
    page = page.replace("../", "").replace("</body>", js, 1)
    page = page.replace('<a href="#inquire">Inquiries</a>', '<a href="index.html#inquire">Inquiries</a>')
    # the page itself is the call to action: drop the duplicate in the footer band
    page = re.sub(r'<a class="cta-big"[^>]*>.*?</a>', '', page, count=1, flags=re.S)
    open(os.path.join(ROOT, "consultation.html"), "w").write(iconify(page))
    return "consultation.html"

if __name__ == "__main__":
    for p in sorted(glob.glob(os.path.join(os.path.dirname(os.path.abspath(__file__)), "*.json"))):
        print("built", build(p))
    print("built", build_consult())
    for f in iconify_static(): print("cleaned", f)
