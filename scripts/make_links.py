import os

GREEN = '#1fdf20'
FONT = 'ui-monospace,SFMono-Regular,Menlo,Consolas,monospace'

def make_link_svg(text, filename):
    w = int(len(text) * 7.8 + 6)
    h = 18
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
           f'viewBox="0 0 {w} {h}" font-family="{FONT}">'
           f'<text x="2" y="14" font-size="13" font-weight="700" fill="{GREEN}">{text}</text>'
           f'</svg>')
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(svg)
    print(f'wrote {filename}')

links = [
    ('TARS-Desktop-AI-Agent', 'link-tars.svg'),
    ('Maya', 'link-maya.svg'),
    ('ASCII_PORTRAIT', 'link-ascii.svg'),
    ('github', 'link-github.svg'),
]
for text, fname in links:
    make_link_svg(text, fname)
