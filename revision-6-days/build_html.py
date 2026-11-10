import markdown, re, pathlib
here = pathlib.Path(__file__).parent
parts = [("plan","6-Day Plan","01-Daily-Plan.md"),
         ("pairs","Decision Pairs","03-Top-Decision-Pairs.md"),
         ("cards","All Pocket Cards","02-All-Pocket-Cards.md"),
         ("traps","Exam Traps","../topic-guides/36-Exam-Traps-KeyPatterns.md"),
         ("rules","Rules & Technique","00-README.md")]
def conv(p):
    t = (here/p).read_text()
    html = markdown.markdown(t, extensions=["tables","fenced_code"])
    html = re.sub(r'href="(?:\.\./topic-guides/|\.\./)?[^"]*\.md"', 'href="#"', html)
    return html
tabs = "".join(f'<button data-t="{i}">{n}</button>' for i,n,_ in parts)
secs = "".join(f'<section id="{i}">{conv(p)}</section>' for i,_,p in parts)
page = f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>AWS SAA-C03 — 6-Day Crash Revision</title>
<style>
:root{{--bg:#fff;--fg:#1d2433;--mut:#5b6678;--acc:#ff9900;--card:#f6f8fb;--bd:#d9dfe8}}
@media(prefers-color-scheme:dark){{:root{{--bg:#12161f;--fg:#e6eaf2;--mut:#9aa6ba;--card:#1b2130;--bd:#2c3446}}}}
body{{margin:0;background:var(--bg);color:var(--fg);font:16px/1.6 system-ui,sans-serif}}
header{{position:sticky;top:0;background:var(--bg);border-bottom:2px solid var(--acc);padding:10px 16px;z-index:5}}
h1.t{{margin:0 0 8px;font-size:18px}}
nav button{{margin:2px 4px 2px 0;padding:6px 12px;border:1px solid var(--bd);background:var(--card);color:var(--fg);border-radius:6px;cursor:pointer}}
nav button.on{{background:var(--acc);color:#000;border-color:var(--acc)}}
#q{{margin-top:6px;width:100%;max-width:420px;padding:7px 10px;border:1px solid var(--bd);border-radius:6px;background:var(--card);color:var(--fg)}}
main{{max-width:960px;margin:0 auto;padding:16px}}
section{{display:none}}section.on{{display:block}}
table{{border-collapse:collapse;width:100%;margin:12px 0;font-size:15px}}
th,td{{border:1px solid var(--bd);padding:6px 10px;text-align:left;vertical-align:top}}
th{{background:var(--card)}}tr:nth-child(even) td{{background:var(--card)}}
tr.hide,li.hide{{display:none}}
h1,h2{{border-bottom:1px solid var(--bd);padding-bottom:4px}}h2{{color:var(--acc)}}
blockquote{{margin:8px 0;padding:6px 12px;border-left:4px solid var(--acc);background:var(--card);color:var(--mut)}}
code{{background:var(--card);padding:1px 4px;border-radius:3px}}
li input{{margin-right:6px}}
@media print{{header{{display:none}}section{{display:block!important}}}}
</style></head><body>
<header><h1 class="t">AWS SAA-C03 — 6-Day Crash Revision</h1><nav>{tabs}</nav>
<input id="q" type="search" placeholder="Filter rows (e.g. NACL, Glacier, FIPS)…"></header>
<main>{secs}</main>
<script>
const S=[...document.querySelectorAll('section')],B=[...document.querySelectorAll('nav button')];
function show(i){{S.forEach((s,k)=>s.classList.toggle('on',k==i));B.forEach((b,k)=>b.classList.toggle('on',k==i));localStorage.t=i;scrollTo(0,0)}}
B.forEach((b,i)=>b.onclick=()=>show(i));show(+localStorage.t||0);
document.querySelectorAll('#plan li').forEach((li,n)=>{{const c=document.createElement('input');c.type='checkbox';const k='c'+n;c.checked=localStorage[k]=='1';c.onchange=()=>localStorage[k]=c.checked?'1':'0';li.prepend(c)}});
q.oninput=()=>{{const v=q.value.toLowerCase();document.querySelectorAll('tbody tr').forEach(r=>r.classList.toggle('hide',v&&!r.textContent.toLowerCase().includes(v)))}};
</script></body></html>"""
(here/"index.html").write_text(page)
