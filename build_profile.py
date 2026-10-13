#!/usr/bin/env python3
"""Rebuild the 985x530 neofetch-style profile with automatically updated GitHub stats."""
import json, os, urllib.request
from pathlib import Path
from xml.sax.saxutils import escape
from PIL import Image,ImageOps,ImageEnhance,ImageFilter
ROOT=Path(__file__).resolve().parent
USER=os.getenv('GITHUB_USERNAME','kaua-ananiass')
TOKEN=os.getenv('GH_TOKEN') or os.getenv('GITHUB_TOKEN','')

def api(url,payload=None):
    headers={'Accept':'application/vnd.github+json','User-Agent':'kaua-profile-readme','X-GitHub-Api-Version':'2022-11-28'}
    if TOKEN: headers['Authorization']='Bearer '+TOKEN
    data=json.dumps(payload).encode() if payload is not None else None
    if data: headers['Content-Type']='application/json'
    req=urllib.request.Request(url,headers=headers,data=data)
    with urllib.request.urlopen(req,timeout=25) as r:return json.load(r)

def stats():
    base='https://api.github.com'
    person=api(base+'/users/'+USER)
    repos=[]
    for n in range(1,21):
        part=api(f'{base}/users/{USER}/repos?per_page=100&page={n}&type=owner')
        repos.extend(part)
        if len(part)<100:break
    data={'repos':person['public_repos'],'stars':sum(x['stargazers_count'] for x in repos if not x.get('fork')),'followers':person['followers'],'commits':'N/D','contributions':'N/D'}
    if TOKEN:
        q='query($login:String!){user(login:$login){contributionsCollection{totalCommitContributions contributionCalendar{totalContributions}}}}'
        result=api(base+'/graphql',{'query':q,'variables':{'login':USER}})
        if result.get('errors'):raise RuntimeError(str(result['errors']))
        coll=result['data']['user']['contributionsCollection']
        data['commits']=coll['totalCommitContributions']
        data['contributions']=coll['contributionCalendar']['totalContributions']
    return data

def ascii_portrait():
    path=ROOT/'portrait-source.jpg'
    im=Image.open(path).convert('L')
    # Close portrait crop, avoiding the largely empty mirror and wall.
    im=im.crop((275,405,858,1145))
    im=ImageOps.autocontrast(im,cutoff=3)
    im=ImageEnhance.Contrast(im).enhance(1.65)
    im=im.resize((46,26),Image.Resampling.LANCZOS)
    ramp='@%#*+=-:.  '
    return [''.join(ramp[min(len(ramp)-1,int(p)*len(ramp)//256)] for p in list(im.crop((0,y,46,y+1)).getdata())) for y in range(26)]

def render(data,light=False):
    dark=not light
    bg='#161b22' if dark else '#f6f8fa'
    fg='#c9d1d9' if dark else '#24292f'
    key='#ffa657' if dark else '#953800'
    val='#a5d6ff' if dark else '#0969da'
    cc='#616e7f' if dark else '#7d8590'
    parts=[f'''<svg xmlns="http://www.w3.org/2000/svg" width="985" height="530" viewBox="0 0 985 530"><style>
    text {{font-family:Consolas, 'Liberation Mono',monospace;font-size:15px;white-space:pre;}}
    .fg {{fill:{fg}}}.key {{fill:{key}}}.value {{fill:{val}}}.cc {{fill:{cc}}}
    </style><rect width="985" height="530" rx="15" fill="{bg}"/>''']
    for i,line in enumerate(ascii_portrait()):
        parts.append(f'<text x="15" y="{30+i*19}" class="fg">{escape(line)}</text>')
    def t(x,y,s,c='fg',id=None):
        att=f' id="{id}"' if id else ''
        parts.append(f'<text x="{x}" y="{y}" class="{c}"{att}>{escape(str(s))}</text>')
    # Original's right column x=390, text rows with 20px cadence.
    t(390,30,'kaua@ananiass ----------------------------------------------')
    def field(y,label,value):
        # End-aligned values: fixed width of 59 monospace cells from x=390.
        left='. '+label+': '
        room=60-len(left)-len(str(value))
        if room<2:room=2
        dot='.'*room+' '
        t(390,y,'. ','cc')
        # single text line with coloured spans and spaces preserving original styling
        parts.append(f'<text x="409" y="{y}"><tspan class="key">{escape(label)}</tspan><tspan class="fg">:</tspan><tspan class="cc"> {escape(dot)}</tspan><tspan class="value">{escape(str(value))}</tspan></text>')
    field(50,'OS','Windows')
    field(70,'Focus','Desktop Development, Automation')
    field(90,'Host','FlowDetect')
    field(110,'Kernel','Visual Automation, OCR')
    field(130,'IDE','VS Code, GitHub')
    field(170,'Languages.Programming','Python, JavaScript, Rust')
    field(190,'Languages.Computer','HTML, CSS')
    field(210,'Frameworks','Tauri, OpenCV')
    field(250,'Projects.Software','FlowDetect, Duka Gamedev')
    field(270,'Interests.Software','Desktop Apps, Visual Workflows')
    t(390,310,'- Contact -------------------------------------------------')
    field(330,'GitHub','github.com/kaua-ananiass')
    field(350,'Instagram','@kaua_ananiass')
    field(370,'Project','FlowDetect')
    field(390,'GameDev','Duka Gamedev / itch.io')
    t(390,450,'- GitHub Stats --------------------------------------------')
    def v(k):return str(data.get(k,'--'))
    # Fit in right column without clipping; custom right-hand groups mimic original.
    parts.append(f'<text x="390" y="470"><tspan class="cc">. </tspan><tspan class="key">Repos</tspan><tspan class="fg">: </tspan><tspan class="cc">.... </tspan><tspan class="value">{escape(v("repos"))}</tspan><tspan class="fg"> {{</tspan><tspan class="key">Contributions</tspan><tspan class="fg">: </tspan><tspan class="value">{escape(v("contributions"))}</tspan><tspan class="fg">}} | </tspan><tspan class="key">Stars</tspan><tspan class="fg">: </tspan><tspan class="cc">....... </tspan><tspan class="value">{escape(v("stars"))}</tspan></text>')
    parts.append(f'<text x="390" y="490"><tspan class="cc">. </tspan><tspan class="key">Commits (year)</tspan><tspan class="fg">: </tspan><tspan class="cc">........... </tspan><tspan class="value">{escape(v("commits"))}</tspan><tspan class="fg"> | </tspan><tspan class="key">Followers</tspan><tspan class="fg">: </tspan><tspan class="cc">......... </tspan><tspan class="value">{escape(v("followers"))}</tspan></text>')
    t(390,510,'- Automatically refreshed via GitHub Actions','cc')
    parts.append('</svg>')
    (ROOT/('light_mode.svg' if light else 'dark_mode.svg')).write_text('\n'.join(parts),encoding='utf-8')

if __name__=='__main__':
    # Offline preview: don't replace real stats when GitHub API isn't available.
    if os.getenv('PREVIEW')=='1':
        numbers={'repos':3,'stars':1,'followers':1,'commits':31,'contributions':338}
    else:numbers=stats()
    render(numbers,False);render(numbers,True)
    print(numbers)
