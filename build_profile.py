#!/usr/bin/env python3
"""Update SVG profile stats with GitHub public REST and GraphQL APIs."""
import json, os, urllib.request, urllib.error
from datetime import datetime, timedelta, timezone
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parent
USERNAME=os.getenv('GITHUB_USERNAME','kaua-ananiass')
TOKEN=os.getenv('GH_TOKEN') or os.getenv('GITHUB_TOKEN','')
SVGNS='http://www.w3.org/2000/svg'
ET.register_namespace('', SVGNS)

def api(path, method='GET', body=None):
    headers={'Accept':'application/vnd.github+json','User-Agent':'profile-readme-kaua','X-GitHub-Api-Version':'2022-11-28'}
    if TOKEN: headers['Authorization']='Bearer '+TOKEN
    data=json.dumps(body).encode() if body else None
    if data: headers['Content-Type']='application/json'
    with urllib.request.urlopen(urllib.request.Request('https://api.github.com'+path, data=data,headers=headers,method=method),timeout=25) as resp:
        return json.load(resp)

def statistics():
    user=api('/users/'+USERNAME)
    repos=[]
    for page in range(1,21):
        chunk=api(f'/users/{USERNAME}/repos?per_page=100&page={page}&type=owner')
        repos+=chunk
        if len(chunk)<100: break
    owned=[r for r in repos if not r.get('fork') and r.get('owner',{}).get('login','').lower()==USERNAME.lower()]
    result={'repos':user['public_repos'],'followers':user['followers'],'stars':sum(r['stargazers_count'] for r in owned), 'commits':None,'contributions':None}
    if TOKEN:
        try:
            now=datetime.now(timezone.utc).replace(microsecond=0)
            query='query($name:String!,$from:DateTime!,$to:DateTime!){user(login:$name){contributionsCollection(from:$from,to:$to){totalCommitContributions contributionCalendar{totalContributions}}}}'
            answer=api('/graphql', 'POST', {'query':query,'variables':{'name':USERNAME,'from':(now-timedelta(days=365)).isoformat().replace('+00:00','Z'),'to':now.isoformat().replace('+00:00','Z')}})
            if answer.get('errors'): raise ValueError(answer['errors'])
            collection=answer['data']['user']['contributionsCollection']
            result['commits']=collection['totalCommitContributions']
            result['contributions']=collection['contributionCalendar']['totalContributions']
        except (KeyError, ValueError, urllib.error.URLError) as exc:
            print('GraphQL contributions unavailable:',str(exc)[:200])
    return result

def make_svg(stats,light=False):
    tree=ET.parse(ROOT/'perfil-terminal.svg')
    svg=tree.getroot()
    svg.set('height','875'); svg.set('viewBox','0 0 1260 875')
    rects=svg.findall('{'+SVGNS+'}rect')
    rects[0].set('height','875')
    rects[1].set('height','827')
    rects[2].set('height','785')
    if light:
        rects[0].set('fill','#f6f8fa');rects[1].set('fill','#ffffff');rects[1].set('stroke','#d0d7de');rects[2].set('fill','#f6f8fa')
        style=svg.find('{'+SVGNS+'}style')
        style.text=(style.text or '').replace('#9dd5ff','#0969da').replace('#ffffff','#24292f').replace('#ff9736','#bc4c00').replace('#9ed2ff','#0969da').replace('#7d8590','#57606a').replace('#8b949e','#57606a')
    def add_text(x,y,content,cls,identifier=None):
        attrib={'x':str(x),'y':str(y),'class':cls}
        if identifier: attrib['id']=identifier
        ET.SubElement(svg,'{'+SVGNS+'}text',attrib).text=content
    ET.SubElement(svg,'{'+SVGNS+'}path',{'d':'M660 700 H1180','stroke':'#303b47','stroke-dasharray':'4 6'})
    add_text(660,725,'- GitHub Stats  (atualizado automaticamente)','line')
    add_text(660,758,'· Repositórios públicos','key')
    add_text(920,758,str(stats['repos']),'value','github_repos')
    add_text(660,783,'· Estrelas recebidas','key')
    add_text(920,783,str(stats['stars']),'value','github_stars')
    add_text(660,808,'· Seguidores','key')
    add_text(920,808,str(stats['followers']),'value','github_followers')
    add_text(660,833,'· Commits (último ano)','key')
    add_text(920,833,str(stats['commits']) if stats['commits'] is not None else 'Indisponível','value','github_commits')
    add_text(660,858,'· Contribuições (último ano)','key')
    add_text(920,858,str(stats['contributions']) if stats['contributions'] is not None else 'Indisponível','value','github_contributions')
    tree.write(ROOT/('light_mode.svg' if light else 'dark_mode.svg'), encoding='unicode',xml_declaration=True)

if __name__=='__main__':
    try: numbers=statistics()
    except (OSError,ValueError,KeyError) as exc:
        raise SystemExit('Não foi possível consultar o GitHub: '+str(exc))
    make_svg(numbers)
    make_svg(numbers,True)
    print('Generated dark_mode.svg and light_mode.svg:', numbers)
