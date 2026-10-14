#!/usr/bin/env python3
"""Rebuild the 985x530 neofetch-style profile with automatically updated GitHub stats."""
import json, os, urllib.request
from pathlib import Path
from xml.sax.saxutils import escape
from PIL import Image,ImageOps
ROOT=Path(__file__).resolve().parent
USER='kaua-ananiass'
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
    data={'repos':person['public_repos'],'stars':sum(x['stargazers_count'] for x in repos if not x.get('fork')),'followers':person['followers'],'commits':'N/D','contributions':'N/D','loc_add':'N/D','loc_del':'N/D','loc_net':'N/D'}
    if TOKEN:
        q='query($login:String!){user(login:$login){contributionsCollection{totalCommitContributions contributionCalendar{totalContributions}}}}'
        result=api(base+'/graphql',{'query':q,'variables':{'login':USER}})
        if result.get('errors'):raise RuntimeError(str(result['errors']))
        coll=result['data']['user']['contributionsCollection']
        data['commits']=coll['totalCommitContributions']
        data['contributions']=coll['contributionCalendar']['totalContributions']
        # Count code changes authored by this user on the default branch of each
        # non-fork public repository. Same metric as the reference project:
        # added lines, removed lines, and net lines (additions - deletions).
        added=removed=0
        for repo in repos:
            if repo.get('fork') or not repo.get('default_branch') or repo.get('size',0)==0:
                continue
            cursor=None
            while True:
                query='''query($owner:String!, $name:String!, $cursor:String){repository(owner:$owner,name:$name){defaultBranchRef{target{... on Commit{history(first:100,after:$cursor){nodes{additions deletions author{user{login}}} pageInfo{hasNextPage endCursor}}}}}}}'''
                response=api(base+'/graphql',{'query':query,'variables':{'owner':USER,'name':repo['name'],'cursor':cursor}})
                if response.get('errors'):
                    raise RuntimeError('GraphQL LOC '+repr(response['errors']))
                branch=response['data']['repository']['defaultBranchRef']
                if not branch:break
                history=branch['target'].get('history')
                if not history:break
                for node in history['nodes']:
                    author=node.get('author') or {}
                    ghuser=author.get('user') or {}
                    if ghuser.get('login','').lower()==USER.lower():
                        added+=node['additions'];removed+=node['deletions']
                if not history['pageInfo']['hasNextPage']:break
                cursor=history['pageInfo']['endCursor']
        data.update(loc_add=added,loc_del=removed,loc_net=added-removed)
    return data

def ascii_portrait():
    # Frame the head, torso and bag like a portrait; never stretch the source.
    source=Image.open(ROOT/'portrait-source.jpg').convert('RGB')
    w,h=source.size
    top=round(h*0.18)
    bottom=round(h*0.70)
    crop_height=bottom-top
    # Consolas cells are narrower than their 12px line spacing. This source
    # ratio matches the displayed 51x39 grid, so the person is not stretched.
    crop_width=min(w,round(crop_height*0.74))
    left=max(0,min(w-crop_width,round(w*0.52)-crop_width//2))
    scene=source.crop((left,top,left+crop_width,bottom))
    cols,rows=51,39
    color=scene.resize((cols,rows),Image.Resampling.LANCZOS)
    # Equalization preserves shading in the dark jacket that global contrast
    # previously flattened into one solid block of @ characters.
    tone=ImageOps.equalize(scene.convert('L'))
    tone=tone.resize((cols,rows),Image.Resampling.LANCZOS)
    cells=[]
    for y in range(rows):
        line=[]
        for x in range(cols):
            r,g,b=color.getpixel((x,y))
            gray=tone.getpixel((x,y))
            nx,ny=(x+0.5)/cols,(y+0.5)/rows
            green_ground=ny>0.76 and g>r*1.12 and g>b*1.10
            blue_sky=b>90 and b>g*1.2 and b>r*1.5
            dark_figure=0.12<nx<0.83 and gray<145 and not green_ground and not blue_sky
            if dark_figure:
                kind='person'
                char='@' if gray<55 else '%' if gray<75 else '#' if gray<95 else '*' if gray<115 else '+' if gray<130 else '='
            else:
                kind='scene'
                if ny<0.76:
                    # Show only faint cloud edges, not broad bands of sky.
                    edge=max(abs(gray-tone.getpixel((max(0,x-1),y))),
                             abs(gray-tone.getpixel((x,max(0,y-1)))))
                    char='.' if gray>130 and edge>30 else ' '
                else:
                    char='.' if (x+y)%5==0 else ' '
            line.append((char,kind))
        cells.append(line)
    # Classify the original pixels within the bag, rather than averaging away
    # its narrow WinRAR-like stripes in the much smaller ASCII grid.
    bag_left,bag_right=round(w*0.490),round(w*0.598)
    bag_top,bag_bottom=round(h*0.480),round(h*0.556)
    bag_colors={'R':'bag-red','Y':'bag-yellow','B':'bag-blue','G':'bag-green'}
    pixels=source.load()
    for y in range(rows):
        y0=top+round(y*crop_height/rows)
        y1=top+round((y+1)*crop_height/rows)
        if y1<=bag_top or y0>=bag_bottom:continue
        for x in range(cols):
            x0=left+round(x*crop_width/cols)
            x1=left+round((x+1)*crop_width/cols)
            if x1<=bag_left or x0>=bag_right:continue
            counts={key:0 for key in bag_colors}
            for py in range(max(y0,bag_top),min(y1,bag_bottom)):
                for px in range(max(x0,bag_left),min(x1,bag_right)):
                    r,g,b=pixels[px,py]
                    if r>105 and g>75 and b<min(r,g)*0.82:counts['Y']+=1
                    elif r>g*1.2 and r>b*1.2 and r>70:counts['R']+=1
                    elif b>r*1.22 and b>g*1.08 and b>65:counts['B']+=1
                    elif g>r*1.16 and g>b*1.05 and g>55:counts['G']+=1
            key=max(counts,key=counts.get)
            # The yellow belt is narrower than one cell; preserve its strong
            # local signal even when adjacent red/green pixels are more numerous.
            if x<=25 and counts['Y']>=(x1-x0)*(y1-y0)*0.18 and counts['Y']>=counts[key]*0.35:
                key='Y'
            if counts[key]>=max(3,(x1-x0)*(y1-y0)*0.13):
                cells[y][x]=('#',bag_colors[key])
    # Dark clasp/folds remain visible between photo-derived colored runs.
    for line in cells:
        colored=[x for x,(_,kind) in enumerate(line) if kind in bag_colors.values()]
        if len(colored)>=2:
            for x in range(min(colored),max(colored)+1):
                if line[x][1] not in bag_colors.values():line[x]=('#','bag-shadow')
    return cells

def render(data,light=False):
    dark=not light
    bg='#161b22' if dark else '#f6f8fa'
    fg='#c9d1d9' if dark else '#24292f'
    key='#ffa657' if dark else '#953800'
    val='#a5d6ff' if dark else '#0969da'
    cc='#616e7f' if dark else '#7d8590'
    parts=[f'''<svg xmlns="http://www.w3.org/2000/svg" width="985" height="530" viewBox="0 0 985 530"><style>
    text {{font-family:Consolas, 'Liberation Mono',monospace;font-size:15px;white-space:pre;}}
    .fg {{fill:{fg}}}.key {{fill:{key}}}.value {{fill:{val}}}.cc {{fill:{cc}}}.green {{fill:#3fb950}}.red {{fill:#f85149}}
    .portrait-row {{font-size:11px;letter-spacing:0}}
    .scene {{fill:{'#596777' if dark else '#a8b0b9'}}}.person {{fill:{fg}}}
    .bag-red {{fill:#bd4b71}}.bag-yellow {{fill:#e5c45b}}.bag-blue {{fill:#4b70b9}}.bag-green {{fill:#3ba36b}}
    .bag-shadow {{fill:{'#71808f' if dark else '#66727f'}}}
    </style><rect width="985" height="530" rx="15" fill="{bg}"/>''']
    # Large portrait frame, close to the height of the reference profile.
    frame='#30363d' if dark else '#d0d7de'
    shade='#0d1117' if dark else '#ffffff'
    parts.append(f'<rect x="14" y="18" width="360" height="494" rx="9" fill="{shade}" stroke="{frame}" stroke-width="1.3"/>')
    for i,line in enumerate(ascii_portrait()):
        runs=[]
        for char,kind in line:
            if runs and runs[-1][0]==kind:runs[-1]=(kind,runs[-1][1]+char)
            else:runs.append((kind,char))
        spans=''.join(f'<tspan class="{kind}">{escape(chars)}</tspan>' for kind,chars in runs)
        parts.append(f'<text x="25" y="40" dy="{i*12.1:.1f}" class="portrait-row">{spans}</text>')
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
    t(390,450,'- GitHub Stats ------------------------------------------------')
    def v(k):
        value=data.get(k,'N/D')
        return f'{value:,}' if isinstance(value,int) else str(value)
    # Match original label, dotted spacer and right-hand grouping, including
    # an authentic green additions / red deletions pair on the third line.
    parts.append(f'<text x="390" y="470"><tspan class="cc">. </tspan><tspan class="key">Repos</tspan><tspan class="fg">: </tspan><tspan class="cc">.... </tspan><tspan class="value">{escape(v("repos"))}</tspan><tspan class="fg"> {{</tspan><tspan class="key">Contributed</tspan><tspan class="fg">: </tspan><tspan class="value">{escape(v("contributions"))}</tspan><tspan class="fg">}} | </tspan><tspan class="key">Stars</tspan><tspan class="fg">: </tspan><tspan class="cc">........ </tspan><tspan class="value">{escape(v("stars"))}</tspan></text>')
    parts.append(f'<text x="390" y="490"><tspan class="cc">. </tspan><tspan class="key">Commits</tspan><tspan class="fg">: </tspan><tspan class="cc">.............. </tspan><tspan class="value">{escape(v("commits"))}</tspan><tspan class="fg"> | </tspan><tspan class="key">Followers</tspan><tspan class="fg">: </tspan><tspan class="cc">....... </tspan><tspan class="value">{escape(v("followers"))}</tspan></text>')
    parts.append(f'<text x="390" y="510"><tspan class="cc">. </tspan><tspan class="key">Lines of Code on GitHub</tspan><tspan class="fg">: </tspan><tspan class="value">{escape(v("loc_net"))}</tspan><tspan class="fg"> ( </tspan><tspan class="green">{escape(v("loc_add"))}++</tspan><tspan class="fg">,  </tspan><tspan class="red">{escape(v("loc_del"))}--</tspan><tspan class="fg"> )</tspan></text>')
    parts.append('</svg>')
    (ROOT/('light_mode.svg' if light else 'dark_mode.svg')).write_text('\n'.join(parts),encoding='utf-8')

if __name__=='__main__':
    # Offline preview: don't replace real stats when GitHub API isn't available.
    if os.getenv('PREVIEW')=='1':
        numbers={'repos':3,'stars':1,'followers':1,'commits':31,'contributions':338,'loc_net':'N/D','loc_add':'N/D','loc_del':'N/D'}
    else:numbers=stats()
    render(numbers,False);render(numbers,True)
    print(numbers)
