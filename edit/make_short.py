import subprocess, os
from PIL import Image, ImageDraw, ImageFilter
S='/tmp/claude-0/-home-user-Video-editing/4d7dc574-3fc0-580b-80b9-20581d59e953/scratchpad'
B=S+'/build'; V='/root/.claude/uploads/4d7dc574-3fc0-580b-80b9-20581d59e953/52af61d8-v26044gc0000d9dk6v7og65g9v9l5ta0.mp4'
OUT='/home/user/Video-editing/stroopwafel_short.mp4'
W,H=576,1024
WM_R=(0.82,0.75,1.0,0.87)   # TikTok watermark bottom-right (x0,y0,x1,y1 fractions)
WM_L=(0.0,0.44,0.17,0.56)   # watermark at left in the opening shot
# (start, end, caption boxes, transition INTO next, step label, title)
segs=[
 (0,3,    [(0.04,0.26,0.96,0.39),WM_L], 'fade',       None,  None),
 (5.5,10, [(0.15,0.24,0.85,0.32),WM_R], 'smoothleft', '01', 'Cut into a perfect circle'),
 (15,18,  [(0.15,0.19,0.85,0.27),WM_R], 'fade',       '02', 'Sliced in half'),
 (23,28.5,[(0.20,0.22,0.85,0.30),WM_R], 'smoothleft', '03', 'Warm caramel filling'),
 (30,33,  [(0.08,0.27,0.92,0.35),WM_R], 'fade',       '04', 'Sealed back together'),
 (44,50,  [(0.20,0.17,0.80,0.25),WM_R], 'smoothup',   '05', 'Dipped in chocolate'),
 (57.5,61,[(0.20,0.21,0.80,0.30),WM_R], 'fade',       '06', 'Choose your topping'),
 (65,70,  [(0.25,0.26,0.75,0.34),WM_R], 'smoothleft', '07', 'Biscoff crumble'),
 (80,88.5,[(0.18,0.18,0.85,0.37),WM_R], None,         '08', 'Boxed with care'),
]
D=0.5
# masks: white = blur. feathered edges
for i,(a,b,boxes,*_) in enumerate(segs):
    m=Image.new('L',(W,H),0); d=ImageDraw.Draw(m)
    for x0,y0,x1,y1 in boxes: d.rounded_rectangle([x0*W,y0*H,x1*W,y1*H],radius=18,fill=255)
    m=m.filter(ImageFilter.GaussianBlur(10)); m.convert('RGB').save(f'{B}/mask{i}.png')
# top/bottom gradient for legibility
g=Image.new('RGBA',(W,H),(0,0,0,0)); px=g.load()
for y in range(H):
    t=y/H; a=0
    if t<0.24: a=int(150*(1-t/0.24)**1.6)
    if t>0.86: a=int(90*((t-0.86)/0.14)**1.5)
    for x in range(W): px[x,y]=(0,0,0,a)
g.save(f'{B}/grad.png')
# timeline
lens=[b-a for a,b,*_ in segs]; starts=[0.0]; 
for k in range(1,len(segs)): starts.append(starts[-1]+lens[k-1]-D)
TOT=starts[-1]+lens[-1]
inputs=['-i',V]+sum([['-loop','1','-i',f'{B}/mask{i}.png'] for i in range(len(segs))],[])+['-loop','1','-i',f'{B}/grad.png']
gi=len(segs)+1
fc=[]
for i,(a,b,*_) in enumerate(segs):
    L=b-a
    fc.append(f'[0:v]trim={a}:{b},setpts=PTS-STARTPTS,fps=30,format=yuv420p,split[o{i}][c{i}];'
              f'[c{i}]gblur=sigma=22[bl{i}];[{i+1}:v]trim=0:{L},format=gray,setpts=PTS-STARTPTS[m{i}];'
              f'[bl{i}][m{i}]alphamerge[ba{i}];[o{i}][ba{i}]overlay=shortest=1,format=yuv420p,settb=1/30[s{i}]')
prev='s0'
for k in range(1,len(segs)):
    tr=segs[k-1][3]; off=starts[k]
    fc.append(f'[{prev}][s{k}]xfade=transition={tr}:duration={D}:offset={off:.3f}[x{k}]'); prev=f'x{k}'
ass=f'{B}/titles.ass'
fc.append(f'[{prev}]eq=contrast=1.05:saturation=1.08[cg];[{gi}:v]format=rgba,trim=0:{TOT},setpts=PTS-STARTPTS[gr];[cg][gr]overlay=shortest=1,'
          f"subtitles={ass}:fontsdir={S}/ttf,fade=t=in:d=0.4,fade=t=out:st={TOT-0.7:.2f}:d=0.7,format=yuv420p[v]")
fc.append(f'[0:a]atrim=0:{TOT},asetpts=PTS-STARTPTS,afade=t=in:d=0.3,afade=t=out:st={TOT-1.5}:d=1.5[a]')
# ASS titles
def ts(t):
    t=max(t,0); h=int(t//3600); m=int(t%3600//60); s=t%60; return f'{h}:{m:02d}:{s:05.2f}'
ev=[]
cx=W//2
def add(style,t0,t1,y,text,fad=(350,300),dy=14):
    ev.append(f'Dialogue: 0,{ts(t0)},{ts(t1)},{style},,0,0,0,,{{\\an5\\fad({fad[0]},{fad[1]})\\move({cx},{y+dy},{cx},{y},0,450)}}{text}')
# intro
add('Kicker',0.35,starts[1]+0.1,300,'F R E S H L Y   M A D E')
add('Big',0.55,starts[1]+0.1,355,'Our Stroopwafels')
add('Rule',0.75,starts[1]+0.1,405,'—  step by step  —')
for k in range(1,len(segs)):
    n,title=segs[k][4],segs[k][5]
    t0=starts[k]+D*0.7; t1=starts[k]+lens[k]-(D*0.6 if k<len(segs)-1 else 0)
    if k==len(segs)-1: t1=starts[k]+3.6
    add('Kicker',t0,t1,90,f'S T E P   {n}')
    add('Title',t0+0.12,t1,136,title)
end0=starts[-1]+4.0
add('Big',end0,TOT,338,'Enjoy!',fad=(450,600))
add('Kicker',end0+0.25,TOT,390,'M A D E   F R E S H ,   J U S T   F O R   Y O U',fad=(450,600))
hdr=f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Kicker,Montserrat Thin ExtraBold,23,&H006AC4F0,&H000000FF,&H00000000,&H90000000,0,0,0,0,100,100,1,0,1,0,2,5,20,20,20,1
Style: Title,Playfair Display,44,&H00FFFFFF,&H000000FF,&H00000000,&H80000000,-1,-1,0,0,100,100,0,0,1,0,3,5,20,20,20,1
Style: Big,Playfair Display,64,&H00FFFFFF,&H000000FF,&H00000000,&H80000000,-1,-1,0,0,100,100,0,0,1,0,4,5,20,20,20,1
Style: Rule,Montserrat Thin Medium,20,&H00E6F0F5,&H000000FF,&H00000000,&H90000000,0,0,0,0,100,100,1,0,1,0,2,5,20,20,20,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
open(ass,'w').write(hdr+'\n'.join(ev)+'\n')
print('total',TOT,'starts',[round(s,2) for s in starts])
cmd=['ffmpeg','-v','error','-y',*inputs,'-filter_complex',';'.join(fc),'-map','[v]','-map','[a]','-c:v','libx264','-crf','19','-preset','medium','-pix_fmt','yuv420p','-r','30','-c:a','aac','-b:a','160k','-movflags','+faststart',OUT]
subprocess.run(cmd,check=True)
