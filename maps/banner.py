import sys
from PIL import Image, ImageDraw, ImageFont
K="/home/claude/sohyun-blog-kit/fonts/Pretendard-"; f=lambda w,s: ImageFont.truetype(K+w+".otf",s)
W,H,S=1080,360,3
im=Image.new("RGB",(W*S,H*S),(12,82,48)); d=ImageDraw.Draw(im)
d.ellipse((W*S-330*S,-120*S,W*S+120*S,330*S),fill=(30,145,80))
d.ellipse((W*S-170*S,210*S,W*S-60*S,320*S),fill=(224,86,59))
d.ellipse((W*S-250*S,250*S,W*S-200*S,300*S),fill=(255,194,77))
d.rounded_rectangle((64*S,58*S,64*S+d.textlength(sys.argv[1],font=f("Bold",26*S))+44*S,108*S),radius=25*S,fill=(205,238,92))
d.text((86*S,83*S),sys.argv[1],font=f("Bold",26*S),fill=(12,82,48),anchor="lm")
d.text((64*S,150*S),sys.argv[2],font=f("ExtraBold",54*S),fill=(251,255,246))
d.text((64*S,238*S),sys.argv[3],font=f("Medium",28*S),fill=(205,238,92))
im.resize((W,H),Image.LANCZOS).save(sys.argv[4],quality=92)
